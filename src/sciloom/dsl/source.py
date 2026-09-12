"""Locate one registered runtime method in an ordinary Python source file."""

from __future__ import annotations

import ast
import builtins
import inspect
import tokenize
from typing import Any
from .context import LoweringContext
from ..units import SpeedUnit


def runtime_source(context: LoweringContext) -> ast.FunctionDef:
    for name in context.instance.model_fields:
        if name in vars(context.instance):
            context.fail("runtime_field_write", f"Instance configuration shadows runtime field {name!r}.")
    members: dict[str, Any] = {}
    for cls in reversed(type(context.instance).__mro__):
        members.update(vars(cls))
    methods = [
        getattr(value, "__sciloom_runtime__")
        for value in members.values()
        if inspect.isfunction(value) and hasattr(value, "__sciloom_runtime__")
    ]
    if len(methods) != 1:
        context.fail("runtime_method", "A Function requires exactly one @runtime instance method.")
    method = methods[0]
    bindings = inspect.getclosurevars(method)
    resolved_len = bindings.nonlocals.get("len", bindings.globals.get("len", bindings.builtins.get("len", builtins.len)))
    context.allows_len = resolved_len is builtins.len
    context.unit_names = {name: value for name, value in method.__globals__.items() if isinstance(value, SpeedUnit)}
    context.filename = method.__code__.co_filename
    if not context.filename.endswith(".py"):
        context.fail("source_unavailable", "Runtime source must come from an ordinary .py file.")
    try:
        with tokenize.open(context.filename) as source:
            module = ast.parse(source.read(), filename=context.filename)
    except (OSError, UnicodeError, SyntaxError) as error:
        context.fail("source_unavailable", f"Cannot read runtime source: {error}")
    candidates = [
        node
        for node in ast.walk(module)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == method.__name__
        and min([node.lineno, *(d.lineno for d in node.decorator_list)]) == method.__code__.co_firstlineno
    ]
    if len(candidates) != 1 or not isinstance(candidates[0], ast.FunctionDef):
        context.fail("source_unavailable", "Cannot locate one synchronous runtime method in its source file.")
    node = candidates[0]
    args = node.args
    if (
        len(args.args) != 1
        or args.args[0].arg != "self"
        or args.posonlyargs
        or args.kwonlyargs
        or args.vararg
        or args.kwarg
        or args.defaults
    ):
        context.fail("python_subset", "Runtime methods take only self; declare Input fields on the class.", node)
    return node
