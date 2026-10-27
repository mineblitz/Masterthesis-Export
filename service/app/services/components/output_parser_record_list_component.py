"""Output parser for structured record-list extraction experiments."""

from typing import Any

from app.services.components.output_parser_boolean_map_component import _load_json_object


FieldKind = str


def _normalize_string(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"extracted_value records require non-empty string field '{field_name}'")
    return value.strip()


def _normalize_number(value: Any, *, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"extracted_value records require numeric field '{field_name}'")
    return float(value)


def _normalize_string_list(value: Any, *, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"extracted_value records require list field '{field_name}'")

    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(
                f"extracted_value records require list '{field_name}' to contain only non-empty strings"
            )
        normalized.append(item.strip())

    return normalized


def _normalize_record(record: Any, *, field_schema: dict[str, FieldKind]) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("extracted_value entries must be JSON objects")

    record_keys = set(record.keys())
    expected_keys = set(field_schema.keys())
    missing_keys = sorted(expected_keys - record_keys)
    extra_keys = sorted(record_keys - expected_keys)
    if missing_keys or extra_keys:
        raise ValueError(
            "extracted_value records must contain exactly the expected keys. "
            f"Missing: {missing_keys}; Extra: {extra_keys}"
        )

    normalized: dict[str, Any] = {}
    for field_name, field_kind in field_schema.items():
        value = record[field_name]
        if field_kind == "string":
            normalized[field_name] = _normalize_string(value, field_name=field_name)
        elif field_kind == "number":
            normalized[field_name] = _normalize_number(value, field_name=field_name)
        elif field_kind == "string_list":
            normalized[field_name] = _normalize_string_list(value, field_name=field_name)
        else:
            raise ValueError(f"Unsupported field kind '{field_kind}' for '{field_name}'")

    return normalized


def normalize_record_list(
    records: Any,
    *,
    field_schema: dict[str, FieldKind],
    allow_empty: bool = False,
    value_label: str = "expected_value",
) -> list[dict[str, Any]]:
    if not isinstance(records, list):
        raise ValueError(f"{value_label} must be an array of record objects")

    if not records and not allow_empty:
        raise ValueError(f"{value_label} must be a non-empty array of record objects")

    return [_normalize_record(record, field_schema=field_schema) for record in records]


def parse_extracted_record_list(
    raw_output: str,
    *,
    field_schema: dict[str, FieldKind],
) -> tuple[list[dict[str, Any]] | None, float | None]:
    """Parse strict JSON output and normalize extracted_value to a record list with confidence."""
    data = _load_json_object(raw_output)

    extracted = data.get("extracted_value")
    confidence = data.get("confidence")

    if extracted is None:
        return None, None
    if not isinstance(extracted, list):
        raise ValueError("extracted_value must be an array or null")

    normalized_records = normalize_record_list(
        extracted,
        field_schema=field_schema,
        allow_empty=True,
        value_label="extracted_value",
    )

    if confidence is not None:
        try:
            confidence = float(confidence)
            if not (0.0 <= confidence <= 1.0):
                confidence = max(0.0, min(1.0, confidence))
        except (TypeError, ValueError):
            confidence = None

    return normalized_records, confidence