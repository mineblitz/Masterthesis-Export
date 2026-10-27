"""Cross-encoder embedding reranker using sentence-transformers.

New component for v27+ pipelines. Replaces the token-Jaccard semantic overlap
approximation in retrieval_enhancer_v21_text.py with a real cross-encoder relevance
model. Existing retrieval enhancers are unchanged.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.services.components.hybrid_context_ranker import RankedChunk

if TYPE_CHECKING:
    pass

logger = logging.getLogger("app.components.embedding_reranker")

# Default multilingual cross-encoder model.
# Uses a small multilingual model that understands German out of the box.
_DEFAULT_CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
_MULTILINGUAL_CROSS_ENCODER_MODEL = "cross-encoder/msmarco-MiniLM-L6-en-de-v1"

_cross_encoder_cache: dict[str, object] = {}


def _get_cross_encoder(model_name: str) -> object:
    """Lazy-load and cache the cross-encoder model.

    Raises:
        ImportError: If sentence-transformers is not installed.
    """
    if model_name in _cross_encoder_cache:
        return _cross_encoder_cache[model_name]

    try:
        from sentence_transformers import CrossEncoder  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "sentence-transformers is required for embedding_reranker. "
            "Install it with: pip install sentence-transformers"
        ) from exc

    logger.info("Loading cross-encoder model: %s", model_name)
    model = CrossEncoder(model_name)
    _cross_encoder_cache[model_name] = model
    return model


def rerank(
    ranked_chunks: list[RankedChunk],
    query: str,
    *,
    top_n: int = 5,
    model_name: str = _DEFAULT_CROSS_ENCODER_MODEL,
) -> list[RankedChunk]:
    """Rerank BM25 candidates using a cross-encoder model.

    The cross-encoder scores each (query, chunk_text) pair with a learned
    relevance model, which is semantically stronger than BM25 or token-Jaccard.

    Args:
        ranked_chunks: Candidates from BM25 or heuristic ranker.
        query: The retrieval query string (typically the value name + conditions).
        top_n: Number of top results to return after reranking.
        model_name: HuggingFace model identifier for the cross-encoder.

    Returns:
        Top-n reranked chunks, sorted by cross-encoder score descending.

    Raises:
        ImportError: If sentence-transformers is not installed.
    """
    if not ranked_chunks:
        return []

    model = _get_cross_encoder(model_name)

    pairs = [(query, item.chunk.text) for item in ranked_chunks]

    try:
        from sentence_transformers import CrossEncoder  # type: ignore[import-untyped]
        assert isinstance(model, CrossEncoder)
        scores: list[float] = model.predict(pairs).tolist()
    except Exception as exc:
        logger.warning("Cross-encoder prediction failed (%s); falling back to BM25 order", exc)
        return ranked_chunks[:top_n]

    reranked = sorted(
        zip(ranked_chunks, scores),
        key=lambda pair: -pair[1],
    )

    result: list[RankedChunk] = []
    for item, score in reranked[:top_n]:
        # Update score to reflect cross-encoder score while preserving other fields
        result.append(
            RankedChunk(
                chunk=item.chunk,
                score=float(score),
                keyword_hits=item.keyword_hits,
                condition_hits=item.condition_hits,
                has_numeric_signal=item.has_numeric_signal,
            )
        )
    return result
