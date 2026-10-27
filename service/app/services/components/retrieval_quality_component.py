"""Retrieval quality heuristics for context selection."""

from dataclasses import dataclass

from app.services.components.hybrid_context_ranker import RankedChunk


@dataclass
class RetrievalQualityResult:
    quality_score: float
    keyword_coverage: float
    selected_chunk_count: int
    should_retry: bool
    reason: str


def assess_retrieval_quality(
    *,
    selected_chunks: list[RankedChunk],
    available_ranked_chunks: list[RankedChunk],
    search_terms: list[str],
    threshold: float,
) -> RetrievalQualityResult:
    if not selected_chunks:
        return RetrievalQualityResult(
            quality_score=0.0,
            keyword_coverage=0.0,
            selected_chunk_count=0,
            should_retry=True,
            reason="no_selected_chunks",
        )

    covered_terms = 0
    selected_text = "\n".join(item.chunk.text for item in selected_chunks).casefold()
    for term in search_terms:
        if term.casefold() in selected_text:
            covered_terms += 1

    keyword_coverage = covered_terms / len(search_terms) if search_terms else 1.0
    average_score = sum(item.score for item in selected_chunks) / len(selected_chunks)
    normalized_score = min(1.0, average_score / 6.0)
    quality_score = round(keyword_coverage * 0.65 + normalized_score * 0.35, 4)

    should_retry = quality_score < threshold and len(selected_chunks) < len(available_ranked_chunks)
    reason = "quality_below_threshold" if should_retry else "quality_sufficient"

    return RetrievalQualityResult(
        quality_score=quality_score,
        keyword_coverage=round(keyword_coverage, 4),
        selected_chunk_count=len(selected_chunks),
        should_retry=should_retry,
        reason=reason,
    )