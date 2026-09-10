"""Diagnostics shared by typed and JSON authoring paths."""

from dataclasses import dataclass

from .model import SourceSpan


@dataclass(frozen=True, kw_only=True)
class Diagnostic:
    code: str
    message: str
    path: str
    node_id: str | None = None
    source: SourceSpan | None = None


class IRValidationError(ValueError):
    def __init__(self, diagnostics: tuple[Diagnostic, ...]):
        self.diagnostics = diagnostics
        super().__init__("\n".join(f"{d.path}: {d.message} [{d.code}]" for d in diagnostics))
