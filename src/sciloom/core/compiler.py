"""Validate semantic programs and delegate emission to an explicit target."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from .diagnostics import CompilationError, Diagnostic, IRValidationError
from .ir import Program, validate
from .devices import DeviceBindings
from .configuration import validate_device_usage
from .specialization import specialize


@dataclass(frozen=True, kw_only=True)
class Artifact:
    content: bytes
    media_type: str
    suffix: str


@runtime_checkable
class Target(Protocol):
    @property
    def target_id(self) -> str: ...

    def resolve_devices(self, program: Program) -> DeviceBindings: ...

    def validate(self, program: Program) -> tuple[Diagnostic, ...]: ...

    def emit(self, program: Program) -> Artifact: ...


@dataclass(frozen=True, kw_only=True)
class CompileResult:
    semantic_ir: Program
    specialized_ir: Program
    target_id: str
    artifact: Artifact
    diagnostics: tuple[Diagnostic, ...] = ()

    def write(self, path: str | Path) -> Path:
        """Write the target's bytes, creating parent directories when necessary."""
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(self.artifact.content)
        return destination


def compile_ir(program: Program, *, target: Target) -> CompileResult:
    """Compile any author's IR; neither Python parsing nor XML belongs here."""
    if not isinstance(target, Target):
        raise TypeError("target must implement target_id, resolve_devices(program), validate(program) and emit(program).")
    diagnostics = validate(program)
    if diagnostics:
        raise IRValidationError(diagnostics)
    bindings = target.resolve_devices(program)
    specialized = specialize(program, bindings=bindings)
    diagnostics = validate_device_usage(specialized, bindings)
    if diagnostics:
        raise CompilationError(diagnostics)
    diagnostics = target.validate(specialized)
    if diagnostics:
        raise CompilationError(diagnostics)
    artifact = target.emit(specialized)
    return CompileResult(semantic_ir=program, specialized_ir=specialized, target_id=target.target_id, artifact=artifact)
