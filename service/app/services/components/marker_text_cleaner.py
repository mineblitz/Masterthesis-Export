"""Clean Marker markdown for retrieval while preserving lightweight page cues."""

import re

_IMAGE_EMBED_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
_PAGE_SPAN_RE = re.compile(r"<span[^>]*id=[\"']page-(\d+)[\"'][^>]*>", re.IGNORECASE)
_CLOSING_SPAN_RE = re.compile(r"</span>", re.IGNORECASE)


def clean_marker_markdown_text(
    markdown_text: str,
    *,
    remove_image_lines: bool = True,
    remove_page_span_tags: bool = True,
    preserve_page_markers: bool = True,
    page_marker_prefix: str = "[[MARKER_PAGE_",
    page_marker_suffix: str = "]]",
) -> str:
    cleaned_lines: list[str] = []

    for line in markdown_text.splitlines():
        span_match = _PAGE_SPAN_RE.search(line)
        if span_match and preserve_page_markers:
            cleaned_lines.append(f"{page_marker_prefix}{span_match.group(1)}{page_marker_suffix}")

        if remove_page_span_tags:
            line = _PAGE_SPAN_RE.sub("", line)
            line = _CLOSING_SPAN_RE.sub("", line)

        contains_image_embed = _IMAGE_EMBED_RE.search(line) is not None
        if contains_image_embed and remove_image_lines:
            continue

        if not remove_image_lines and contains_image_embed:
            line = _IMAGE_EMBED_RE.sub("", line)

        if line.strip() or (cleaned_lines and cleaned_lines[-1].strip()):
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()
