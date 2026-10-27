"""Deterministic regulation-clause IR compiler for text-only v29.

Compiles selected clause evidence into a compact IR object with schema:
- subject
- condition
- operator
- value
- unit
- exception

The module also provides deterministic resolution that combines an LLM scalar
candidate with IR-derived scalar evidence.
"""

from __future__ import annotations

import re
from typing import Any

from app.models import ExperimentRequest
from app.services.components.hybrid_context_ranker import RankedChunk

_NUMERIC_WITH_UNIT_RE = re.compile(
    r"(?<!\d)(\d{1,4}(?:[\.,]\d{1,2})?)(?:\s*)(mm|cm|m|min|minute|minutes|minuten|h|hr|hrs|std|stunde|stunden)?\b",
    re.IGNORECASE,
)
_FIRE_CLASS_RE = re.compile(r"\b(?:EI|REI|F)\s*[- ]?(\d{2,3})\b", re.IGNORECASE)

_OPERATOR_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(mindestens|min\\.|minimum|nicht\\s+weniger\\s+als|at\\s+least)", re.IGNORECASE), ">="),
    (re.compile(r"(hoechstens|h\\u00f6chstens|maximal|maximum|nicht\\s+mehr\\s+als|bis\\s+zu|at\\s+most)", re.IGNORECASE), "<="),
    (re.compile(r"(gleich|genau|betr\\u00e4gt|betragt|entspricht|ist)", re.IGNORECASE), "=="),
]

_EXCEPTION_TERMS = (
    "ausgenommen",
    "abweichend",
    "gilt nicht",
    "nicht zulaessig",
    "nicht zul\u00e4ssig",
    "nur wenn",
    "except",
    "unless",
)

_LENGTH_VALUE_HINTS = (
    "thickness",
    "opening",
    "diameter",
    "width",
    "height",
    "abstand",
    "dicke",
)


def _condition_to_text(payload: ExperimentRequest) -> str:
    parts: list[str] = []
    for condition in payload.conditions or []:
        condition_type = condition.type.strip()
        condition_value = condition.value.strip()
        if condition_type and condition_value:
            parts.append(f"{condition_type}={condition_value}")
        elif condition_type:
            parts.append(condition_type)
        elif condition_value:
            parts.append(condition_value)
    return "; ".join(parts)


def _detect_operator(text: str) -> str | None:
    for pattern, operator in _OPERATOR_PATTERNS:
        if pattern.search(text):
            return operator
    return None


def _extract_exception(text: str) -> str | None:
    lowered = text.casefold()
    for term in _EXCEPTION_TERMS:
        if term in lowered:
            for sentence in re.split(r"[\n\.;]", text):
                if term in sentence.casefold():
                    cleaned = sentence.strip()
                    return cleaned[:240] if cleaned else term
            return term
    return None


def _extract_numeric_value_and_unit(text: str) -> tuple[float | None, str | None]:
    fire_match = _FIRE_CLASS_RE.search(text)
    if fire_match:
        try:
            return float(fire_match.group(1)), None
        except ValueError:
            return None, None

    match = _NUMERIC_WITH_UNIT_RE.search(text)
    if not match:
        return None, None

    raw_value = match.group(1)
    raw_unit = match.group(2)
    try:
        numeric_value = float(raw_value.replace(",", "."))
    except ValueError:
        return None, None

    unit = raw_unit.lower() if raw_unit else None
    return numeric_value, unit


def _normalize_unit(unit: str | None) -> str | None:
    if not unit:
        return None
    alias_map = {
        "minute": "min",
        "minutes": "min",
        "minuten": "min",
        "hr": "h",
        "hrs": "h",
        "std": "h",
        "stunde": "h",
        "stunden": "h",
    }
    return alias_map.get(unit, unit)


def _is_length_like_value(payload_value: str) -> bool:
    value = payload_value.casefold()
    return any(hint in value for hint in _LENGTH_VALUE_HINTS)


