"""Shared implementation for KG Turtle record extraction pipelines."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from app.models import ComponentLog, ExperimentRequest, ExperimentResponse, ExperimentResult
from app.services.components.llm_client_component import generate_text_component
from app.services.components.output_parser_record_list_component import (
    normalize_record_list,
    parse_extracted_record_list,
)
from app.services.components.pdf_text_extractor_v2 import extract_text_from_pdfs_v2
from app.services.components.prompt_builder_kg_record_extraction import (
    build_kg_record_extraction_prompt,
)
from app.services.components.result_matcher_component import evaluate_match
from app.services.prompt_loader import load_prompt_template


_DEFAULT_MAX_DOCUMENT_CHARS = 120_000
_DEFAULT_MAX_HUSK_CHARS = 20_000
_MIN_DOCUMENT_CHARS = 8_000
_MIN_HUSK_CHARS = 2_000
_MAX_CONTEXT_RETRIES = 3


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


def _get_extra(payload: ExperimentRequest, key: str, default: Any = None) -> Any:
    extras = payload.model_extra or {}
    return extras.get(key, default)


def _resolve_metadata(payload: ExperimentRequest) -> dict[str, Any]:
    metadata = _get_extra(payload, "metadata", {})
    return metadata if isinstance(metadata, dict) else {}


def _resolve_positive_int(value: Any, *, fallback: int) -> int:
    try:
        parsed = int(value)
        if parsed >= 1:
            return parsed
    except (TypeError, ValueError):
        pass
    return fallback


def _compact_text_for_prompt(text: str, *, max_chars: int, label: str) -> str:
    if len(text) <= max_chars:
        return text

    if max_chars < 200:
        return text[:max_chars]

    head_len = max_chars // 2
    tail_len = max_chars - head_len - 120
    tail_len = max(0, tail_len)
    marker = (
        f"\n\n[... {label} truncated from {len(text)} to {max_chars} chars to stay under request-size limits ...]\n\n"
    )
    return f"{text[:head_len]}{marker}{text[-tail_len:] if tail_len else ''}"


def _is_context_limit_error(exc: Exception) -> bool:
    message = str(exc).casefold()
    return "exceeds the available context size" in message or "context size" in message


def _next_compaction_limit(current: int, *, minimum: int) -> int:
    if current <= minimum:
        return minimum
    reduced = int(current * 0.6)
    return max(minimum, reduced)


def run_kg_turtle_extraction(
    payload: ExperimentRequest,
    *,
    field_schema: dict[str, str],
    turtle_renderer: Callable[[str, list[dict[str, Any]]], str],
    json_renderer: Callable[[Any, list[dict[str, Any]], str], dict[str, Any]],
    prompt_builder_name: str,
    entity_type: str,
) -> ExperimentResponse:
    pipeline_started_at = _now_iso()
    components: list[ComponentLog] = []

    expected_records = normalize_record_list(payload.expected_value, field_schema=field_schema)
    metadata = _resolve_metadata(payload)
    input_format = str(metadata.get("format", "turtle")).strip().casefold() or "turtle"
    if input_format not in {"turtle", "json"}:
        input_format = "turtle"

    husk_mode = str(metadata.get("husk_mode", "placeholders")).strip() or "placeholders"
    input_turtle_husk = str(_get_extra(payload, "input_turtle_husk", "")).strip()
    input_json_husk = _get_extra(payload, "input_json_husk", {})

    max_document_chars = _resolve_positive_int(
        _get_extra(payload, "max_document_chars", None),
        fallback=_DEFAULT_MAX_DOCUMENT_CHARS,
    )
    max_husk_chars = _resolve_positive_int(
        _get_extra(payload, "max_husk_chars", None),
        fallback=_DEFAULT_MAX_HUSK_CHARS,
    )

    prompt_component = _start_component("prompt_loader")
    template = load_prompt_template(prompt_builder_name)
    components.append(
        _finish_component(
            prompt_component,
            status="success",
            details={"prompt_name": prompt_builder_name, "entity_type": entity_type},
        )
    )

    pdf_component = _start_component("pdf_text_extractor_v2")
    try:
        docs_text, used_documents = extract_text_from_pdfs_v2(payload.approval_links, Path("."))
        components.append(
            _finish_component(
                pdf_component,
                status="success",
                details={"document_count": len(used_documents), "method": "pdf_full_text_v2"},
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

    prompt_builder_component = _start_component(f"prompt_builder_{entity_type}")
    llm_response = None
    full_prompt = ""
    docs_limit = max_document_chars
    husk_limit = max_husk_chars
    context_retry_count = 0

    for attempt in range(1, _MAX_CONTEXT_RETRIES + 1):
        docs_text_for_prompt = _compact_text_for_prompt(
            docs_text,
            max_chars=docs_limit,
            label="document content",
        )
        if input_format == "json":
            serialized_json_husk = json.dumps(input_json_husk, ensure_ascii=True, indent=2)
            input_husk_for_prompt = _compact_text_for_prompt(
                serialized_json_husk,
                max_chars=husk_limit,
                label="json husk",
            )
        else:
            input_husk_for_prompt = _compact_text_for_prompt(
                input_turtle_husk,
                max_chars=husk_limit,
                label="turtle husk",
            )

        full_prompt = build_kg_record_extraction_prompt(
            template=template,
            payload=payload,
            docs_text=docs_text_for_prompt,
            record_schema=field_schema,
            input_husk=input_husk_for_prompt,
            input_format=input_format,
            husk_mode=husk_mode,
            metadata=metadata,
            expected_record_count=len(expected_records),
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
                    details={
                        "model": llm_response.model,
                        "attempt": attempt,
                        "context_retry_count": context_retry_count,
                    },
                    input_tokens=llm_response.input_tokens,
                    output_tokens=llm_response.output_tokens,
                )
            )
            break
        except Exception as exc:
            is_context_error = _is_context_limit_error(exc)
            if is_context_error and attempt < _MAX_CONTEXT_RETRIES:
                context_retry_count += 1
                components.append(
                    _finish_component(
                        llm_component,
                        status="error",
                        details={
                            "attempt": attempt,
                            "context_retry": True,
                            "docs_limit_before": docs_limit,
                            "husk_limit_before": husk_limit,
                        },
                        error=str(exc),
                    )
                )
                docs_limit = _next_compaction_limit(docs_limit, minimum=_MIN_DOCUMENT_CHARS)
                husk_limit = _next_compaction_limit(husk_limit, minimum=_MIN_HUSK_CHARS)
                continue

            components.append(
                _finish_component(
                    llm_component,
                    status="error",
                    details={"attempt": attempt, "context_retry": False},
                    error=str(exc),
                )
            )
            raise RuntimeError(f"LLM generation failed: {exc}") from exc

    if llm_response is None:
        raise RuntimeError("LLM generation failed after adaptive context retries")

    components.append(
        _finish_component(
            prompt_builder_component,
            status="success",
            details={
                "prompt_length": len(full_prompt),
                "husk_mode": husk_mode,
                "expected_record_count": len(expected_records),
                "input_format": input_format,
                "document_chars_original": len(docs_text),
                "document_chars_used": len(docs_text_for_prompt),
                "max_document_chars": max_document_chars,
                "husk_chars_original": len(input_husk_for_prompt),
                "husk_chars_used": len(input_husk_for_prompt),
                "max_husk_chars": max_husk_chars,
                "context_retry_count": context_retry_count,
            },
        )
    )

    parser_component = _start_component("output_parser_record_list")
    try:
        extracted_records, confidence = parse_extracted_record_list(
            llm_response.text,
            field_schema=field_schema,
        )
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
            details={"parsed": extracted_records is not None, "confidence": confidence},
        )
    )

    renderer_component = _start_component("husk_renderer")
    if input_format == "json":
        rendered_json = json_renderer(
            input_json_husk,
            extracted_records or [],
            system=payload.system,
        )
        rendered_preview = json.dumps(rendered_json, ensure_ascii=True, indent=2)[:1000]
        renderer_details = {
            "husk_mode": husk_mode,
            "format": "json",
            "rendered_json_preview": rendered_preview,
            "rendered_record_count": len(extracted_records or []),
        }
    else:
        rendered_turtle = turtle_renderer(input_turtle_husk, extracted_records or [])
        renderer_details = {
            "husk_mode": husk_mode,
            "format": "turtle",
            "rendered_turtle_preview": rendered_turtle[:1000],
            "rendered_record_count": len(extracted_records or []),
        }

    components.append(
        _finish_component(
            renderer_component,
            status="success",
            details=renderer_details,
        )
    )

    is_match = evaluate_match(extracted_records, expected_records)

    result = ExperimentResult(
        expected_value=expected_records,
        extracted_value=extracted_records,
        is_match=is_match,
        confidence=confidence,
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