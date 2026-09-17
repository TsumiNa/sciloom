"""Explicit immutable responses for ordered text and yes/no interactions."""

from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from sciloom.units import Duration


class DialogOutcome(StrEnum):
    """Recorded operator outcome; only ACCEPTED can supply a result."""

    ACCEPTED = "accepted"
    CANCELLED = "cancelled"
    STOPPED = "stopped"
    TIMED_OUT = "timed_out"


@dataclass(frozen=True, kw_only=True)
class DialogResponse:
    """One supplied response, with explicit elapsed time and no implicit default.

    Args:
        outcome: Accepted, cancelled, stopped or timed out.
        value: Exact text/bool for accepted responses; None for other outcomes.
        elapsed: Nonnegative duration since the request; never advances a clock.

    Raises:
        TypeError: Value or elapsed has an unsupported type.
        ValueError: Outcome is unknown, elapsed is negative or a failure has a value.
    """

    outcome: DialogOutcome
    value: str | bool | None = None
    elapsed: Duration = Duration(seconds=0)

    def __post_init__(self) -> None:
        object.__setattr__(self, "outcome", DialogOutcome(self.outcome))
        if type(self.elapsed) is not Duration:
            raise TypeError("Dialog elapsed time must be a Duration.")
        if self.elapsed.seconds < 0:
            raise ValueError("Dialog elapsed time must be nonnegative.")
        if self.outcome == DialogOutcome.ACCEPTED:
            if type(self.value) not in (str, bool):
                raise TypeError("Accepted dialog responses require text or bool, never an absent/default value.")
        elif self.value is not None:
            raise ValueError("Non-accepted dialog responses cannot carry a fallback value.")


class QueuedDialogResponses:
    """Consume a copied sequence of explicit responses without prompting or sleeping.

    Args:
        responses: Immutable response records; the supplied iterable is copied.

    Raises:
        TypeError: An entry is not a DialogResponse record.
    """

    def __init__(self, responses: Iterable[DialogResponse] = ()) -> None:
        copied = tuple(responses)
        if any(type(response) is not DialogResponse for response in copied):
            raise TypeError("Dialog queues require explicit DialogResponse records.")
        self._responses = deque(copied)

    @property
    def remaining(self) -> int:
        """Return the count of unconsumed responses."""
        return len(self._responses)

    def respond(self) -> DialogResponse:
        """Consume exactly one response or raise LookupError without changing the queue."""
        if not self._responses:
            raise LookupError("No dialog response remains.")
        return self._responses.popleft()
