"""Execute ordered well metadata operations against explicit services."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sciloom.core.ir.model import ReadWellProperty, WriteWellProperty
from sciloom.core.locations import Zone
from .environment import WellPropertyReadEvent, WellPropertyWriteEvent, _require_service
from .expressions import evaluate
from .values import RuntimeValue, fail

if TYPE_CHECKING:
    from .runtime import Interpreter


def execute_property(
    session: Interpreter, node: ReadWellProperty | WriteWellProperty, frame: dict[str, RuntimeValue]
) -> None:
    """Capture once, validate locations, then read or write metadata in order."""
    value = evaluate(session, node.value, frame) if isinstance(node, WriteWellProperty) else None
    zone = evaluate(session, node.zone, frame)
    assert isinstance(zone, Zone)
    default = (
        evaluate(session, node.default, frame)
        if isinstance(node, ReadWellProperty) and node.default is not None
        else None
    )
    directory = _require_service(session.environment.locations, "locations", node)
    store = _require_service(session.environment.properties, "properties", node)
    if isinstance(node, ReadWellProperty) and len(zone.well_ids) != 1:
        fail("well_property_selection", "Reading a well property requires exactly one well.", node)
    known = {well.identity for well in directory.wells}
    if any(well not in known for well in zone.well_ids):
        fail("unknown_well", "The selection contains a well absent from the location directory.", node)
    if isinstance(node, WriteWellProperty):
        assert isinstance(value, str)
        try:
            if zone.well_ids:
                returned = store.set(zone.well_ids, node.property.name, value)  # type: ignore[func-returns-value]
                if returned is not None:
                    raise TypeError("WellProperties.set must return None.")
        except Exception as error:
            fail("property_service_error", f"Well-property write failed: {error}", node)
        session._record_event(
            WellPropertyWriteEvent(
                node_id=node.node_id,
                source=node.source,
                zone=zone,
                name=node.property.name,
                type=node.property.type,
                value=value,
            )
        )
    else:
        used_default = False
        try:
            value = store.get(zone.well_ids[0], node.property.name)
            if type(value) is not str:
                raise TypeError("Stored property is not text.")
        except (KeyError, TypeError) as error:
            if default is None:
                fail(
                    "well_property_missing" if isinstance(error, KeyError) else "well_property_type",
                    "The selected well has no compatible text property; supply a default to recover.",
                    node,
                )
            assert isinstance(default, str)
            value, used_default = default, True
        except Exception as error:
            fail("property_service_error", f"Well-property read failed: {error}", node)
        assert isinstance(value, str)
        session._write(node.target, value, frame)
        session._record_event(
            WellPropertyReadEvent(
                node_id=node.node_id,
                source=node.source,
                zone=zone,
                name=node.property.name,
                type=node.property.type,
                value=value,
                used_default=used_default,
            )
        )
