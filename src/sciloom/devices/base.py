"""Device category identity, independent of deployment and Python lowering."""

from typing import ClassVar


class BaseDevice:
    """Base for device contracts; individual categories define their operations."""

    device_type_id: ClassVar[str] = "sciloom.device/v1"
