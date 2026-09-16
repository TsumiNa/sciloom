"""SciLoom — programmable scientific automation from one semantic model."""

from typing import TYPE_CHECKING, Any

from .units import Duration, L, RotationalSpeed, Volume, hour, minute, mL, rpm, rps, s, uL

if TYPE_CHECKING:
    from .devices.agitation import Agitator
    from .flow import comptime, csv, text
    from .flow.fields import Input, Output, Var
    from .flow.function import Function, runtime
    from .flow.logging import log
    from .flow.messages import notify
    from .flow.timing import Timer, now_text, wait

_DSL_EXPORTS = {"Function", "Input", "Output", "Var", "runtime"}


def __getattr__(name: str) -> Any:
    # Importing sciloom.core.ir or the interpreter must not load source analysis.
    if name == "csv":
        from .flow import csv

        return csv
    if name in {"Timer", "wait"}:
        from .flow import timing

        return getattr(timing, name)
    if name == "now_text":
        from .flow.timing import now_text

        return now_text
    if name == "notify":
        from .flow.messages import notify

        return notify
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
    "csv",
    "Timer",
    "wait",
    "now_text",
    "notify",
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
