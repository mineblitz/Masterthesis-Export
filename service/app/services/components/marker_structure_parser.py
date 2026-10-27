"""Parse Marker markdown structure for image refs and page-span metadata."""

from dataclasses import dataclass
from pathlib import Path
import re

_IMAGE_EMBED_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
_PAGE_SPAN_RE = re.compile(r"<span[^>]*id=[\"']page-(\d+)[\"'][^>]*>", re.IGNORECASE)
_PAGE_PICTURE_RE = re.compile(r"_page_(\d+)_Picture_(\d+)", re.IGNORECASE)


@dataclass(frozen=True)
class MarkerImageReference:
    image_ref: str
    image_name: str
    page_number: int | None
    region_index: int | None
    line_number: int


@dataclass(frozen=True)
class MarkerPageSpan:
    page_number: int
    line_number: int


@dataclass(frozen=True)
class MarkerStructureParseResult:
    image_references: list[MarkerImageReference]
    page_spans: list[MarkerPageSpan]


def _extract_page_region(image_ref: str) -> tuple[int | None, int | None]:
    match = _PAGE_PICTURE_RE.search(image_ref)
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def parse_marker_structure(markdown_text: str) -> MarkerStructureParseResult:
    image_references: list[MarkerImageReference] = []
    page_spans: list[MarkerPageSpan] = []

    for line_number, line in enumerate(markdown_text.splitlines(), start=1):
        for match in _PAGE_SPAN_RE.finditer(line):
            page_spans.append(MarkerPageSpan(page_number=int(match.group(1)), line_number=line_number))

        for match in _IMAGE_EMBED_RE.finditer(line):
            image_ref = match.group(1).strip()
            image_name = Path(image_ref).name
            page_number, region_index = _extract_page_region(image_name)
            image_references.append(
                MarkerImageReference(
                    image_ref=image_ref,
                    image_name=image_name,
                    page_number=page_number,
                    region_index=region_index,
                    line_number=line_number,
                )
            )

    return MarkerStructureParseResult(image_references=image_references, page_spans=page_spans)
