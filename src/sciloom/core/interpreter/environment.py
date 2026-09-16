"""Explicit external-state ownership for deterministic reference execution."""

from dataclasses import dataclass, field
from typing import TypeAlias, TypeVar

from sciloom.core.ir.model import Node
from .device_state import DeviceEvent
from .values import fail

ExecutionEvent: TypeAlias = DeviceEvent
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
