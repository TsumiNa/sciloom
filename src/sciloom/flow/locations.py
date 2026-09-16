"""Explicit runtime location scopes for bounded logical device selections."""

from contextlib import AbstractContextManager

from sciloom.core.locations import Zone
from sciloom.devices.base import BaseDevice


def at(device: BaseDevice, location: Zone) -> AbstractContextManager[None]:
    """Select a compatible physical controller for a lexical runtime body.

    Args:
        device: Declared logical device slot, bound to trusted candidates.
        location: Captured nonempty selection within one candidate's allowed wells.

    Returns:
        A source-language context marker used only by ``with at(...)``.

    Raises:
        TypeError: Called from host Python instead of compiled runtime code.
        sciloom.core.diagnostics.ExecutionError: The captured selection is invalid.

    Shared-device child calls inherit the selection. Leaving the scope does not
    stop equipment or undo effects; call stop explicitly when required. Different
    resources can nest, but the same resource cannot be selected again inside a
    scope, including through a child call.
    """
    raise TypeError("at() belongs in a with statement inside compiled @runtime methods.")
