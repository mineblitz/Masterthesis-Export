"""Retrieval enhancements for text-only v22 pipeline with fire-domain query expansion and numeric normalization."""

import re

from app.models import ExperimentRequest
from app.services.components.retrieval_enhancer_v21_text import (
    AdaptiveRetryPlan,
    SelectionConsistencyResult,
    build_multi_query_variants_v21,
    choose_adaptive_retry_plan_v21,
    select_consistent_diverse_chunks_v21,
)


_NUMERIC_WITH_UNIT_PATTERN = re.compile(
    r"(?P<value>[-+]?\d+(?:[\.,]\d+)?)\s*(?P<unit>h|std|stunden|stunde|min|minute|minuten)?",
    re.IGNORECASE,
)

_FIRE_VALUE_HINTS = (
    "fire_resistance",
    "feuerwiderstand",
    "brandklasse",
    "widerstandsklasse",
    "feuerwiderstandsklasse",
)


def _normalize_for_match(text: str) -> str:
    return (
        text.casefold()
        .replace("ae", "a")
        .replace("oe", "o")
        .replace("ue", "u")
        .replace("ß", "ss")
        .replace("ä", "a")
        .replace("ö", "o")
        .replace("ü", "u")
    )


def _is_fire_resistance_value(payload: ExperimentRequest) -> bool:
    value_name = _normalize_for_match(payload.value)
    return any(hint in value_name for hint in _FIRE_VALUE_HINTS)


def _add_term(target: list[str], seen: set[str], term: str) -> None:
    cleaned = " ".join(term.strip().split())
    if not cleaned:
        return
    normalized = _normalize_for_match(cleaned)
    if normalized in seen:
        return
    seen.add(normalized)
    target.append(cleaned)


def _fire_domain_query_expansions(payload: ExperimentRequest) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()

    _add_term(terms, seen, "Feuerwiderstand")
    _add_term(terms, seen, "Feuerwiderstandsklasse")
    _add_term(terms, seen, "Brandklasse")

    minute_candidates: list[float] = []
    if isinstance(payload.expected_value, (int, float)):
        minute_candidates.append(float(payload.expected_value))

    for condition in payload.conditions or []:
        for match in _NUMERIC_WITH_UNIT_PATTERN.finditer(condition.value):
            raw = match.group("value")
            try:
                parsed = float(raw.replace(",", "."))
            except ValueError:
                continue
            unit = (match.group("unit") or "").lower()
            if unit in {"h", "std", "stunden", "stunde"}:
                minute_candidates.append(parsed * 60.0)
            else:
                minute_candidates.append(parsed)

    for minute_value in minute_candidates:
        if minute_value <= 0:
            continue
        rounded_minutes = int(round(minute_value))
        _add_term(terms, seen, f"EI {rounded_minutes}")
        _add_term(terms, seen, f"REI {rounded_minutes}")
        _add_term(terms, seen, f"F {rounded_minutes}")
        _add_term(terms, seen, f"{rounded_minutes} min")
        _add_term(terms, seen, f"{rounded_minutes} Minuten")

        hour_value = minute_value / 60.0
        hour_text = f"{hour_value:g}"
        comma_hour_text = hour_text.replace(".", ",")
        _add_term(terms, seen, f"{hour_text} h")
        _add_term(terms, seen, f"{comma_hour_text} h")
        _add_term(terms, seen, f"{hour_text} Stunden")

    return terms


def build_multi_query_variants_v22(
    *,
    payload: ExperimentRequest,
    base_search_terms: list[str] | None,
    query_limit: int,
) -> list[str]:
    variants = build_multi_query_variants_v21(
        payload=payload,
        base_search_terms=base_search_terms,
        query_limit=max(2, query_limit),
    )

    if not _is_fire_resistance_value(payload):
        return variants[: max(2, query_limit)]

    seen = {_normalize_for_match(term) for term in variants}
    for expansion in _fire_domain_query_expansions(payload):
        _add_term(variants, seen, expansion)

    return variants[: max(2, query_limit)]


