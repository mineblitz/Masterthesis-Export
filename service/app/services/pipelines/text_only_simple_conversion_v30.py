"""Text-only conversion pipeline v30 with deterministic object-model bridging.

v30 builds on v29 by adding an object-model bridge stage after scalar
resolution and before final response assembly.
"""

from __future__ import annotations

import json
from typing import Any

from app.models import ComponentLog, ExperimentRequest, ExperimentResponse
from app.services.components.object_model_bridge_v30 import map_value_to_object_model_v30
from app.services.pipelines.text_only_simple_conversion_v21 import _finish_component, _start_component
from app.services.pipelines.text_only_simple_conversion_v29 import run_text_only_simple_conversion_v29


def _component_details_by_name(components: list[ComponentLog], name: str) -> list[dict[str, Any]]:
    details: list[dict[str, Any]] = []
    for component in components:
        if component.name == name and component.details is not None:
            details.append(component.details)
    return details


def _resolve_source_chunk_ids(components: list[ComponentLog]) -> list[str]:
    chunk_ids: set[str] = set()

    for details in _component_details_by_name(components, "retrieval_diversity_selector"):
        selected = details.get("selected_chunk_ids")
        if isinstance(selected, list):
            for item in selected:
                if isinstance(item, str) and item:
                    chunk_ids.add(item)

    for details in _component_details_by_name(components, "ir_compiler_v29"):
        compiled_ir = details.get("compiled_ir")
        if isinstance(compiled_ir, dict):
            source_chunk_id = compiled_ir.get("source_chunk_id")
            if isinstance(source_chunk_id, str) and source_chunk_id:
                chunk_ids.add(source_chunk_id)

    return sorted(chunk_ids)


def _resolve_property_unit(components: list[ComponentLog]) -> str | None:
    ir_details = _component_details_by_name(components, "ir_compiler_v29")
    for details in reversed(ir_details):
        compiled_ir = details.get("compiled_ir")
        if isinstance(compiled_ir, dict):
            unit = compiled_ir.get("unit")
            if isinstance(unit, str) and unit:
                return unit
    return None


def run_text_only_simple_conversion_v30(payload: ExperimentRequest) -> ExperimentResponse:
    response = run_text_only_simple_conversion_v29(payload)

    result = response.result
    source_chunk_ids = _resolve_source_chunk_ids(result.components)
    property_unit = _resolve_property_unit(result.components)

    object_model_bridge = map_value_to_object_model_v30(
        payload=payload,
        extracted_value=result.extracted_value,
        property_unit=property_unit,
        source_chunk_ids=source_chunk_ids,
        pipeline_name="text_only_simple_conversion_v30",
    )

    bridge_component = _start_component("object_model_bridge_v30")
    bridge_details = {
        "bridge_record": object_model_bridge,
        "canonical_fields": [
            "entity_type",
            "entity_id",
            "property_key",
            "property_value",
            "property_unit",
            "condition_bindings",
            "provenance",
        ],
        "mapping_decisions": object_model_bridge["mapping_decisions"],
        "fallback_reason": object_model_bridge["mapping_decisions"].get("fallback_reason"),
    }
    result.components.append(
        _finish_component(
            bridge_component,
            status="success",
            details=bridge_details,
        )
    )

    object_bridge_section = "\n\n[Object Model Bridge v30]\n" + json.dumps(object_model_bridge, ensure_ascii=True)
    result.full_output = (result.full_output or "") + object_bridge_section

    response.pipeline = "text_only_simple_conversion_v30"
    return response
