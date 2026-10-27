from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import DependencyError


def _is_restricted_h2_h3_p_pdf(relative_path: str) -> bool:
    normalized_path = relative_path.replace("\\", "/").lower()
    path_parts = [part for part in normalized_path.split("/") if part]
    filename = Path(normalized_path).name
    return ("h2" in path_parts or "h3" in path_parts) and filename.startswith("p_")


def extract_text_from_pdfs(paths: list[str], base_dir: Path) -> tuple[str, list[str]]:
    """Extract and concatenate text from multiple PDF files."""
    chunks: list[str] = []
    resolved_paths: list[str] = []

    for relative_path in paths:
        if _is_restricted_h2_h3_p_pdf(relative_path):
            chunks.append(f"## Document: {relative_path}\n")
            resolved_paths.append(relative_path)
            continue

        pdf_path = (base_dir / relative_path).resolve()
        if not pdf_path.exists():
            raise FileNotFoundError(f"Approval PDF not found: {pdf_path}")

        try:
            reader = PdfReader(str(pdf_path))
            page_text = "\n".join((page.extract_text() or "") for page in reader.pages)
        except DependencyError as exc:
            raise RuntimeError(
                f"Cannot extract PDF text from '{relative_path}': the file is encrypted and requires the 'cryptography' package."
            ) from exc

        chunks.append(f"## Document: {relative_path}\n{page_text}")
        resolved_paths.append(relative_path)

    return "\n\n".join(chunks), resolved_paths
