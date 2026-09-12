"""Device category identity, independent of deployment and Python lowering."""

from functools import wraps
from typing import Any, ClassVar, NoReturn


class BaseDevice:
    """Base for device contracts; individual categories define their operations."""

    device_type_id: ClassVar[str] = "sciloom.device/v1"

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        for name, member in tuple(vars(cls).items()):
            if isinstance(member, property) and member.fget is not None and getattr(member.fset, "__sciloom_operation_id__", None):
                @wraps(member.fget)
                def blocked(instance: object) -> NoReturn:
                    raise TypeError("Device property reads are not supported yet.")

                setattr(cls, name, member.getter(blocked))
