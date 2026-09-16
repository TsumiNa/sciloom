"""Explicit external-state ownership for deterministic reference execution."""

from dataclasses import dataclass, field
from typing import TypeAlias, TypeVar

from sciloom.core.diagnostics import SourceSpan
from sciloom.core.ir.model import Node
from sciloom.core.ir.types import ScalarType
from .acknowledgements import QueuedAcknowledgements
from .device_state import DeviceEvent
from .values import InputScalar, fail


@dataclass(frozen=True, kw_only=True)
class LogEvent:
    """A completed typed log record, independent of subsequent variable changes.

    Attributes:
        node_id: Semantic logging occurrence ID.
        source: Optional source location of the operation.
        type: Semantic type of the captured value.
        value: Native scalar or physical quantity in the public value convention.
        category: Captured category text.
        stream: Captured stream text.
    """

    node_id: str
    source: SourceSpan | None
    type: ScalarType
    value: InputScalar
    category: str
    stream: str


@dataclass(frozen=True, kw_only=True)
class AcknowledgementEvent:
    """A message for which an explicit OK response has been consumed.

    Attributes:
        node_id: Semantic notification occurrence ID.
        source: Optional source location of the operation.
        message: Captured text, independent of subsequent variable changes.
    """

    node_id: str
    source: SourceSpan | None
    message: str


ExecutionEvent: TypeAlias = DeviceEvent | LogEvent | AcknowledgementEvent
"""Closed reference-event vocabulary; each effect adds its own immutable record."""

Service = TypeVar("Service")


@dataclass(frozen=True, kw_only=True, eq=False)
class ReferenceEnvironment:
    """Caller-owned external context and chronological event history.

    An omitted environment creates an independent context for each Interpreter.
    Pass the same instance explicitly to share its history across sessions.
    Function variables and device configurations remain session-owned.

    Services are added with the capabilities that use them. This environment
    never reads host files, samples a real clock or acknowledges messages by
    default. Runs are sequential; no concurrent or transactional behavior is
    implied. Completed events remain visible after later execution failures.
    """

    acknowledgements: QueuedAcknowledgements | None = None
    """Explicit OK responses; absent by default and shared only when supplied."""

    _events: list[ExecutionEvent] = field(default_factory=list, init=False, repr=False)

    @property
    def events(self) -> tuple[ExecutionEvent, ...]:
        """Return an immutable history snapshot across runs using this environment."""
        return tuple(self._events)


def _require_service(service: Service | None, name: str, node: Node) -> Service:
    """Fail at the requesting operation when an external dependency is absent."""
    if service is None:
        fail("missing_environment_service", f"Reference execution requires the {name!r} environment service.", node)
    return service
