"""Output parser component for JSON extraction from LLM responses."""

from __future__ import annotations

import json
import re
from typing import Any


def _strip_markdown_fences(raw_output: str) -> str:
    cleaned_output = raw_output.strip()
    if cleaned_output.startswith("```"):
        lines = cleaned_output.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().endswith("```"):
            lines = lines[:-1]
        cleaned_output = "\n".join(lines).strip()
    return cleaned_output


def _extract_first_json_object(text: str) -> str | None:
    """Return the first balanced top-level JSON object from free-form text."""
    start = text.find("{")
    while start != -1:
        depth = 0
        in_string = False
        escaped = False
        for idx in range(start, len(text)):
            char = text[idx]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start : idx + 1]

        start = text.find("{", start + 1)

    return None


def parse_extracted_payload(raw_output: str) -> tuple[dict[str, Any], str]:
    """Parse LLM output into JSON payload and cleaned raw response text.

    If no valid JSON object can be parsed, this returns ({}, cleaned_response)
    instead of raising, so callers can keep processing with plain-text fallback.
    """
    cleaned_output = _strip_markdown_fences(raw_output)

    try:
        data = json.loads(cleaned_output)
        if isinstance(data, dict):
            return data, cleaned_output
    except json.JSONDecodeError:
        pass

    json_candidate = _extract_first_json_object(cleaned_output)
    if json_candidate:
        try:
            data = json.loads(json_candidate)
            if isinstance(data, dict):
                return data, cleaned_output
        except json.JSONDecodeError:
            pass

    return {}, cleaned_output


def parse_extracted_value(raw_output: str) -> float | None:
    """Extract numeric extracted_value from LLM output, with robust fallback.

    The parser never raises on malformed or missing JSON. If JSON cannot be
    parsed, it returns None and leaves handling to the caller.
    """
    data, _ = parse_extracted_payload(raw_output)
    extracted = data.get("extracted_value")
    if extracted is None:
        return None

    if isinstance(extracted, (int, float)):
        return float(extracted)

    if isinstance(extracted, str):
        normalized = extracted.strip()
        if not normalized:
            return None
        match = re.search(r"[-+]?\d+(?:[\.,]\d+)?", normalized)
        if not match:
            return None
        return float(match.group(0).replace(",", "."))

    return None


def parse_extracted_answer(
    raw_output: str,
    *,
    preserve_text: bool = False,
) -> float | str | None:
    """Parse an answer as either the legacy numeric value or its verbatim text."""
    if not preserve_text:
        return parse_extracted_value(raw_output)

    data, _ = parse_extracted_payload(raw_output)
    extracted = data.get("extracted_value")
    if extracted is None or isinstance(extracted, bool):
        return None
    if isinstance(extracted, str):
        return extracted.strip() or None
    if isinstance(extracted, (int, float)):
        return str(extracted)
    return None
