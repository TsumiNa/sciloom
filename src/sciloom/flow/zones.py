"""Runtime queries over a fixed location directory and ordered Zone values."""

from sciloom.core.locations import Zone


def find(name: str) -> Zone:
    """Find a named Zone, returning an empty Zone when the name is unknown.

    Args:
        name: Exact runtime directory name.

    Returns:
        The directory's ordered well references.

    Raises:
        TypeError: Called by host Python instead of inside a runtime method.
    """
    raise TypeError("zones.find is only available inside @runtime methods.")


def combine(left: Zone, right: Zone) -> Zone:
    """Combine Zones in first-occurrence order, including each well only once.

    Args:
        left: Wells that appear first in the result.
        right: Additional wells, preserving their order.

    Returns:
        An independent, immutable Zone value.

    Raises:
        TypeError: Called by host Python instead of inside a runtime method.
    """
    raise TypeError("zones.combine is only available inside @runtime methods.")


def well_name(value: Zone) -> str:
    """Return the directory display name of exactly one known well.

    Args:
        value: A Zone containing one well.

    Returns:
        The display label, which is not a well identity or a numeric index.

    Raises:
        TypeError: Called by host Python instead of inside a runtime method.

    Reference execution rejects empty/multiple wells, unknown identities and a
    missing location directory. Target support depends on its cardinality checks.
    """
    raise TypeError("zones.well_name is only available inside @runtime methods.")
