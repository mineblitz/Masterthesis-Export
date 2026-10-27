"""Render structured cable and pipe records into JSON husks."""

import copy
from typing import Any


def _base_object(input_json_husk: Any, *, system: str, record_count: int) -> dict[str, Any]:
    if isinstance(input_json_husk, dict):
        base = copy.deepcopy(input_json_husk)
    else:
        base = {}

    if "system" not in base:
        base["system"] = system
    if "record_count" not in base:
        base["record_count"] = record_count
    return base


def render_cable_records_to_json_husk(
    input_json_husk: Any,
    records: list[dict[str, Any]],
    *,
    system: str,
) -> dict[str, Any]:
    rendered = _base_object(input_json_husk, system=system, record_count=len(records))
    rendered["cables"] = copy.deepcopy(records)
    return rendered


def render_pipe_records_to_json_husk(
    input_json_husk: Any,
    records: list[dict[str, Any]],
    *,
    system: str,
) -> dict[str, Any]:
    rendered = _base_object(input_json_husk, system=system, record_count=len(records))
    rendered["pipes"] = copy.deepcopy(records)
    return rendered