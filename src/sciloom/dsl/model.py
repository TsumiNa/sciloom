"""Host-specialized Function instances and runtime source registration."""

from __future__ import annotations

from functools import wraps
from types import MappingProxyType
from typing import Any, Callable, ClassVar, Mapping, ParamSpec, TypeVar
from ..core.ir import Program
from ..core.compiler import CompileResult, Target, compile_ir
from .schema import RuntimeField, build_schema
from .device_schema import DeviceSlot, build_device_schema


P = ParamSpec("P")
R = TypeVar("R")


def runtime(method: Callable[P, R]) -> Callable[P, R]:
    """Register a method's source for compilation, preserving its type signature.
    
    Args:
        method: Runtime method declared in an ordinary Python source file.
    
    Returns:
        A guarded method whose body is analyzed rather than executed by Python.
    
    Raises:
        TypeError: The decorated method is called by host Python."""

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
    device_fields: ClassVar[Mapping[str, DeviceSlot]] = MappingProxyType({})

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls.model_fields = build_schema(cls, Function.__dict__)
        cls.device_fields = build_device_schema(cls, Function.__dict__)

    def to_ir(self) -> Program:
        """Build target-independent IR from this specialized instance.
        
        Returns:
            The authored program, including both sides of device conditions.
        
        Raises:
            IRValidationError: Declarations or runtime source violate the DSL.
        
        The instance's host configuration and runtime schema are not mutated."""
        from .lowering import lower

        return lower(self)

    def compile(self, *, target: Target) -> CompileResult:
        """Compile this instance for an explicitly selected platform.
        
        Args:
            target: Target providing trusted device bindings, validation and emission.
        
        Returns:
            Authored and specialized IR together with the target artifact.
        
        Raises:
            IRValidationError: The source or semantic model is invalid.
            CompilationError: Bindings, capabilities or target rules reject the program.
            TypeError: The target does not implement the compiler protocol."""
        return compile_ir(self.to_ir(), target=target)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        raise TypeError("Function calls in @runtime methods are compiled, not executed as Python.")
