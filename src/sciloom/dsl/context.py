"""Shared state and symbol/source identity for lowering one Function."""

from __future__ import annotations

import ast
import inspect
from typing import Any, NoReturn, cast
from .model import Function
from ..units import SpeedUnit
from ..core.diagnostics import Diagnostic, IRValidationError, SourceSpan
from ..core.ir import AgitatorResource, Reference


_MISSING = object()


class LoweringContext:
    def __init__(
        self,
        instance: Function,
        function_id: str,
        instances: list[Function],
        ids: dict[int, str],
        resources: dict[str, AgitatorResource],
    ) -> None:
        self.instance = instance
        self.function_id = function_id
        self.instances = instances
        self.ids = ids
        self.resources = resources
        self.unit_names: dict[str, SpeedUnit] = {}
        self.filename = ""
        self.sequence = 0

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
        if name in vars(self.instance):
            return vars(self.instance)[name]
        return inspect.getattr_static(type(self.instance), name, _MISSING)

    def target(self, node: ast.AST) -> Reference:
        if (
            not isinstance(node, ast.Attribute)
            or not isinstance(node.value, ast.Name)
            or node.value.id != "self"
            or node.attr not in self.instance.model_fields
        ):
            self.fail("runtime_field", "Assignment targets must be declared self.<runtime_field> references.", node)
        return Reference(**self.metadata(node), symbol_id=self.symbol(node.attr))
