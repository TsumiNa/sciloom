"""AutoSuite 2.47.1.1 Function backend derived from FIXED/re-export evidence.

Envelopes and default ordering: Test11/Test12; conditional Macro/branch nesting:
Test08/Test09/Test10_FIXED3. Scalar storage codes/units also use the latest APP.
Agitation uses the typed adapter in agitation.py, with explicit zone bindings.
No reference corpus file is read or modified at compiler runtime.

Type identifiers retain the observed fixed .1 suffix; its formal meaning and
cross-version compatibility await vendor confirmation. See the "typeid suffix"
open question in autosuite/docs/05_SCHEMA_EXTRACTION_AND_CONFIRMED_STRUCTURE.md."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Any, Mapping
from uuid import NAMESPACE_URL, uuid5
from ...core.ir import Program, to_dict
from .agitation import AutoSuiteIndividualShaker
from .context import CodegenContext
from .functions import build_functions
from .device_state import prepare_device_state
from .xml import AutoSuiteVersion, SerializationIR


def _without_source(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _without_source(item) for key, item in value.items() if key != "source"}
    if isinstance(value, list):
        return [_without_source(item) for item in value]
    return value


def lower_asfp(
    program: Program,
    target: AutoSuiteVersion,
    *,
    devices: Mapping[str, AutoSuiteIndividualShaker],
) -> SerializationIR:
    """Lower validated semantics and deployment bindings to target records."""
    identity = {
        "program": _without_source(to_dict(program)),
        "agitators": [{"logical_id": name, **asdict(binding)} for name, binding in sorted(devices.items())],
    }
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    namespace = uuid5(NAMESPACE_URL, f"https://sciloom.invalid/{target.value}/{digest}")
    bindings = devices
    resources = {resource.node_id: bindings[resource.logical_id] for resource in program.resources}
    context = CodegenContext(program, namespace, resources)
    prepare_device_state(context)
    return build_functions(context, target)
