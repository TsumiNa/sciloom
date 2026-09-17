"""Write a deployment assessment tied to checked semantic and artifact bytes."""

import hashlib
from dataclasses import replace
from pathlib import Path

from sciloom.core.bindings import DeviceBindings, validate_bindings
from sciloom.core.compiler import CompileResult
from sciloom.core.configuration import validate_device_usage
from sciloom.core.device_locations import validate_device_locations
from sciloom.core.diagnostics import CompilationError, IRValidationError
from sciloom.core.ir import DeviceIf, DeviceResource, to_json, validate
from sciloom.core.ir.traversal import iter_nodes
from sciloom.core.timing import validate_timer_usage
from .deployment import AutoSuiteDeploymentReport
from .selection import profile_binding
from .target import AutoSuiteTarget


def write_autosuite_review(
    result: CompileResult, *, target: AutoSuiteTarget, path: str | Path
) -> AutoSuiteDeploymentReport:
    """Write an ASFP and same-base deployment report after checking their association.

    Args:
        result: Successful result from the standard compilation pipeline.
        target: AutoSuite target whose profiles and settings should be assessed.
        path: Artifact filename; the sidecar replaces its suffix with .deployment.json.

    Returns:
        The report written to the sidecar, including artifact and selected IR hashes.

    Raises:
        ValueError: Identity, concrete binding, artifact or selected-result checks fail,
            or the two destination paths coincide.
        IRValidationError: Selected semantic IR is malformed.
        CompilationError: Existing binding, state or target validation rejects the result.
        OSError: Either destination cannot be written. Two-file writes are not atomic.

    This does not resolve or specialize authored IR, compile a second program,
    mutate a target cache or run Executor. All semantic checks precede writes.
    """
    destination = Path(path)
    sidecar = destination.with_suffix(".deployment.json")
    if destination.resolve() == sidecar.resolve():
        raise ValueError("Artifact and deployment sidecar must have distinct paths.")
    if result.target_id != target.target_id or result.diagnostics:
        raise ValueError("Review export requires a successful result for this target identity.")
    program = result.specialized_ir
    errors = validate(program)
    if errors:
        raise IRValidationError(errors)
    if any(isinstance(node, DeviceIf) for node, _ in iter_nodes(program)):
        raise ValueError("Review export requires already-specialized IR without DeviceIf.")
    bindings = DeviceBindings(
        devices=tuple(profile_binding(name, profile, target.layout) for name, profile in sorted(target.devices.items()))
    )
    errors = validate_bindings(program, bindings)
    if errors:
        raise CompilationError(errors)
    concrete = {binding.logical_id: binding.contract.type_id for binding in bindings.devices}
    if any(
        resource.device_type_id != concrete[resource.logical_id]
        for resource in program.resources
        if isinstance(resource, DeviceResource)
    ):
        raise ValueError("Result concrete device contracts do not match this target's selected bindings.")
    errors = (
        validate_device_usage(program, bindings)
        + validate_timer_usage(program)
        + validate_device_locations(program, bindings)
        + target.validate(program)
    )
    if errors:
        raise CompilationError(errors)
    if target.emit(program) != result.artifact:
        raise ValueError("Result artifact does not match this target's deterministic emission and bindings.")
    report = replace(
        target.deployment_report(program),
        artifact_sha256=hashlib.sha256(result.artifact.content).hexdigest(),
        specialized_ir_sha256=hashlib.sha256(to_json(program).encode("utf-8")).hexdigest(),
    )
    result.write(destination)
    sidecar.write_text(report.to_json(), encoding="utf-8")
    return report