def normalize_numeric_value_for_payload_v22(
    value: float | int | None,
    payload: ExperimentRequest,
    *,
    source_text: str | None = None,
) -> float | None:
    if value is None:
        return None

    normalized = float(value)
    if not _is_fire_resistance_value(payload):
        return normalized

    normalized_source = _normalize_for_match(source_text or "")
    explicit_hour_unit = any(token in normalized_source for token in [" h", "std", "stunde", "stunden"])

    # For fire-resistance classes, low scalar values typically represent hours and are normalized to minutes.
    if explicit_hour_unit or (0 < normalized <= 6.0):
        normalized *= 60.0

    rounded = round(normalized, 4)
    if abs(rounded - round(rounded)) <= 1e-9:
        return float(int(round(rounded)))
    return rounded


def _extract_normalized_numeric_values(text: str, payload: ExperimentRequest) -> list[float]:
    values: list[float] = []
    for match in _NUMERIC_WITH_UNIT_PATTERN.finditer(text):
        raw = match.group("value")
        try:
            parsed = float(raw.replace(",", "."))
        except ValueError:
            continue

        unit = (match.group("unit") or "").lower()
        local_source = unit
        if unit in {"h", "std", "stunden", "stunde"}:
            local_source = "h"
        elif unit in {"min", "minute", "minuten"}:
            local_source = "min"

        normalized = normalize_numeric_value_for_payload_v22(parsed, payload, source_text=local_source)
        if normalized is not None:
            values.append(normalized)
    return values


def select_consistent_diverse_chunks_v22(
    *,
    ranked_chunks,
    top_k: int,
    max_per_document: int,
    max_per_heading: int,
    payload: ExperimentRequest,
    query_variants: list[str],
    minimum_query_length: int,
    rerank_strategy: str,
) -> SelectionConsistencyResult:
    base = select_consistent_diverse_chunks_v21(
        ranked_chunks=ranked_chunks,
        top_k=top_k,
        max_per_document=max_per_document,
        max_per_heading=max_per_heading,
        payload=payload,
        query_variants=query_variants,
        minimum_query_length=minimum_query_length,
        rerank_strategy=rerank_strategy,
    )

    numeric_candidates: list[float] = []
    bucket_counts: dict[float, int] = {}
    for item in base.selected_chunks:
        for numeric_value in _extract_normalized_numeric_values(item.chunk.text, payload):
            bucket = round(numeric_value, 1)
            bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
            numeric_candidates.append(numeric_value)

    if not numeric_candidates:
        consistency = 1.0
        conflicting: list[float] = []
    elif len(bucket_counts) == 1:
        consistency = 1.0
        conflicting = []
    else:
        dominant = max(bucket_counts.values())
        consistency = round(dominant / len(numeric_candidates), 4)
        dominant_bucket = max(bucket_counts.items(), key=lambda item: item[1])[0]
        conflicting = [value for value in numeric_candidates if round(value, 1) != dominant_bucket]

    return SelectionConsistencyResult(
        selected_chunks=base.selected_chunks,
        average_evidence_score=base.average_evidence_score,
        chunk_evidence=base.chunk_evidence,
        evidence_consistency_score=consistency,
        conflicting_numeric_candidates=conflicting,
        contradiction_hit_count=base.contradiction_hit_count,
        skipped_for_document_cap=base.skipped_for_document_cap,
        skipped_for_heading_cap=base.skipped_for_heading_cap,
        skipped_for_redundancy=base.skipped_for_redundancy,
    )


def choose_adaptive_retry_plan_v22(
    *,
    retry_index: int,
    top_k: int,
    narrow_expansion_step: int,
    broad_expansion_multiplier: int,
) -> AdaptiveRetryPlan:
    return choose_adaptive_retry_plan_v21(
        retry_index=retry_index,
        top_k=top_k,
        narrow_expansion_step=narrow_expansion_step,
        broad_expansion_multiplier=broad_expansion_multiplier,
    )
