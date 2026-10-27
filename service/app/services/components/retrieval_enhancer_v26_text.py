"""Retrieval and verification enhancements for text-only v26.

v26 extends v25 compliance routing with:
- lightweight clause typing metadata on selected chunks
- deterministic semantic verifier for extracted numeric candidates
"""

from __future__ import annotations

import re

from app.models import ExperimentRequest
from app.services.components.hybrid_context_ranker import RankedChunk
from app.services.components.retrieval_enhancer_v25_text import (
    build_multi_query_variants_v25,
    choose_adaptive_retry_plan_v25,
    normalize_numeric_value_for_payload_v25,
    select_consistent_diverse_chunks_v25,
)

_REQUIREMENT_TERMS = (
    "anforderung",
    "mindest",
    "mindestens",
    "maximal",
    "hoechstens",
    "hochstens",
    "muss",
    "duerfen",
    "darf",
    "zulaessig",
    "zulassig",
    "feuerwiderstand",
    "klassifizierung",
    "abschottung",
    "dicke",
    "abstand",
)

_EXCEPTION_TERMS = (
    "ausgenommen",
    "abweichend",
    "gilt nicht",
    "nicht zulaessig",
    "nicht zulassig",
    "nur wenn",
)

_ADMINISTRATIVE_TERMS = (
    "antragsteller",
    "hersteller",
    "gebuehren",
    "gebuhren",
    "hinweis",
    "allgemeines",
    "bescheid",
    "rechtsbehelf",
    "ueberwachung",
    "uberwachung",
)

_SCOPE_TERMS = (
    "anwendungsbereich",
    "geltungsbereich",
    "einsatzbereich",
    "system",
    "wand",
    "decke",
)

_NUMBER_RE = re.compile(r"(?<!\d)(\d{1,4}(?:[\.,]\d{1,2})?)(?!\d)")


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


def _count_hits(text: str, terms: tuple[str, ...]) -> int:
    return sum(1 for term in terms if term in text)


def _classify_clause_type_v26(*, heading: str | None, text: str) -> str:
    merged = _normalize_for_match(f"{heading or ''}\n{text}")
    exception_hits = _count_hits(merged, _EXCEPTION_TERMS)
    requirement_hits = _count_hits(merged, _REQUIREMENT_TERMS)
    scope_hits = _count_hits(merged, _SCOPE_TERMS)
    administrative_hits = _count_hits(merged, _ADMINISTRATIVE_TERMS)

    if exception_hits > 0:
        return "exception"
    if requirement_hits > 0:
        return "requirement"
    if scope_hits > 0 and administrative_hits == 0:
        return "scope"
    if administrative_hits > 0:
        return "administrative"
    return "informational"


def _semantic_anchors_v26(payload: ExperimentRequest) -> list[str]:
    anchors: list[str] = []
    anchors.extend(part for part in payload.value.replace("_", " ").split() if part)

    for condition in payload.conditions or []:
        if condition.type.strip():
            anchors.append(condition.type.strip())
        if condition.value.strip():
            anchors.append(condition.value.strip())

    normalized: list[str] = []
    seen: set[str] = set()
    for anchor in anchors:
        norm = _normalize_for_match(anchor)
        if len(norm) < 4:
            continue
        if norm in seen:
            continue
        seen.add(norm)
        normalized.append(norm)
    return normalized


def _extract_numeric_candidates(text: str) -> list[float]:
    numbers: list[float] = []
    for raw in _NUMBER_RE.findall(text):
        try:
            numbers.append(float(raw.replace(",", ".")))
        except ValueError:
            continue
    return numbers


def _has_numeric_support(text: str, candidate: float, tolerance: float = 0.2) -> bool:
    for value in _extract_numeric_candidates(text):
        if abs(value - candidate) <= tolerance:
            return True
    return False


def build_multi_query_variants_v26(
    *,
    payload: ExperimentRequest,
    base_search_terms: list[str] | None,
    query_limit: int,
) -> list[str]:
    return build_multi_query_variants_v25(
        payload=payload,
        base_search_terms=base_search_terms,
        query_limit=query_limit,
    )


