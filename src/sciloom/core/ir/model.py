"""Target-independent semantics for the SciLoom scientific programs.

IDs identify semantic occurrences, never XML objects. Tuples and frozen records
make a validated package safe to share between frontends without hidden mutation.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar

from sciloom.core.diagnostics import SourceSpan
from .device_contracts import DeviceTypeContract
from .types import ListType, ScalarType, ValueType


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
    """Sign, magnitude, integer rounding and Boolean negation operations.

    FLOOR and ROUND return integers; ROUND uses Python ties-to-even semantics.
    ABSOLUTE preserves the operand's numeric or signed-quantity type.
    """

    POSITIVE = "+"
    NEGATIVE = "-"
    NOT = "not"
    ABSOLUTE = "abs"
    FLOOR = "floor"
    ROUND = "round"


@dataclass(frozen=True, kw_only=True)
class Node:
    """Semantic occurrence with a program-unique ID and optional source position."""

    __ir_kind__: ClassVar[str] = "Node"

    node_id: str
    source: SourceSpan | None = None


@dataclass(frozen=True, kw_only=True)
class Literal(Node):
    """Typed scalar constant; rotational speeds store canonical revolutions per second."""

    __ir_kind__: ClassVar[str] = "Literal"

    type: ScalarType
    value: bool | int | float | str


@dataclass(frozen=True, kw_only=True)
class Reference(Node):
    """Read a variable by its semantic symbol ID, within the owning function."""

    __ir_kind__: ClassVar[str] = "Reference"

    symbol_id: str


@dataclass(frozen=True, kw_only=True)
class Unary(Node):
    """Apply a typed unary operation to one expression."""

    __ir_kind__: ClassVar[str] = "Unary"

    op: UnaryOp
    operand: "Expression"


@dataclass(frozen=True, kw_only=True)
class Binary(Node):
    """Combine two expressions; AND and OR short-circuit in reference execution."""

    __ir_kind__: ClassVar[str] = "Binary"

    op: BinaryOp
    left: "Expression"
    right: "Expression"


@dataclass(frozen=True, kw_only=True)
class ListLiteral(Node):
    """Construct a typed list by evaluating elements in order; empty lists retain type."""

    __ir_kind__: ClassVar[str] = "ListLiteral"

    type: ListType
    elements: tuple["Expression", ...] = ()


@dataclass(frozen=True, kw_only=True)
class ListLength(Node):
    """Return the integer length of a list expression."""

    __ir_kind__: ClassVar[str] = "ListLength"

    value: "Expression"


@dataclass(frozen=True, kw_only=True)
class ListGet(Node):
    """Read an existing element using a nonnegative integer index; bool is invalid."""

    __ir_kind__: ClassVar[str] = "ListGet"

    value: "Expression"
    index: "Expression"


@dataclass(frozen=True, kw_only=True)
class TextLength(Node):
    """Count Unicode code points without encoding conversion or normalization."""

    __ir_kind__: ClassVar[str] = "TextLength"

    value: "Expression"


@dataclass(frozen=True, kw_only=True)
class TextTrim(Node):
    """Remove only space, tab, CR and LF at both ends of a text value."""

    __ir_kind__: ClassVar[str] = "TextTrim"

    value: "Expression"


@dataclass(frozen=True, kw_only=True)
class TextSplitPart(Node):
    """Split on a nonempty delimiter and select a nonnegative part; missing means empty."""

    __ir_kind__: ClassVar[str] = "TextSplitPart"

    value: "Expression"
    delimiter: "Expression"
    index: "Expression"


Expression = (
    Literal | Reference | Unary | Binary | ListLiteral | ListLength | ListGet | TextLength | TextTrim | TextSplitPart
)
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

    __ir_kind__: ClassVar[str] = "Variable"

    owner_id: str
    name: str
    role: VariableRole
    type: ValueType
    initial: Literal | ListLiteral | None = None


@dataclass(frozen=True, kw_only=True)
class Assignment(Node):
    """Capture an expression value into a variable, copying list values."""

    __ir_kind__: ClassVar[str] = "Assignment"

    target: Reference
    value: Expression


@dataclass(frozen=True, kw_only=True)
class LogValue(Node):
    """Capture a scalar/quantity, category and stream once, in that order.

    The value's type is derived from its expression. Category and stream must be
    text. Logging is ordered with other statements and never measures a device.
    """

    __ir_kind__: ClassVar[str] = "LogValue"

    value: Expression
    category: Expression
    stream: Expression


@dataclass(frozen=True, kw_only=True)
class Notify(Node):
    """Capture one text message and require OK before the next statement.

    No value is returned. Missing acknowledgement prevents subsequent effects;
    neither a timeout nor an automatic confirmation is implied.
    """

    __ir_kind__: ClassVar[str] = "Notify"

    message: Expression


@dataclass(frozen=True, kw_only=True)
class ReadWallTime(Node):
    """Read wall time once and assign its formatted text to a declared field.

    The constant format is portable and locale-independent. This ordered
    operation cannot be embedded in a value expression or duplicated by codegen.
    """

    __ir_kind__: ClassVar[str] = "ReadWallTime"

    target: Reference
    format: str


class CsvReadMode(StrEnum):
    """Read one zero-based data row or all rows of selected columns."""

    ROW = "row"
    COLUMNS = "columns"


class CsvErrorPolicy(StrEnum):
    """Stop on CSV failure or return a status with a complete fallback payload."""

    RAISE = "raise"
    STATUS = "status"


@dataclass(frozen=True, kw_only=True)
class CsvColumn:
    """One typed CSV selection, independent of vendor parsing or variable names.

    Attributes:
        index: Zero-based nonnegative integer selector captured before reading.
        type: Scalar result type; column mode returns a list of this type.
        unit: Positive quantity literal for one input unit in canonical SI.
        default: Optional typed fallback for missing or invalid cells, already in SI.
    """

    __ir_kind__: ClassVar[str] = "CsvColumn"

    index: Expression
    type: ScalarType
    unit: Literal | None = None
    default: Expression | None = None


@dataclass(frozen=True, kw_only=True)
class ReadCsv(Node):
    """Capture selectors/defaults, read a file and commit all typed results together.

    Targets are ordered column results, with an INTEGER status first for STATUS
    policy. A single column still has one explicit result binding. A failed
    RAISE read leaves every destination unchanged and stops later operations.
    """

    __ir_kind__: ClassVar[str] = "ReadCsv"

    mode: CsvReadMode
    error_policy: CsvErrorPolicy
    path: Expression
    header: bool
    columns: tuple[CsvColumn, ...]
    targets: tuple[Reference, ...]
    row: Expression | None = None


@dataclass(frozen=True, kw_only=True)
class AppendCsv(Node):
    """Capture an ordered scalar row and append it with explicit failure policy.

    Attributes:
        path: Runtime text path captured before the row values.
        values: Nonempty ordered scalar expressions; quantities use canonical SI.
        error_policy: Stop on I/O failure or return a status after the attempt.
        status: Integer destination required only for STATUS policy.

    A failed write may have external partial effects; it is never rolled back.
    """

    __ir_kind__: ClassVar[str] = "AppendCsv"

    path: Expression
    values: tuple[Expression, ...]
    error_policy: CsvErrorPolicy = CsvErrorPolicy.RAISE
    status: Reference | None = None


@dataclass(frozen=True, kw_only=True)
class Wait(Node):
    """Capture a nonnegative Duration and wait without changing device state."""

    __ir_kind__: ClassVar[str] = "Wait"

    duration: Expression


@dataclass(frozen=True, kw_only=True)
class StartTimer(Node):
    """Set or reset a Function-owned timer's monotonic origin."""

    __ir_kind__: ClassVar[str] = "StartTimer"

    resource_id: str


