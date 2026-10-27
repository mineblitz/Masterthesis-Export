"""PDF text extractor component with lightweight text cleanup for pipeline v3."""
from pathlib import Path
import math
import re

from pypdf import PdfReader
from pypdf.errors import DependencyError


_PAGE_INDICATOR_RE = re.compile(r"^(seite|page)\s+\d+(\s*/\s*\d+)?$", re.IGNORECASE)
_PURE_NUMBER_RE = re.compile(r"^\d{1,4}$")
_NOISE_RE = re.compile(
    r"^(www\.|http|stand\s*:|version\s*:|copyright|all rights reserved)",
    re.IGNORECASE,
)


def _is_restricted_h2_h3_p_pdf(relative_path: str) -> bool:
    normalized_path = relative_path.replace("\\", "/").lower()
    path_parts = [part for part in normalized_path.split("/") if part]
    filename = Path(normalized_path).name
    return ("h2" in path_parts or "h3" in path_parts) and filename.startswith("p_")


def _normalize_line(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def _is_noise_line(line: str) -> bool:
    if not line:
        return True
    if _PAGE_INDICATOR_RE.match(line):
        return True
    if _PURE_NUMBER_RE.match(line):
        return True
    if _NOISE_RE.match(line):
        return True
    if len(line) <= 1:
        return True
    return False


def _collect_common_header_footer_lines(pages: list[list[str]]) -> set[str]:
    if len(pages) < 2:
        return set()

    frequency: dict[str, int] = {}
    for page_lines in pages:
        candidates = page_lines[:3] + page_lines[-3:]
        unique_candidates = {line for line in candidates if line}
        for line in unique_candidates:
            frequency[line] = frequency.get(line, 0) + 1

    min_occurrences = max(2, math.ceil(len(pages) * 0.6))
    return {line for line, count in frequency.items() if count >= min_occurrences}


def _merge_hyphenated_lines(lines: list[str]) -> list[str]:
    merged: list[str] = []
    for line in lines:
        if not merged:
            merged.append(line)
            continue
        previous = merged[-1]
        if previous.endswith("-") and line and line[0].islower():
            merged[-1] = previous[:-1] + line
            continue
        merged.append(line)
    return merged


def _clean_page_lines(page_text: str) -> list[str]:
    raw_lines = page_text.splitlines()
    return [_normalize_line(line) for line in raw_lines if _normalize_line(line)]


def _clean_document_text(raw_pages: list[str]) -> str:
    pages = [_clean_page_lines(page_text) for page_text in raw_pages]
    common_header_footer = _collect_common_header_footer_lines(pages)

    cleaned_pages: list[str] = []
    for page_lines in pages:
        filtered_lines = [
            line
            for line in page_lines
            if line not in common_header_footer and not _is_noise_line(line)
        ]
        merged_lines = _merge_hyphenated_lines(filtered_lines)
        if merged_lines:
            cleaned_pages.append("\n".join(merged_lines))

    return "\n\n".join(cleaned_pages)


def extract_text_from_pdfs_v2(
    paths: list[str],
    base_dir: Path,
) -> tuple[str, list[str]]:
    """
    Extract text from PDFs and remove recurring headers, footers, and noise.

    This intentionally keeps a plain text style for prompting and avoids heavy layout tooling.
    """
    chunks: list[str] = []
    resolved_paths: list[str] = []

    for relative_path in paths:
        if _is_restricted_h2_h3_p_pdf(relative_path):
            chunks.append(f"## Document: {relative_path}\n")
            resolved_paths.append(relative_path)
            continue

        pdf_path = (base_dir / relative_path).resolve()
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        try:
            reader = PdfReader(str(pdf_path))
            raw_pages = [(page.extract_text() or "") for page in reader.pages]
            cleaned_text = _clean_document_text(raw_pages)
        except DependencyError as exc:
            raise RuntimeError(
                f"Cannot extract PDF text from '{relative_path}': the file is encrypted and requires the 'cryptography' package."
            ) from exc
        except Exception as exc:
            raise RuntimeError(f"PDF extraction failed for '{relative_path}': {exc}") from exc

        chunks.append(f"## Document: {relative_path}\n{cleaned_text}")
        resolved_paths.append(relative_path)

    return "\n\n".join(chunks), resolved_paths
