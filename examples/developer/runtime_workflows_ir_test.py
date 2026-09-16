"""Whole workflows agree across source, direct IR, JSON and an independent target."""

from dataclasses import fields, replace
from pathlib import Path

import pytest

from examples.label_sample_log import LabelSampleLog
from examples.read_reagent_table import ReadReagentTable
from examples.stir_selected_location import StirSelectedLocation, deployment
from sciloom import Function, rpm, runtime
from sciloom.core.bindings import DeviceBindings
from sciloom.core.compiler import compile_ir
from sciloom.core.diagnostics import CompilationError, ExecutionError
from sciloom.core.interpreter import Interpreter, MemoryFiles, ReferenceEnvironment
from sciloom.core.ir import from_json, to_json
from sciloom.core.locations import Zone
from sciloom.devices.declarations import bind_device
from sciloom.units import mL
from sciloom_autosuite import AutoSuiteTarget
from .demo_contribution import DemoAgitator
from .runtime_workflows_ir import (
    ReferenceArchiveTarget,
    labels_program,
    reagent_program,
    reference_environment,
    selected_program,
)


def trace(events):
    return tuple(
        (
            type(event).__name__,
            {
                field.name: getattr(event, field.name)
                for field in fields(event)
                if field.name not in {"node_id", "source", "resource_id"}
            },
        )
        for event in events
    )


def forms(model, direct):
    authored = model().to_ir()
    return authored, direct, from_json(to_json(direct)), from_json(to_json(authored))


def test_recipe_heading_dynamic_column_and_aligned_defaults_across_all_entries():
    data = Path(__file__).parents[1].joinpath("read_reagent_table.csv").read_bytes()
    expected_trace = None
    for program in forms(ReadReagentTable, reagent_program()):
        before = to_json(program)
        result = compile_ir(program, target=ReferenceArchiveTarget())
        env = ReferenceEnvironment(files=MemoryFiles({"recipe.csv": data}))
        executed = Interpreter(from_json(result.artifact.content.decode()), environment=env).run(
            inputs={"path": "recipe.csv", "reagent_index": 0}
        )
        assert executed.outputs == {"reagent_name": "reagent_A", "ids": ("E01", "E02"), "volumes": (1.5 * mL, 0 * mL)}
        actual = trace(executed.events)
        if expected_trace is None:
            expected_trace = actual
        assert actual == expected_trace and to_json(program) == before
        assert result.semantic_ir == program
        second_reagent = Interpreter(program, environment=env).run(inputs={"path": "recipe.csv", "reagent_index": 1})
        assert second_reagent.outputs == {
            "reagent_name": "reagent_B",
            "ids": ("E01", "E02"),
            "volumes": (2 * mL, 3 * mL),
        }
        with pytest.raises(CompilationError, match="unsupported_csv_semantics"):
            compile_ir(program, target=AutoSuiteTarget())
        header_only = Interpreter(
            program, environment=ReferenceEnvironment(files=MemoryFiles({"recipe.csv": b"id,name\n"}))
        ).run(inputs={"path": "recipe.csv", "reagent_index": 0})
        assert header_only.outputs == {"reagent_name": "name", "ids": (), "volumes": ()}
        with pytest.raises(ExecutionError, match="csv_eof"):
            Interpreter(program, environment=ReferenceEnvironment(files=MemoryFiles({"empty": b""}))).run(
                inputs={"path": "empty", "reagent_index": 0}
            )


def test_selected_shaker_waits_with_running_state_then_stops_only_that_controller():
    expected_trace = None
    for program in forms(StirSelectedLocation, selected_program()):
        env = reference_environment()
        compiled = compile_ir(program, target=ReferenceArchiveTarget(bindings=env.device_bindings))
        session = Interpreter(from_json(compiled.artifact.content.decode()), environment=env)
        result = session.run(inputs={"location": Zone(well_ids=("well:B",)), "speed": 300 * rpm})
        assert env.clock.monotonic() == 5
        assert result.physical_devices["shaker:A"].applied_configuration == {}
        assert result.physical_devices["shaker:B"].applied_configuration == {"speed": 300 * rpm}
        assert not any(state.enabled for state in result.physical_devices.values())
        assert [type(e).__name__ for e in result.events] == ["DeviceEvent", "DeviceEvent", "WaitEvent", "DeviceEvent"]
        assert result.events[1].physical_state.enabled
        if expected_trace is None:
            expected_trace = trace(result.events)
        assert trace(result.events) == expected_trace
        for invalid in (Zone.empty(), Zone(well_ids=("well:A", "well:B")), Zone(well_ids=("unknown",))):
            prior = len(env.events)
            with pytest.raises(ExecutionError, match="device_location|unknown_well"):
                session.run(inputs={"location": invalid, "speed": 450 * rpm})
            assert env.clock.monotonic() == 5
            assert len(env.events) == prior + 1  # The earlier logical configuration write remains.


