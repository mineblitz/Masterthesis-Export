"""Filter likely logo images from multimodal candidates using Marker metadata."""

from dataclasses import dataclass

from app.services.components.marker_structure_parser import MarkerImageReference
from app.services.components.multimodal_evidence_selector_v19 import ImageCandidate


@dataclass(frozen=True)
class LogoFilterResult:
    filtered_candidates: list[ImageCandidate]
    filtered_out_candidates: list[ImageCandidate]


def filter_probable_logo_images(
    *,
    candidates: list[ImageCandidate],
    marker_image_references: list[MarkerImageReference],
    logo_region_index_max: int = 1,
    repeat_page_threshold: int = 2,
) -> LogoFilterResult:
    if not candidates:
        return LogoFilterResult(filtered_candidates=[], filtered_out_candidates=[])

    max_region = max(0, logo_region_index_max)
    min_repeat = max(1, repeat_page_threshold)

    pages_by_region: dict[int, set[int]] = {}
    for item in marker_image_references:
        if item.page_number is None or item.region_index is None:
            continue
        pages_by_region.setdefault(item.region_index, set()).add(item.page_number)

    repeated_logo_regions = {
        region_index
        for region_index, pages in pages_by_region.items()
        if region_index <= max_region and len(pages) >= min_repeat
    }

    filtered_candidates: list[ImageCandidate] = []
    filtered_out: list[ImageCandidate] = []

    for candidate in candidates:
        is_low_region = candidate.region_index <= max_region
        should_filter = is_low_region and (
            candidate.region_index in repeated_logo_regions or candidate.region_index <= 1
        )
        if should_filter:
            filtered_out.append(candidate)
            continue
        filtered_candidates.append(candidate)

    return LogoFilterResult(filtered_candidates=filtered_candidates, filtered_out_candidates=filtered_out)
