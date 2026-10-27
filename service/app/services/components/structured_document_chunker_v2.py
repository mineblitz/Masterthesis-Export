"""Markdown-header-aware document chunker backed by langchain-text-splitters.

New component for v27+ pipelines. Replaces the custom heading/blank-line chunking
in structured_document_chunker.py with MarkdownHeaderTextSplitter from
langchain-text-splitters. Produces the same DocumentChunk type.
Existing structured_document_chunker.py is unchanged.
"""

from app.services.components.structured_document_chunker import DocumentChunk

try:
    from langchain_text_splitters import MarkdownHeaderTextSplitter  # type: ignore[import-untyped]
    _LANGCHAIN_AVAILABLE = True
except ImportError:
    _LANGCHAIN_AVAILABLE = False


_HEADERS_TO_SPLIT = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
    ("####", "h4"),
]


def _split_document_sections(docs_text: str) -> list[tuple[str, str]]:
    """Extract (document_path, content) pairs from the multi-document text format."""
    sections: list[tuple[str, str]] = []
    current_doc: str | None = None
    current_lines: list[str] = []

    for line in docs_text.splitlines():
        if line.startswith("## Document: "):
            if current_doc is not None:
                sections.append((current_doc, "\n".join(current_lines)))
            current_doc = line.removeprefix("## Document: ").strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_doc is not None:
        sections.append((current_doc, "\n".join(current_lines)))

    return sections


def build_structured_document_chunks_v2(docs_text: str) -> list[DocumentChunk]:
    """Split documents into chunks using MarkdownHeaderTextSplitter.

    Handles the multi-document text format (## Document: <path> prefix blocks).
    Returns DocumentChunk objects with the same fields as the custom chunker,
    so new pipelines can use this as a direct replacement.

    Args:
        docs_text: Combined document text in the ## Document: path format.

    Returns:
        List of DocumentChunk objects sorted by (document_path, start_line).

    Raises:
        ImportError: If langchain-text-splitters is not installed.
    """
    if not _LANGCHAIN_AVAILABLE:
        raise ImportError(
            "langchain-text-splitters is required for structured_document_chunker_v2. "
            "Install it with: pip install langchain-text-splitters"
        )

    splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=_HEADERS_TO_SPLIT,
        strip_headers=False,
    )

    chunks: list[DocumentChunk] = []

    for document_path, content in _split_document_sections(docs_text):
        if not content.strip():
            continue

        langchain_docs = splitter.split_text(content)

        lines_so_far = 0
        for chunk_index, doc in enumerate(langchain_docs, start=1):
            text = doc.page_content.strip()
            if not text:
                continue

            # Derive heading from langchain metadata (last non-empty header level)
            heading: str | None = None
            for level in ("h4", "h3", "h2", "h1"):
                if doc.metadata.get(level):
                    heading = str(doc.metadata[level]).strip()
                    break

            # Approximate start/end line numbers based on text position in content
            text_start = content.find(doc.page_content, lines_so_far)
            if text_start == -1:
                text_start = lines_so_far
            start_line = content[:text_start].count("\n") + 1
            end_line = start_line + doc.page_content.count("\n")
            lines_so_far = text_start + len(doc.page_content)

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

    return chunks