@dataclass(frozen=True, kw_only=True)
class WaitUntil(Node):
    """Wait until a captured Duration has elapsed from the timer's latest start."""

    __ir_kind__: ClassVar[str] = "WaitUntil"

    resource_id: str
    duration: Expression


@dataclass(frozen=True, kw_only=True)
class ListSet(Node):
    """Update one existing element; an augmented op evaluates the index/read once."""

    __ir_kind__: ClassVar[str] = "ListSet"

    target: Reference
    index: Expression
    value: Expression
    op: BinaryOp | None = None


@dataclass(frozen=True, kw_only=True)
class InputBinding:
    """Bind a callee input parameter ID to a caller expression, by value."""

    __ir_kind__: ClassVar[str] = "InputBinding"

    parameter_id: str
    value: Expression


@dataclass(frozen=True, kw_only=True)
class OutputBinding:
    """Copy a callee output parameter back into a caller variable."""

    __ir_kind__: ClassVar[str] = "OutputBinding"

    parameter_id: str
    target: Reference


@dataclass(frozen=True, kw_only=True)
class Call(Node):
    """Invoke a function by occurrence ID with explicit input and output bindings."""

    __ir_kind__: ClassVar[str] = "Call"

    function_id: str
    inputs: tuple[InputBinding, ...] = ()
    outputs: tuple[OutputBinding, ...] = ()


@dataclass(frozen=True, kw_only=True)
class If(Node):
    """Select a runtime branch using a Boolean expression; no implicit truthiness."""

    __ir_kind__: ClassVar[str] = "If"

    condition: Expression
    then_body: tuple["Statement", ...] = ()
    else_body: tuple["Statement", ...] = ()


