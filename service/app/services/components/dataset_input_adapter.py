"""Normalize dataset-provided document text for extraction pipelines."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from app.models import ExperimentRequest
from app.services.components.keyword_context_extractor import DEFAULT_GERMAN_SEARCH_TERMS
from app.services.pdf_text_extractor import extract_text_from_pdfs


@dataclass(frozen=True)
class ResolvedDocumentInput:
    text: str
    used_documents: list[str]
    details: dict[str, Any]


_QUESTION_STOP_WORDS = {
    "welcher", "welche", "welches", "konkrete", "konkreter", "konkreten",
    "zahlen", "zahl", "messwert", "wird", "werden", "folgendem", "folgende",
    "satz", "gefordert", "the", "which", "what", "concrete", "value",
    "following", "sentence", "requested", "asked", "should", "would", "could",
    "have", "has", "does", "than", "that", "this", "with", "from", "into",
    "where", "when", "whose", "there", "their", "they", "them", "and", "for",
    "are", "was", "were", "not", "its", "who", "all",
}


def resolve_document_input(
    payload: ExperimentRequest,
    base_dir: Path,
    pdf_extractor: Callable[[list[str], Path], tuple[str, list[str]]] | None = None,
) -> ResolvedDocumentInput:
    """Use explicit dataset text when requested; otherwise preserve PDF extraction."""
    extras = payload.model_extra or {}
    input_source = extras.get("input_source")

    if input_source not in (None, "approval_links", "dataset_text"):
        raise ValueError(f"Unsupported input_source '{input_source}'.")

    if input_source != "dataset_text":
        extractor = pdf_extractor or extract_text_from_pdfs
        text, used_documents = extractor(payload.approval_links, base_dir)
        return ResolvedDocumentInput(
            text=text,
            used_documents=used_documents,
            details={
                "input_source": "approval_links",
                "requested_input_extent": "source_pdf",
                "actual_input_extent": "source_pdf",
                "source_text_truncated": False,
            },
        )

    if payload.content is None or not payload.content.strip():
        raise ValueError(
            "input_source='dataset_text' requires a non-empty 'content' or 'chunk' field."
        )

    metadata = extras.get("metadata")
    metadata_id = metadata.get("ID") if isinstance(metadata, dict) else None
    source_id = (
        extras.get("source_example_id")
        or metadata_id
        or (f"order-{payload.order}" if payload.order is not None else None)
    )
    source_name = (
        extras.get("full_pdf_source")
        or extras.get("context_source_pdf")
        or source_id
        or "dataset_text"
    )

    full_pdf_status = extras.get("full_pdf_status")
    requested_extent = extras.get("input_extent", "dataset_text")
    if full_pdf_status in {"pdf_text_unavailable", "no_source_pdf"}:
        actual_extent = "passage_fallback"
    else:
        actual_extent = requested_extent

    source_details = {
        key: extras[key]
        for key in (
            "full_pdf_status",
            "full_pdf_source",
            "context_match_status",
            "context_source_pdf",
            "context_source_pages",
            "source_dataset",
            "source_split",
            "source_example_id",
            "value_span_index",
        )
        if key in extras
    }
    if isinstance(metadata, dict):
        source_details["metadata"] = metadata

    return ResolvedDocumentInput(
        text=f"## Document: {source_name}\n{payload.content}",
        used_documents=[str(source_name)],
        details={
            "input_source": "dataset_text",
            "requested_input_extent": requested_extent,
            "actual_input_extent": actual_extent,
            "source_id": source_id,
            "source_metadata": source_details,
            "source_text_chars": len(payload.content),
            "source_text_truncated": False,
        },
    )


def resolve_dataset_search_terms(payload: ExperimentRequest) -> list[str] | None:
    """Use existing value-key terms, or derive compact CODE-ACCORD query terms."""
    extras = payload.model_extra or {}
    raw_terms = extras.get("search_terms")
    if isinstance(raw_terms, str) and raw_terms.strip():
        return [raw_terms.strip()]
    if isinstance(raw_terms, list):
        terms = [str(term).strip() for term in raw_terms if str(term).strip()]
        if terms:
            return terms

    if payload.value in DEFAULT_GERMAN_SEARCH_TERMS:
        return None

    question_target = ""
    if payload.question:
        question_target = payload.question.partition(":")[2] or payload.question
    terms = _extract_query_terms(question_target)
    if not terms:
        terms = _extract_query_terms(payload.content or "")

    if terms:
        return terms[:12]
    if payload.value.casefold() == "value":
        return ["value"]
    return None


def _extract_query_terms(text: str) -> list[str]:
    terms: list[str] = []
    for term in re.findall(r"[^\W\d_]+", text.casefold(), flags=re.UNICODE):
        if len(term) < 5 or term in _QUESTION_STOP_WORDS or term in terms:
            continue
        terms.append(term)
        if len(terms) == 12:
            break
    return terms


def append_question_to_prompt(prompt: str, payload: ExperimentRequest) -> str:
    """Give Q&A dataset records' question to non-direct-QA extraction prompts."""
    if not payload.question or not payload.question.strip():
        return prompt
    return (
        f"{prompt}\n\nQuestion from the dataset "
        "(source text may be German or English):\n"
        f"{payload.question.strip()}"
    )
