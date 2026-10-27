"""Layout-aware document parser backed by docling.

New component for multimodal v23 pipeline. Replaces the custom Marker structure
regex parser (marker_structure_parser.py) and filename-heuristic image selection
with docling's full layout model, which classifies page elements into typed blocks
(Text, Table, Figure, SectionHeading) with bounding boxes.
Existing marker_structure_parser.py and multimodal_evidence_selector_v19.py
are unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LayoutBlock:
    """A typed block extracted from a document page."""
    block_type: str          # "text" | "table" | "figure" | "heading" | "list" | "other"
    page_number: int
    text: str                # Extracted text content; empty for pure figure blocks
    image_path: str | None   # Absolute path to a saved figure image (figures only)
    confidence: float        # Layout model confidence [0, 1]
    heading: str | None      # Nearest section heading (for text/table blocks)
    document_path: str       # Source document path (POSIX, workspace-relative)
    bbox: list[float] = field(default_factory=list)  # [x0, y0, x1, y1] in points


def _parse_with_docling(pdf_path: Path, document_path: str) -> list[LayoutBlock]:
    """Parse a PDF into typed layout blocks using docling."""
    try:
        from docling.document_converter import DocumentConverter  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "docling is required for layout_document_parser. "
            "Install it with: pip install docling"
        ) from exc

    converter = DocumentConverter()
    result = converter.convert(str(pdf_path))
    doc = result.document

    blocks: list[LayoutBlock] = []
    current_heading: str | None = None

    for element, _level in doc.iterate_items():
        label = type(element).__name__.lower()  # e.g. "sectionheadingitem", "textitem", etc.

        # Normalise element type label
        if "heading" in label or "title" in label:
            block_type = "heading"
        elif "table" in label:
            block_type = "table"
        elif "figure" in label or "picture" in label:
            block_type = "figure"
        elif "list" in label:
            block_type = "list"
        else:
            block_type = "text"

        text = ""
        try:
            text = element.text or ""
        except AttributeError:
            pass

        if block_type == "heading" and text:
            current_heading = text.strip()

        # Page number
        page_no = 1
        try:
            prov = element.prov[0] if element.prov else None
            if prov:
                page_no = int(prov.page_no)
        except (AttributeError, IndexError, TypeError, ValueError):
            pass

        blocks.append(
            LayoutBlock(
                block_type=block_type,
                page_number=page_no,
                text=text.strip(),
                image_path=None,
                confidence=1.0,
                heading=current_heading,
                document_path=document_path,
            )
        )

    return blocks


def _parse_from_marker_markdown(marker_path: Path, document_path: str) -> list[LayoutBlock]:
    """Fallback: parse a Marker markdown file into layout blocks using headings/text heuristics."""
    text = marker_path.read_text(encoding="utf-8")
    blocks: list[LayoutBlock] = []
    current_heading: str | None = None
    buffer: list[str] = []
    page_no = 1

    def _flush(btype: str) -> None:
        content = "\n".join(buffer).strip()
        if content:
            blocks.append(
                LayoutBlock(
                    block_type=btype,
                    page_number=page_no,
                    text=content,
                    image_path=None,
                    confidence=0.7,
                    heading=current_heading,
                    document_path=document_path,
                )
            )
        buffer.clear()

    for line in text.splitlines():
        stripped = line.strip()
        # Page boundary markers inserted by Marker
        if stripped.startswith("<!-- Page") or stripped.startswith("<page"):
            try:
                page_no = int("".join(c for c in stripped if c.isdigit()) or page_no)
            except ValueError:
                pass
            continue
        if stripped.startswith("#"):
            _flush("text")
            heading_text = stripped.lstrip("#").strip()
            current_heading = heading_text
            blocks.append(
                LayoutBlock(
                    block_type="heading",
                    page_number=page_no,
                    text=heading_text,
                    image_path=None,
                    confidence=0.8,
                    heading=None,
                    document_path=document_path,
                )
            )
            continue
        if stripped.startswith("!["):
            _flush("text")
            # Extract image path from Markdown image syntax
            import re
            m = re.search(r"\!\[.*?\]\((.+?)\)", stripped)
            img_path = m.group(1) if m else None
            blocks.append(
                LayoutBlock(
                    block_type="figure",
                    page_number=page_no,
                    text="",
                    image_path=img_path,
                    confidence=0.7,
                    heading=current_heading,
                    document_path=document_path,
                )
            )
            continue
        if not stripped:
            _flush("text")
            continue
        buffer.append(line)

    _flush("text")
    return blocks


def parse_document(
    document_path: str,
    base_dir: Path,
    *,
    prefer_pdf: bool = True,
) -> list[LayoutBlock]:
    """Parse a document into typed layout blocks.

    Tries docling on the PDF first if prefer_pdf is True. Falls back to the
    Marker markdown file (_marker.md) if PDF parsing fails or if the file
    is already a Markdown file.

    Args:
        document_path: Workspace-relative path to the PDF or markdown file.
        base_dir: Base directory of the workspace (usually Path(".")).
        prefer_pdf: If True, attempt docling PDF parsing before markdown fallback.

    Returns:
        List of LayoutBlock objects ordered as they appear in the document.

    Raises:
        FileNotFoundError: If neither the PDF nor the marker markdown is found.
    """
    resolved = (base_dir / document_path).resolve()

    if document_path.lower().endswith(".md") or not prefer_pdf:
        marker_path = resolved
        if not marker_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {marker_path}")
        return _parse_from_marker_markdown(marker_path, document_path)

    # Try docling on the PDF
    pdf_path = resolved
    if pdf_path.exists() and pdf_path.suffix.lower() == ".pdf":
        try:
            return _parse_with_docling(pdf_path, document_path)
        except ImportError:
            raise  # propagate ImportError so the caller knows docling is missing
        except Exception:
            pass  # fall through to Marker markdown fallback

    # Marker markdown fallback
    marker_path = pdf_path.with_name(f"{pdf_path.stem}_marker.md")
    if not marker_path.exists():
        marker_path = pdf_path.with_suffix(".md")
    if not marker_path.exists():
        raise FileNotFoundError(
            f"Could not parse document: no PDF or _marker.md found for {document_path}"
        )

    rel_marker = marker_path.relative_to(base_dir.resolve()).as_posix()
    return _parse_from_marker_markdown(marker_path, rel_marker)
