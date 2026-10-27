"""Context expansion helpers for corrective retries."""

from app.services.components.hybrid_context_ranker import RankedChunk


def select_ranked_chunks(ranked_chunks: list[RankedChunk], *, top_k: int) -> list[RankedChunk]:
    if top_k <= 0:
        return []
    return ranked_chunks[:top_k]


def expand_ranked_chunks(
    ranked_chunks: list[RankedChunk],
    *,
    current_count: int,
    expansion_step: int,
) -> list[RankedChunk]:
    next_count = min(len(ranked_chunks), current_count + expansion_step)
    return ranked_chunks[:next_count]