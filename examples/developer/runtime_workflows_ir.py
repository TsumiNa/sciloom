r"""For developers: three complete workflows from typed IR, JSON and explicit services.

Run: ``uv run python -m examples.developer.runtime_workflows_ir``
Expected terminal output:
    Reagent: reagent_A; IDs: ('E01', 'E02'); volumes: (1.5, 0.0) mL
    Shaker: stopped after 5 s at 300 rpm
    Label log: logs/2026-09-17_130000.csv; rows: 2
    Contents: b'B:batch A\r\nA:batch A\r\n'

Complete artifacts: runtime_workflows_ir.reagent.json, .shaker.json and .labels.json.
The independent ReferenceArchiveTarget emits JSON for reference execution, not
an equipment program. Every service is supplied explicitly. These examples
perform no hardware I/O; AutoSuite CSV/dynamic-location compilation is gated.
The paired authors are ../read_reagent_table.py, ../stir_selected_location.py
and ../label_sample_log.py. All three direct builders avoid Python source analysis.
"""

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

from sciloom.core.bindings import DeviceBinding, DeviceBindings, DeviceCandidate, DeviceSelectionBinding
from sciloom.core.compiler import Artifact, compile_ir
from sciloom.core.diagnostics import Diagnostic
from sciloom.core.interpreter import (
    Interpreter,
    MemoryFiles,
    QueuedAcknowledgements,
    ReferenceEnvironment,
    VirtualClock,
    VirtualWallClock,
    WellProperties,
)
from sciloom.core.ir import (
    AppendCsv,
    Assignment,
    Binary,
    BinaryOp,
    ConfigureProperty,
    CsvColumn,
    CsvErrorPolicy,
    CsvReadMode,
    DeviceAt,
    DeviceCommand,
    DeviceResource,
    ForEachZone,
    FunctionIR,
    ListType,
    Literal,
    LogValue,
    Notify,
    Program,
    ReadCsv,
    ReadWallTime,
    ReadWellProperty,
    Reference,
    ScalarType,
    StartAgitation,
    StopAgitation,
    TextTrim,
    Variable,
    VariableRole,
    Wait,
    WellName,
    WellPropertySpec,
    WriteWellProperty,
    ZoneLiteral,
    ZoneType,
    from_json,
    to_json,
)
from sciloom.core.ir.device_contracts import (
    AGITATION_SPEED_ID,
    AGITATOR_CONTRACT,
    BASE_DEVICE_CONTRACT,
    START_AGITATION_ID,
    STOP_AGITATION_ID,
)
from sciloom.core.ir.traversal import iter_nodes
from sciloom.core.locations import LocationDirectory, Well, Zone
from sciloom.units import Volume, mL, rpm


@dataclass(frozen=True, kw_only=True)
class ReferenceArchiveTarget:
    """Archive portable reference programs; native command execution is undefined."""

    bindings: DeviceBindings = DeviceBindings()
    target_id = "example.reference-archive/v1"

    def resolve_devices(self, program: Program) -> DeviceBindings:
        return self.bindings

    def validate(self, program: Program) -> tuple[Diagnostic, ...]:
        return tuple(
            Diagnostic(
                code="unsupported_native_command",
                message="This archive is for reference execution; native command semantics are undefined.",
                path=path,
                node_id=node.node_id,
                source=node.source,
            )
            for node, path in iter_nodes(program)
            if isinstance(node, DeviceCommand)
        )

    def emit(self, program: Program) -> Artifact:
        return Artifact(content=to_json(program).encode("utf-8"), media_type="application/json", suffix=".json")


