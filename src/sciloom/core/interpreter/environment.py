"""Explicit external-state ownership for deterministic reference execution."""

from dataclasses import dataclass, field
from typing import TypeAlias, TypeVar

from sciloom.core.diagnostics import SourceSpan
from sciloom.core.ir.model import CsvReadMode, Node
from sciloom.core.ir.types import ScalarType
from sciloom.core.locations import LocationDirectory, Zone
from sciloom.units import Duration
from .acknowledgements import QueuedAcknowledgements
from .clocks import VirtualClock, WallClock
from .device_state import DeviceEvent
from .files import FileService
from .properties import WellProperties
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


@dataclass(frozen=True, kw_only=True)
class WallTimeEvent:
    """A completed wall-time read, retaining only immutable formatted text.

    Attributes:
        node_id: Semantic clock-read occurrence ID.
        source: Optional source location.
        format: Constant portable format used by the operation.
        value: Captured formatted text, independent of subsequent clock changes.
    """

    node_id: str
    source: SourceSpan | None
    format: str
    value: str


@dataclass(frozen=True, kw_only=True)
class TimerEvent:
    """A timer's new monotonic origin, captured at each successful start/reset.

    Attributes:
        node_id: Semantic start occurrence.
        source: Optional source location.
        resource_id: Function-owned timer identity.
        started_at: Captured monotonic seconds at this start/reset.
    """

    node_id: str
    source: SourceSpan | None
    resource_id: str
    started_at: float


@dataclass(frozen=True, kw_only=True)
class WaitEvent:
    """A completed wait, including its captured request and elapsed clock interval.

    Attributes:
        node_id: Semantic wait occurrence.
        source: Optional source location.
        duration: Interval for ordinary wait; elapsed threshold for a timer wait.
        started_at: Monotonic seconds at the beginning of this wait operation.
        finished_at: Monotonic seconds after waiting, possibly unchanged.
        timer_id: Timer resource ID for wait_until, otherwise None.
    """

    node_id: str
    source: SourceSpan | None
    duration: Duration
    started_at: float
    finished_at: float
    timer_id: str | None


@dataclass(frozen=True, kw_only=True)
class CsvReadEvent:
    """Outcome of one read attempt after argument capture, without copying file data.

    A failed ordinary read records its outcome before raising, without committing
    destination fields. Invalid arguments or missing services emit no read event.
    """

    node_id: str
    source: SourceSpan | None
    path: str
    mode: CsvReadMode
    header: bool
    row: int | None
    columns: tuple[int, ...]
    status: int


@dataclass(frozen=True, kw_only=True)
class CsvAppendEvent:
    """Outcome of a file append attempt and its captured logical row.

    Values describe the requested record, not guaranteed bytes after an I/O
    failure. Earlier or partial writes are not rolled back. All snapshots are
    immutable and physical quantities retain their public value types.
    """

    node_id: str
    source: SourceSpan | None
    path: str
    types: tuple[ScalarType, ...]
    values: tuple[InputScalar, ...]
    status: int


@dataclass(frozen=True, kw_only=True)
class WellPropertyReadEvent:
    """A completed metadata read with its selection, text and fallback decision."""

    node_id: str
    source: SourceSpan | None
    zone: Zone
    name: str
    type: ScalarType
    value: str
    used_default: bool


@dataclass(frozen=True, kw_only=True)
class WellPropertyWriteEvent:
    """A completed write of one captured text to an immutable well selection."""

    node_id: str
    source: SourceSpan | None
    zone: Zone
    name: str
    type: ScalarType
    value: str


ExecutionEvent: TypeAlias = (
    DeviceEvent
    | LogEvent
    | AcknowledgementEvent
    | WallTimeEvent
    | TimerEvent
    | WaitEvent
    | CsvReadEvent
    | CsvAppendEvent
    | WellPropertyReadEvent
    | WellPropertyWriteEvent
)
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

    wall_clock: WallClock | None = None
    """Explicit aware wall-time provider; never defaults to the host clock."""

    clock: VirtualClock | None = None
    """Explicit monotonic virtual clock; waiting never sleeps on the host."""

    files: FileService | None = None
    """Explicit byte adapter; host files are inaccessible unless supplied."""

    locations: LocationDirectory | None = None
    """Fixed, immutable location names and well identities; never inferred from hardware."""

    properties: WellProperties | None = None
    """Explicit stored well metadata, shared only when the caller supplies it."""

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
