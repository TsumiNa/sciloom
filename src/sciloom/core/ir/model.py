"""Target-independent semantics for the SciLoom scientific programs.

IDs identify semantic occurrences, never XML objects. Tuples and frozen records
make a validated package safe to share between frontends without hidden mutation.
"""

from dataclasses import dataclass
from enum import StrEnum

from ..diagnostics import SourceSpan
from .types import ScalarType


class VariableRole(StrEnum):
    INPUT = "input"
    OUTPUT = "output"
    INTERNAL = "internal"


class BinaryOp(StrEnum):
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
    POSITIVE = "+"
    NEGATIVE = "-"
    NOT = "not"


@dataclass(frozen=True, kw_only=True)
class Node:
    node_id: str
    source: SourceSpan | None = None


@dataclass(frozen=True, kw_only=True)
class Literal(Node):
    type: ScalarType
    value: bool | int | float


@dataclass(frozen=True, kw_only=True)
class Reference(Node):
    symbol_id: str


@dataclass(frozen=True, kw_only=True)
class Unary(Node):
    op: UnaryOp
    operand: "Expression"


@dataclass(frozen=True, kw_only=True)
class Binary(Node):
    op: BinaryOp
    left: "Expression"
    right: "Expression"


Expression = Literal | Reference | Unary | Binary


@dataclass(frozen=True, kw_only=True)
class Variable(Node):
    owner_id: str
    name: str
    role: VariableRole
    type: ScalarType
    initial: Literal | None = None


@dataclass(frozen=True, kw_only=True)
class Assignment(Node):
    target: Reference
    value: Expression


@dataclass(frozen=True, kw_only=True)
class InputBinding:
    parameter_id: str
    value: Expression


@dataclass(frozen=True, kw_only=True)
class OutputBinding:
    parameter_id: str
    target: Reference


@dataclass(frozen=True, kw_only=True)
class Call(Node):
    function_id: str
    inputs: tuple[InputBinding, ...] = ()
    outputs: tuple[OutputBinding, ...] = ()


@dataclass(frozen=True, kw_only=True)
class If(Node):
    condition: Expression
    then_body: tuple["Statement", ...] = ()
    else_body: tuple["Statement", ...] = ()


@dataclass(frozen=True, kw_only=True)
class While(Node):
    condition: Expression
    body: tuple["Statement", ...] = ()


@dataclass(frozen=True, kw_only=True)
class AgitatorResource(Node):
    """A logical agitation controller, independent of zones and vendor IDs."""

    logical_id: str


@dataclass(frozen=True, kw_only=True)
class SetAgitation(Node):
    """Enable the resource and command its rotational-speed setpoint."""

    resource_id: str
    speed: Expression


@dataclass(frozen=True, kw_only=True)
class StopAgitation(Node):
    """Disable the resource without promising any physical mixing outcome."""

    resource_id: str


Statement = Assignment | Call | If | While | SetAgitation | StopAgitation


@dataclass(frozen=True, kw_only=True)
class FunctionIR(Node):
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
    resources: tuple[AgitatorResource, ...] = ()
    format_version: int = 2
