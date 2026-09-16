"""Source locations and structured errors shared across compilation and execution."""

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, kw_only=True)
class SourceSpan:
    """One-based source line and zero-based UTF-8 byte column."""

    __ir_kind__: ClassVar[str] = "SourceSpan"

    path: str
    line: int
    column: int = 0


@dataclass(frozen=True, kw_only=True)
class Diagnostic:
    """A structured error attached to a semantic path and optional source occurrence.

    Attributes:
        code: Machine-readable category.
        message: Human-readable explanation.
        path: JSON-style semantic path.
        node_id: Associated semantic occurrence, when available.
        source: Original Python source position, when available."""

    code: str
    message: str
    path: str
    node_id: str | None = None
    source: SourceSpan | None = None


class DiagnosticError(ValueError):
    """Base ValueError carrying an ordered tuple of structured diagnostics.

    Args:
        diagnostics: Errors rendered in the exception message and retained unchanged."""

    def __init__(self, diagnostics: tuple[Diagnostic, ...]) -> None:
        self.diagnostics = diagnostics
        super().__init__("\n".join(f"{d.path}: {d.message} [{d.code}]" for d in diagnostics))


class IRValidationError(DiagnosticError):
    """Invalid declarations, source or target-independent semantics."""


class CompilationError(DiagnosticError):
    """A target cannot validate or emit this program."""


class ExecutionError(DiagnosticError):
    """Reference execution stopped with an invalid operation or exhausted budget."""
