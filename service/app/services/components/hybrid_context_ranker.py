"""Hybrid heuristic ranking for structured document chunks."""

from dataclasses import dataclass

from app.models import ExperimentRequest
from app.services.components.dataset_input_adapter import resolve_dataset_search_terms
from app.services.components.keyword_context_extractor import resolve_search_terms
from app.services.components.structured_document_chunker import DocumentChunk


@dataclass
class RankedChunk:
    chunk: DocumentChunk
    score: float
    keyword_hits: int
    condition_hits: int
    has_numeric_signal: bool


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


def _condition_terms(payload: ExperimentRequest) -> list[str]:
    if not payload.conditions:
        return []

    terms: list[str] = []
    for condition in payload.conditions:
        if condition.type.strip():
            terms.append(condition.type.strip())
        if condition.value.strip():
            terms.append(condition.value.strip())
    return terms


def rank_document_chunks(
    *,
    chunks: list[DocumentChunk],
    payload: ExperimentRequest,
    search_terms: list[str] | None = None,
) -> tuple[list[RankedChunk], list[str]]:
    if not search_terms or not any(term.strip() for term in search_terms):
        search_terms = resolve_dataset_search_terms(payload)
    resolved_terms = resolve_search_terms(payload.value, search_terms)
    normalized_terms = [_normalize_for_match(term) for term in resolved_terms]
    normalized_condition_terms = [_normalize_for_match(term) for term in _condition_terms(payload)]

    ranked: list[RankedChunk] = []
    for chunk in chunks:
        haystack = _normalize_for_match(chunk.text)
        heading = _normalize_for_match(chunk.heading or "")
        keyword_hits = sum(1 for term in normalized_terms if term in haystack)
        condition_hits = sum(1 for term in normalized_condition_terms if term in haystack)
        heading_bonus = sum(1 for term in normalized_terms if term in heading)
        has_numeric_signal = any(char.isdigit() for char in chunk.text)

        score = float(keyword_hits * 2 + condition_hits * 1.5 + heading_bonus * 1.5)
        if has_numeric_signal:
            score += 0.5

        if score <= 0:
            continue

        ranked.append(
            RankedChunk(
                chunk=chunk,
                score=score,
                keyword_hits=keyword_hits,
                condition_hits=condition_hits,
                has_numeric_signal=has_numeric_signal,
            )
        )

    ranked.sort(key=lambda item: (-item.score, item.chunk.document_path, item.chunk.start_line))
    return ranked, resolved_terms