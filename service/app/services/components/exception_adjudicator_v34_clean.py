"""Exception-aware adjudication for text-only pipeline v34.

Detects exclusion and override language and applies soft confidence adjustments.
This component is strictly non-blocking and never forces null extraction.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


_EXCEPTION_TERMS = (
    "ausgenommen",
    "abweichend",
    "gilt nicht",
    "ausser",
    "except",
    "unless",
    "nicht zulaessig",
    "nicht zulassig",
)

_OVERRIDE_TERMS = (
    "vorrang",
    "hat vorrang",
    "massgeblich",
    "override",
    "ueberschreibt",
)

_NUMBER_RE = re.compile(r"(?<!\d)(\d{1,4}(?:[\.,]\d{1,2})?)(?!\d)")


@dataclass(frozen=True)
class ExceptionAdjudicationResultV34:
    exception_hits: int
    override_hits: int
    matched_chunk_ids: list[str]
    exception_penalty: float
    override_bonus: float
    net_adjustment: float
    contradiction_window_lines: int


def _normalize(text: str) -> str:
    return (
        text.casefold()
        .replace("ae", "a")
        .replace("oe", "o")
        .replace("ue", "u")
        .replace("\u00df", "ss")
        .replace("\u00e4", "a")
        .replace("\u00f6", "o")
        .replace("\u00fc", "u")
    )


def _extract_numbers(text: str) -> list[float]:
    numbers: list[float] = []
    for raw in _NUMBER_RE.findall(text):
        try:
            numbers.append(float(raw.replace(",", ".")))
        except ValueError:
            continue
    return numbers


def _matches_candidate_value(text: str, extracted_value: float | None, tolerance: float = 0.2) -> bool:
    if extracted_value is None:
        return False
    for number in _extract_numbers(text):
        if abs(number - extracted_value) <= tolerance:
            return True
    return False


def _chunk_attr(item: Any, key: str, default: Any) -> Any:
    chunk = getattr(item, "chunk", item)
    return getattr(chunk, key, default)


def adjudicate_exceptions_v34(
    *,
    selected_chunks: list[Any],
    extracted_value: float | None,
    contradiction_window_lines: int = 2,
) -> ExceptionAdjudicationResultV34:
    exception_hits = 0
    override_hits = 0
    matched_chunk_ids: list[str] = []

    local_penalty = 0.0
    local_bonus = 0.0

    candidate_locations: list[tuple[str, int, int]] = []
    exception_locations: list[tuple[str, int, int]] = []

    for item in selected_chunks:
        text = str(_chunk_attr(item, "text", ""))
        norm = _normalize(text)
        chunk_id = str(_chunk_attr(item, "chunk_id", "unknown"))
        doc_path = str(_chunk_attr(item, "document_path", ""))
        start_line = int(_chunk_attr(item, "start_line", 0))
        end_line = int(_chunk_attr(item, "end_line", start_line))

        has_exception = any(term in norm for term in _EXCEPTION_TERMS)
        has_override = any(term in norm for term in _OVERRIDE_TERMS)
        candidate_match = _matches_candidate_value(text, extracted_value)

        if candidate_match:
            candidate_locations.append((doc_path, start_line, end_line))

        if has_exception:
            exception_hits += 1
            local_penalty += 0.03
            exception_locations.append((doc_path, start_line, end_line))
            if chunk_id not in matched_chunk_ids:
                matched_chunk_ids.append(chunk_id)
            if candidate_match:
                local_penalty += 0.025

        if has_override:
            override_hits += 1
            local_bonus += 0.02
            if chunk_id not in matched_chunk_ids:
                matched_chunk_ids.append(chunk_id)
            if candidate_match:
                local_bonus += 0.015

    proximity_hits = 0
    for ex_doc, ex_start, ex_end in exception_locations:
        for cand_doc, cand_start, cand_end in candidate_locations:
            if ex_doc != cand_doc:
                continue
            distance = min(abs(ex_start - cand_end), abs(cand_start - ex_end))
            if distance <= contradiction_window_lines:
                proximity_hits += 1

    if proximity_hits > 0:
        local_penalty += min(0.05, 0.01 * proximity_hits)

    exception_penalty = round(min(0.22, local_penalty), 4)
    override_bonus = round(min(0.12, local_bonus), 4)
    net_adjustment = round(max(-0.22, min(0.12, override_bonus - exception_penalty)), 4)

    return ExceptionAdjudicationResultV34(
        exception_hits=exception_hits,
        override_hits=override_hits,
        matched_chunk_ids=matched_chunk_ids,
        exception_penalty=exception_penalty,
        override_bonus=override_bonus,
        net_adjustment=net_adjustment,
        contradiction_window_lines=contradiction_window_lines,
    )
