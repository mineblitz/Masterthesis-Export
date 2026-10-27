"""Retrieval enhancements for text-only v20 pipeline."""

from dataclasses import dataclass
import re

from app.models import ExperimentRequest
from app.services.components.hybrid_context_ranker import RankedChunk
from app.services.components.keyword_context_extractor import resolve_search_terms
from app.services.components.prompt_builder_v5 import describe_value


NUMERIC_PATTERN = re.compile(r"[-+]?\d+(?:[\.,]\d+)?")


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


def _compact_whitespace(text: str) -> str:
    return " ".join(text.strip().split())


def _add_term(target: list[str], seen: set[str], term: str) -> None:
    cleaned = _compact_whitespace(term)
    if not cleaned:
        return
    normalized = _normalize_for_match(cleaned)
    if normalized in seen:
        return
    seen.add(normalized)
    target.append(cleaned)


def _term_variants(term: str) -> list[str]:
    variants = [term]
    lowered = term.casefold()

    if "_" in term:
        variants.append(term.replace("_", " "))
    if "-" in term:
        variants.append(term.replace("-", " "))
    if "(" in term or ")" in term:
        variants.append(term.replace("(", " ").replace(")", " "))

    compact = (
        lowered.replace("-", " ")
        .replace("_", " ")
        .replace("/", " ")
        .replace(".", " ")
        .strip()
    )
    if compact and compact != lowered:
        variants.append(compact)

    ascii_fallback = (
        lowered.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )
    if ascii_fallback and ascii_fallback != lowered:
        variants.append(ascii_fallback)

    return variants


def build_multi_query_variants_v20(
    *,
    payload: ExperimentRequest,
    base_search_terms: list[str] | None,
    query_limit: int,
) -> list[str]:
    """Build normalized retrieval query variants for broader text-only recall."""
    terms: list[str] = []
    seen: set[str] = set()

    try:
        resolved = resolve_search_terms(payload.value, base_search_terms)
    except ValueError:
        resolved = base_search_terms or []

    for term in resolved:
        for variant in _term_variants(term):
            _add_term(terms, seen, variant)

    for candidate in [payload.value, payload.value.replace("_", " "), describe_value(payload.value)]:
        for variant in _term_variants(candidate):
            _add_term(terms, seen, variant)

    for condition in payload.conditions or []:
        if condition.type.strip():
            for variant in _term_variants(condition.type.strip()):
                _add_term(terms, seen, variant)
        if condition.value.strip():
            for variant in _term_variants(condition.value.strip()):
                _add_term(terms, seen, variant)
        if condition.type.strip() and condition.value.strip():
            composite = f"{condition.type.strip()} {condition.value.strip()}"
            for variant in _term_variants(composite):
                _add_term(terms, seen, variant)

    for system_term in [payload.system, payload.system_name]:
        for variant in _term_variants(system_term):
            _add_term(terms, seen, variant)

    return terms[: max(2, query_limit)]


def _extract_numeric_values(text: str) -> list[float]:
    values: list[float] = []
    for match in NUMERIC_PATTERN.findall(text):
        try:
            values.append(float(match.replace(",", ".")))
        except ValueError:
            continue
    return values


def score_chunk_evidence_v20(
    *,
    ranked_chunk: RankedChunk,
    query_variants: list[str],
    payload: ExperimentRequest,
    minimum_query_length: int,
) -> float:
    text = _normalize_for_match(ranked_chunk.chunk.text)
    heading = _normalize_for_match(ranked_chunk.chunk.heading or "")

    significant_queries = [
        query for query in query_variants if len(_compact_whitespace(query)) >= max(2, minimum_query_length)
    ]
    query_hits = sum(1 for query in significant_queries if _normalize_for_match(query) in text)
    query_coverage = min(1.0, query_hits / max(1, min(7, len(significant_queries))))

    conditions = payload.conditions or []
    condition_hits = 0
    for condition in conditions:
        condition_terms = [condition.type.strip(), condition.value.strip()]
        for term in condition_terms:
            if term and _normalize_for_match(term) in text:
                condition_hits += 1
    condition_coverage = min(1.0, condition_hits / max(1, len(conditions) * 2))

    numeric_values = _extract_numeric_values(ranked_chunk.chunk.text)
    has_unit = any(unit in text for unit in [" mm", " cm", " m ", "mindestens", "maximal", "min.", "max."])
    numeric_signal = 1.0 if numeric_values and has_unit else 0.7 if numeric_values else 0.0

    heading_signal = 0.0
    if heading:
        if any(_normalize_for_match(query) in heading for query in significant_queries):
            heading_signal = 1.0
        elif any(cue in heading for cue in ["techn", "daten", "abmess", "dimension", "kennwert"]):
            heading_signal = 0.65

    evidence = query_coverage * 0.38 + condition_coverage * 0.24 + numeric_signal * 0.28 + heading_signal * 0.10
    return round(min(1.0, max(0.0, evidence)), 4)


