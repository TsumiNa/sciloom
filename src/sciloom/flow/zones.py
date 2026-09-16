"""Runtime queries over a fixed location directory and ordered Zone values."""

from collections.abc import Iterable

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


def fragments(value: Zone, *, size: int) -> Iterable[Zone]:
    """Visit fixed-size groups in a runtime for loop over a captured Zone.

    Args:
        value: Selection captured once before iteration.
        size: Positive host-time integer; the well count must be divisible by it.

    Returns:
        A runtime-only iterable for a declared Var[Zone] loop target. Empty
        selections skip the body and preserve the target's previous value.

    Raises:
        TypeError: Called by host Python instead of as a runtime for iterable.

    Reference execution rejects incomplete final groups before assigning the
    target or executing the body. Equipment targets may restrict grouping until
    their runtime failure propagation has been verified.
    """
    raise TypeError("zones.fragments is only available as a @runtime for iterable.")
