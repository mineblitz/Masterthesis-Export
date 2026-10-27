"""Retrieval enhancements for text-only v18 pipeline."""

from dataclasses import dataclass

from app.models import ExperimentRequest
from app.services.components.hybrid_context_ranker import RankedChunk
from app.services.components.keyword_context_extractor import resolve_search_terms
from app.services.components.prompt_builder_v5 import describe_value


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


def _deduplicate_terms(terms: list[str], *, limit: int) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for term in terms:
        cleaned = " ".join(term.strip().split())
        if not cleaned:
            continue
        normalized = _normalize_for_match(cleaned)
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(cleaned)
        if len(unique) >= limit:
            break
    return unique


def build_multi_query_variants(
    *,
    payload: ExperimentRequest,
    base_search_terms: list[str] | None,
    query_limit: int,
) -> list[str]:
    """Build retrieval query variants from value, conditions, and system metadata."""
    terms: list[str] = []
    try:
        terms.extend(resolve_search_terms(payload.value, base_search_terms))
    except ValueError:
        if base_search_terms:
            terms.extend(base_search_terms)

    terms.append(payload.value.replace("_", " "))
    terms.append(describe_value(payload.value))

    for condition in payload.conditions or []:
        if condition.value.strip():
            terms.append(condition.value.strip())
        if condition.type.strip() and condition.value.strip():
            terms.append(f"{condition.type.strip()} {condition.value.strip()}")

    if payload.system.strip():
        terms.append(payload.system.strip())
    if payload.system_name.strip():
        terms.append(payload.system_name.strip())

    limit = max(2, query_limit)
    return _deduplicate_terms(terms, limit=limit)


def score_chunk_evidence(
    *,
    ranked_chunk: RankedChunk,
    query_variants: list[str],
    payload: ExperimentRequest,
) -> float:
    """Estimate evidence strength using numeric, condition, and heading cues."""
    text = _normalize_for_match(ranked_chunk.chunk.text)
    heading = _normalize_for_match(ranked_chunk.chunk.heading or "")

    significant_queries = [query for query in query_variants if len(query.strip()) >= 4]
    query_hits = sum(1 for query in significant_queries if _normalize_for_match(query) in text)
    query_coverage = min(1.0, query_hits / max(1, min(5, len(significant_queries))))

    conditions = payload.conditions or []
    condition_hits = 0
    for condition in conditions:
        condition_terms = [condition.type.strip(), condition.value.strip()]
        for term in condition_terms:
            if term and _normalize_for_match(term) in text:
                condition_hits += 1
    condition_coverage = min(1.0, condition_hits / max(1, len(conditions) * 2))

    has_digits = any(char.isdigit() for char in ranked_chunk.chunk.text)
    has_unit = any(unit in text for unit in [" mm", " cm", " m ", "mindestens", "maximal", "min.", "max."])
    numeric_signal = 1.0 if has_digits and has_unit else 0.7 if has_digits else 0.0

    heading_signal = 0.0
    if heading:
        if any(_normalize_for_match(query) in heading for query in significant_queries):
            heading_signal = 1.0
        elif any(cue in heading for cue in ["techn", "daten", "abmess", "dimension"]):
            heading_signal = 0.6

    evidence = query_coverage * 0.4 + condition_coverage * 0.25 + numeric_signal * 0.25 + heading_signal * 0.1
    return round(min(1.0, max(0.0, evidence)), 4)


@dataclass
class DiversitySelectionResult:
    selected_chunks: list[RankedChunk]
    average_evidence_score: float
    chunk_evidence: dict[str, float]
    skipped_for_document_cap: int
    skipped_for_heading_cap: int
    skipped_for_redundancy: int


def _chunk_signature(chunk: RankedChunk) -> str:
    lines = [line.strip() for line in chunk.chunk.text.splitlines() if line.strip()]
    preview = " ".join(lines[:2])
    return _normalize_for_match(preview)[:220]


def select_diverse_chunks(
    *,
    ranked_chunks: list[RankedChunk],
    top_k: int,
    max_per_document: int,
    max_per_heading: int,
    payload: ExperimentRequest,
    query_variants: list[str],
) -> DiversitySelectionResult:
    if top_k <= 0 or not ranked_chunks:
        return DiversitySelectionResult(
            selected_chunks=[],
            average_evidence_score=0.0,
            chunk_evidence={},
            skipped_for_document_cap=0,
            skipped_for_heading_cap=0,
            skipped_for_redundancy=0,
        )

    effective_doc_cap = max(1, max_per_document)
    effective_heading_cap = max(1, max_per_heading)

    scored_candidates: list[tuple[RankedChunk, float]] = []
    evidence_by_chunk: dict[str, float] = {}
    for item in ranked_chunks:
        evidence = score_chunk_evidence(ranked_chunk=item, query_variants=query_variants, payload=payload)
        evidence_by_chunk[item.chunk.chunk_id] = evidence
        combined_score = item.score + evidence * 2.0
        scored_candidates.append((item, combined_score))

    scored_candidates.sort(
        key=lambda pair: (-pair[1], pair[0].chunk.document_path, pair[0].chunk.start_line)
    )

    selected: list[RankedChunk] = []
    seen_signatures: set[str] = set()
    per_document: dict[str, int] = {}
    per_heading: dict[tuple[str, str], int] = {}
    skipped_doc = 0
    skipped_heading = 0
    skipped_redundancy = 0

    for item, _ in scored_candidates:
        if len(selected) >= top_k:
            break

        doc_key = item.chunk.document_path
        heading_key = (doc_key, _normalize_for_match(item.chunk.heading or "<none>"))

        if per_document.get(doc_key, 0) >= effective_doc_cap:
            skipped_doc += 1
            continue
        if per_heading.get(heading_key, 0) >= effective_heading_cap:
            skipped_heading += 1
            continue

        signature = _chunk_signature(item)
        if signature in seen_signatures:
            skipped_redundancy += 1
            continue

        seen_signatures.add(signature)
        per_document[doc_key] = per_document.get(doc_key, 0) + 1
        per_heading[heading_key] = per_heading.get(heading_key, 0) + 1
        selected.append(item)

    if len(selected) < top_k:
        for item, _ in scored_candidates:
            if len(selected) >= top_k:
                break
            if item in selected:
                continue
            signature = _chunk_signature(item)
            if signature in seen_signatures:
                continue
            seen_signatures.add(signature)
            selected.append(item)

    average_evidence = 0.0
    if selected:
        average_evidence = round(
            sum(evidence_by_chunk[item.chunk.chunk_id] for item in selected) / len(selected),
            4,
        )

    return DiversitySelectionResult(
        selected_chunks=selected,
        average_evidence_score=average_evidence,
        chunk_evidence={item.chunk.chunk_id: evidence_by_chunk[item.chunk.chunk_id] for item in selected},
        skipped_for_document_cap=skipped_doc,
        skipped_for_heading_cap=skipped_heading,
        skipped_for_redundancy=skipped_redundancy,
    )