@dataclass
class SelectionConsistencyResult:
    selected_chunks: list[RankedChunk]
    average_evidence_score: float
    chunk_evidence: dict[str, float]
    evidence_consistency_score: float
    conflicting_numeric_candidates: list[float]
    skipped_for_document_cap: int
    skipped_for_heading_cap: int
    skipped_for_redundancy: int


def _chunk_signature(chunk: RankedChunk) -> str:
    lines = [line.strip() for line in chunk.chunk.text.splitlines() if line.strip()]
    preview = " ".join(lines[:2])
    return _normalize_for_match(preview)[:220]


def _rounded_bucket(value: float) -> float:
    return round(value, 1)


def select_consistent_diverse_chunks(
    *,
    ranked_chunks: list[RankedChunk],
    top_k: int,
    max_per_document: int,
    max_per_heading: int,
    payload: ExperimentRequest,
    query_variants: list[str],
    minimum_query_length: int,
) -> SelectionConsistencyResult:
    if top_k <= 0 or not ranked_chunks:
        return SelectionConsistencyResult(
            selected_chunks=[],
            average_evidence_score=0.0,
            chunk_evidence={},
            evidence_consistency_score=0.0,
            conflicting_numeric_candidates=[],
            skipped_for_document_cap=0,
            skipped_for_heading_cap=0,
            skipped_for_redundancy=0,
        )

    effective_doc_cap = max(1, max_per_document)
    effective_heading_cap = max(1, max_per_heading)

    scored_candidates: list[tuple[RankedChunk, float]] = []
    evidence_by_chunk: dict[str, float] = {}
    for item in ranked_chunks:
        evidence = score_chunk_evidence_v20(
            ranked_chunk=item,
            query_variants=query_variants,
            payload=payload,
            minimum_query_length=minimum_query_length,
        )
        evidence_by_chunk[item.chunk.chunk_id] = evidence
        combined_score = item.score + evidence * 2.2
        scored_candidates.append((item, combined_score))

    scored_candidates.sort(key=lambda pair: (-pair[1], pair[0].chunk.document_path, pair[0].chunk.start_line))

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

    numeric_candidates: list[float] = []
    bucket_counts: dict[float, int] = {}
    for item in selected:
        for numeric_value in _extract_numeric_values(item.chunk.text):
            bucket = _rounded_bucket(numeric_value)
            bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
            numeric_candidates.append(numeric_value)

    if not numeric_candidates:
        consistency = 1.0
        conflicting: list[float] = []
    elif len(bucket_counts) == 1:
        consistency = 1.0
        conflicting = []
    else:
        dominant = max(bucket_counts.values())
        consistency = round(dominant / len(numeric_candidates), 4)
        dominant_bucket = max(bucket_counts.items(), key=lambda item: item[1])[0]
        conflicting = [value for value in numeric_candidates if _rounded_bucket(value) != dominant_bucket]

    return SelectionConsistencyResult(
        selected_chunks=selected,
        average_evidence_score=average_evidence,
        chunk_evidence={item.chunk.chunk_id: evidence_by_chunk[item.chunk.chunk_id] for item in selected},
        evidence_consistency_score=consistency,
        conflicting_numeric_candidates=conflicting,
        skipped_for_document_cap=skipped_doc,
        skipped_for_heading_cap=skipped_heading,
        skipped_for_redundancy=skipped_redundancy,
    )


@dataclass
class AdaptiveRetryWindow:
    fallback_stage: str
    expansion_step: int


def choose_adaptive_retry_window(
    *,
    retry_index: int,
    top_k: int,
    narrow_expansion_step: int,
    broad_expansion_multiplier: int,
) -> AdaptiveRetryWindow:
    """Alternate between narrow and broad context expansion windows."""
    if retry_index % 2 == 1:
        return AdaptiveRetryWindow(fallback_stage="narrow_retry", expansion_step=max(1, narrow_expansion_step))

    return AdaptiveRetryWindow(
        fallback_stage="broad_retry",
        expansion_step=max(1, top_k * max(1, broad_expansion_multiplier)),
    )
