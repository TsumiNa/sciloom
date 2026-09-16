"""SciLoom — programmable scientific automation from one semantic model."""

from typing import TYPE_CHECKING, Any

from .units import Duration, L, RotationalSpeed, Volume, hour, minute, mL, rpm, rps, s, uL

if TYPE_CHECKING:
    from .devices.agitation import Agitator
    from .flow import comptime, text
    from .flow.fields import Input, Output, Var
    from .flow.function import Function, runtime
    from .flow.logging import log

_DSL_EXPORTS = {"Function", "Input", "Output", "Var", "runtime"}


def __getattr__(name: str) -> Any:
    # Importing sciloom.core.ir or the interpreter must not load source analysis.
    if name == "log":
        from .flow.logging import log

        return log
    if name == "comptime":
        from .flow import comptime

        return comptime
    if name == "text":
        from .flow import text

        return text
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
    "log",
    "text",
    "comptime",
    "Agitator",
    "RotationalSpeed",
    "Volume",
    "Duration",
    "uL",
    "mL",
    "L",
    "s",
    "minute",
    "hour",
    "rpm",
    "rps",
    "Function",
    "Input",
    "Output",
    "Var",
    "runtime",
]
