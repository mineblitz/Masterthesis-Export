"""Heuristic multimodal evidence selection for v18 pipeline."""

from dataclasses import dataclass
from pathlib import Path
import re

from app.services.components.hybrid_context_ranker import RankedChunk

_ALLOWED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


@dataclass
class ImageCandidate:
    image_path: str
    document_path: str
    page_number: int
    region_index: int
    layout_score: float


@dataclass
class ImageSelectionResult:
    selected_images: list[ImageCandidate]
    average_evidence_score: float
    evidence_by_image: dict[str, float]
    skipped_for_document_cap: int
    skipped_for_page_cap: int


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


def _extract_page_region(stem: str) -> tuple[int, int] | None:
    match = re.search(r"_page_(\d+)_Picture_(\d+)", stem)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def _layout_score(*, page_number: int, region_index: int) -> float:
    # Prefer earlier pages and non-logo early regions as a lightweight layout prior.
    page_decay = 1.0 / (1.0 + max(0, page_number - 1) * 0.18)
    region_bonus = 1.0 / (1.0 + abs(region_index - 2) * 0.35)
    return round(min(1.0, page_decay * 0.55 + region_bonus * 0.45), 4)


def collect_multimodal_image_candidates(
    paths: list[str],
    base_dir: Path,
    *,
    max_images_total: int,
) -> list[ImageCandidate]:
    candidates: list[ImageCandidate] = []

    for document_path in paths:
        source_path = (base_dir / document_path).resolve()
        files_dir = source_path.parent
        if not files_dir.exists() or not files_dir.is_dir():
            continue

        for image_path in sorted(files_dir.iterdir()):
            if not image_path.is_file() or image_path.suffix.lower() not in _ALLOWED_IMAGE_SUFFIXES:
                continue
            if not image_path.name.startswith("_page_"):
                continue

            page_region = _extract_page_region(image_path.stem)
            if page_region is None:
                continue
            page_number, region_index = page_region

            # The first image on a page is usually logo/branding and rarely carries values.
            if region_index == 1:
                continue

            candidate = ImageCandidate(
                image_path=image_path.as_posix(),
                document_path=source_path.as_posix(),
                page_number=page_number,
                region_index=region_index,
                layout_score=_layout_score(page_number=page_number, region_index=region_index),
            )
            candidates.append(candidate)
            if len(candidates) >= max_images_total:
                return candidates

    return candidates


def infer_layout_priority_pages(
    *,
    selected_text_chunks: list[RankedChunk],
    query_variants: list[str],
    max_pages: int,
) -> list[int]:
    page_scores: dict[int, float] = {}
    normalized_queries = [_normalize_for_match(item) for item in query_variants if item.strip()]

    for ranked in selected_text_chunks:
        text = ranked.chunk.text
        normalized_text = _normalize_for_match(text)
        query_hits = sum(1 for query in normalized_queries if len(query) >= 4 and query in normalized_text)
        mentions = re.findall(r"(?:seite|page)\s*(\d{1,3})", normalized_text)
        if not mentions:
            continue

        signal = 1.0 + min(3.0, query_hits * 0.25)
        for page_match in mentions:
            page_number = int(page_match)
            page_scores[page_number] = page_scores.get(page_number, 0.0) + signal

    if not page_scores:
        return []

    ordered = sorted(page_scores.items(), key=lambda item: (-item[1], item[0]))
    return [page for page, _ in ordered[: max(1, max_pages)]]


def _score_image_evidence(
    *,
    candidate: ImageCandidate,
    prioritized_pages: list[int],
) -> float:
    prioritized_page_scores = {
        page: max(0.0, 1.0 - index * 0.2)
        for index, page in enumerate(prioritized_pages)
    }
    page_bonus = prioritized_page_scores.get(candidate.page_number, 0.0)
    evidence = candidate.layout_score * 0.75 + page_bonus * 0.25
    return round(min(1.0, max(0.0, evidence)), 4)


def select_diverse_image_evidence(
    *,
    candidates: list[ImageCandidate],
    top_k: int,
    max_per_document: int,
    max_regions_per_page: int,
    prioritized_pages: list[int],
) -> ImageSelectionResult:
    if top_k <= 0 or not candidates:
        return ImageSelectionResult(
            selected_images=[],
            average_evidence_score=0.0,
            evidence_by_image={},
            skipped_for_document_cap=0,
            skipped_for_page_cap=0,
        )

    effective_document_cap = max(1, max_per_document)
    effective_page_cap = max(1, max_regions_per_page)

    evidence_map = {
        item.image_path: _score_image_evidence(candidate=item, prioritized_pages=prioritized_pages)
        for item in candidates
    }
    sorted_candidates = sorted(
        candidates,
        key=lambda item: (
            -evidence_map[item.image_path],
            item.document_path,
            item.page_number,
            item.region_index,
        ),
    )

    selected: list[ImageCandidate] = []
    per_document: dict[str, int] = {}
    per_page: dict[tuple[str, int], int] = {}
    skipped_doc = 0
    skipped_page = 0

    for item in sorted_candidates:
        if len(selected) >= top_k:
            break

        doc_key = item.document_path
        page_key = (item.document_path, item.page_number)
        if per_document.get(doc_key, 0) >= effective_document_cap:
            skipped_doc += 1
            continue
        if per_page.get(page_key, 0) >= effective_page_cap:
            skipped_page += 1
            continue

        selected.append(item)
        per_document[doc_key] = per_document.get(doc_key, 0) + 1
        per_page[page_key] = per_page.get(page_key, 0) + 1

    if len(selected) < top_k:
        for item in sorted_candidates:
            if len(selected) >= top_k:
                break
            if item in selected:
                continue
            selected.append(item)

    average_evidence = 0.0
    if selected:
        average_evidence = round(
            sum(evidence_map[item.image_path] for item in selected) / len(selected),
            4,
        )

    return ImageSelectionResult(
        selected_images=selected,
        average_evidence_score=average_evidence,
        evidence_by_image={item.image_path: evidence_map[item.image_path] for item in selected},
        skipped_for_document_cap=skipped_doc,
        skipped_for_page_cap=skipped_page,
    )
