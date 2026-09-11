"""SciLoom — programmable scientific automation from one semantic model."""

from .frontends.python.model import Boolean, Function, Input, Integer, Output, Real, RuntimeField, runtime
from .compiler import CompileResult, compile_ir
from .backends.autosuite.xml import Target

__all__ = [
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
