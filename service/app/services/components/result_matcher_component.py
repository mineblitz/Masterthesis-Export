"""Shared result matching helpers for experiment pipelines."""

import json
import re
from typing import Any


ExperimentValue = float | str | dict[str, Any] | list[dict[str, Any]] | None


def _try_parse_number(value: float | str | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return None
        if re.fullmatch(r"[-+]?\d+(?:[\.,]\d+)?", normalized):
            return float(normalized.replace(",", "."))
    return None


def _is_record_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, dict) for item in value)


def _normalize_structured_value(value: Any) -> Any:
    if isinstance(value, bool) or value is None:
        return value

    if isinstance(value, (int, float)):
        return round(float(value), 9)

    if isinstance(value, str):
        return value.strip().casefold()

    if isinstance(value, dict):
        normalized_items = {
            key: _normalize_structured_value(item_value)
            for key, item_value in sorted(value.items())
        }
        return normalized_items

    if isinstance(value, list):
        normalized_items = [_normalize_structured_value(item) for item in value]
        return sorted(
            normalized_items,
            key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=True),
        )

    return value


def evaluate_match(
    extracted_value: ExperimentValue,
    expected_value: ExperimentValue,
) -> bool:
    """Compare extracted and expected values for both numeric and label experiments."""
    if expected_value is None:
        return extracted_value is None
    if extracted_value is None:
        return False

    if _is_record_list(expected_value):
        if not _is_record_list(extracted_value):
            return False
        return _normalize_structured_value(expected_value) == _normalize_structured_value(
            extracted_value
        )

    if isinstance(expected_value, dict):
        if not isinstance(extracted_value, dict):
            return False
        return expected_value == extracted_value

    extracted_number = _try_parse_number(extracted_value)
    expected_number = _try_parse_number(expected_value)
    if extracted_number is not None and expected_number is not None:
        return abs(extracted_number - expected_number) < 1e-9

    return str(extracted_value).strip().casefold() == str(expected_value).strip().casefold()
