"""Source locations and structured errors shared across compilation and execution."""

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class SourceSpan:
    """One-based source line and zero-based UTF-8 byte column."""

    path: str
    line: int
    column: int = 0


@dataclass(frozen=True, kw_only=True)
class Diagnostic:
    code: str
    message: str
    path: str
    node_id: str | None = None
    source: SourceSpan | None = None


class DiagnosticError(ValueError):
    def __init__(self, diagnostics: tuple[Diagnostic, ...]):
        self.diagnostics = diagnostics
        super().__init__("\n".join(f"{d.path}: {d.message} [{d.code}]" for d in diagnostics))


class IRValidationError(DiagnosticError):
    """Invalid declarations, source or target-independent semantics."""


class CompilationError(DiagnosticError):
    """A target cannot validate or emit this program."""
