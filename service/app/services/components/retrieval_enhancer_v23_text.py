"""Retrieval enhancements for text-only v23 with marker-noise-aware chunk suppression."""

import re

from app.models import ExperimentRequest
from app.services.components.hybrid_context_ranker import RankedChunk
from app.services.components.retrieval_enhancer_v22_text import (
    AdaptiveRetryPlan,
    SelectionConsistencyResult,
    build_multi_query_variants_v22,
    choose_adaptive_retry_plan_v22,
    normalize_numeric_value_for_payload_v22,
    select_consistent_diverse_chunks_v22,
)
from app.services.components.structured_document_chunker import DocumentChunk

_MARKER_NOISE_LINE_PATTERNS = (
    re.compile(r"!\[[^\]]*\]\([^\)]*\)", re.IGNORECASE),
    re.compile(r"<span\b[^>]*>", re.IGNORECASE),
    re.compile(r"</span>", re.IGNORECASE),
    re.compile(r"\bclass\s*=\s*[\"'][^\"']+[\"']", re.IGNORECASE),
    re.compile(r"\bdata-page\b", re.IGNORECASE),
    re.compile(r"\b(page|seite)\s*\d+\s*(/|von)\s*\d+\b", re.IGNORECASE),
)

_MARKER_NOISE_TOKEN_PATTERN = re.compile(
    r"!\[[^\]]*\]\([^\)]*\)|<span\b|</span>|\bclass\s*=|\.(png|jpg|jpeg|webp)\b",
    re.IGNORECASE,
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


def _is_noise_line(line: str) -> bool:
    candidate = line.strip()
    if not candidate:
        return False
    return any(pattern.search(candidate) for pattern in _MARKER_NOISE_LINE_PATTERNS)


def _condition_anchors(payload: ExperimentRequest) -> list[str]:
    anchors: list[str] = []
    for condition in payload.conditions or []:
        if condition.type.strip():
            anchors.append(condition.type.strip())
        if condition.value.strip():
            anchors.append(condition.value.strip())
    return anchors


def _compute_anchor_hits(text: str, query_variants: list[str], payload: ExperimentRequest) -> int:
    normalized = _normalize_for_match(text)
    hits = 0
    for anchor in [*query_variants[:10], *_condition_anchors(payload)[:10]]:
        if not anchor:
            continue
        if _normalize_for_match(anchor) in normalized:
            hits += 1
    return hits


def _strip_marker_noise_lines(text: str) -> tuple[str, int, int]:
    lines = text.splitlines()
    kept_lines: list[str] = []
    removed = 0
    for line in lines:
        if _is_noise_line(line):
            removed += 1
            continue
        kept_lines.append(line)

    cleaned = "\n".join(kept_lines).strip()
    if not cleaned:
        return text, removed, len(lines)
    return cleaned, removed, len(lines)


def _noise_adjusted_candidates(
    *,
    ranked_chunks: list[RankedChunk],
    query_variants: list[str],
    payload: ExperimentRequest,
) -> list[RankedChunk]:
    adjusted: list[RankedChunk] = []

    for item in ranked_chunks:
        cleaned_text, removed_lines, total_lines = _strip_marker_noise_lines(item.chunk.text)
        line_noise_ratio = removed_lines / max(1, total_lines)
        marker_noise_hits = len(_MARKER_NOISE_TOKEN_PATTERN.findall(item.chunk.text))
        anchor_hits = _compute_anchor_hits(cleaned_text, query_variants, payload)

        suppress_chunk = line_noise_ratio >= 0.65 and anchor_hits == 0
        if suppress_chunk:
            continue

        score_penalty = min(0.68, line_noise_ratio * 0.75 + min(0.2, marker_noise_hits * 0.03))
        adjusted_score = max(0.0, item.score * (1.0 - score_penalty))

        adjusted_chunk = DocumentChunk(
            document_path=item.chunk.document_path,
            chunk_id=item.chunk.chunk_id,
            heading=item.chunk.heading,
            text=cleaned_text,
            start_line=item.chunk.start_line,
            end_line=item.chunk.end_line,
        )
        adjusted.append(
            RankedChunk(
                chunk=adjusted_chunk,
                score=adjusted_score,
                keyword_hits=item.keyword_hits,
                condition_hits=item.condition_hits,
                has_numeric_signal=item.has_numeric_signal,
            )
        )

    adjusted.sort(key=lambda ranked: (-ranked.score, ranked.chunk.document_path, ranked.chunk.start_line))
    return adjusted


def build_multi_query_variants_v23(
    *,
    payload: ExperimentRequest,
    base_search_terms: list[str] | None,
    query_limit: int,
) -> list[str]:
    return build_multi_query_variants_v22(
        payload=payload,
        base_search_terms=base_search_terms,
        query_limit=query_limit,
    )


def normalize_numeric_value_for_payload_v23(
    value: float | int | None,
    payload: ExperimentRequest,
    *,
    source_text: str | None = None,
) -> float | None:
    return normalize_numeric_value_for_payload_v22(value, payload, source_text=source_text)


def select_consistent_diverse_chunks_v23(
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
    noise_adjusted = _noise_adjusted_candidates(
        ranked_chunks=ranked_chunks,
        query_variants=query_variants,
        payload=payload,
    )
    if not noise_adjusted:
        noise_adjusted = ranked_chunks

    return select_consistent_diverse_chunks_v22(
        ranked_chunks=noise_adjusted,
        top_k=top_k,
        max_per_document=max_per_document,
        max_per_heading=max_per_heading,
        payload=payload,
        query_variants=query_variants,
        minimum_query_length=minimum_query_length,
        rerank_strategy=rerank_strategy,
    )


def choose_adaptive_retry_plan_v23(
    *,
    retry_index: int,
    top_k: int,
    narrow_expansion_step: int,
    broad_expansion_multiplier: int,
) -> AdaptiveRetryPlan:
    return choose_adaptive_retry_plan_v22(
        retry_index=retry_index,
        top_k=top_k,
        narrow_expansion_step=narrow_expansion_step,
        broad_expansion_multiplier=broad_expansion_multiplier,
    )
