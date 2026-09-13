"""SciLoom — programmable scientific automation from one semantic model."""

from typing import TYPE_CHECKING, Any

from .units import RotationalSpeed, rpm, rps

if TYPE_CHECKING:
    from .devices.agitation import Agitator
    from .flow import comptime
    from .flow.fields import Input, Output, Var
    from .flow.function import Function, runtime

_DSL_EXPORTS = {"Function", "Input", "Output", "Var", "runtime"}


def __getattr__(name: str) -> Any:
    # Importing sciloom.core.ir or the interpreter must not load source analysis.
    if name == "comptime":
        from .flow import comptime

        return comptime
    if name == "Agitator":
        from .devices.agitation import Agitator

        return Agitator
    if name in _DSL_EXPORTS:
        if name in {"Function", "runtime"}:
            from .flow import function

            return getattr(function, name)
        from .flow import fields

        return getattr(fields, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "comptime",
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
