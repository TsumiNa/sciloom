"""Shared state and symbol/source identity for lowering one Function."""

from __future__ import annotations

import ast
import inspect
from typing import Any, NoReturn, cast
from .model import Function
from .device_schema import DeviceReference
from ..units import SpeedUnit
from ..core.diagnostics import Diagnostic, IRValidationError, SourceSpan
from ..core.ir import AgitatorResource, Expression, FunctionIR, Reference, ValueType
from ..core.ir.expressions import ExpressionChecker
from ..core.ir.model import Node


_MISSING = object()


class LoweringContext:
    def __init__(
        self,
        instance: Function,
        function_id: str,
        instances: list[Function],
        ids: dict[int, str],
        resources: dict[str, AgitatorResource],
        paths: dict[int, str],
    ) -> None:
        self.instance = instance
        self.function_id = function_id
        self.instances = instances
        self.ids = ids
        self.resources = resources
        self.paths = paths
        self.unit_names: dict[str, SpeedUnit] = {}
        self.filename = ""
        self.sequence = 0
        self.function_schema: FunctionIR | None = None
        self.allows_len = False

    def fail(self, code: str, message: str, node: ast.AST | None = None) -> NoReturn:
        source = self.span(node) if node is not None else None
        raise IRValidationError(
            (Diagnostic(code=code, message=message, path=f"$.python.{self.function_id}", source=source),)
        )

    def span(self, node: ast.AST) -> SourceSpan:
        location = cast(ast.expr | ast.stmt, node)
        return SourceSpan(path=self.filename, line=location.lineno, column=location.col_offset)

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

    def device_resource(self, reference: DeviceReference) -> AgitatorResource:
        if id(reference.owner) not in self.paths:
            self.fail("device_reference", "Shared device owner must belong to this Function composition.")
        logical_id = ".".join(filter(None, (self.paths[id(reference.owner)], reference.name)))
        return self.resources.setdefault(logical_id, AgitatorResource(node_id=f"resource:{logical_id}", logical_id=logical_id))

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
            errors.append(Diagnostic(code=code, message=message, path=path, node_id=node.node_id if node else None, source=node.source if node else None))

        checker = ExpressionChecker({v.node_id: v for v in self.function_schema.variables}, report)
        value_type = checker.check(expression, self.function_schema, f"$.python.{self.function_id}")
        if errors:
            raise IRValidationError(tuple(errors))
        assert value_type is not None
        return value_type
