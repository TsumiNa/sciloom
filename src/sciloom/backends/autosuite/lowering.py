"""AutoSuite 2.47.1.1 Function backend derived from FIXED/re-export evidence.

Envelopes and default ordering: Test11/Test12; conditional Macro/branch nesting:
Test08/Test09/Test10_FIXED3. Scalar storage codes/units also use the latest APP.
No reference corpus file is read or modified at compiler runtime.

Type identifiers retain the observed fixed .1 suffix; its formal meaning and
cross-version compatibility await vendor confirmation. See the "typeid suffix"
open question in autosuite/docs/05_SCHEMA_EXTRACTION_AND_CONFIRMED_STRUCTURE.md.
"""

import hashlib
import json
import re
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from ...ir import (
    Assignment,
    BinaryOp,
    Call,
    Expression,
    FunctionIR,
    If,
    Literal,
    Package,
    Reference,
    ScalarType,
    Statement,
    Unary,
    Variable,
    VariableRole,
    While,
    to_dict,
)
from .xml import SerializationIR, Target, XmlNode

_PARAMETER_TYPES = {ScalarType.INTEGER: "integer", ScalarType.REAL: "realnumber", ScalarType.BOOLEAN: "bool"}
_STORAGE_TYPES = {ScalarType.INTEGER: "3", ScalarType.REAL: "5", ScalarType.BOOLEAN: "11"}


def _xml(tag: str, text: str = "", *children: XmlNode, **attributes: str) -> XmlNode:
    return XmlNode(tag=tag, text=text, attributes=tuple(attributes.items()), children=tuple(children))


def _number(value: bool | int | float) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _without_source(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _without_source(item) for key, item in value.items() if key != "source"}
    if isinstance(value, list):
        return [_without_source(item) for item in value]
    return value


def lower_asfp(package: Package, target: Target) -> SerializationIR:
    """Lower a validated package, allocating target IDs within its semantic digest."""
    digest = hashlib.sha256(json.dumps(_without_source(to_dict(package)), sort_keys=True).encode()).hexdigest()
    namespace = uuid5(NAMESPACE_URL, f"https://sciloom.invalid/{target.value}/{digest}")
    return _Writer(package, namespace).build(target)


