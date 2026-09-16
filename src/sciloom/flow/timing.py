"""Runtime time vocabulary, independent of the host Python clock."""

from sciloom.units import Duration


class Timer:
    """Declare a Function-owned elapsed-time resource with ``timer: Timer``.

    A timer is not a runtime value or a device. It cannot be constructed or
    shared by host Python. Its start must precede every reachable wait in the
    current entry invocation; no previous run supplies an implicit start.
    """

    def __init__(self) -> None:
        raise TypeError("Declare timers with a bare Timer annotation on a Function.")

    def start(self) -> None:
        """Set or reset this timer's monotonic origin at this runtime step.

        Raises:
            TypeError: Called by host Python instead of compiled runtime source.
        """
        raise TypeError("Timer operations belong in compiled @runtime methods.")

    def wait_until(self, duration: Duration) -> None:
        """Wait until duration has elapsed since the latest start.

        Args:
            duration: Nonnegative elapsed threshold; already elapsed means no wait.

        Raises:
            TypeError: Called by host Python instead of compiled runtime source.

        Waiting preserves device configuration and running state.
        """
        raise TypeError("Timer operations belong in compiled @runtime methods.")


def wait(duration: Duration) -> None:
    """Pause runtime flow for a captured interval without changing devices.

    Args:
        duration: Nonnegative interval.

    Raises:
        TypeError: Called by host Python instead of compiled runtime source.

    Reference execution advances an explicitly provided virtual clock; it never
    sleeps. AutoSuite compilation does not start a wait on the host computer.
    """
    raise TypeError("Waits belong in compiled @runtime methods.")


def now_text(format: str) -> str:
    """Read wall time once and format it into a declared runtime text field.

    Args:
        format: Host-time text using %Y, %m, %d, %H, %M, %S, %% and literal text.

    Returns:
        Formatted runtime time. Assign the entire call to one text field before
        using the result in a larger expression.

    AutoSuite uses platform-local time; reference execution needs an explicit
    aware wall clock. This does not guarantee a unique filename.

    Raises:
        TypeError: Called by host Python instead of written in a runtime method.
    """
    raise TypeError("Wall-time reads belong in compiled @runtime methods.")
