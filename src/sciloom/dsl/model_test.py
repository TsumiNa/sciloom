"""The frontend inspects runtime source and never executes it."""

import pytest

from sciloom import Boolean, Function, Input, Integer, Output, Real, runtime
from sciloom.core.ir import IRValidationError, ScalarType, from_json, to_json


class Identity(Function):
    x: Input[Real]
    y: Output[Real]

    @runtime
    def run(self):
        self.y = self.x


class Caller(Function):
    result: Real = 0.0

    def __init__(self, value=2.5):
        self.value = value
        self.identity = Identity()

    @runtime
    def run(self):
        self.result = self.identity(x=self.value)


class Counter(Function):
    count: Integer = 0
    done: Boolean = False
    limit: int = 3

    @runtime
    def run(self):
        self.count = 0
        while self.count < self.limit:
            if self.count == 1:
                self.done = True
            elif self.count == 2:
                self.done = not self.done
            else:
                self.done = False
            self.count += 1


def test_class_schema_exists_before_instantiation():
    assert tuple(Identity.model_fields) == ("x", "y")
    assert tuple(Counter.model_fields) == ("count", "done")
    assert Counter.model_fields["count"].type == ScalarType.INTEGER
    with pytest.raises(TypeError):
        Counter.model_fields["extra"] = Counter.model_fields["count"]


def test_specialization_and_composition_preserve_instance():
    caller = Caller()
    before = vars(caller).copy()
    first = caller.to_ir()
    assert vars(caller) == before
    assert first == caller.to_ir()
    assert first == from_json(to_json(first))
    assert len(first.functions) == 2
    call = first.functions[0].body[0]
    assert call.inputs[0].value.value == 2.5
    assert call.function_id == first.functions[1].node_id
    assert call.outputs[0].parameter_id == first.functions[1].variables[1].node_id
    assert Caller(8).to_ir().functions[0].body[0].inputs[0].value.value == 8


def test_control_flow_and_default_scope():
    package = Counter().to_ir()
    assert len(package.functions[0].variables) == 2
    assert from_json(to_json(package)) == package
    assert package.functions[0].body[1].body[0].else_body[0].condition.op == "=="


def test_runtime_method_cannot_execute_as_host_python():
    with pytest.raises(TypeError, match="compiled"):
        Counter().run()


def test_initializer_cannot_shadow_runtime_field():
    class Bad(Function):
        count: Integer = 0

        def __init__(self):
            self.count = 3

        @runtime
        def run(self):
            pass

    with pytest.raises(IRValidationError, match="runtime_field_write"):
        Bad().to_ir()


def test_unsupported_syntax_reports_location():
    class Bad(Function):
        @runtime
        def run(self):
            print("must never run")

    with pytest.raises(IRValidationError) as error:
        Bad().to_ir()
    diagnostic = error.value.diagnostics[0]
    assert diagnostic.code == "python_subset"
    assert diagnostic.source.path == __file__
    assert diagnostic.source.line > 0


def test_unavailable_source_is_explicit():
    class Bad(Function):
        @runtime
        def run(self):
            pass

    original = Bad.run.__sciloom_runtime__
    original.__code__ = original.__code__.replace(co_filename="<interactive>")
    with pytest.raises(IRValidationError, match="source_unavailable"):
        Bad().to_ir()


def test_host_property_is_not_executed():
    class Bad(Function):
        result: Real = 0.0

        @property
        def secret(self):
            raise AssertionError("property must not execute")

        @runtime
        def run(self):
            self.result = self.secret

    with pytest.raises(IRValidationError, match="host_value"):
        Bad().to_ir()


def test_runtime_assignment_does_not_create_undeclared_field():
    class Bad(Function):
        @runtime
        def run(self):
            self.missing = 1

    with pytest.raises(IRValidationError, match="runtime_field"):
        Bad().to_ir()


def test_subprogram_recursion_can_be_represented():
    class Recursive(Function):
        def __init__(self):
            self.again = self

        @runtime
        def run(self):
            self.again()

    package = Recursive().to_ir()
    assert package.functions[0].body[0].function_id == package.entry_function_id


def test_host_type_mismatch_uses_semantic_diagnostics():
    with pytest.raises(IRValidationError, match="type_mismatch"):
        Caller(True).to_ir()


def test_inherited_schema_and_runtime_method():
    class Derived(Counter):
        limit: int = 5

    package = Derived().to_ir()
    assert tuple(Derived.model_fields) == ("count", "done")
    assert package.functions[0].body[1].condition.right.value == 5


def test_invalid_schema_fails_at_class_definition():
    with pytest.raises(IRValidationError, match="class_schema"):

        class Bad(Function):
            x: Input[str]

    with pytest.raises(IRValidationError, match="class_schema"):

        class BadOverride(Counter):
            count: int = 3

    with pytest.raises(IRValidationError, match="class_schema"):

        class BadDefault(Function):
            x: Input[Real] = None






def test_missing_call_argument_is_located():
    class BadCaller(Caller):
        @runtime
        def run(self):
            self.result = self.identity()

    with pytest.raises(IRValidationError, match="call_binding") as error:
        BadCaller().to_ir()
    assert error.value.diagnostics[0].source.path == __file__


def test_multiple_outputs_bind_in_declared_order():
    class Pair(Function):
        x: Input[Real]
        first: Output[Real]
        second: Output[Real]

        @runtime
        def run(self):
            self.first = self.x
            self.second = -self.x

    class PairCaller(Function):
        a: Real = 0.0
        b: Real = 0.0

        def __init__(self):
            self.pair = Pair()

        @runtime
        def run(self):
            self.a, self.b = self.pair(2.5)

    package = PairCaller().to_ir()
    assert [binding.parameter_id for binding in package.functions[0].body[0].outputs] == [
        package.functions[1].variables[1].node_id,
        package.functions[1].variables[2].node_id,
    ]
