"""Prompt builder for KG Turtle record extraction pipelines."""

import json
from typing import Any

from app.models import ExperimentRequest


def _format_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, indent=2)


def build_kg_record_extraction_prompt(
    *,
    template: str,
    payload: ExperimentRequest,
    docs_text: str,
    record_schema: dict[str, str],
    input_husk: str,
    input_format: str,
    husk_mode: str,
    metadata: dict[str, Any],
    expected_record_count: int,
) -> str:
    scope_profile = metadata.get("scope_profile", {}) if isinstance(metadata, dict) else {}
    placeholders = {
        "{{SYSTEM}}": payload.system,
        "{{SYSTEM_NAME}}": payload.system_name,
        "{{VALUE}}": payload.value,
        "{{INPUT_HUSK}}": input_husk.strip(),
        "{{INPUT_FORMAT}}": input_format,
        "{{INPUT_TURTLE_HUSK}}": input_husk.strip(),
        "{{INPUT_JSON_HUSK}}": input_husk.strip(),
        "{{HUSK_MODE}}": husk_mode,
        "{{RECORD_SCHEMA_JSON}}": _format_json(record_schema),
        "{{SCOPE_PROFILE_JSON}}": _format_json(scope_profile),
        "{{EXPECTED_RECORD_COUNT}}": str(expected_record_count),
        "{{DOCUMENT_CONTENT}}": docs_text,
    }

    rendered = template
    for token, value in placeholders.items():
        rendered = rendered.replace(token, value)

    return rendered