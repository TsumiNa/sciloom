"""Definite timer starts across structured flow and Function calls."""

from typing import assert_never

from .diagnostics import Diagnostic
from .ir import (
    AppendCsv,
    AskYesNo,
    Assignment,
    Call,
    ConfigureProperty,
    DeviceAt,
    DeviceCommand,
    DeviceIf,
    ForEachZone,
    If,
    ListSet,
    Literal,
    LogValue,
    Notify,
    Program,
    ReadCsv,
    ReadWallTime,
    ReadWellProperty,
    RequestText,
    StartAgitation,
    StartTimer,
    Statement,
    StopAgitation,
    Wait,
    WaitUntil,
    While,
    WriteWellProperty,
    ZoneLiteral,
)
from .ir.traversal import iter_nodes


def validate_timer_usage(program: Program) -> tuple[Diagnostic, ...]:
    """Check a valid, specialized program without assuming starts from earlier runs.

    Args:
        program: Structurally valid IR with device conditions already selected.

    Returns:
        Diagnostics for waits not definitely preceded by a start in this entry.

    Function summaries are monotone fixed points, including recursive call
    graphs. Loops can execute zero times; only branch intersections escape.
    """
    guarantees: dict[str, set[str]] = {f.node_id: set() for f in program.functions}
    # Requirements retain wait occurrences, not just timer IDs, so call summaries
    # preserve the actual failing node and its source location.
    requirements: dict[str, set[str]] = {f.node_id: set() for f in program.functions}
    waits = {node.node_id: (node, path) for node, path in iter_nodes(program) if isinstance(node, WaitUntil)}

    def analyze(body: tuple[Statement, ...], available: set[str]) -> tuple[set[str], set[str]]:
        started, required = available.copy(), set[str]()
        for statement in body:
            if isinstance(statement, StartTimer):
                started.add(statement.resource_id)
            elif isinstance(statement, WaitUntil):
                if statement.resource_id not in started:
                    required.add(statement.node_id)
            elif isinstance(statement, Call):
                required |= {
                    node_id
                    for node_id in requirements[statement.function_id]
                    if waits[node_id][0].resource_id not in started
                }
                started |= guarantees[statement.function_id]
            elif isinstance(statement, If):
                if isinstance(statement.condition, Literal):
                    selected = statement.then_body if statement.condition.value else statement.else_body
                    started, needs = analyze(selected, started)
                    required |= needs
                else:
                    left, left_needs = analyze(statement.then_body, started)
                    right, right_needs = analyze(statement.else_body, started)
                    started = left & right
                    required |= left_needs | right_needs
            elif isinstance(statement, DeviceAt):
                started, needs = analyze(statement.body, started)
                required |= needs
            elif isinstance(statement, While):
                if not (isinstance(statement.condition, Literal) and statement.condition.value is False):
                    _, needs = analyze(statement.body, started)
                    required |= needs
            elif isinstance(statement, ForEachZone):
                if not (isinstance(statement.value, ZoneLiteral) and not statement.value.well_ids):
                    _, needs = analyze(statement.body, started)
                    required |= needs
            elif isinstance(statement, DeviceIf):
                raise AssertionError("Specialize device conditions before timer analysis.")
            elif isinstance(
                statement,
                (
                    Assignment,
                    ListSet,
                    LogValue,
                    Notify,
                    ReadWallTime,
                    RequestText,
                    AskYesNo,
                    ReadWellProperty,
                    WriteWellProperty,
                    AppendCsv,
                    ReadCsv,
                    Wait,
                    ConfigureProperty,
                    StartAgitation,
                    StopAgitation,
                    DeviceCommand,
                ),
            ):
                pass
            else:
                assert_never(statement)
        return started, required

    for summaries, component in ((guarantees, 0), (requirements, 1)):
        changed = True
        while changed:
            changed = False
            for function in program.functions:
                value = analyze(function.body, set())[component]
                if summaries[function.node_id] != value:
                    summaries[function.node_id] = value
                    changed = True
    errors = []
    for node, path in waits.values():
        if node.node_id not in requirements[program.entry_function_id]:
            continue
        errors.append(
            Diagnostic(
                code="timer_not_started",
                message="Timer must be started on every reachable path in this entry invocation.",
                path=path,
                node_id=node.node_id,
                source=node.source,
            )
        )
    return tuple(errors)