class _Writer:
    def __init__(self, package: Package, namespace: Any):
        self.package = package
        self.namespace = namespace
        self.functions = {function.node_id: function for function in package.functions}
        self.variables = {v.node_id: v for f in package.functions for v in f.variables}
        self.names: dict[str, str] = {}
        for function in package.functions:
            used: set[str] = set()
            for i, variable in enumerate(function.variables):
                # The manual requires an ASCII letter as the first character.
                candidate = variable.name if re.fullmatch(r"[A-Za-z][A-Za-z_0-9]*", variable.name) else f"v_{i}"
                if candidate.lower() in {"true", "false", "not", "and", "or"}:
                    candidate = f"v_{i}"
                while candidate in used:
                    candidate += "_"
                used.add(candidate)
                self.names[variable.node_id] = candidate

    def identifier(self, role: str, semantic_id: str) -> str:
        return "{" + str(uuid5(self.namespace, json.dumps((role, semantic_id)))).upper() + "}"

    def metadata(self, name: str, *, expanded: bool = False) -> list[XmlNode]:
        # Fixed epoch metadata makes recompilation reproducible; it is not execution state.
        result = [_xml("description"), _xml("name", name), _xml("edittime", "0")]
        if expanded:
            result.append(_xml("expanded", "1"))
        return result

    def expression(self, expression: Expression, *, nested: bool = False) -> str:
        if isinstance(expression, Literal):
            return (
                ("true" if expression.value else "false")
                if expression.type == ScalarType.BOOLEAN
                else _number(expression.value)
            )
        if isinstance(expression, Reference):
            return self.names[expression.symbol_id]
        if isinstance(expression, Unary):
            text = f"{expression.op.value} {self.expression(expression.operand, nested=True)}"
        else:
            operator = {BinaryOp.EQUAL: "=", BinaryOp.NOT_EQUAL: "<>"}.get(expression.op, expression.op.value)
            text = f"{self.expression(expression.left, nested=True)} {operator} {self.expression(expression.right, nested=True)}"
        return f"({text})" if nested else text

    def functiondata(self, function: FunctionIR, call: Call | None = None) -> XmlNode:
        groups = []
        for tag, role in (("inputs", VariableRole.INPUT), ("outputs", VariableRole.OUTPUT)):
            parameters = [v for v in function.variables if v.role == role]
            entries = [_xml("count", str(len(parameters)))]
            inputs = {b.parameter_id: b.value for b in call.inputs} if call else {}
            outputs = {b.parameter_id: b.target for b in call.outputs} if call else {}
            for i, variable in enumerate(parameters):
                variable_name = self.names[variable.node_id]
                expression = ""
                if call and role == VariableRole.INPUT:
                    variable_name = ""
                    expression = self.expression(inputs[variable.node_id])
                elif call:
                    variable_name = self.names[outputs[variable.node_id].symbol_id]
                entries.append(
                    _xml(
                        f"item{i}",
                        "",
                        _xml("id", self.identifier("parameter", variable.node_id)),
                        _xml("name", variable.name),
                        _xml("variablename", variable_name),
                        _xml("variabletype", _PARAMETER_TYPES[variable.type]),
                        _xml("isarray", "0"),
                        _xml("expression", expression),
                    )
                )
            entries.append(_xml("sortType", "0"))
            groups.append(_xml(tag, "", *entries))
        return _xml("functiondata", "", *groups)

    def macro(
        self,
        tag: str,
        identity: str,
        function: FunctionIR,
        body: tuple[Statement, ...],
        *,
        name: str = "Macro Task",
        condition_type: str = "0",
        condition: str = "",
        variables: tuple[Variable, ...] = (),
        branches: tuple[XmlNode, ...] = (),
        role: str = "statement",
    ) -> XmlNode:
        declared = []
        for variable in variables:
            assert variable.initial is not None  # guaranteed by shared validation
            value = (
                ("-1" if variable.initial.value else "0")
                if variable.type == ScalarType.BOOLEAN
                else _number(variable.initial.value)
            )
            declared.append(
                _xml(
                    "variable",
                    "",
                    _xml("name", self.names[variable.node_id]),
                    _xml("value", "", _xml("type", _STORAGE_TYPES[variable.type]), _xml("value", value)),
                    _xml("siunit", "1"),
                    _xml("unit", "1" if variable.type == ScalarType.REAL else "s"),
                    _xml("array", "0"),
                    _xml("creationtime", "0"),
                    _xml("constant", "0"),
                )
            )
        occupied = {self.names[v.node_id] for v in function.variables}
        loop_name, fragment_name = "loop", "fragment"
        while loop_name in occupied:
            loop_name += "_"
        while fragment_name in occupied:
            fragment_name += "_"
        children = [
            *self.metadata(name, expanded=True),
            _xml("conditionloop", "1"),
            _xml("conditionif", condition if condition_type == "1" else ""),
            _xml("conditionwhile", condition if condition_type == "2" else ""),
            _xml("conditiontype", condition_type),
            _xml("loopvariable", loop_name),
            _xml("fragmentvariable", fragment_name),
            _xml("executionmode", "0"),
            _xml("sequentialzones", "", _xml("count", "0")),
            _xml("multicondition", "1" if branches else "0"),
            _xml("multiloop", "0"),
            _xml("variables", "", *declared, sortingType="1"),
            _xml("id", self.identifier(role, identity)),
            _xml("tasks", "", *(branches or self.statements(body, function, "task"))),
        ]
        return _xml(tag, "", *children, typeid="Chemspeed.SAMacroTask.1")

    def statements(self, body: tuple[Statement, ...], function: FunctionIR, tag: str) -> tuple[XmlNode, ...]:
        result = []
        for statement in body:
            if isinstance(statement, Assignment):
                children = [
                    *self.metadata("Set Variable"),
                    _xml("variablename", self.names[statement.target.symbol_id]),
                    _xml("expressiontext", self.expression(statement.value)),
                    _xml("elementselectmode", "0"),
                    _xml("elementnumber"),
                    _xml("numberofelements"),
                    _xml("startindex", "0"),
                    _xml("clearvariable", "0"),
                    _xml("sortwells", "0"),
                    _xml("enumerationtype", "0"),
                    _xml("wellsenumeration", "0"),
                    _xml("elementsenumeration", "0"),
                    _xml("id", self.identifier("statement", statement.node_id)),
                ]
                result.append(_xml(tag, "", *children, typeid="Chemspeed.SATaskSetVariable.1"))
            elif isinstance(statement, Call):
                result.append(
                    _xml(
                        tag,
                        "",
                        *self.metadata("Execute Function"),
                        self.functiondata(self.functions[statement.function_id], statement),
                        _xml("functionid", self.identifier("function", statement.function_id)),
                        _xml("id", self.identifier("statement", statement.node_id)),
                        typeid="Chemspeed.SATaskExecuteFunction.1",
                    )
                )
            elif isinstance(statement, While):
                result.append(
                    self.macro(
                        tag,
                        statement.node_id,
                        function,
                        statement.body,
                        name="While",
                        condition_type="2",
                        condition=self.expression(statement.condition),
                    )
                )
            elif isinstance(statement, If) and not statement.else_body:
                result.append(
                    self.macro(
                        tag,
                        statement.node_id,
                        function,
                        statement.then_body,
                        name="If",
                        condition_type="1",
                        condition=self.expression(statement.condition),
                    )
                )
            else:
                branches = []
                for label, condition_type, condition, branch_body in (
                    ("If", "0", self.expression(statement.condition), statement.then_body),
                    ("Else", "2", "", statement.else_body),
                ):
                    branches.append(
                        _xml(
                            "task",
                            "",
                            *self.metadata(label, expanded=True),
                            _xml("conditiontype", condition_type),
                            _xml("condition", condition),
                            _xml("id", self.identifier(label, statement.node_id)),
                            _xml("components", "", *self.statements(branch_body, function, "component")),
                            typeid="Chemspeed.SATaskCondition.1",
                        )
                    )
                result.append(
                    self.macro(tag, statement.node_id, function, (), name="If-Else", branches=tuple(branches))
                )
        return tuple(result)

    def build(self, target: Target) -> SerializationIR:
        functions = []
        used_names: set[str] = set()
        for function in self.package.functions:
            name = function.name
            while name in used_names:
                name += "_"
            used_names.add(name)
            internal = tuple(v for v in function.variables if v.role == VariableRole.INTERNAL)
            body = (
                (self.macro("component", function.node_id, function, function.body, variables=internal, role="locals"),)
                if internal
                else self.statements(function.body, function, "component")
            )
            functions.append(
                _xml(
                    "function",
                    "",
                    *self.metadata(name, expanded=True),
                    self.functiondata(function),
                    _xml("id", self.identifier("function", function.node_id)),
                    _xml("components", "", *body),
                    typeid="Chemspeed.SATaskFunctionDefinition.1",
                )
            )
        return SerializationIR(target=target, root=_xml("functions", "", *functions))