def test_label_workflow_preserves_order_repeated_appends_empty_input_and_old_snapshots():
    expected_trace = None
    for program in forms(LabelSampleLog, labels_program()):
        env = replace(reference_environment(acknowledgements=3), device_bindings=None)
        session = Interpreter(
            from_json(compile_ir(program, target=ReferenceArchiveTarget()).artifact.content.decode()), environment=env
        )
        inputs = {"rack": Zone(well_ids=("well:B", "well:A")), "label": "  batch A\t", "directory": "logs"}
        result = session.run(inputs=inputs)
        path = "logs/2026-09-17_130000.csv"
        assert result.outputs == {"path": path, "count": 2}
        assert env.files.read_bytes(path) == b"B:batch A\r\nA:batch A\r\n"
        assert env.properties.snapshot() == {("well:B", "sample_ID"): "batch A", ("well:A", "sample_ID"): "batch A"}
        if expected_trace is None:
            expected_trace = trace(result.events)
        assert trace(result.events) == expected_trace
        old = env.files.snapshot()
        later = session.run(inputs={**inputs, "label": "new"})
        assert later.outputs["count"] == 2 and result.outputs["count"] == 2
        assert env.files.read_bytes(path) == old[path] + b"B:new\r\nA:new\r\n"
        empty = session.run(inputs={**inputs, "rack": Zone.empty()})
        assert empty.outputs["count"] == 0
        assert len([e for e in empty.events if type(e).__name__ == "CsvAppendEvent"]) == 0
        assert sum(type(e).__name__ == "WallTimeEvent" for e in result.events) == 1
        assert old[path] == b"B:batch A\r\nA:batch A\r\n"
        with pytest.raises(CompilationError) as rejected:
            compile_ir(program, target=AutoSuiteTarget())
        assert {d.code for d in rejected.value.diagnostics} == {
            "unsupported_csv_append",
            "unsupported_zone_cardinality",
        }


def test_confirmation_and_file_failures_do_not_fabricate_rollback_or_later_log_events():
    class FailingFiles(MemoryFiles):
        calls = 0

        def append_bytes(self, path, data):
            self.calls += 1
            if self.calls == 2:
                super().append_bytes(path, b"partial")
                raise OSError("simulated failure after partial external write")
            super().append_bytes(path, data)

    inputs = {"rack": Zone(well_ids=("well:B", "well:A")), "label": "batch", "directory": "logs"}
    for program in forms(LabelSampleLog, labels_program()):
        env = replace(reference_environment(acknowledgements=0), device_bindings=None)
        with pytest.raises(ExecutionError, match="acknowledgement"):
            Interpreter(program, environment=env).run(inputs=inputs)
        assert env.events == () and env.files.snapshot() == {} and env.properties.snapshot() == {}
        env = replace(reference_environment(), device_bindings=None, files=FailingFiles())
        with pytest.raises(ExecutionError, match="csv_io_error"):
            Interpreter(program, environment=env).run(inputs=inputs)
        assert env.files.read_bytes("logs/2026-09-17_130000.csv") == b"B:batch\r\npartial"
        assert len(env.properties.snapshot()) == 2
        assert not any(type(e).__name__ == "LogEvent" for e in env.events)


def test_archive_target_rejects_undefined_extension_semantics():
    class Calibrate(Function):
        shaker: DemoAgitator

        @runtime
        def run(self) -> None:
            self.shaker.calibrate()

    binding = bind_device(logical_id="shaker", device=DemoAgitator(), physical_id="demo")
    target = ReferenceArchiveTarget(bindings=DeviceBindings(devices=(binding,)))
    with pytest.raises(CompilationError, match="unsupported_native_command"):
        Calibrate().compile(target=target)


def test_direct_companions_match_their_generating_programs():
    root = Path(__file__).parent
    env = reference_environment()
    for name, program in (("reagent", reagent_program()), ("shaker", selected_program()), ("labels", labels_program())):
        target = ReferenceArchiveTarget(bindings=env.device_bindings) if name == "shaker" else ReferenceArchiveTarget()
        assert (
            root.joinpath(f"runtime_workflows_ir.{name}.json").read_bytes()
            == compile_ir(program, target=target).artifact.content
        )


@pytest.mark.requires_corpus
def test_author_shaker_deployment_uses_real_app_without_rewriting_it():
    path = Path(__file__).resolve().parents[2] / "autosuite/corpus/app/config20260909_polymerization.app"
    if not path.exists():
        pytest.skip("Local primary APP is absent.")
    before = path.read_bytes()
    with pytest.raises(CompilationError, match="unsupported_device_location"):
        StirSelectedLocation().compile(target=deployment(path))
    assert path.read_bytes() == before