def reagent_program() -> Program:
    """Read a selected heading and aligned IDs/volumes, preserving cell defaults."""
    variables = (
        Variable(node_id="path", owner_id="recipe", name="path", type=ScalarType.TEXT, role=VariableRole.INPUT),
        Variable(
            node_id="reagent_index",
            owner_id="recipe",
            name="reagent_index",
            type=ScalarType.INTEGER,
            role=VariableRole.INPUT,
        ),
        Variable(
            node_id="reagent_name",
            owner_id="recipe",
            name="reagent_name",
            type=ScalarType.TEXT,
            role=VariableRole.OUTPUT,
        ),
        Variable(
            node_id="ids",
            owner_id="recipe",
            name="ids",
            type=ListType(element_type=ScalarType.TEXT),
            role=VariableRole.OUTPUT,
        ),
        Variable(
            node_id="volumes",
            owner_id="recipe",
            name="volumes",
            type=ListType(element_type=ScalarType.VOLUME),
            role=VariableRole.OUTPUT,
        ),
    )
    header_column = Binary(
        node_id="header-column",
        op=BinaryOp.ADD,
        left=Reference(node_id="header-choice", symbol_id="reagent_index"),
        right=Literal(node_id="header-offset", type=ScalarType.INTEGER, value=1),
    )
    data_column = Binary(
        node_id="data-column",
        op=BinaryOp.ADD,
        left=Reference(node_id="data-choice", symbol_id="reagent_index"),
        right=Literal(node_id="data-offset", type=ScalarType.INTEGER, value=1),
    )
    body = (
        ReadCsv(
            node_id="heading",
            mode=CsvReadMode.ROW,
            error_policy=CsvErrorPolicy.RAISE,
            path=Reference(node_id="header-path", symbol_id="path"),
            row=Literal(node_id="header-row", type=ScalarType.INTEGER, value=0),
            header=False,
            columns=(CsvColumn(index=header_column, type=ScalarType.TEXT),),
            targets=(Reference(node_id="heading-result", symbol_id="reagent_name"),),
        ),
        ReadCsv(
            node_id="table",
            mode=CsvReadMode.COLUMNS,
            error_policy=CsvErrorPolicy.RAISE,
            path=Reference(node_id="data-path", symbol_id="path"),
            header=True,
            columns=(
                CsvColumn(
                    index=Literal(node_id="id-column", type=ScalarType.INTEGER, value=0),
                    type=ScalarType.TEXT,
                    default=Literal(node_id="id-default", type=ScalarType.TEXT, value=""),
                ),
                CsvColumn(
                    index=data_column,
                    type=ScalarType.VOLUME,
                    unit=Literal(node_id="mL", type=ScalarType.VOLUME, value=1e-6),
                    default=Literal(node_id="zero-volume", type=ScalarType.VOLUME, value=0),
                ),
            ),
            targets=(
                Reference(node_id="ids-result", symbol_id="ids"),
                Reference(node_id="volumes-result", symbol_id="volumes"),
            ),
        ),
    )
    return Program(
        entry_function_id="recipe",
        functions=(FunctionIR(node_id="recipe", name="ReadReagentTable", variables=variables, body=body),),
    )


def selected_program() -> Program:
    """Save speed, capture a location, start, wait and explicitly stop."""
    return Program(
        entry_function_id="selected",
        device_types=(BASE_DEVICE_CONTRACT, AGITATOR_CONTRACT),
        resources=(DeviceResource(node_id="shaker", logical_id="shaker", device_type_id=AGITATOR_CONTRACT.type_id),),
        functions=(
            FunctionIR(
                node_id="selected",
                name="StirSelectedLocation",
                variables=(
                    Variable(
                        node_id="location",
                        owner_id="selected",
                        name="location",
                        type=ZoneType(),
                        role=VariableRole.INPUT,
                    ),
                    Variable(
                        node_id="speed",
                        owner_id="selected",
                        name="speed",
                        type=ScalarType.ROTATIONAL_SPEED,
                        role=VariableRole.INPUT,
                    ),
                ),
                body=(
                    ConfigureProperty(
                        node_id="configure",
                        resource_id="shaker",
                        property_id=AGITATION_SPEED_ID,
                        value=Reference(node_id="input-speed", symbol_id="speed"),
                    ),
                    DeviceAt(
                        node_id="select",
                        resource_id="shaker",
                        location=Reference(node_id="input-location", symbol_id="location"),
                        body=(
                            StartAgitation(node_id="start", resource_id="shaker"),
                            Wait(
                                node_id="wait",
                                duration=Literal(node_id="five-seconds", type=ScalarType.DURATION, value=5.0),
                            ),
                            StopAgitation(node_id="stop", resource_id="shaker"),
                        ),
                    ),
                ),
            ),
        ),
    )