def normalize_ir_value_for_payload_v29(
    *,
    value: float | None,
    unit: str | None,
    payload: ExperimentRequest,
) -> float | None:
    if value is None:
        return None

    normalized_unit = _normalize_unit(unit)
    normalized_value = float(value)

    if _is_length_like_value(payload.value):
        if normalized_unit == "cm":
            normalized_value *= 10.0
        elif normalized_unit == "m":
            normalized_value *= 1000.0

    if payload.value.casefold() == "fire_resistance_class" and normalized_unit == "h":
        normalized_value *= 60.0

    return round(normalized_value, 4)


def _prioritized_chunks(
    selected_chunks: list[RankedChunk],
    clause_type_by_chunk_id: dict[str, str] | None,
) -> list[RankedChunk]:
    clause_types = clause_type_by_chunk_id or {}
    preferred = {"requirement", "scope"}
    preferred_chunks: list[RankedChunk] = []
    other_chunks: list[RankedChunk] = []

    for item in selected_chunks:
        clause_type = clause_types.get(item.chunk.chunk_id, "informational")
        if clause_type in preferred:
            preferred_chunks.append(item)
        else:
            other_chunks.append(item)

    return preferred_chunks + other_chunks


def compile_clause_ir_v29(
    *,
    payload: ExperimentRequest,
    selected_chunks: list[RankedChunk],
    clause_type_by_chunk_id: dict[str, str] | None,
) -> dict[str, Any]:
    condition_text = _condition_to_text(payload)
    subject = payload.value

    best_value: float | None = None
    best_unit: str | None = None
    best_operator: str | None = None
    best_exception: str | None = None
    source_chunk_id: str | None = None

    merged_text_for_exception: list[str] = []

    for item in _prioritized_chunks(selected_chunks, clause_type_by_chunk_id):
        chunk_text = item.chunk.text or ""
        merged_text_for_exception.append(chunk_text)
        numeric_value, numeric_unit = _extract_numeric_value_and_unit(chunk_text)
        operator = _detect_operator(chunk_text)
        exception = _extract_exception(chunk_text)

        if numeric_value is not None and best_value is None:
            best_value = numeric_value
            best_unit = _normalize_unit(numeric_unit)
            best_operator = operator or "=="
            best_exception = exception
            source_chunk_id = item.chunk.chunk_id
            break

    if best_exception is None:
        best_exception = _extract_exception("\n".join(merged_text_for_exception))

    return {
        "subject": subject,
        "condition": condition_text,
        "operator": best_operator,
        "value": best_value,
        "unit": best_unit,
        "exception": best_exception,
        "source_chunk_id": source_chunk_id,
        "deterministic": True,
        "schema_version": "v29_ir_1",
    }


def select_scalar_using_ir_v29(
    *,
    llm_value: float | None,
    ir_compiled: dict[str, Any],
    payload: ExperimentRequest,
    tolerance: float = 0.2,
) -> dict[str, Any]:
    ir_raw_value = ir_compiled.get("value")
    ir_unit = ir_compiled.get("unit")
    ir_normalized_value = normalize_ir_value_for_payload_v29(
        value=ir_raw_value if isinstance(ir_raw_value, (int, float)) else None,
        unit=ir_unit if isinstance(ir_unit, str) else None,
        payload=payload,
    )

    if llm_value is None and ir_normalized_value is None:
        return {
            "selected_value": None,
            "decision": "no_candidate",
            "ir_normalized_value": None,
            "aligned": False,
        }

    if llm_value is None and ir_normalized_value is not None:
        return {
            "selected_value": ir_normalized_value,
            "decision": "ir_fallback",
            "ir_normalized_value": ir_normalized_value,
            "aligned": True,
        }

    if llm_value is not None and ir_normalized_value is None:
        return {
            "selected_value": llm_value,
            "decision": "llm_only",
            "ir_normalized_value": None,
            "aligned": True,
        }

    assert llm_value is not None
    assert ir_normalized_value is not None

    aligned = abs(llm_value - ir_normalized_value) <= tolerance
    if aligned:
        return {
            "selected_value": llm_value,
            "decision": "llm_aligned_with_ir",
            "ir_normalized_value": ir_normalized_value,
            "aligned": True,
        }

    return {
        "selected_value": ir_normalized_value,
        "decision": "ir_override_mismatch",
        "ir_normalized_value": ir_normalized_value,
        "aligned": False,
    }
