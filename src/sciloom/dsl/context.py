"""Shared state and symbol/source identity for lowering one Function."""

from __future__ import annotations

import ast
import inspect
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, NoReturn, cast

from sciloom.core.diagnostics import Diagnostic, IRValidationError, SourceSpan
from sciloom.core.ir import DeviceResource, DeviceTypeContract, Expression, FunctionIR, Reference, ValueType
from sciloom.core.ir.expressions import ExpressionChecker
from sciloom.core.ir.model import Node
from sciloom.devices.base import BaseDevice
from sciloom.devices.declarations import device_contract
from sciloom.flow.device_slots import DeviceReference
from sciloom.flow.function import Function
from sciloom.units import SpeedUnit

_MISSING = object()


@dataclass
class ProgramScope:
    """Accumulators every function lowered into one program shares.

    Attributes:
        paths: Host composition path of each composed Function, by identity.
        instances: Worklist of Function instances discovered so far.
        ids: Function identifier of each discovered instance, by identity.
        resources: Logical device resources interned across the program.
        device_types: Device contracts recorded for the program, by type ID.
    """

    paths: dict[int, str]
    instances: list[Function] = field(default_factory=list)
    ids: dict[int, str] = field(default_factory=dict)
    resources: dict[str, DeviceResource] = field(default_factory=dict)
    device_types: dict[str, DeviceTypeContract] = field(default_factory=dict)


@dataclass(frozen=True, kw_only=True)
class RuntimeSource:
    """What the analysis learns from one registered runtime method.

    Attributes:
        filename: Path of the .py file defining the method.
        static_names: Globals and closure bindings visible to the method.
        unit_names: Physical quantity units bound in the defining module.
        allows_len: Whether len still resolves to the builtin.
    """

    filename: str = ""
    static_names: Mapping[str, Any] = MappingProxyType({})
    unit_names: Mapping[str, SpeedUnit] = MappingProxyType({})
    allows_len: bool = False


class LoweringContext:
    def __init__(self, instance: Function, function_id: str, scope: ProgramScope) -> None:
        self.instance = instance
        self.function_id = function_id
        self.scope = scope
        # Filled once by source discovery, which runs after the declared device
        # slots are registered so a slot error still precedes a source error.
        self.source = RuntimeSource()
        self.sequence = 0
        self.function_schema: FunctionIR | None = None
        self.narrowed_devices: dict[str, type[BaseDevice]] = {}

    def fail(self, code: str, message: str, node: ast.AST | None = None) -> NoReturn:
        source = self.span(node) if node is not None else None
        raise IRValidationError(
            (Diagnostic(code=code, message=message, path=f"$.python.{self.function_id}", source=source),)
        )

    def span(self, node: ast.AST) -> SourceSpan:
        location = cast(ast.expr | ast.stmt, node)
        return SourceSpan(path=self.source.filename, line=location.lineno, column=location.col_offset)

    def metadata(self, node: ast.AST) -> dict[str, Any]:
        self.sequence += 1
        return {"node_id": f"{self.function_id}:node:{self.sequence}", "source": self.span(node)}

    def symbol(self, name: str, function_id: str | None = None) -> str:
        return f"{function_id or self.function_id}:var:{name}"

    def host_attribute(self, name: str) -> Any:
        if name in self.instance.device_fields:
            return self.instance.device_fields[name].__get__(self.instance)
        if name in vars(self.instance):
            return vars(self.instance)[name]
        return inspect.getattr_static(type(self.instance), name, _MISSING)

    def static_object(self, node: ast.AST) -> object:
        """Resolve a trusted declaration by identity without running descriptors."""
        if isinstance(node, ast.Name):
            return self.source.static_names.get(node.id)
        if isinstance(node, ast.Attribute):
            return inspect.getattr_static(self.static_object(node.value), node.attr, None)
        return None

    def device_member(self, node: ast.AST) -> tuple[DeviceReference, str] | None:
        """Recognize `self.<device slot>.<member>`; any other shape returns None."""
        if not (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Attribute)
            and isinstance(node.value.value, ast.Name)
            and node.value.value.id == "self"
        ):
            return None
        component = self.host_attribute(node.value.attr)
        return (component, node.attr) if isinstance(component, DeviceReference) else None

    def device_resource(self, reference: DeviceReference) -> DeviceResource:
        if id(reference.owner) not in self.scope.paths:
            self.fail("device_reference", "Shared device owner must belong to this Function composition.")
        logical_id = ".".join(filter(None, (self.scope.paths[id(reference.owner)], reference.name)))
        self.register_device_type(reference.device_type)
        return self.scope.resources.setdefault(
            logical_id,
            DeviceResource(
                node_id=f"resource:{logical_id}",
                logical_id=logical_id,
                device_type_id=reference.device_type.device_type_id,
            ),
        )

    def register_device_type(self, device_type: type[BaseDevice]) -> None:
        for cls in reversed(device_type.__mro__):
            if issubclass(cls, BaseDevice):
                contract = device_contract(cls)
                previous = self.scope.device_types.setdefault(contract.type_id, contract)
                if previous != contract:
                    self.fail("device_contract", "A device type identifier has conflicting declarations.")

    def device_type(self, reference: DeviceReference) -> type[BaseDevice]:
        return self.narrowed_devices.get(self.device_resource(reference).node_id, reference.device_type)

    @contextmanager
    def narrowing(self, resource_id: str, device_type: type[BaseDevice] | None) -> Iterator[None]:
        """Apply one branch-local device narrowing and restore the enclosing scope."""
        original = self.narrowed_devices.copy()
        if device_type is not None:
            self.narrowed_devices[resource_id] = device_type
        try:
            yield
        finally:
            self.narrowed_devices = original

    def target(self, node: ast.AST) -> Reference:
        if (
            not isinstance(node, ast.Attribute)
            or not isinstance(node.value, ast.Name)
            or node.value.id != "self"
            or node.attr not in self.instance.model_fields
        ):
            self.fail("runtime_field", "Assignment targets must be declared self.<runtime_field> references.", node)
        return Reference(**self.metadata(node), symbol_id=self.symbol(node.attr))

    def type_of(self, expression: Expression) -> ValueType:
        """Use shared expression rules for contextual list construction."""
        assert self.function_schema is not None
        errors: list[Diagnostic] = []

        def report(code: str, message: str, path: str, node: Node | None) -> None:
            errors.append(
                Diagnostic(
                    code=code,
                    message=message,
                    path=path,
                    node_id=node.node_id if node else None,
                    source=node.source if node else None,
                )
            )

        checker = ExpressionChecker({v.node_id: v for v in self.function_schema.variables}, report)
        value_type = checker.check(expression, self.function_schema, f"$.python.{self.function_id}")
        if errors:
            raise IRValidationError(tuple(errors))
        assert value_type is not None
        return value_type
