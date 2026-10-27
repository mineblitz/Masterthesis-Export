"""Deterministic object-model bridge for text-only v30.

Maps resolved extraction outputs into canonical entity/property records used by
KG/BIM-oriented downstream validation.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from app.models import ExperimentRequest

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def _slugify(value: str) -> str:
    lowered = value.strip().lower()
    normalized = _NON_ALNUM_RE.sub("_", lowered)
    return normalized.strip("_") or "na"


def _canonicalize_conditions(conditions: list[ExperimentRequest.Condition] | None) -> list[dict[str, str]]:
    canonical: list[dict[str, str]] = []
    for item in conditions or []:
        condition_type = _slugify(item.type)
        condition_value = item.value.strip().lower()
        canonical.append({"type": condition_type, "value": condition_value})
    canonical.sort(key=lambda entry: (entry["type"], entry["value"]))
    return canonical


def _normalize_scalar(value: Any) -> float | int | str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return round(float(value), 4)
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    return str(value)


def canonical_entity_type_v30(value_key: str) -> str:
    normalized = value_key.strip().lower()
    if normalized in {"min_thickness", "max_thickness"}:
        return "firestop_system"
    if normalized.startswith("allowed"):
        return "requirement"
    if normalized == "fire_resistance_class":
        return "requirement"
    return "requirement"


def canonical_property_key_v30(value_key: str) -> tuple[str, str | None]:
    normalized = value_key.strip().lower()
    if normalized == "min_thickness":
        return "minimum_thickness", None
    if normalized == "max_thickness":
        return "maximum_thickness", None
    if normalized == "fire_resistance_class":
        return "fire_resistance_class", None
    if normalized.startswith("allowed"):
        return "allowed_types", None
    return "generic_requirement_property", f"no_specialized_mapping_for_{_slugify(value_key)}"


def _deterministic_entity_id(
    *,
    system: str,
    system_name: str,
    value_key: str,
    condition_bindings: list[dict[str, str]],
) -> str:
    base_slug = "_".join(
        [
            _slugify(system),
            _slugify(system_name),
            _slugify(value_key),
        ]
    )
    condition_signature = json.dumps(condition_bindings, ensure_ascii=True, sort_keys=True)
    digest = hashlib.sha1(condition_signature.encode("utf-8")).hexdigest()[:10]
    return f"ent_{base_slug}_{digest}"


def map_value_to_object_model_v30(
    *,
    payload: ExperimentRequest,
    extracted_value: Any,
    property_unit: str | None,
    source_chunk_ids: list[str],
    pipeline_name: str,
    pipeline_version: str = "v30",
) -> dict[str, Any]:
    condition_bindings = _canonicalize_conditions(payload.conditions)
    entity_type = canonical_entity_type_v30(payload.value)
    property_key, fallback_reason = canonical_property_key_v30(payload.value)
    property_value = _normalize_scalar(extracted_value)
    entity_id = _deterministic_entity_id(
        system=payload.system,
        system_name=payload.system_name,
        value_key=payload.value,
        condition_bindings=condition_bindings,
    )

    mapping_decisions = {
        "value_key": payload.value,
        "entity_type_rule": entity_type,
        "property_key_rule": property_key,
        "used_generic_fallback": property_key == "generic_requirement_property",
    }
    if fallback_reason:
        mapping_decisions["fallback_reason"] = fallback_reason

    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "property_key": property_key,
        "property_value": property_value,
        "property_unit": property_unit,
        "condition_bindings": condition_bindings,
        "provenance": {
            "source_chunk_ids": sorted(source_chunk_ids),
            "pipeline": pipeline_name,
            "pipeline_version": pipeline_version,
            "experiment_id": payload.experiment_id,
            "deterministic": True,
        },
        "mapping_decisions": mapping_decisions,
    }
