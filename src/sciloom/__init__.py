"""SciLoom — programmable scientific automation from one semantic model."""

from typing import TYPE_CHECKING, Any

from .units import RotationalSpeed, rpm, rps

if TYPE_CHECKING:
    from .dsl.model import Agitator, Boolean, Function, Input, Integer, Output, Real, runtime

_DSL_EXPORTS = {"Agitator", "Boolean", "Function", "Input", "Integer", "Output", "Real", "runtime"}


def __getattr__(name: str) -> Any:
    # Importing sciloom.core.ir or the interpreter must not load the Python DSL.
    if name in _DSL_EXPORTS:
        from .dsl import model

        return getattr(model, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Agitator",
    "RotationalSpeed",
    "rpm",
    "rps",
    "Boolean",
    "Function",
    "Input",
    "Integer",
    "Output",
    "Real",
    "runtime",
]
