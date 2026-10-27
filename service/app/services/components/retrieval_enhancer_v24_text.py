"""Retrieval enhancements for text-only v24 with adaptive consistency gating for multi-valued evidence."""

from dataclasses import dataclass
import re

from app.models import ExperimentRequest
from app.services.components.retrieval_enhancer_v23_text import (
    build_multi_query_variants_v23,
    choose_adaptive_retry_plan_v23,
    normalize_numeric_value_for_payload_v23,
    select_consistent_diverse_chunks_v23,
)
from app.services.components.retrieval_enhancer_v22_text import (
    _extract_normalized_numeric_values,
)


@dataclass
class AdaptiveConsistencyResult:
    """Extended consistency result that includes modal value and multi-valued detection."""
    evidence_consistency_score: float
    modal_numeric_value: float | None
    modal_candidate_frequency: float
    is_multi_valued_variable: bool
    should_accept_modal: bool
    conflicting_numeric_candidates: list[float]


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


def _is_multi_valued_variable(payload: ExperimentRequest) -> bool:
    """Detect variables that intentionally have multiple valid values in spec documents."""
    value_lower = _normalize_for_match(payload.value)
    
    multi_valued_patterns = (
        "fire_resistance",
        "feuerwiderstand",
        "brandklasse",
        "thickness",
        "dicke",
        "min_thickness",
        "max_thickness",
        "range",
        "bereich",
        "fire_rating",
        "rating",
    )
    
    for pattern in multi_valued_patterns:
        if pattern in value_lower:
            return True
    
    has_conditional = any((condition.type or "").strip() for condition in payload.conditions or [])
    return has_conditional


def _compute_adaptive_consistency(
    *,
    numeric_candidates: list[float],
    payload: ExperimentRequest,
) -> AdaptiveConsistencyResult:
    """
    Compute consistency with modal value extraction and multi-valued acceptance logic.
    
    For multi-valued variables, relaxes the consistency gate to accept the modal (most frequent) value
    even if strict consistency check would fail.
    """
    
    is_multi_valued = _is_multi_valued_variable(payload)
    
    if not numeric_candidates:
        return AdaptiveConsistencyResult(
            evidence_consistency_score=1.0,
            modal_numeric_value=None,
            modal_candidate_frequency=0.0,
            is_multi_valued_variable=is_multi_valued,
            should_accept_modal=False,
            conflicting_numeric_candidates=[],
        )
    
    bucket_counts: dict[float, int] = {}
    for value in numeric_candidates:
        bucket = round(value, 1)
        bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
    
    if len(bucket_counts) == 1:
        single_bucket = list(bucket_counts.keys())[0]
        return AdaptiveConsistencyResult(
            evidence_consistency_score=1.0,
            modal_numeric_value=single_bucket,
            modal_candidate_frequency=1.0,
            is_multi_valued_variable=is_multi_valued,
            should_accept_modal=True,
            conflicting_numeric_candidates=[],
        )
    
    dominant_bucket = max(bucket_counts.items(), key=lambda item: item[1])[0]
    dominant_count = bucket_counts[dominant_bucket]
    total_count = len(numeric_candidates)
    consistency = round(dominant_count / total_count, 4)
    modal_frequency = round(dominant_count / total_count, 4)
    
    conflicting = [value for value in numeric_candidates if round(value, 1) != dominant_bucket]
    
    should_accept = False
    if consistency >= 0.58:
        should_accept = True
    elif is_multi_valued and modal_frequency >= 0.2:
        should_accept = True
    
    return AdaptiveConsistencyResult(
        evidence_consistency_score=consistency,
        modal_numeric_value=dominant_bucket,
        modal_candidate_frequency=modal_frequency,
        is_multi_valued_variable=is_multi_valued,
        should_accept_modal=should_accept,
        conflicting_numeric_candidates=conflicting,
    )


def build_multi_query_variants_v24(
    *,
    payload: ExperimentRequest,
    base_search_terms: list[str] | None,
    query_limit: int,
) -> list[str]:
    """Delegates to v23 for query variant building."""
    return build_multi_query_variants_v23(
        payload=payload,
        base_search_terms=base_search_terms,
        query_limit=query_limit,
    )


def normalize_numeric_value_for_payload_v24(
    value: float | int | None,
    payload: ExperimentRequest,
    *,
    source_text: str | None = None,
) -> float | None:
    """Delegates to v23 for numeric normalization."""
    return normalize_numeric_value_for_payload_v23(value, payload, source_text=source_text)


def select_consistent_diverse_chunks_v24(
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
    """
    Select chunks with adaptive consistency gating for multi-valued evidence.
    
    Returns extended result including modal value information for pipeline-level gating decisions.
    """
    base = select_consistent_diverse_chunks_v23(
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
    for item in base.selected_chunks:
        for numeric_value in _extract_normalized_numeric_values(item.chunk.text, payload):
            numeric_candidates.append(numeric_value)
    
    adaptive_result = _compute_adaptive_consistency(
        numeric_candidates=numeric_candidates,
        payload=payload,
    )
    
    return {
        "selected_chunks": base.selected_chunks,
        "average_evidence_score": base.average_evidence_score,
        "chunk_evidence": base.chunk_evidence,
        "evidence_consistency_score": adaptive_result.evidence_consistency_score,
        "modal_numeric_value": adaptive_result.modal_numeric_value,
        "modal_candidate_frequency": adaptive_result.modal_candidate_frequency,
        "is_multi_valued_variable": adaptive_result.is_multi_valued_variable,
        "should_accept_modal": adaptive_result.should_accept_modal,
        "conflicting_numeric_candidates": adaptive_result.conflicting_numeric_candidates,
        "contradiction_hit_count": base.contradiction_hit_count,
        "skipped_for_document_cap": base.skipped_for_document_cap,
        "skipped_for_heading_cap": base.skipped_for_heading_cap,
        "skipped_for_redundancy": base.skipped_for_redundancy,
    }


def choose_adaptive_retry_plan_v24(
    *,
    retry_index: int,
    top_k: int,
    narrow_expansion_step: int,
    broad_expansion_multiplier: int,
) -> dict:
    """Delegates to v23 for adaptive retry planning."""
    plan = choose_adaptive_retry_plan_v23(
        retry_index=retry_index,
        top_k=top_k,
        narrow_expansion_step=narrow_expansion_step,
        broad_expansion_multiplier=broad_expansion_multiplier,
    )
    return {
        "fallback_stage": plan.fallback_stage,
        "expansion_step": plan.expansion_step,
        "rerank_strategy": plan.rerank_strategy,
    }
