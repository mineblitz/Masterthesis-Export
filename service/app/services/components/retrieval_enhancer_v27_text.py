"""Retrieval enhancement aliases for text-only v27.

Re-exports all v26 retrieval helpers under v27 names so that the v27 pipeline
is self-contained and future v27-specific overrides can be added here without
touching v26.
"""

from app.services.components.retrieval_enhancer_v26_text import (
    build_multi_query_variants_v26 as build_multi_query_variants_v27,
    choose_adaptive_retry_plan_v26 as choose_adaptive_retry_plan_v27,
    normalize_numeric_value_for_payload_v26 as normalize_numeric_value_for_payload_v27,
    select_consistent_diverse_chunks_v26 as select_consistent_diverse_chunks_v27,
    verify_extracted_value_with_clause_semantics_v26 as verify_extracted_value_with_clause_semantics_v27,
)

__all__ = [
    "build_multi_query_variants_v27",
    "choose_adaptive_retry_plan_v27",
    "normalize_numeric_value_for_payload_v27",
    "select_consistent_diverse_chunks_v27",
    "verify_extracted_value_with_clause_semantics_v27",
]