def labels_program() -> Program:
    """Capture one timestamp, then write/read/append each well in selection order."""
    prop = WellPropertySpec(name="sample_ID", type=ScalarType.TEXT)
    variables = (
        Variable(node_id="rack", owner_id="labels", name="rack", type=ZoneType(), role=VariableRole.INPUT),
        Variable(node_id="label", owner_id="labels", name="label", type=ScalarType.TEXT, role=VariableRole.INPUT),
        Variable(
            node_id="directory", owner_id="labels", name="directory", type=ScalarType.TEXT, role=VariableRole.INPUT
        ),
        Variable(node_id="path", owner_id="labels", name="path", type=ScalarType.TEXT, role=VariableRole.OUTPUT),
        Variable(node_id="count", owner_id="labels", name="count", type=ScalarType.INTEGER, role=VariableRole.OUTPUT),
        Variable(
            node_id="well",
            owner_id="labels",
            name="well",
            type=ZoneType(),
            role=VariableRole.INTERNAL,
            initial=ZoneLiteral(node_id="empty-well"),
        ),
        *(
            Variable(
                node_id=name,
                owner_id="labels",
                name=name,
                type=ScalarType.TEXT,
                role=VariableRole.INTERNAL,
                initial=Literal(node_id=name + "-initial", type=ScalarType.TEXT, value=""),
            )
            for name in ("cleaned", "stamp", "record")
        ),
    )
    path_expression = Binary(
        node_id="extension",
        op=BinaryOp.ADD,
        left=Binary(
            node_id="timestamp-path",
            op=BinaryOp.ADD,
            left=Binary(
                node_id="directory-slash",
                op=BinaryOp.ADD,
                left=Reference(node_id="input-directory", symbol_id="directory"),
                right=Literal(node_id="slash", type=ScalarType.TEXT, value="/"),
            ),
            right=Reference(node_id="read-stamp", symbol_id="stamp"),
        ),
        right=Literal(node_id="csv-extension", type=ScalarType.TEXT, value=".csv"),
    )
    row = Binary(
        node_id="row",
        op=BinaryOp.ADD,
        left=Binary(
            node_id="prefix",
            op=BinaryOp.ADD,
            left=WellName(node_id="name", value=Reference(node_id="name-well", symbol_id="well")),
            right=Literal(node_id="separator", type=ScalarType.TEXT, value=":"),
        ),
        right=Reference(node_id="record-value", symbol_id="record"),
    )
    body = (
        Notify(
            node_id="confirm",
            message=Literal(
                node_id="message", type=ScalarType.TEXT, value="Samples are ready. Confirm to label and record them."
            ),
        ),
        Assignment(
            node_id="trim-label",
            target=Reference(node_id="cleaned-target", symbol_id="cleaned"),
            value=TextTrim(node_id="trim", value=Reference(node_id="label-input", symbol_id="label")),
        ),
        ReadWallTime(
            node_id="clock", target=Reference(node_id="stamp-target", symbol_id="stamp"), format="%Y-%m-%d_%H%M%S"
        ),
        Assignment(
            node_id="make-path", target=Reference(node_id="path-target", symbol_id="path"), value=path_expression
        ),
        Assignment(
            node_id="reset-count",
            target=Reference(node_id="reset-target", symbol_id="count"),
            value=Literal(node_id="zero", type=ScalarType.INTEGER, value=0),
        ),
        ForEachZone(
            node_id="visit",
            target=Reference(node_id="loop-well", symbol_id="well"),
            value=Reference(node_id="input-rack", symbol_id="rack"),
            body=(
                WriteWellProperty(
                    node_id="label-well",
                    property=prop,
                    zone=Reference(node_id="write-well", symbol_id="well"),
                    value=Reference(node_id="write-label", symbol_id="cleaned"),
                ),
                ReadWellProperty(
                    node_id="read-label",
                    property=prop,
                    zone=Reference(node_id="read-well", symbol_id="well"),
                    target=Reference(node_id="record-target", symbol_id="record"),
                    default=Literal(node_id="fallback", type=ScalarType.TEXT, value=""),
                ),
                AppendCsv(node_id="append", path=Reference(node_id="append-path", symbol_id="path"), values=(row,)),
                Assignment(
                    node_id="increment",
                    target=Reference(node_id="count-target", symbol_id="count"),
                    value=Binary(
                        node_id="plus-one",
                        op=BinaryOp.ADD,
                        left=Reference(node_id="old-count", symbol_id="count"),
                        right=Literal(node_id="one", type=ScalarType.INTEGER, value=1),
                    ),
                ),
            ),
        ),
        LogValue(
            node_id="log-count",
            value=Reference(node_id="final-count", symbol_id="count"),
            category=Literal(node_id="category", type=ScalarType.TEXT, value="samples"),
            stream=Literal(node_id="stream", type=ScalarType.TEXT, value="records"),
        ),
    )
    return Program(
        entry_function_id="labels",
        functions=(FunctionIR(node_id="labels", name="LabelSampleLog", variables=variables, body=body),),
    )


