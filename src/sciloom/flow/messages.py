"""Runtime messages requiring acknowledgement before the next experiment step."""


def notify(message: str) -> None:
    """Display a message and wait for an explicit OK acknowledgement.

    Args:
        message: Runtime text, captured once when this operation begins.

    Subsequent steps execute only after acknowledgement. This operation has no
    return value, timeout, cancellation branch or implicit confirmation.

    Raises:
        TypeError: Called by host Python instead of written in a runtime method.
    """
    raise TypeError("Notifications belong in compiled @runtime methods.")
