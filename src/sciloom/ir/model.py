"""Target-independent semantics for the first AutoSuite Function compiler.

IDs identify semantic occurrences, never XML objects. Tuples and frozen records
make a validated package safe to share between frontends without hidden mutation.
"""

from dataclasses import dataclass
from enum import StrEnum


class ScalarType(StrEnum):
    INTEGER = "integer"
    REAL = "real"
    BOOLEAN = "boolean"


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
class SourceSpan:
    """Optional Python origin: one-based line, zero-based UTF-8 byte column."""

    path: str
    line: int
    column: int = 0


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


Statement = Assignment | Call | If | While


@dataclass(frozen=True, kw_only=True)
class FunctionIR(Node):
    name: str
    variables: tuple[Variable, ...] = ()
    body: tuple[Statement, ...] = ()


@dataclass(frozen=True, kw_only=True)
class Package:
    """A selected entry function and the functions packaged with it.

    Internal variables belong to functions here. The XML backend determines the
    corresponding Macro containers. Application/global state is not supported yet.
    """

    entry_function_id: str
    functions: tuple[FunctionIR, ...] = ()
    format_version: int = 1