def reference_environment(*, acknowledgements: int = 1) -> ReferenceEnvironment:
    """Create independent files, clocks, metadata and synthetic candidate facts."""
    directory = LocationDirectory(wells=(Well(identity="well:A", name="A"), Well(identity="well:B", name="B")))
    candidates = tuple(
        DeviceCandidate(
            binding=DeviceBinding(
                logical_id="shaker",
                physical_id=f"shaker:{name}",
                contract=AGITATOR_CONTRACT,
                base_contracts=(BASE_DEVICE_CONTRACT,),
                writable_properties=(AGITATION_SPEED_ID,),
                supported_operations=(START_AGITATION_ID, STOP_AGITATION_ID),
            ),
            wells=Zone(well_ids=(f"well:{name}",)),
        )
        for name in ("A", "B")
    )
    return ReferenceEnvironment(
        locations=directory,
        device_bindings=DeviceBindings(devices=(DeviceSelectionBinding(logical_id="shaker", candidates=candidates),)),
        clock=VirtualClock(),
        wall_clock=VirtualWallClock(datetime(2026, 9, 17, 13, tzinfo=timezone.utc)),
        acknowledgements=QueuedAcknowledgements([True] * acknowledgements),
        properties=WellProperties(),
        files=MemoryFiles(),
    )


if __name__ == "__main__":
    # Deployment bindings are supplied only to the program that declares devices.
    env = reference_environment()
    assert env.device_bindings is not None and env.files is not None and env.clock is not None
    targets = {
        "reagent": ReferenceArchiveTarget(),
        "shaker": ReferenceArchiveTarget(bindings=env.device_bindings),
        "labels": ReferenceArchiveTarget(),
    }
    programs = {"reagent": reagent_program(), "shaker": selected_program(), "labels": labels_program()}
    restored = {}
    for name, program in programs.items():
        result = compile_ir(program, target=targets[name])
        path = Path(__file__).with_suffix(f".{name}.json")
        result.write(path)
        restored[name] = from_json(path.read_text(encoding="utf-8"))
    # Host setup explicitly supplies this small, project-authored fixture.
    data = Path(__file__).parents[1].joinpath("read_reagent_table.csv").read_bytes()
    recipe = Interpreter(
        restored["reagent"], environment=ReferenceEnvironment(files=MemoryFiles({"recipe.csv": data}))
    ).run(inputs={"path": "recipe.csv", "reagent_index": 0})
    volumes = recipe.outputs["volumes"]
    assert isinstance(volumes, tuple) and all(isinstance(v, Volume) for v in volumes)
    print(
        f"Reagent: {recipe.outputs['reagent_name']}; IDs: {recipe.outputs['ids']}; volumes: {tuple(v / mL for v in volumes if isinstance(v, Volume))} mL"
    )
    shaker = Interpreter(restored["shaker"], environment=env).run(
        inputs={"location": Zone(well_ids=("well:A",)), "speed": 300 * rpm}
    )
    assert not shaker.physical_devices["shaker:A"].enabled
    print(f"Shaker: stopped after {env.clock.monotonic():g} s at 300 rpm")
    label_env = replace(reference_environment(), device_bindings=None)
    labels = Interpreter(restored["labels"], environment=label_env).run(
        inputs={"rack": Zone(well_ids=("well:B", "well:A")), "label": "  batch A\t", "directory": "logs"}
    )
    print(f"Label log: {labels.outputs['path']}; rows: {labels.outputs['count']}")
    path_value = labels.outputs["path"]
    assert isinstance(path_value, str) and label_env.files is not None
    print("Contents:", label_env.files.read_bytes(path_value))
