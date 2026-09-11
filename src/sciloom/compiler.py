"""Compile validated semantics into a target artifact without source mutation."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from .backends.autosuite.lowering import lower_asfp
from .ir import Diagnostic, IRValidationError, Package, validate
from .backends.autosuite.xml import SerializationIR, Target


@dataclass(frozen=True, kw_only=True)
class CompileResult:
    semantic_ir: Package
    serialization_ir: SerializationIR
    artifact: bytes
    diagnostics: tuple[Diagnostic, ...] = ()

    def write(self, path: str | Path) -> Path:
        """Write the ASFP bytes, creating parent directories when necessary."""
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(self.artifact)
        return destination


def compile_ir(package: Package, *, target: Target | str = Target.AUTOSUITE_2_47_1_1) -> CompileResult:
    """Compile either Python-lowered or JSON-authored IR using one backend."""
    try:
        target = Target(target)
    except ValueError:
        raise ValueError(f"Unsupported compilation target: {target!r}") from None
    diagnostics = validate(package)
    if diagnostics:
        raise IRValidationError(diagnostics)
    serialization_ir = lower_asfp(package, target)
    try:
        artifact = serialization_ir.to_xml()
        ET.fromstring(artifact)
    except (ET.ParseError, ValueError, TypeError) as error:
        # ValueError includes UnicodeError from XML encoding.
        raise IRValidationError((Diagnostic(code="xml_text", message=str(error), path="$"),)) from error
    return CompileResult(semantic_ir=package, serialization_ir=serialization_ir, artifact=artifact)
