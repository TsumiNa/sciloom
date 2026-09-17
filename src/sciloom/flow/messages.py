"""Runtime messages requiring acknowledgement before the next experiment step."""

from sciloom.units import Duration


def request_text(message: str, *, timeout: Duration | None = None) -> str:
    """Request one text result, including a valid empty string.

    Args:
        message: Text captured once before timeout evaluation.
        timeout: Optional positive duration; reaching the deadline terminates.

    Returns:
        Accepted text, assigned as a whole RHS to a declared runtime field.

    Raises:
        TypeError: Called by host Python instead of written in a runtime method.

    Cancellation, Stop, timeout and absent responses terminate the experiment;
    there is no fallback. Reference execution requires an explicit dialog service.
    """
    raise TypeError("Text requests belong in compiled @runtime assignments.")


def ask_yes_no(message: str, *, timeout: Duration | None = None) -> bool:
    """Request one Boolean result; No is a normal False result.

    Args:
        message: Text captured once before timeout evaluation.
        timeout: Optional positive duration; reaching the deadline terminates.

    Returns:
        Accepted bool, assigned as a whole RHS to a declared runtime field.

    Raises:
        TypeError: Called by host Python instead of written in a runtime method.

    Cancellation, Stop, timeout and absent responses terminate without returning
    a default or performing following effects.
    """
    raise TypeError("Yes/no requests belong in compiled @runtime assignments.")


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
