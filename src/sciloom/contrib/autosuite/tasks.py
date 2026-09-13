"""Schedule semantic statements, expression checks and target-private call copies."""

from sciloom.core.diagnostics import CompilationError, Diagnostic
from sciloom.core.ir import (
    Assignment,
    Call,
    ConfigureProperty,
    FunctionIR,
    If,
    ListSet,
    ListType,
    StartAgitation,
    Statement,
    StopAgitation,
    While,
)
from .agitation import agitation_task
from .context import CodegenContext
from .expressions import checked_read, materialize, plan_expression
from .parameters import functiondata
from .primitives import macro, set_variable
from .xml import XmlNode, xml_node as _xml


def statements(
    context: CodegenContext, body: tuple[Statement, ...], function: FunctionIR, tag: str
) -> tuple[XmlNode, ...]:
    result: list[XmlNode] = []
    for statement in body:
        if isinstance(statement, Assignment):
            value = plan_expression(context, function, statement.value, tag)
            result.extend(value.prerequisites)
            result.append(
                set_variable(
                    context,
                    tag,
                    context.names[statement.target.symbol_id],
                    value.text,
                    identity=statement.node_id,
                    array=isinstance(value.type, ListType),
                )
            )
        elif isinstance(statement, ListSet):
            array = context.names[statement.target.symbol_id]
            value_type = context.variables[statement.target.symbol_id].type
            assert isinstance(value_type, ListType)
            value = plan_expression(context, function, statement.value, tag)
            if statement.op is None:
                value = materialize(context, function, value, tag)
                result.extend(value.prerequisites)
            index = plan_expression(context, function, statement.index, tag)
            previous, captured_index = checked_read(context, function, array, index, value_type.element_type, tag)
            result.extend(previous.prerequisites)
            if statement.op is not None:
                result.extend(value.prerequisites)
            text = value.text if statement.op is None else f"{previous.text} {statement.op.value} ({value.text})"
            result.append(set_variable(context, tag, array, text, identity=statement.node_id, index=captured_index))
        elif isinstance(statement, ConfigureProperty):
            value = plan_expression(context, function, statement.value, tag)
            result.extend(value.prerequisites)
            result.append(
                set_variable(
                    context,
                    tag,
                    context.device_state[function.node_id][statement.resource_id].name,
                    value.text,
                    identity=statement.node_id,
                )
            )
        elif isinstance(statement, (StartAgitation, StopAgitation)):
            speed = (
                context.device_state[function.node_id][statement.resource_id].name
                if isinstance(statement, StartAgitation)
                else None
            )
            result.append(
                agitation_task(
                    tag=tag,
                    binding=context.resources[statement.resource_id],
                    speed=speed,
                    identifier=context.identifier("statement", statement.node_id),
                )
            )
        elif isinstance(statement, Call):
            inputs, outputs = {}, {}
            after = []
            plans = [(binding, plan_expression(context, function, binding.value, tag)) for binding in statement.inputs]
            needs_evaluation = any(plan.prerequisites or isinstance(plan.type, ListType) for _, plan in plans)
            for binding, plan in plans:
                if needs_evaluation:
                    plan = materialize(context, function, plan, tag)
                result.extend(plan.prerequisites)
                inputs[binding.parameter_id] = plan.text
            for output in statement.outputs:
                name = context.names[output.target.symbol_id]
                value_type = context.variables[output.parameter_id].type
                if isinstance(value_type, ListType):
                    temporary = context.temporary(function, value_type)
                    outputs[output.parameter_id] = temporary
                    after.append(set_variable(context, tag, name, temporary, array=True))
                else:
                    outputs[output.parameter_id] = name
            for resource_id, storage in context.device_state[statement.function_id].items():
                assert storage.input_id is not None and storage.output_id is not None
                caller_name = context.device_state[function.node_id][resource_id].name
                inputs[storage.input_id] = caller_name
                outputs[storage.output_id] = caller_name
            result.append(
                _xml(
                    tag,
                    "",
                    *context.metadata("Execute Function"),
                    functiondata(context, context.functions[statement.function_id], inputs=inputs, outputs=outputs),
                    _xml("functionid", context.identifier("function", statement.function_id)),
                    _xml("id", context.identifier("statement", statement.node_id)),
                    typeid="Chemspeed.SATaskExecuteFunction.1",
                )
            )
            result.extend(after)
        elif isinstance(statement, While):
            condition = plan_expression(context, function, statement.condition, tag)
            loop_body = statements(context, statement.body, function, "task")
            if condition.prerequisites:
                condition = materialize(context, function, condition, tag)
                result.extend(condition.prerequisites)
                # Re-plan at the loop tail: distinct task IDs and checks on every retest.
                retest = plan_expression(context, function, statement.condition, "task")
                loop_body += (*retest.prerequisites, set_variable(context, "task", condition.text, retest.text))
            result.append(
                macro(
                    context,
                    tag,
                    statement.node_id,
                    function,
                    loop_body,
                    name="While",
                    condition_type="2",
                    condition=condition.text,
                )
            )
        elif isinstance(statement, If):
            condition = plan_expression(context, function, statement.condition, tag)
            result.extend(condition.prerequisites)
            if not statement.else_body:
                result.append(
                    macro(
                        context,
                        tag,
                        statement.node_id,
                        function,
                        statements(context, statement.then_body, function, "task"),
                        name="If",
                        condition_type="1",
                        condition=condition.text,
                    )
                )
            else:
                branches = []
                for label, condition_type, text, branch_body in (
                    ("If", "0", condition.text, statement.then_body),
                    ("Else", "2", "", statement.else_body),
                ):
                    branches.append(
                        _xml(
                            "task",
                            "",
                            *context.metadata(label, expanded=True),
                            _xml("conditiontype", condition_type),
                            _xml("condition", text),
                            _xml("id", context.identifier(label, statement.node_id)),
                            _xml("components", "", *statements(context, branch_body, function, "component")),
                            typeid="Chemspeed.SATaskCondition.1",
                        )
                    )
                result.append(
                    macro(context, tag, statement.node_id, function, tuple(branches), name="If-Else", branches=True)
                )
        else:
            raise CompilationError(
                (
                    Diagnostic(
                        code="unsupported_operation",
                        message=f"AutoSuite cannot emit {type(statement).__name__}.",
                        path="$",
                        node_id=statement.node_id,
                        source=statement.source,
                    ),
                )
            )
    return tuple(result)
