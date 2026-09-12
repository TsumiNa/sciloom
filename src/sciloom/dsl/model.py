"""Host-specialized Function instances and runtime source registration."""

from __future__ import annotations

from functools import wraps
from types import MappingProxyType
from typing import Any, Callable, ClassVar, Mapping, ParamSpec, TypeVar
from ..core.ir import Program
from ..core.compiler import CompileResult, Target, compile_ir
from .schema import RuntimeField, build_schema


P = ParamSpec("P")
R = TypeVar("R")


def runtime(method: Callable[P, R]) -> Callable[P, R]:
    """Register source for compilation and prevent accidental host execution."""

    @wraps(method)
    def registered(*args: P.args, **kwargs: P.kwargs) -> R:
        raise TypeError("SciLoom runtime methods must be compiled, not executed as Python.")

    setattr(registered, "__sciloom_runtime__", method)
    return registered


class Function:
    """Base for statically declared, instance-specialized SciLoom functions.

    Declare runtime fields with Input[T], Output[T] or Var[T]; other annotations
    describe host configuration. Var requires an explicit initial value, retained
    across calls rather than reset automatically. Use class docstrings for the
    function's purpose and an Attributes section keyed by runtime field names.
    Constructor Args document host specialization. These descriptions help authors
    and future tooling; field declarations and IR define execution semantics.
    """

    model_fields: ClassVar[Mapping[str, RuntimeField]] = MappingProxyType({})

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls.model_fields = build_schema(cls, Function.__dict__)

    def to_ir(self) -> Program:
        """Lower this instance without changing its configuration or runtime schema."""
        from .lowering import lower

        return lower(self)

    def compile(self, *, target: Target) -> CompileResult:
        """Compile this specialized instance using an explicit compilation target."""
        return compile_ir(self.to_ir(), target=target)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        raise TypeError("Function calls in @runtime methods are compiled, not executed as Python.")