def normalize_numeric_value_for_payload_v26(
    value: float | int | None,
    payload: ExperimentRequest,
    *,
    source_text: str | None = None,
) -> float | None:
    return normalize_numeric_value_for_payload_v25(value, payload, source_text=source_text)


def select_consistent_diverse_chunks_v26(
    *,
    ranked_chunks,
    top_k: int,
    max_per_document: int,
    max_per_heading: int,
    payload: ExperimentRequest,
    query_variants: list[str],
    minimum_query_length: int,
    rerank_strategy: str,
) -> dict:
    base = select_consistent_diverse_chunks_v25(
        ranked_chunks=ranked_chunks,
        top_k=top_k,
        max_per_document=max_per_document,
        max_per_heading=max_per_heading,
        payload=payload,
        query_variants=query_variants,
        minimum_query_length=minimum_query_length,
        rerank_strategy=rerank_strategy,
    )

    clause_type_by_chunk_id: dict[str, str] = {}
    clause_type_distribution: dict[str, int] = {}
    requirement_like_chunk_ids: list[str] = []

    for item in base["selected_chunks"]:
        clause_type = _classify_clause_type_v26(heading=item.chunk.heading, text=item.chunk.text)
        clause_type_by_chunk_id[item.chunk.chunk_id] = clause_type
        clause_type_distribution[clause_type] = clause_type_distribution.get(clause_type, 0) + 1
        if clause_type in {"requirement", "scope"}:
            requirement_like_chunk_ids.append(item.chunk.chunk_id)

    return {
        **base,
        "clause_type_by_chunk_id": clause_type_by_chunk_id,
        "clause_type_distribution": clause_type_distribution,
        "requirement_like_chunk_ids": requirement_like_chunk_ids,
    }


def verify_extracted_value_with_clause_semantics_v26(
    *,
    extracted_value: float | None,
    payload: ExperimentRequest,
    selected_chunks: list[RankedChunk],
    clause_type_by_chunk_id: dict[str, str] | None,
) -> dict[str, object]:
    if extracted_value is None:
        return {
            "is_verified": False,
            "verifier_score": 0.0,
            "reason": "no_extracted_value",
            "semantic_anchor_count": 0,
            "supporting_chunk_ids": [],
            "requirement_support_count": 0,
        }

    anchors = _semantic_anchors_v26(payload)
    supporting_chunk_ids: list[str] = []
    requirement_support_count = 0
    semantic_match_count = 0

    for item in selected_chunks:
        text_norm = _normalize_for_match(item.chunk.text)
        clause_type = (clause_type_by_chunk_id or {}).get(item.chunk.chunk_id, "informational")
        anchor_hits = sum(1 for anchor in anchors if anchor in text_norm)
        has_value = _has_numeric_support(item.chunk.text, extracted_value)
        if anchor_hits > 0:
            semantic_match_count += 1
        if has_value and (anchor_hits > 0 or clause_type in {"requirement", "scope"}):
            supporting_chunk_ids.append(item.chunk.chunk_id)
            if clause_type in {"requirement", "scope"}:
                requirement_support_count += 1

    semantic_ratio = semantic_match_count / max(1, len(selected_chunks))
    requirement_ratio = requirement_support_count / max(1, len(selected_chunks))
    support_ratio = len(supporting_chunk_ids) / max(1, len(selected_chunks))

    verifier_score = round(semantic_ratio * 0.35 + requirement_ratio * 0.4 + support_ratio * 0.25, 4)
    is_verified = requirement_support_count > 0 and len(supporting_chunk_ids) > 0

    return {
        "is_verified": is_verified,
        "verifier_score": verifier_score,
        "reason": "verified" if is_verified else "insufficient_requirement_semantic_support",
        "semantic_anchor_count": len(anchors),
        "supporting_chunk_ids": supporting_chunk_ids,
        "requirement_support_count": requirement_support_count,
    }


def choose_adaptive_retry_plan_v26(
    *,
    retry_index: int,
    top_k: int,
    narrow_expansion_step: int,
    broad_expansion_multiplier: int,
) -> dict:
    return choose_adaptive_retry_plan_v25(
        retry_index=retry_index,
        top_k=top_k,
        narrow_expansion_step=narrow_expansion_step,
        broad_expansion_multiplier=broad_expansion_multiplier,
    )