@dataclass(frozen=True, kw_only=True)
class While(Node):
    """Repeat a body while a Boolean expression remains true; zero iterations are possible."""

    __ir_kind__: ClassVar[str] = "While"

    condition: Expression
    body: tuple["Statement", ...] = ()


@dataclass(frozen=True, kw_only=True)
class DeviceResource(Node):
    """A typed logical device, independent of deployment addresses."""

    __ir_kind__: ClassVar[str] = "DeviceResource"

    logical_id: str
    device_type_id: str


@dataclass(frozen=True, kw_only=True)
class TimerResource(Node):
    """A Function-owned elapsed-time reference, never a hardware binding.

    Attributes:
        owner_id: The only FunctionIR allowed to start or wait on this timer.
        name: Public declaration name, unique within the owning Function.
    """

    __ir_kind__: ClassVar[str] = "TimerResource"

    owner_id: str
    name: str


Resource = DeviceResource | TimerResource
"""Closed set of logical resources; only devices require Target deployment."""


@dataclass(frozen=True, kw_only=True)
class ConfigureProperty(Node):
    """Capture a value now; it is applied only by the device's explicit command."""

    __ir_kind__: ClassVar[str] = "ConfigureProperty"

    resource_id: str
    property_id: str
    value: Expression


@dataclass(frozen=True, kw_only=True)
class StartAgitation(Node):
    """Apply the complete saved configuration and enable/reapply agitation."""

    __ir_kind__: ClassVar[str] = "StartAgitation"

    resource_id: str


@dataclass(frozen=True, kw_only=True)
class StopAgitation(Node):
    """Disable the resource without promising any physical mixing outcome."""

    __ir_kind__: ClassVar[str] = "StopAgitation"

    resource_id: str


@dataclass(frozen=True, kw_only=True)
class CommandArgument:
    """Named expression argument for a declared device command."""

    __ir_kind__: ClassVar[str] = "CommandArgument"

    name: str
    value: Expression


@dataclass(frozen=True, kw_only=True)
class DeviceCommand(Node):
    """Invoke a declared extension command with no return value."""

    __ir_kind__: ClassVar[str] = "DeviceCommand"

    resource_id: str
    operation_id: str
    arguments: tuple[CommandArgument, ...] = ()


@dataclass(frozen=True, kw_only=True)
class CanWrite(Node):
    """Compile-time query for a bound resource's writable property semantic ID."""

    __ir_kind__: ClassVar[str] = "CanWrite"

    resource_id: str
    property_id: str


@dataclass(frozen=True, kw_only=True)
class SupportsOperation(Node):
    """Compile-time query for a bound resource's supported command semantic ID."""

    __ir_kind__: ClassVar[str] = "SupportsOperation"

    resource_id: str
    operation_id: str


@dataclass(frozen=True, kw_only=True)
class IsDevice(Node):
    """Compile-time query for a bound resource's concrete type or ancestor identity."""

    __ir_kind__: ClassVar[str] = "IsDevice"

    resource_id: str
    device_type_id: str


DevicePredicate = CanWrite | SupportsOperation | IsDevice
"""Device queries resolved from trusted deployment facts during specialization."""


@dataclass(frozen=True, kw_only=True)
class DeviceIf(Node):
    """Preserve both device-dependent branches until trusted binding specialization."""

    __ir_kind__: ClassVar[str] = "DeviceIf"

    condition: DevicePredicate
    then_body: tuple["Statement", ...] = ()
    else_body: tuple["Statement", ...] = ()


Statement = (
    Assignment
    | LogValue
    | Notify
    | ReadWallTime
    | ReadCsv
    | AppendCsv
    | Wait
    | StartTimer
    | WaitUntil
    | ListSet
    | Call
    | If
    | While
    | ConfigureProperty
    | StartAgitation
    | StopAgitation
    | DeviceCommand
    | DeviceIf
)
"""Closed set of high-level flow, state and device operations."""


@dataclass(frozen=True, kw_only=True)
class FunctionIR(Node):
    """One callable semantic function with owned variables and ordered statements."""

    __ir_kind__: ClassVar[str] = "FunctionIR"

    name: str
    variables: tuple[Variable, ...] = ()
    body: tuple[Statement, ...] = ()


@dataclass(frozen=True, kw_only=True)
class Program:
    """A selected entry function and the functions packaged with it.

    Internal variables belong to functions here. The XML backend determines the
    corresponding Macro containers. Application/global state is not supported yet.
    """

    __ir_kind__: ClassVar[str] = "Program"

    entry_function_id: str
    functions: tuple[FunctionIR, ...] = ()
    resources: tuple[Resource, ...] = ()
    device_types: tuple[DeviceTypeContract, ...] = ()
    format_version: int = 4
