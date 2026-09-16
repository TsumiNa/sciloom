"""Lower explicit metadata reads and indexed writes into ordered IR statements."""

import ast
import inspect

from sciloom.core.ir import ReadWellProperty, ScalarType, WellPropertySpec, WriteWellProperty
from sciloom.flow.properties import WellProperty
from .context import LoweringContext
from .expressions import expression


def property_statement(context: LoweringContext, node: ast.stmt) -> ReadWellProperty | WriteWellProperty | None:
    """Resolve only declared host metadata objects, never Python getter bodies."""
    if isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Subscript):
        if context.well_property(node.target.value) is not None:
            context.fail("well_property_write", "Well properties support plain indexed assignment only.", node)
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        if isinstance(target, ast.Subscript) and (declaration := context.well_property(target.value)) is not None:
            return WriteWellProperty(
                **context.metadata(node),
                property=WellPropertySpec(name=declaration.name, type=ScalarType.TEXT),
                value=expression(context, node.value, ScalarType.TEXT),
                zone=expression(context, target.slice),
            )
    if not isinstance(node, (ast.Assign, ast.Expr)) or not isinstance(node.value, ast.Call):
        return None
    invocation = node.value
    member = invocation.func
    if not isinstance(member, ast.Attribute) or (declaration := context.well_property(member.value)) is None:
        return None
    if member.attr != "get":
        context.fail("well_property_read", "Read a well property with get(...), or write by indexed assignment.", node)
    if not isinstance(node, ast.Assign) or len(node.targets) != 1:
        context.fail("external_operation", "Assign a property read to one declared text field.", node)
    names = [keyword.arg for keyword in invocation.keywords]
    if len(names) != len(set(names)) or None in names or any(isinstance(a, ast.Starred) for a in invocation.args):
        context.fail("call_binding", "Property reads do not accept duplicate or expanded arguments.", node)
    try:
        bound = inspect.signature(WellProperty.get).bind(
            declaration,
            *invocation.args,
            **{keyword.arg: keyword.value for keyword in invocation.keywords if keyword.arg is not None},
        )
    except TypeError as error:
        context.fail("call_binding", str(error), invocation)
    return ReadWellProperty(
        **context.metadata(invocation),
        property=WellPropertySpec(name=declaration.name, type=ScalarType.TEXT),
        zone=expression(context, bound.arguments["zone"]),
        default=expression(context, bound.arguments["default"], ScalarType.TEXT)
        if "default" in bound.arguments
        else None,
        target=context.target(node.targets[0]),
    )
