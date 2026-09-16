"""Native timer/wait tasks and their lexical Macro visibility boundary."""

from typing import assert_never

from sciloom.core.diagnostics import Diagnostic
from sciloom.core.ir import (
    Assignment,
    Call,
    ConfigureProperty,
    DeviceCommand,
    DeviceIf,
    If,
    ListSet,
    Literal,
    LogValue,
    Notify,
    Program,
    ReadWallTime,
    StartAgitation,
    StartTimer,
    Statement,
    StopAgitation,
    Wait,
    WaitUntil,
    While,
)
from .context import CodegenContext
from .encoding import literal_value
from .xml import XmlNode, xml_node as _xml


def validate_timer_scopes(program: Program) -> tuple[Diagnostic, ...]:
    """Reject starts/resets escaping the observed native timer scope.

    Shared core analysis proves starts by flow. Native timers additionally need
    starts in one lexical Macro scope, and waits in that scope or its descendants.
    This adapter never moves a timer start earlier to manufacture visibility.
    """
    starts: dict[str, set[tuple[str, ...]]] = {}
    declarations: dict[str, tuple[StartTimer, str]] = {}
    waits: list[tuple[WaitUntil, tuple[str, ...], str]] = []

    def visit(body: tuple[Statement, ...], scope: tuple[str, ...], path: str) -> None:
        for index, node in enumerate(body):
            location = f"{path}[{index}]"
            if isinstance(node, StartTimer):
                starts.setdefault(node.resource_id, set()).add(scope)
                declarations.setdefault(node.resource_id, (node, location))
            elif isinstance(node, WaitUntil):
                waits.append((node, scope, location))
            elif isinstance(node, If):
                visit(node.then_body, (*scope, node.node_id, "then"), f"{location}.then_body")
                visit(node.else_body, (*scope, node.node_id, "else"), f"{location}.else_body")
            elif isinstance(node, While):
                visit(node.body, (*scope, node.node_id), f"{location}.body")
            elif isinstance(node, DeviceIf):
                raise AssertionError("Specialize device conditions before native timer scope checks.")
            elif isinstance(
                node,
                (
                    Assignment,
                    Call,
                    ConfigureProperty,
                    DeviceCommand,
                    ListSet,
                    LogValue,
                    Notify,
                    ReadWallTime,
                    StartAgitation,
                    StopAgitation,
                    Wait,
                ),
            ):
                pass
            else:
                assert_never(node)

    for index, function in enumerate(program.functions):
        visit(function.body, (function.node_id,), f"$.functions[{index}].body")
    errors = []
    for resource_id, scopes in starts.items():
        if len(scopes) > 1:
            declaration, location = declarations[resource_id]
            errors.append(
                Diagnostic(
                    code="unsupported_timer_scope",
                    message="AutoSuite timer starts/resets must share one lexical Macro scope.",
                    path=location,
                    node_id=declaration.node_id,
                    source=declaration.source,
                )
            )
    for node, scope, path in waits:
        definitions = starts.get(node.resource_id, set())
        if len(definitions) > 1:
            continue
        if len(definitions) != 1 or any(scope[: len(declared)] != declared for declared in definitions):
            errors.append(
                Diagnostic(
                    code="unsupported_timer_scope",
                    message="AutoSuite timer starts/resets must share one Macro scope, with waits in that scope or its descendants.",
                    path=path,
                    node_id=node.node_id,
                    source=node.source,
                )
            )
    return tuple(errors)


def timing_task(context: CodegenContext, node: StartTimer | Wait | WaitUntil, tag: str) -> XmlNode:
    """Emit documented native tasks after type, start, scope and duration checks."""
    if isinstance(node, StartTimer):
        return _xml(
            tag,
            "",
            *context.metadata("Set Timer"),
            _xml("timername", context.timers[node.resource_id]),
            _xml("id", context.identifier("statement", node.node_id)),
            typeid="Chemspeed.SATaskSetTimer.1",
        )
    assert isinstance(node.duration, Literal)  # Guard gate accepts only statically bounded durations.
    timer_name = context.timers[node.resource_id] if isinstance(node, WaitUntil) else ""
    return _xml(
        tag,
        "",
        *context.metadata("Wait"),
        _xml("time", literal_value(node.duration)),
        _xml("timeunit", "s"),
        _xml("msgtodisplay"),
        _xml("waitmode", "2" if isinstance(node, WaitUntil) else "0"),
        _xml("contacts"),
        _xml("timername", timer_name),
        _xml("cancelwait", "0"),
        _xml("id", context.identifier("statement", node.node_id)),
        typeid="Chemspeed.SATaskWait.1",
    )
