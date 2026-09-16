"""Runtime time vocabulary, independent of the host Python clock."""


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
