"""Multimodal evidence selector v23 backed by BM25 + rapidfuzz.

New component for multimodal v23 pipeline. Replaces the filename/position heuristics
in multimodal_evidence_selector_v19.py with BM25 scoring for text blocks and
rapidfuzz fuzzy matching for figure/table caption anchoring.
Existing multimodal_evidence_selector_v19.py is unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.components.layout_document_parser import LayoutBlock

try:
    from rapidfuzz import fuzz  # type: ignore[import-untyped]
    _RAPIDFUZZ_AVAILABLE = True
except ImportError:
    _RAPIDFUZZ_AVAILABLE = False


@dataclass
class EvidenceItem:
    """A selected evidence item (text block or figure) with score metadata."""
    block: LayoutBlock
    score: float
    score_source: str  # "bm25" | "fuzzy" | "layout_type"


@dataclass
class EvidenceSelectionResult:
    """Result from select_evidence_v23."""
    text_blocks: list[EvidenceItem]
    figure_blocks: list[EvidenceItem]
    table_blocks: list[EvidenceItem]
    all_items: list[EvidenceItem]


def _build_query_string(query_variants: list[str]) -> str:
    return " ".join(query_variants)


def _score_text_blocks_bm25(
    blocks: list[LayoutBlock],
    query_variants: list[str],
) -> list[tuple[LayoutBlock, float]]:
    """Score text/heading/list blocks using BM25Okapi."""
    try:
        from app.services.components.bm25_context_ranker import _tokenize
        from rank_bm25 import BM25Okapi  # type: ignore[import-untyped]
    except ImportError:
        # Fallback: simple substring overlap
        query_lower = _build_query_string(query_variants).lower()
        results: list[tuple[LayoutBlock, float]] = []
        for block in blocks:
            hits = sum(q.lower() in block.text.lower() for q in query_variants)
            results.append((block, float(hits)))
        return results

    tokenized_corpus = [_tokenize(b.text + " " + (b.heading or "")) for b in blocks]
    if not any(tokenized_corpus):
        return [(b, 0.0) for b in blocks]

    bm25 = BM25Okapi(tokenized_corpus)
    query_tokens = _tokenize(_build_query_string(query_variants))
    if not query_tokens:
        return [(b, 0.0) for b in blocks]

    scores = bm25.get_scores(query_tokens)
    return list(zip(blocks, [float(s) for s in scores]))


def _score_figure_table_blocks_fuzzy(
    blocks: list[LayoutBlock],
    query_variants: list[str],
) -> list[tuple[LayoutBlock, float]]:
    """Score figure and table blocks using rapidfuzz token-sort ratio on captions."""
    query_str = _build_query_string(query_variants)
    results: list[tuple[LayoutBlock, float]] = []

    for block in blocks:
        anchor = (block.text or "") + " " + (block.heading or "")
        if not anchor.strip():
            # Blocks with no text/caption get a small layout-type bonus
            score = 0.1
        elif _RAPIDFUZZ_AVAILABLE:
            score = fuzz.token_sort_ratio(query_str, anchor) / 100.0
        else:
            # Fallback: simple character overlap fraction
            query_set = set(query_str.lower().split())
            anchor_set = set(anchor.lower().split())
            overlap = len(query_set & anchor_set)
            score = overlap / max(1, len(query_set)) if query_set else 0.0

        results.append((block, score))

    return results


def select_evidence_v23(
    blocks: list[LayoutBlock],
    query_variants: list[str],
    *,
    top_text: int = 5,
    top_figures: int = 3,
    max_per_page: int = 2,
) -> EvidenceSelectionResult:
    """Select diverse text + figure/table evidence from layout blocks.

    Text blocks are scored with BM25 (library-backed ranking).
    Figure and table blocks are scored with rapidfuzz fuzzy caption matching.
    A per-page diversity cap prevents one page from dominating.

    Args:
        blocks: All layout blocks from layout_document_parser.parse_document.
        query_variants: Query strings used for scoring (value name + conditions).
        top_text: Maximum text/heading/list blocks to select.
        top_figures: Maximum figure+table blocks to select.
        max_per_page: Maximum blocks from the same page (applied per type group).

    Returns:
        EvidenceSelectionResult with text_blocks, figure_blocks, table_blocks.
    """
    text_type_blocks = [b for b in blocks if b.block_type in {"text", "heading", "list"}]
    figure_blocks_raw = [b for b in blocks if b.block_type == "figure"]
    table_blocks_raw = [b for b in blocks if b.block_type == "table"]

    # Score text blocks
    scored_text = _score_text_blocks_bm25(text_type_blocks, query_variants)
    scored_text.sort(key=lambda pair: -pair[1])

    # Score figure + table blocks together
    scored_figures = _score_figure_table_blocks_fuzzy(figure_blocks_raw, query_variants)
    scored_tables = _score_figure_table_blocks_fuzzy(table_blocks_raw, query_variants)
    scored_figures.sort(key=lambda pair: -pair[1])
    scored_tables.sort(key=lambda pair: -pair[1])

    def _apply_page_cap(
        scored: list[tuple[LayoutBlock, float]],
        limit: int,
    ) -> list[EvidenceItem]:
        selected: list[EvidenceItem] = []
        page_count: dict[int, int] = {}
        for block, score in scored:
            if len(selected) >= limit:
                break
            page_count.setdefault(block.page_number, 0)
            if page_count[block.page_number] >= max_per_page:
                continue
            page_count[block.page_number] += 1
            selected.append(EvidenceItem(block=block, score=score, score_source="bm25"))
        return selected

    selected_text = _apply_page_cap(scored_text, top_text)
    for item in selected_text:
        item.score_source = "bm25"

    selected_figures = _apply_page_cap(scored_figures, top_figures)
    for item in selected_figures:
        item.score_source = "fuzzy"

    selected_tables = _apply_page_cap(scored_tables, top_figures)
    for item in selected_tables:
        item.score_source = "fuzzy"

    all_items = sorted(
        selected_text + selected_figures + selected_tables,
        key=lambda item: -item.score,
    )

    return EvidenceSelectionResult(
        text_blocks=selected_text,
        figure_blocks=selected_figures,
        table_blocks=selected_tables,
        all_items=all_items,
    )
