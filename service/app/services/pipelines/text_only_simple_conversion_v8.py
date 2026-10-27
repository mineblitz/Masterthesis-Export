"""Text-only conversion pipeline v8 using full PDF text plus keyword-context chunking."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.models import ComponentLog, ExperimentRequest, ExperimentResponse, ExperimentResult
from app.services.components.dataset_input_adapter import (
    append_question_to_prompt,
    resolve_dataset_search_terms,
    resolve_document_input,
)
from app.services.components.keyword_context_extractor import extract_keyword_context_chunks
from app.services.components.llm_client_component import generate_text_component
from app.services.components.output_parser_component import parse_extracted_value
from app.services.components.prompt_builder_v5 import (
    build_conditions_block,
    build_conditions_block_de,
    build_prompt_v5,
)
from app.services.components.result_matcher_component import evaluate_match
from app.services.pdf_text_extractor import extract_text_from_pdfs
from app.services.prompt_loader import load_prompt_template


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _start_component(name: str) -> ComponentLog:
    now = _now_iso()
    return ComponentLog(name=name, status="running", started_at=now, finished_at=now)


def _finish_component(
    component: ComponentLog,
    *,
    status: str,
    details: dict[str, Any] | None = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    error: str | None = None,
) -> ComponentLog:
    component.status = status
    component.finished_at = _now_iso()
    component.details = details
    component.input_tokens = input_tokens
    component.output_tokens = output_tokens
    component.error = error
    return component


def _resolve_context_window(payload: ExperimentRequest) -> tuple[int, int]:
    raw_common = getattr(payload, "context_window_lines", None)
    raw_before = getattr(payload, "context_lines_before", None)
    raw_after = getattr(payload, "context_lines_after", None)

    if raw_before is not None or raw_after is not None:
        raise ValueError(
            "Bitte nur 'context_window_lines' verwenden. "
            "Separate Werte 'context_lines_before' und 'context_lines_after' sind in v8 nicht erlaubt."
        )

    default_window = 3
    common = int(raw_common) if raw_common is not None else default_window
    return common, common


def run_text_only_simple_conversion_v8(payload: ExperimentRequest) -> ExperimentResponse:
    """
    Pipeline v8:
    1) Extract full text from PDFs using the basic parser.
    2) Find value-specific German keywords.
    3) Keep n lines before/after each hit and pass collected chunks to the LLM.
    """
    pipeline_started_at = _now_iso()
    components: list[ComponentLog] = []

    prompt_component = _start_component("prompt_loader")
    template = load_prompt_template(payload.prompt)
    components.append(
        _finish_component(
            prompt_component,
            status="success",
            details={"prompt_name": payload.prompt},
        )
    )

    pdf_component = _start_component("document_text_resolver")
    try:
        document_input = resolve_document_input(
            payload,
            Path("."),
            pdf_extractor=extract_text_from_pdfs,
        )
        docs_text = document_input.text
        used_documents = document_input.used_documents
        components.append(
            _finish_component(
                pdf_component,
                status="success",
                details={
                    "document_count": len(used_documents),
                    "method": (
                        "dataset_text"
                        if document_input.details["input_source"] == "dataset_text"
                        else "pdf_full_text"
                    ),
                    **document_input.details,
                },
            )
        )
    except Exception as exc:
        components.append(
            _finish_component(
                pdf_component,
                status="error",
                details={"document_count": 0},
                error=str(exc),
            )
        )
        raise RuntimeError(f"PDF extraction failed: {exc}") from exc

    keyword_chunk_component = _start_component("keyword_context_extractor")
    try:
        lines_before, lines_after = _resolve_context_window(payload)
        keyword_result = extract_keyword_context_chunks(
            docs_text,
            value=payload.value,
            search_terms=resolve_dataset_search_terms(payload),
            lines_before=lines_before,
            lines_after=lines_after,
        )
        docs_for_prompt = keyword_result.filtered_documents_text
        if not docs_for_prompt.strip():
            docs_for_prompt = docs_text

        components.append(
            _finish_component(
                keyword_chunk_component,
                status="success",
                details={
                    "search_terms": keyword_result.search_terms,
                    "lines_before": lines_before,
                    "lines_after": lines_after,
                    "document_count": keyword_result.document_count,
                    "chunk_count": keyword_result.chunk_count,
                    "hit_count": keyword_result.hit_count,
                    "fallback_to_full_text": keyword_result.chunk_count == 0,
                    "prompt_input_scope": (
                        "keyword_windows"
                        if keyword_result.chunk_count
                        else "full_text_fallback_no_keyword_hits"
                    ),
                    "window_coordinate_system": (
                        "one-based lines and zero-based, end-exclusive character offsets "
                        "within each extracted source-text section"
                    ),
                    "window_boundaries": keyword_result.window_boundaries,
                },
            )
        )
    except Exception as exc:
        components.append(
            _finish_component(
                keyword_chunk_component,
                status="error",
                error=str(exc),
            )
        )
        raise RuntimeError(f"Keyword context extraction failed: {exc}") from exc

    prompt_builder_component = _start_component("prompt_builder_v5")
    conditions_text_raw, conditions_count = build_conditions_block(payload.conditions)
    conditions_text_de, _ = build_conditions_block_de(payload.conditions)
    full_prompt = append_question_to_prompt(
        build_prompt_v5(
            template=template,
            system=payload.system,
            system_name=payload.system_name,
            value=payload.value,
            conditions=payload.conditions,
            docs_text=docs_for_prompt,
        ),
        payload,
    )
    components.append(
        _finish_component(
            prompt_builder_component,
            status="success",
            details={
                "prompt_length": len(full_prompt),
                "conditions_count": conditions_count,
                "has_conditions": conditions_count > 0,
                "conditions_preview_raw": conditions_text_raw[:250],
                "conditions_preview_de": conditions_text_de[:250],
            },
        )
    )

    llm_component = _start_component("llm_client")
    try:
        llm_response = generate_text_component(
            prompt=full_prompt,
            llm=payload.llm,
            temperature=payload.temperature,
        )
        components.append(
            _finish_component(
                llm_component,
                status="success",
                details={"model": llm_response.model},
                input_tokens=llm_response.input_tokens,
                output_tokens=llm_response.output_tokens,
            )
        )
    except Exception as exc:
        components.append(
            _finish_component(
                llm_component,
                status="error",
                error=str(exc),
            )
        )
        raise RuntimeError(f"LLM generation failed: {exc}") from exc

    parser_component = _start_component("output_parser")
    try:
        extracted_value = parse_extracted_value(llm_response.text)
    except Exception as exc:
        components.append(
            _finish_component(
                parser_component,
                status="error",
                details={"parsed": False},
                error=str(exc),
            )
        )
        raise RuntimeError(f"Output parsing failed: {exc}") from exc

    components.append(
        _finish_component(
            parser_component,
            status="success",
            details={"parsed": extracted_value is not None},
        )
    )

    is_match = evaluate_match(extracted_value, payload.expected_value)

    result = ExperimentResult(
        expected_value=payload.expected_value,
        extracted_value=extracted_value,
        is_match=is_match,
        full_prompt=full_prompt,
        full_output=llm_response.text,
        input_tokens=llm_response.input_tokens,
        output_tokens=llm_response.output_tokens,
        temperature=payload.temperature,
        experiment_id=payload.experiment_id,
        pipeline_started_at=pipeline_started_at,
        pipeline_finished_at=_now_iso(),
        experiment_description=payload.experiment_description,
        used_documents=used_documents,
        system=payload.system,
        extracted_value_type=payload.value,
        min_or_max=payload.min_or_max,
        used_llm=payload.llm.value,
        components=components,
    )

    return ExperimentResponse(
        status="success",
        experiment_id=payload.experiment_id,
        pipeline=payload.pipeline,
        result=result,
    )