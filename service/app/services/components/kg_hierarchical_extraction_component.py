"""Helpers for hierarchical KG schema extraction pipelines."""

import json
import re
from typing import Any


def _strip_markdown_fences(text: str) -> str:
    cleaned = text.strip()
    if not cleaned.startswith("```"):
        return cleaned

    lines = cleaned.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def parse_json_object_best_effort(text: str) -> dict[str, Any]:
    """Parse a best-effort JSON object from possibly noisy LLM output."""
    cleaned = _strip_markdown_fences(text)

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", cleaned)
    if not match:
        return {}

    try:
        data = json.loads(match.group(0))
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        return {}

    return {}


def extract_schema_top_level_branches(input_kg_schema_ttl: str, max_branches: int = 12) -> list[str]:
    """Heuristically extract top-level class/entity names from schema turtle."""
    candidates: list[str] = []

    for match in re.finditer(r"\ba\s+([A-Za-z_][\w\-]*:[A-Za-z_][\w\-]*)", input_kg_schema_ttl):
        iri = match.group(1)
        local = iri.split(":", 1)[1].strip()
        if not local:
            continue
        if local.lower() in {"class", "property", "thing", "resource"}:
            continue
        if local not in candidates:
            candidates.append(local)
        if len(candidates) >= max_branches:
            break

    if candidates:
        return candidates

    for match in re.finditer(r"([A-Za-z_][\w\-]*):([A-Za-z_][\w\-]*)", input_kg_schema_ttl):
        local = match.group(2).strip()
        if not local:
            continue
        if local.lower() in {"class", "property", "thing", "resource", "type"}:
            continue
        if local not in candidates:
            candidates.append(local)
        if len(candidates) >= max_branches:
            break

    return candidates


def normalize_presence_output(parsed: dict[str, Any], candidates: list[str]) -> list[str]:
    """Return detected branch names from staged presence JSON output."""
    requested = parsed.get("detected_branches")
    if isinstance(requested, list):
        result = [str(item).strip() for item in requested if str(item).strip() in candidates]
        if result:
            return result

    presence_map = parsed.get("presence")
    if isinstance(presence_map, dict):
        selected: list[str] = []
        for branch in candidates:
            value = presence_map.get(branch)
            if isinstance(value, bool) and value:
                selected.append(branch)
            elif isinstance(value, str) and value.strip().lower() in {"true", "yes", "1", "present"}:
                selected.append(branch)
        if selected:
            return selected

    return []


def normalize_subtype_output(parsed: dict[str, Any], branch: str, max_subtypes: int = 6) -> list[str]:
    """Return detected subtype labels for a branch from staged subtype JSON output."""
    by_branch = parsed.get("subtypes")
    items: list[str] = []

    if isinstance(by_branch, dict) and isinstance(by_branch.get(branch), list):
        items = [str(v).strip() for v in by_branch[branch] if str(v).strip()]
    elif isinstance(parsed.get("detected_subtypes"), list):
        items = [str(v).strip() for v in parsed["detected_subtypes"] if str(v).strip()]

    unique: list[str] = []
    for item in items:
        if item not in unique:
            unique.append(item)
        if len(unique) >= max_subtypes:
            break

    return unique
