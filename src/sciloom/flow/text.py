"""Typed text operations for use inside compiled runtime methods."""


def trim(value: str) -> str:
    """Remove space, tab, carriage return and line feed from both ends.

    Args:
        value: Runtime text to trim; other Unicode whitespace is retained.

    Returns:
        Trimmed runtime text, without changing the input.

    Raises:
        TypeError: Called by host Python instead of written in a runtime method.
    """
    raise TypeError("Text operations belong in compiled @runtime methods.")


def split_part(value: str, delimiter: str, index: int) -> str:
    """Select one zero-based part, retaining empty parts between delimiters.

    Args:
        value: Runtime text to split.
        delimiter: Nonempty text separating parts; treated literally.
        index: Nonnegative integer part index, excluding bool.

    Returns:
        The selected text, or empty text if the part does not exist.

    Raises:
        TypeError: Called by host Python instead of written in a runtime method.
        sciloom.core.diagnostics.ExecutionError: Reference execution encounters
            an empty delimiter or negative index.
    """
    raise TypeError("Text operations belong in compiled @runtime methods.")
