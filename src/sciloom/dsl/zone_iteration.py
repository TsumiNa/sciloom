"""Lower Zone loop headers without executing user iterators or host descriptors."""

import ast
import inspect

from sciloom.core.ir import ForEachZone, VariableRole, ZoneType
from sciloom.flow import zones
from .context import LoweringContext
from .expressions import expression


def zone_loop(context: LoweringContext, node: ast.For) -> ForEachZone:
    """Build a typed loop header; statement lowering supplies the body."""
    if node.orelse:
        context.fail("python_subset", "Zone traversal does not support for/else.", node)
    if isinstance(node.target, ast.Name):
        context.fail(
            "python_subset",
            "Runtime for loops require a declared self.<Var[Zone]> target; Python locals are unsupported.",
            node.target,
        )
    metadata = context.metadata(node)
    target = context.target(node.target)
    assert isinstance(node.target, ast.Attribute)
    field = context.instance.model_fields[node.target.attr]
    if field.role != VariableRole.INTERNAL or not isinstance(field.type, ZoneType):
        context.fail("zone_loop_target", "Zone loop targets must be declared Var[Zone] fields.", node.target)
    selection = node.iter
    size = 1
    if isinstance(selection, ast.Call) and context.static_object(selection.func) is zones.fragments:
        if any(isinstance(arg, ast.Starred) for arg in selection.args) or any(
            k.arg is None for k in selection.keywords
        ):
            context.fail("python_subset", "zones.fragments does not accept argument expansion.", selection)
        try:
            bound = inspect.signature(zones.fragments).bind(
                *selection.args, **{k.arg: k.value for k in selection.keywords if k.arg is not None}
            )
        except TypeError as error:
            context.fail("python_subset", str(error), selection)
        size_node = bound.arguments["size"]
        size_value: object = None
        if isinstance(size_node, ast.Constant):
            size_value = size_node.value
        elif (
            isinstance(size_node, ast.Attribute)
            and isinstance(size_node.value, ast.Name)
            and size_node.value.id == "self"
            and size_node.attr not in context.instance.model_fields
        ):
            size_value = context.host_attribute(size_node.attr)
        if type(size_value) is not int or size_value <= 0:
            context.fail("zone_fragment_size", "Fragment size must be a positive host-time integer.", size_node)
        size = size_value
        selection = bound.arguments["value"]
    value = expression(context, selection)
    if not isinstance(context.type_of(value), ZoneType):
        context.fail("zone_type", "Runtime for loops require a Zone selection.", selection)
    return ForEachZone(**metadata, target=target, value=value, fragment_size=size)
