"""Structure-aware chunking for markdown and plain document text."""

from dataclasses import dataclass


@dataclass
class DocumentChunk:
    document_path: str
    chunk_id: str
    heading: str | None
    text: str
    start_line: int
    end_line: int


def _split_document_sections(docs_text: str) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    current_doc: str | None = None
    current_lines: list[str] = []

    for line in docs_text.splitlines():
        if line.startswith("## Document: "):
            if current_doc is not None:
                sections.append((current_doc, current_lines))
            current_doc = line.removeprefix("## Document: ").strip()
            current_lines = []
            continue
        current_lines.append(line)

    if current_doc is not None:
        sections.append((current_doc, current_lines))

    return sections


def _is_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("#"):
        return True
    if stripped.endswith(":") and len(stripped) <= 120:
        return True
    return False


def _flush_chunk(
    chunks: list[DocumentChunk],
    *,
    document_path: str,
    heading: str | None,
    buffer_lines: list[str],
    start_line: int,
    end_line: int,
    chunk_index: int,
) -> None:
    text = "\n".join(buffer_lines).strip()
    if not text:
        return

    chunks.append(
        DocumentChunk(
            document_path=document_path,
            chunk_id=f"{document_path}::chunk_{chunk_index}",
            heading=heading,
            text=text,
            start_line=start_line,
            end_line=end_line,
        )
    )


def build_structured_document_chunks(docs_text: str) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []

    for document_path, lines in _split_document_sections(docs_text):
        heading: str | None = None
        buffer_lines: list[str] = []
        chunk_start_line = 1
        chunk_index = 1

        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if _is_heading(line):
                if buffer_lines:
                    _flush_chunk(
                        chunks,
                        document_path=document_path,
                        heading=heading,
                        buffer_lines=buffer_lines,
                        start_line=chunk_start_line,
                        end_line=line_number - 1,
                        chunk_index=chunk_index,
                    )
                    chunk_index += 1
                    buffer_lines = []
                heading = stripped
                chunk_start_line = line_number
                buffer_lines.append(line)
                continue

            if not stripped:
                if buffer_lines:
                    _flush_chunk(
                        chunks,
                        document_path=document_path,
                        heading=heading,
                        buffer_lines=buffer_lines,
                        start_line=chunk_start_line,
                        end_line=line_number - 1,
                        chunk_index=chunk_index,
                    )
                    chunk_index += 1
                    buffer_lines = []
                heading = heading
                chunk_start_line = line_number + 1
                continue

            if not buffer_lines:
                chunk_start_line = line_number
            buffer_lines.append(line)

        if buffer_lines:
            _flush_chunk(
                chunks,
                document_path=document_path,
                heading=heading,
                buffer_lines=buffer_lines,
                start_line=chunk_start_line,
                end_line=len(lines),
                chunk_index=chunk_index,
            )

    return chunks