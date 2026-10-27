"""Retrieval enhancements for text-only v25 with compliance-routing prefilter."""

from app.models import ExperimentRequest
from app.services.components.hybrid_context_ranker import RankedChunk
from app.services.components.retrieval_enhancer_v24_text import (
    build_multi_query_variants_v24,
    choose_adaptive_retry_plan_v24,
    normalize_numeric_value_for_payload_v24,
    select_consistent_diverse_chunks_v24,
)


_ROUTING_POSITIVE_HEADING_TERMS = (
    "anforderung",
    "anwendungsbereich",
    "klassifizierung",
    "feuerwiderstand",
    "feuerwiderstandsklasse",
    "belegung",
    "abschottung",
    "einbau",
    "durchfuhrung",
    "durchfuehrung",
    "wand",
    "decke",
)

_ROUTING_POSITIVE_TEXT_TERMS = (
    "mindestens",
    "mindest",
    "hochstens",
    "maximal",
    "zulassig",
    "zulassige",
    "muss",
    "durfen",
    "darf",
    "feuerwiderstand",
    "klassifizierung",
    "abschottung",
    "rohdichte",
    "dicke",
    "abstand",
    "offnung",
    "oeffnung",
    "belegung",
)

_ROUTING_NEGATIVE_HEADING_TERMS = (
    "allgemeines",
    "hinweise",
    "verweise",
    "grundlagen",
    "antragsteller",
    "hersteller",
    "uberwachung",
    "ueberwachung",
    "bescheid",
    "kosten",
    "gebuhren",
    "gebuehren",
    "unterschrift",
    "inhalt",
)

_ROUTING_NEGATIVE_TEXT_TERMS = (
    "deutsches institut",
    "antragsteller",
    "hersteller",
    "verwaltungsverfahren",
    "gebuhren",
    "gebuehren",
    "allgemeine bestimmungen",
    "rechtsbehelf",
    "zustandige stelle",
    "zustaendige stelle",
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


def _count_hits(text: str, terms: tuple[str, ...]) -> int:
    return sum(1 for term in terms if term in text)


def _route_anchors(payload: ExperimentRequest, query_variants: list[str]) -> list[str]:
    anchors: list[str] = []

    anchors.extend(query_variants[:12])
    anchors.extend(part for part in payload.value.replace("_", " ").split() if part)

    for condition in payload.conditions or []:
        if condition.type.strip():
            anchors.append(condition.type.strip())
        if condition.value.strip():
            anchors.append(condition.value.strip())

    normalized: list[str] = []
    seen: set[str] = set()
    for anchor in anchors:
        normalized_anchor = _normalize_for_match(anchor.strip())
        if len(normalized_anchor) < 4:
            continue
        if normalized_anchor in seen:
            continue
        seen.add(normalized_anchor)
        normalized.append(normalized_anchor)
    return normalized


def _route_prefilter_candidates_v25(
    *,
    ranked_chunks: list[RankedChunk],
    payload: ExperimentRequest,
    query_variants: list[str],
) -> tuple[list[RankedChunk], dict[str, object]]:
    anchors = _route_anchors(payload, query_variants)
    reranked: list[tuple[RankedChunk, float]] = []
    boosted_chunk_ids: list[str] = []
    penalized_chunk_ids: list[str] = []

    for item in ranked_chunks:
        heading = _normalize_for_match(item.chunk.heading or "")
        body = _normalize_for_match(item.chunk.text)

        positive_heading_hits = _count_hits(heading, _ROUTING_POSITIVE_HEADING_TERMS)
        positive_text_hits = _count_hits(body, _ROUTING_POSITIVE_TEXT_TERMS)
        negative_heading_hits = _count_hits(heading, _ROUTING_NEGATIVE_HEADING_TERMS)
        negative_text_hits = _count_hits(body, _ROUTING_NEGATIVE_TEXT_TERMS)
        heading_anchor_hits = sum(1 for anchor in anchors if anchor in heading)
        body_anchor_hits = sum(1 for anchor in anchors if anchor in body)

        route_score = (
            positive_heading_hits * 1.8
            + positive_text_hits * 0.7
            + heading_anchor_hits * 1.2
            + body_anchor_hits * 0.35
            - negative_heading_hits * 1.7
            - negative_text_hits * 0.8
        )
        if item.has_numeric_signal:
            route_score += 0.15

        if route_score >= 0:
            multiplier = min(2.1, 1.0 + route_score * 0.16)
            boosted_chunk_ids.append(item.chunk.chunk_id)
        else:
            multiplier = max(0.35, 1.0 + route_score * 0.18)
            penalized_chunk_ids.append(item.chunk.chunk_id)

        if negative_heading_hits and positive_heading_hits == 0 and body_anchor_hits == 0:
            multiplier = min(multiplier, 0.55)

        reranked.append(
            (
                RankedChunk(
                    chunk=item.chunk,
                    score=round(item.score * multiplier, 4),
                    keyword_hits=item.keyword_hits,
                    condition_hits=item.condition_hits,
                    has_numeric_signal=item.has_numeric_signal,
                ),
                route_score,
            )
        )

    reranked.sort(key=lambda entry: (-entry[0].score, -entry[1], entry[0].chunk.document_path, entry[0].chunk.start_line))
    adjusted_chunks = [entry[0] for entry in reranked]
    metadata = {
        "route_focus": "requirement_first_v25",
        "route_anchor_count": len(anchors),
        "route_boosted_chunk_ids": boosted_chunk_ids[:8],
        "route_penalized_chunk_ids": penalized_chunk_ids[:8],
    }
    return adjusted_chunks, metadata


def build_multi_query_variants_v25(
    *,
    payload: ExperimentRequest,
    base_search_terms: list[str] | None,
    query_limit: int,
) -> list[str]:
    return build_multi_query_variants_v24(
        payload=payload,
        base_search_terms=base_search_terms,
        query_limit=query_limit,
    )


def normalize_numeric_value_for_payload_v25(
    value: float | int | None,
    payload: ExperimentRequest,
    *,
    source_text: str | None = None,
) -> float | None:
    return normalize_numeric_value_for_payload_v24(value, payload, source_text=source_text)


def select_consistent_diverse_chunks_v25(
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
    routed_chunks, routing_metadata = _route_prefilter_candidates_v25(
        ranked_chunks=ranked_chunks,
        payload=payload,
        query_variants=query_variants,
    )
    base = select_consistent_diverse_chunks_v24(
        ranked_chunks=routed_chunks,
        top_k=top_k,
        max_per_document=max_per_document,
        max_per_heading=max_per_heading,
        payload=payload,
        query_variants=query_variants,
        minimum_query_length=minimum_query_length,
        rerank_strategy=rerank_strategy,
    )
    return {
        **base,
        **routing_metadata,
    }


def choose_adaptive_retry_plan_v25(
    *,
    retry_index: int,
    top_k: int,
    narrow_expansion_step: int,
    broad_expansion_multiplier: int,
) -> dict:
    return choose_adaptive_retry_plan_v24(
        retry_index=retry_index,
        top_k=top_k,
        narrow_expansion_step=narrow_expansion_step,
        broad_expansion_multiplier=broad_expansion_multiplier,
    )