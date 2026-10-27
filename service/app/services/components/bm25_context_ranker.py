"""BM25-based context ranker using rank-bm25 library.

New component for v27+ pipelines. Replaces heuristic substring scoring in
hybrid_context_ranker.py with proper TF-IDF-weighted BM25 scoring.
Existing hybrid_context_ranker.py is unchanged.
"""

import re

from app.models import ExperimentRequest
from app.services.components.hybrid_context_ranker import RankedChunk
from app.services.components.keyword_context_extractor import resolve_search_terms
from app.services.components.structured_document_chunker import DocumentChunk

try:
    from rank_bm25 import BM25Okapi  # type: ignore[import-untyped]
    _BM25_AVAILABLE = True
except ImportError:
    _BM25_AVAILABLE = False


_TOKEN_RE = re.compile(r"[a-zA-Z0-9\u00c0-\u024f]+")

_UMLAUT_MAP: dict[str, str] = {
    "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
    "Ä": "Ae", "Ö": "Oe", "Ü": "Ue",
}


def _normalize_text(text: str) -> str:
    for char, replacement in _UMLAUT_MAP.items():
        text = text.replace(char, replacement)
    return text.lower()


def _tokenize(text: str) -> list[str]:
    normalized = _normalize_text(text)
    return [t for t in _TOKEN_RE.findall(normalized) if len(t) >= 2]


def _condition_terms(payload: ExperimentRequest) -> list[str]:
    terms: list[str] = []
    for condition in payload.conditions or []:
        if condition.type.strip():
            terms.append(condition.type.strip())
        if condition.value.strip():
            terms.append(condition.value.strip())
    return terms


def rank_bm25(
    *,
    chunks: list[DocumentChunk],
    payload: ExperimentRequest,
    search_terms: list[str] | None = None,
    max_results: int | None = None,
) -> tuple[list[RankedChunk], list[str]]:
    """Rank document chunks with BM25Okapi scoring.

    Args:
        chunks: Chunks to rank.
        payload: Experiment request (provides value and conditions as query terms).
        search_terms: Optional pre-resolved search terms; resolved from payload.value if None.
        max_results: If set, return at most this many ranked chunks.

    Returns:
        Tuple of (ranked_chunks sorted descending by score, resolved_search_terms).

    Raises:
        ImportError: If rank-bm25 is not installed.
    """
    if not _BM25_AVAILABLE:
        raise ImportError(
            "rank-bm25 is required for bm25_context_ranker. "
            "Install it with: pip install rank-bm25"
        )
    if not chunks:
        return [], search_terms or []

    resolved_terms = resolve_search_terms(payload.value, search_terms)
    extra_terms = _condition_terms(payload)
    all_query_terms = resolved_terms + extra_terms

    tokenized_corpus = [_tokenize(chunk.text + " " + (chunk.heading or "")) for chunk in chunks]
    bm25 = BM25Okapi(tokenized_corpus)

    # Build combined query by tokenizing all query terms together
    query_tokens = _tokenize(" ".join(all_query_terms))
    if not query_tokens:
        # No meaningful query tokens; return empty ranking
        return [], resolved_terms

    scores = bm25.get_scores(query_tokens)

    # Count heading hits separately for heading_bonus
    normalized_query_tokens = set(query_tokens)

    ranked: list[RankedChunk] = []
    for index, (chunk, score) in enumerate(zip(chunks, scores)):
        if score <= 0.0:
            continue
        heading_tokens = set(_tokenize(chunk.heading or ""))
        heading_hit_count = len(normalized_query_tokens & heading_tokens)
        # Give a small additive bonus for heading matches (same spirit as the heuristic ranker)
        adjusted_score = float(score) + heading_hit_count * 0.5
        has_numeric = any(char.isdigit() for char in chunk.text)

        ranked.append(
            RankedChunk(
                chunk=chunk,
                score=adjusted_score,
                keyword_hits=int(score > 0),
                condition_hits=0,
                has_numeric_signal=has_numeric,
            )
        )

    ranked.sort(key=lambda item: (-item.score, item.chunk.document_path, item.chunk.start_line))

    if max_results is not None:
        ranked = ranked[:max_results]

    return ranked, resolved_terms
