"""SciLoom — programmable scientific automation from one semantic model."""

from typing import TYPE_CHECKING, Any

from .units import Duration, L, RotationalSpeed, Volume, hour, minute, mL, rpm, rps, s, uL

if TYPE_CHECKING:
    from .core.locations import Zone
    from .devices.agitation import Agitator
    from .devices.heating import Heater
    from .flow import comptime, csv, text, zones
    from .flow.fields import Input, Output, Var
    from .flow.function import Function, runtime
    from .flow.locations import at
    from .flow.logging import log
    from .flow.messages import ask_yes_no, notify, request_text
    from .flow.properties import WellProperty
    from .flow.timing import Timer, now_text, wait
    from .units import (
        Temperature,
        TemperatureDifference,
        TemperatureRate,
        degC,
        degC_per_min,
        delta_degC,
        delta_kelvin,
        kelvin,
        kelvin_per_s,
    )

_DSL_EXPORTS = {"Function", "Input", "Output", "Var", "runtime"}
_THERMAL_EXPORTS = {
    "Temperature",
    "TemperatureDifference",
    "TemperatureRate",
    "degC",
    "kelvin",
    "delta_degC",
    "delta_kelvin",
    "degC_per_min",
    "kelvin_per_s",
}


def __getattr__(name: str) -> Any:
    if name in _THERMAL_EXPORTS:
        from . import units

        return getattr(units, name)
    # Importing sciloom.core.ir or the interpreter must not load source analysis.
    if name == "at":
        from .flow.locations import at

        return at
    if name == "WellProperty":
        from .flow.properties import WellProperty

        return WellProperty
    if name == "Zone":
        from .core.locations import Zone

        return Zone
    if name == "zones":
        from .flow import zones

        return zones
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
    if name in {"request_text", "ask_yes_no"}:
        from .flow import messages

        return getattr(messages, name)
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
    if name == "Heater":
        from .devices.heating import Heater

        return Heater
    if name in _DSL_EXPORTS:
        if name in {"Function", "runtime"}:
            from .flow import function

            return getattr(function, name)
        from .flow import fields

        return getattr(fields, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Temperature",
    "TemperatureDifference",
    "TemperatureRate",
    "degC",
    "kelvin",
    "delta_degC",
    "delta_kelvin",
    "degC_per_min",
    "kelvin_per_s",
    "at",
    "WellProperty",
    "Zone",
    "zones",
    "csv",
    "Timer",
    "wait",
    "now_text",
    "notify",
    "request_text",
    "ask_yes_no",
    "log",
    "text",
    "comptime",
    "Agitator",
    "Heater",
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
