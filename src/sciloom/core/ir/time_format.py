"""The portable, locale-independent subset of wall-time format directives."""

import re


def validate_wall_time_format(format: str) -> None:
    """Reject unknown directives and dangling percent signs.

    Args:
        format: Constant format text; ordinary characters and empty text are valid.

    Raises:
        ValueError: A directive is outside Y, m, d, H, M, S or literal percent.
    """
    for match in re.finditer(r"%(.)?", format, flags=re.DOTALL):
        directive = match.group(1)
        if directive is None or directive not in "YmdHMS%":
            raise ValueError(f"Unsupported wall-time directive {match.group()!r}; use %Y, %m, %d, %H, %M, %S or %%.")
