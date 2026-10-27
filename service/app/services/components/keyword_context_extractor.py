"""Keyword context extraction for narrowing document text before LLM processing."""

from dataclasses import dataclass


DEFAULT_GERMAN_SEARCH_TERMS: dict[str, list[str]] = {
    "min_thickness": ["Mindestdicke", "Mindestbauteildicke", "Bauteildicke", "Dicke"],
    "max_thickness": ["Maximaldicke", "Hoechstdicke", "Bauteildicke", "Dicke"],
    "thickness": ["Bauteildicke", "Dicke"],
    "min_opening_width": ["Mindestoeffnungsbreite", "Mindest-Offnungsbreite", "Oeffnungsbreite", "Breite"],
    "max_opening_width": ["Maximaloeffnungsbreite", "Hoechstoeffnungsbreite", "Oeffnungsbreite", "Breite"],
    "opening_width": ["Oeffnungsbreite", "Breite"],
    "min_opening_height": ["Mindestoeffnungshoehe", "Mindest-Offnungshoehe", "Oeffnungshoehe", "Hoehe"],
    "max_opening_height": ["Maximaloeffnungshoehe", "Hoechstoeffnungshoehe", "Oeffnungshoehe", "Hoehe"],
    "opening_height": ["Oeffnungshoehe", "Hoehe"],
    "min_diameter": ["Mindestdurchmesser", "Oeffnungsdurchmesser", "Durchmesser"],
    "max_diameter": ["Maximaldurchmesser", "Hoechstdurchmesser", "Oeffnungsdurchmesser", "Durchmesser"],
    "diameter": ["Oeffnungsdurchmesser", "Durchmesser"],
    "fire_resistance_class": ["Feuerwiderstandsklasse", "Feuerwiderstand", "Klassifizierung"],
}


@dataclass
class KeywordChunkExtractionResult:
    filtered_documents_text: str
    document_count: int
    chunk_count: int
    hit_count: int
    search_terms: list[str]
    window_boundaries: list[dict[str, int | str]]


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


def resolve_search_terms(value: str, custom_terms: list[str] | None = None) -> list[str]:
    if custom_terms:
        resolved = [term.strip() for term in custom_terms if term.strip()]
        if resolved:
            return resolved

    mapped = DEFAULT_GERMAN_SEARCH_TERMS.get(value, [])
    if mapped:
        return mapped

    raise ValueError(
        "Kein deutscher Suchbegriff fuer value '"
        f"{value}"
        "' hinterlegt. Bitte search_terms im Request mitgeben (z. B. ['Bauteildicke'])."
    )


def _split_document_sections(docs_text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    current_doc: str | None = None
    current_lines: list[str] = []

    for line in docs_text.splitlines():
        if line.startswith("## Document: "):
            if current_doc is not None:
                sections.append((current_doc, "\n".join(current_lines).strip("\n")))
            current_doc = line.removeprefix("## Document: ").strip()
            current_lines = []
            continue
        current_lines.append(line)

    if current_doc is not None:
        sections.append((current_doc, "\n".join(current_lines).strip("\n")))

    return sections


def _find_hit_line_indexes(lines: list[str], search_terms: list[str]) -> list[int]:
    if not lines:
        return []

    normalized_terms = [_normalize_for_match(term) for term in search_terms]
    hit_indexes: list[int] = []
    for idx, line in enumerate(lines):
        normalized_line = _normalize_for_match(line)
        if any(term in normalized_line for term in normalized_terms):
            hit_indexes.append(idx)
    return hit_indexes


def _build_merged_windows(
    hit_indexes: list[int],
    max_index: int,
    lines_before: int,
    lines_after: int,
) -> list[tuple[int, int]]:
    if not hit_indexes:
        return []

    windows = [
        (max(0, hit - lines_before), min(max_index, hit + lines_after)) for hit in hit_indexes
    ]
    windows.sort(key=lambda item: item[0])

    merged: list[tuple[int, int]] = []
    current_start, current_end = windows[0]
    for start, end in windows[1:]:
        if start <= current_end + 1:
            current_end = max(current_end, end)
            continue
        merged.append((current_start, current_end))
        current_start, current_end = start, end
    merged.append((current_start, current_end))
    return merged


def extract_keyword_context_chunks(
    docs_text: str,
    *,
    value: str,
    search_terms: list[str] | None,
    lines_before: int,
    lines_after: int,
) -> KeywordChunkExtractionResult:
    sections = _split_document_sections(docs_text)
    resolved_terms = resolve_search_terms(value, search_terms)

    if lines_before < 0 or lines_after < 0:
        raise ValueError("lines_before und lines_after muessen >= 0 sein")

    rendered_documents: list[str] = []
    window_boundaries: list[dict[str, int | str]] = []
    total_chunks = 0
    total_hits = 0

    for document_path, document_text in sections:
        lines = document_text.splitlines()
        raw_lines = document_text.splitlines(keepends=True)
        line_offsets: list[int] = []
        char_offset = 0
        for raw_line in raw_lines:
            line_offsets.append(char_offset)
            char_offset += len(raw_line)

        hit_indexes = _find_hit_line_indexes(lines, resolved_terms)
        total_hits += len(hit_indexes)
        windows = _build_merged_windows(
            hit_indexes,
            max_index=max(0, len(lines) - 1),
            lines_before=lines_before,
            lines_after=lines_after,
        )
        if not windows:
            continue

        chunk_blocks: list[str] = []
        for chunk_idx, (start, end) in enumerate(windows, start=1):
            total_chunks += 1
            header = f"### Chunk {chunk_idx} (lines {start + 1}-{end + 1})"
            chunk_lines = lines[start : end + 1]
            chunk_blocks.append(f"{header}\n" + "\n".join(chunk_lines))
            window_boundaries.append(
                {
                    "document": document_path,
                    "start_line": start + 1,
                    "end_line": end + 1,
                    "start_char": line_offsets[start],
                    "end_char": line_offsets[end] + len(lines[end]),
                }
            )

        rendered_documents.append(
            "\n".join(
                [
                    f"## Document: {document_path}",
                    f"Suchbegriffe: {', '.join(resolved_terms)}",
                    *chunk_blocks,
                ]
            )
        )

    filtered_text = "\n\n".join(rendered_documents)
    return KeywordChunkExtractionResult(
        filtered_documents_text=filtered_text,
        document_count=len(rendered_documents),
        chunk_count=total_chunks,
        hit_count=total_hits,
        search_terms=resolved_terms,
        window_boundaries=window_boundaries,
    )