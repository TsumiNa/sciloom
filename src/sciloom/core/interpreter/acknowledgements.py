"""Explicit, finite OK responses for deterministic reference execution."""

from collections.abc import Iterable


class QueuedAcknowledgements:
    """Consume caller-supplied OK responses, without prompting or auto-confirming.

    Args:
        responses: Copied iterable containing only literal ``True`` entries.

    Raises:
        ValueError: An entry is not exactly ``True``; cancellation is unsupported.
    """

    def __init__(self, responses: Iterable[bool] = ()) -> None:
        copied = tuple(responses)
        if any(response is not True for response in copied):
            raise ValueError("Acknowledgements must be explicit True responses.")
        self._remaining = len(copied)

    @property
    def remaining(self) -> int:
        """Return the number of unconsumed OK responses."""
        return self._remaining

    def acknowledge(self, message: str) -> None:
        """Consume one OK response for the captured message.

        Args:
            message: Text being acknowledged; empty text is allowed.

        Raises:
            TypeError: The message is not text.
            LookupError: No response remains; the queue is unchanged.
        """
        if not isinstance(message, str):
            raise TypeError("Acknowledgement messages must be text.")
        if not self._remaining:
            raise LookupError("No acknowledgement response remains.")
        self._remaining -= 1
