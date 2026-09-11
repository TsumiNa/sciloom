"""SciLoom — programmable scientific automation from one semantic model."""

from typing import TYPE_CHECKING, Any

from .units import RotationalSpeed, rpm, rps
from .compiler import Artifact, CompileResult, Target, compile_ir

if TYPE_CHECKING:
    from .frontends.python.model import Agitator, Boolean, Function, Input, Integer, Output, Real, RuntimeField, runtime

_FRONTEND_EXPORTS = {"Agitator", "Boolean", "Function", "Input", "Integer", "Output", "Real", "RuntimeField", "runtime"}


def __getattr__(name: str) -> Any:
    # Importing sciloom.ir or the interpreter must not load a source frontend.
    if name in _FRONTEND_EXPORTS:
        from .frontends.python import model

        return getattr(model, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Agitator",
    "RotationalSpeed",
    "rpm",
    "rps",
    "Artifact",
    "Boolean",
    "CompileResult",
    "Function",
    "Input",
    "Integer",
    "Output",
    "Real",
    "RuntimeField",
    "Target",
    "compile_ir",
    "runtime",
]
