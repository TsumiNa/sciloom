"""SciLoom — programmable scientific automation from one semantic model."""

from typing import TYPE_CHECKING, Any

from .units import RotationalSpeed, rpm, rps

if TYPE_CHECKING:
    from .dsl.model import Agitator, Function, runtime
    from .dsl.schema import Input, Output, Var

_DSL_EXPORTS = {"Agitator", "Function", "Input", "Output", "Var", "runtime"}


def __getattr__(name: str) -> Any:
    # Importing sciloom.core.ir or the interpreter must not load the Python DSL.
    if name in _DSL_EXPORTS:
        if name in {"Agitator", "Function", "runtime"}:
            from .dsl import model

            return getattr(model, name)
        from .dsl import schema

        return getattr(schema, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Agitator",
    "RotationalSpeed",
    "rpm",
    "rps",
    "Function",
    "Input",
    "Output",
    "Var",
    "runtime",
]
