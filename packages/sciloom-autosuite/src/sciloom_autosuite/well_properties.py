"""Observed user-property tasks and conservative single-well read validation."""

from typing import assert_never

from sciloom.core.diagnostics import Diagnostic
from sciloom.core.ir import (
    AppendCsv,
    AskYesNo,
    Assignment,
    Call,
    ConfigureProperty,
    DeviceAt,
    DeviceCommand,
    DeviceIf,
    Expression,
    ForEachZone,
    FunctionIR,
    If,
    ListSet,
    LogValue,
    Notify,
    Program,
    ReadCsv,
    ReadWallTime,
    ReadWellProperty,
    Reference,
    RequestText,
    StartAgitation,
    StartTimer,
    Statement,
    StopAgitation,
    Wait,
    WaitUntil,
    While,
    WriteWellProperty,
    ZoneGet,
    ZoneLiteral,
)
from .context import CodegenContext
from .expressions import materialize, plan_expression
from .primitives import macro
from .xml import XmlNode, xml_node as _xml


def validate_well_properties(program: Program) -> tuple[Diagnostic, ...]:
    """Require a fallback and a locally proven single-well selection for reads.

    Loop facts reach a fixed point before checking the body. They account for
    target reassignment, calls and subsequent iterations; empty loops cannot
    establish a fact. This analysis does not assume a previous entry invocation.
    """
    errors: list[Diagnostic] = []

    def single(value: Expression, facts: set[str]) -> bool:
        return (
            isinstance(value, Reference)
            and value.symbol_id in facts
            or isinstance(value, ZoneLiteral)
            and len(value.well_ids) == 1
            or isinstance(value, ZoneGet)
        )

    def block(body: tuple[Statement, ...], incoming: set[str], path: str, report: bool) -> set[str]:
        facts = incoming.copy()
        for index, node in enumerate(body):
            p = f"{path}[{index}]"
            if isinstance(node, Assignment):
                known = single(node.value, facts)
                facts.discard(node.target.symbol_id)
                if known:
                    facts.add(node.target.symbol_id)
            elif isinstance(node, Call):
                facts.difference_update(binding.target.symbol_id for binding in node.outputs)
            elif isinstance(node, ReadWellProperty):
                if report and (node.default is None or not single(node.zone, facts)):
                    errors.append(
                        Diagnostic(
                            code="unsupported_well_property_read",
                            message=(
                                "Strict well-property reads need verified fatal failure propagation."
                                if node.default is None
                                else "Well-property reads require a proven single well, such as an unchanged size-one Zone loop target."
                            ),
                            path=p,
                            node_id=node.node_id,
                            source=node.source,
                        )
                    )
                facts.discard(node.target.symbol_id)
            elif isinstance(node, If):
                facts = block(node.then_body, facts, f"{p}.then_body", report) & block(
                    node.else_body, facts, f"{p}.else_body", report
                )
            elif isinstance(node, (While, ForEachZone)):
                invariant = facts.copy()
                while True:
                    entry = invariant.copy()
                    if isinstance(node, ForEachZone):
                        entry.discard(node.target.symbol_id)
                        if node.fragment_size == 1:
                            entry.add(node.target.symbol_id)
                    after = block(node.body, entry, f"{p}.body", False)
                    narrowed = invariant & after
                    if narrowed == invariant:
                        break
                    invariant = narrowed
                block(node.body, entry, f"{p}.body", report)
                facts &= after
            elif isinstance(node, DeviceAt):
                facts = block(node.body, facts, f"{p}.body", report)
            elif isinstance(node, DeviceIf):
                raise AssertionError("Specialize device conditions before checking property reads.")
            elif isinstance(
                node,
                (
                    WriteWellProperty,
                    AppendCsv,
                    ReadCsv,
                    ReadWallTime,
                    RequestText,
                    AskYesNo,
                    ListSet,
                    LogValue,
                    Notify,
                    ConfigureProperty,
                    DeviceCommand,
                    StartAgitation,
                    StopAgitation,
                    StartTimer,
                    Wait,
                    WaitUntil,
                ),
            ):
                pass  # No Zone-valued destination in these operations.
            else:
                assert_never(node)
        return facts

    for index, function in enumerate(program.functions):
        block(function.body, set(), f"$.functions[{index}].body", True)
    return tuple(errors)


def property_tasks(
    context: CodegenContext, function: FunctionIR, node: ReadWellProperty | WriteWellProperty, tag: str
) -> tuple[XmlNode, ...]:
    """Capture arguments and emit documented user text-property task forms."""
    if isinstance(node, WriteWellProperty):
        value = materialize(context, function, plan_expression(context, function, node.value, tag), tag)
        zone = materialize(context, function, plan_expression(context, function, node.zone, tag), tag)
        task = _xml(
            "task",
            "",
            _xml("destzonename", zone.text),
            *context.metadata("Set Property"),
            _xml("propertytype", "2"),
            _xml("propname", node.property.name),
            _xml("valuemode", "0"),
            _xml("variablename"),
            _xml("propvalueexprtext", value.text),
            _xml("resulttype", "text"),
            _xml("propertyunit"),
            _xml("id", context.identifier("statement", node.node_id)),
            typeid="Chemspeed.SATaskSetProperty.1",
        )
        return (
            *value.prerequisites,
            *zone.prerequisites,
            macro(
                context,
                tag,
                context.fresh_id(),
                function,
                (task,),
                name="Skip empty property selection",
                condition_type="1",
                condition=f"ZoneSize({zone.text}) > 0",
            ),
        )
    assert node.default is not None  # Target validation gates strict reads.
    zone = materialize(context, function, plan_expression(context, function, node.zone, tag), tag)
    fallback = materialize(context, function, plan_expression(context, function, node.default, tag), tag)
    return (
        *zone.prerequisites,
        *fallback.prerequisites,
        _xml(
            tag,
            "",
            _xml("sourcezonename", zone.text),
            *context.metadata("Get Property"),
            _xml("propname", node.property.name),
            _xml("destvariablename", context.names[node.target.symbol_id]),
            _xml("userpropertymode", "2"),
            _xml("fallbackmode", "1"),
            _xml("fallback", fallback.text),
            _xml("id", context.identifier("statement", node.node_id)),
            typeid="Chemspeed.SATaskGetProperty.1",
        ),
    )
