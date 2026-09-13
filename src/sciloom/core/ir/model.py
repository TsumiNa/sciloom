"""Target-independent semantics for the SciLoom scientific programs.

IDs identify semantic occurrences, never XML objects. Tuples and frozen records
make a validated package safe to share between frontends without hidden mutation.
"""

from dataclasses import dataclass
from enum import StrEnum

from ..diagnostics import SourceSpan
from .types import ListType, ScalarType, ValueType
from .device_contracts import DeviceTypeContract


class VariableRole(StrEnum):
    """Function input, output or persistent internal state."""
    INPUT = "input"
    OUTPUT = "output"
    INTERNAL = "internal"


class BinaryOp(StrEnum):
    """Arithmetic, comparison and Boolean operations with typed IR semantics."""
    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    EQUAL = "=="
    NOT_EQUAL = "!="
    LESS = "<"
    LESS_EQUAL = "<="
    GREATER = ">"
    GREATER_EQUAL = ">="
    AND = "and"
    OR = "or"


class UnaryOp(StrEnum):
    """Numeric sign and Boolean negation operations."""
    POSITIVE = "+"
    NEGATIVE = "-"
    NOT = "not"


@dataclass(frozen=True, kw_only=True)
class Node:
    """Semantic occurrence with a program-unique ID and optional source position."""
    node_id: str
    source: SourceSpan | None = None


@dataclass(frozen=True, kw_only=True)
class Literal(Node):
    """Typed scalar constant; rotational speeds store canonical revolutions per second."""
    type: ScalarType
    value: bool | int | float


@dataclass(frozen=True, kw_only=True)
class Reference(Node):
    """Read a variable by its semantic symbol ID, within the owning function."""
    symbol_id: str


@dataclass(frozen=True, kw_only=True)
class Unary(Node):
    """Apply a typed unary operation to one expression."""
    op: UnaryOp
    operand: "Expression"


@dataclass(frozen=True, kw_only=True)
class Binary(Node):
    """Combine two expressions; AND and OR short-circuit in reference execution."""
    op: BinaryOp
    left: "Expression"
    right: "Expression"


@dataclass(frozen=True, kw_only=True)
class ListLiteral(Node):
    """Construct a typed list by evaluating elements in order; empty lists retain type."""
    type: ListType
    elements: tuple["Expression", ...] = ()


@dataclass(frozen=True, kw_only=True)
class ListLength(Node):
    """Return the integer length of a list expression."""
    value: "Expression"


@dataclass(frozen=True, kw_only=True)
class ListGet(Node):
    """Read an existing element using a nonnegative integer index; bool is invalid."""
    value: "Expression"
    index: "Expression"


Expression = Literal | Reference | Unary | Binary | ListLiteral | ListLength | ListGet
"""Closed set of typed runtime expressions."""


@dataclass(frozen=True, kw_only=True)
class Variable(Node):
    """Function-owned runtime field.

    Attributes:
        owner_id: Owning FunctionIR occurrence ID.
        name: User-facing field name.
        role: Input, output or persistent internal state.
        type: Scalar or homogeneous list type.
        initial: Required literal default for internal state; not reset on each call."""
    owner_id: str
    name: str
    role: VariableRole
    type: ValueType
    initial: Literal | ListLiteral | None = None


@dataclass(frozen=True, kw_only=True)
class Assignment(Node):
    """Capture an expression value into a variable, copying list values."""
    target: Reference
    value: Expression


@dataclass(frozen=True, kw_only=True)
class ListSet(Node):
    """Update one existing element; an augmented op evaluates the index/read once."""

    target: Reference
    index: Expression
    value: Expression
    op: BinaryOp | None = None


@dataclass(frozen=True, kw_only=True)
class InputBinding:
    """Bind a callee input parameter ID to a caller expression, by value."""
    parameter_id: str
    value: Expression


@dataclass(frozen=True, kw_only=True)
class OutputBinding:
    """Copy a callee output parameter back into a caller variable."""
    parameter_id: str
    target: Reference


@dataclass(frozen=True, kw_only=True)
class Call(Node):
    """Invoke a function by occurrence ID with explicit input and output bindings."""
    function_id: str
    inputs: tuple[InputBinding, ...] = ()
    outputs: tuple[OutputBinding, ...] = ()


@dataclass(frozen=True, kw_only=True)
class If(Node):
    """Select a runtime branch using a Boolean expression; no implicit truthiness."""
    condition: Expression
    then_body: tuple["Statement", ...] = ()
    else_body: tuple["Statement", ...] = ()


@dataclass(frozen=True, kw_only=True)
class While(Node):
    """Repeat a body while a Boolean expression remains true; zero iterations are possible."""
    condition: Expression
    body: tuple["Statement", ...] = ()


@dataclass(frozen=True, kw_only=True)
class DeviceResource(Node):
    """A typed logical device, independent of deployment addresses."""

    logical_id: str
    device_type_id: str


@dataclass(frozen=True, kw_only=True)
class ConfigureProperty(Node):
    """Capture a value now; it is applied only by the device's explicit command."""

    resource_id: str
    property_id: str
    value: Expression


@dataclass(frozen=True, kw_only=True)
class StartAgitation(Node):
    """Apply the complete saved configuration and enable/reapply agitation."""

    resource_id: str


@dataclass(frozen=True, kw_only=True)
class StopAgitation(Node):
    """Disable the resource without promising any physical mixing outcome."""

    resource_id: str


@dataclass(frozen=True, kw_only=True)
class CommandArgument:
    """Named expression argument for a declared device command."""
    name: str
    value: Expression


@dataclass(frozen=True, kw_only=True)
class DeviceCommand(Node):
    """Invoke a declared extension command with no return value."""
    resource_id: str
    operation_id: str
    arguments: tuple[CommandArgument, ...] = ()


@dataclass(frozen=True, kw_only=True)
class CanWrite(Node):
    """Compile-time query for a bound resource's writable property semantic ID."""
    resource_id: str
    property_id: str


@dataclass(frozen=True, kw_only=True)
class SupportsOperation(Node):
    """Compile-time query for a bound resource's supported command semantic ID."""
    resource_id: str
    operation_id: str


@dataclass(frozen=True, kw_only=True)
class IsDevice(Node):
    """Compile-time query for a bound resource's concrete type or ancestor identity."""
    resource_id: str
    device_type_id: str


DevicePredicate = CanWrite | SupportsOperation | IsDevice
"""Device queries resolved from trusted deployment facts during specialization."""


@dataclass(frozen=True, kw_only=True)
class DeviceIf(Node):
    """Preserve both device-dependent branches until trusted binding specialization."""
    condition: DevicePredicate
    then_body: tuple["Statement", ...] = ()
    else_body: tuple["Statement", ...] = ()


Statement = Assignment | ListSet | Call | If | While | ConfigureProperty | StartAgitation | StopAgitation | DeviceCommand | DeviceIf
"""Closed set of high-level flow, state and device operations."""


@dataclass(frozen=True, kw_only=True)
class FunctionIR(Node):
    """One callable semantic function with owned variables and ordered statements."""
    name: str
    variables: tuple[Variable, ...] = ()
    body: tuple[Statement, ...] = ()


@dataclass(frozen=True, kw_only=True)
class Program:
    """A selected entry function and the functions packaged with it.

    Internal variables belong to functions here. The XML backend determines the
    corresponding Macro containers. Application/global state is not supported yet.
    """

    entry_function_id: str
    functions: tuple[FunctionIR, ...] = ()
    resources: tuple[DeviceResource, ...] = ()
    device_types: tuple[DeviceTypeContract, ...] = ()
    format_version: int = 4
