"""Text-only conversion pipeline v15 for strict cable/pipe boolean-map extraction."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.models import ComponentLog, ExperimentRequest, ExperimentResponse, ExperimentResult
from app.services.components.llm_client_component import generate_text_component
from app.services.components.output_parser_boolean_map_component import (
    parse_extracted_boolean_map,
)
from app.services.components.prompt_builder_v5 import (
    build_conditions_block,
    build_conditions_block_de,
)
from app.services.components.result_matcher_component import evaluate_match
from app.services.components.pdf_text_extractor_v2 import extract_text_from_pdfs_v2
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


def _resolve_requested_types(payload: ExperimentRequest) -> list[str]:
    if not isinstance(payload.expected_value, dict) or not payload.expected_value:
        raise ValueError(
            "Pipeline v15 requires expected_value to be a non-empty object of {type: boolean}."
        )
    return list(payload.expected_value.keys())


def _build_prompt(
    *,
    template: str,
    payload: ExperimentRequest,
    docs_text: str,
    requested_types: list[str],
) -> tuple[str, int, str, str]:
    conditions_text_raw, conditions_count = build_conditions_block(payload.conditions)
    conditions_text_de, _ = build_conditions_block_de(payload.conditions)
    requested_types_json = json.dumps(requested_types, ensure_ascii=True, indent=2)

    replacements = {
        "{{SYSTEM}}": payload.system,
        "{{SYSTEM_NAME}}": payload.system_name,
        "{{VALUE}}": payload.value,
        "{{REQUESTED_TYPES_JSON}}": requested_types_json,
        "{{CONDITIONS}}": conditions_text_raw,
        "{{CONDITIONS_DE}}": conditions_text_de,
        "{{DOCUMENT_CONTENT}}": docs_text,
    }

    full_prompt = template
    for placeholder, value in replacements.items():
        full_prompt = full_prompt.replace(placeholder, value)

    return full_prompt, conditions_count, conditions_text_raw, conditions_text_de


def run_text_only_simple_conversion_v15(payload: ExperimentRequest) -> ExperimentResponse:
    """
    Pipeline v15:
    1) Extract full text from PDFs using cleaner v2.
    2) Ask for strict true/false values for the provided cable/pipe type list.
    3) Parse the returned boolean map under extracted_value.
    """
    pipeline_started_at = _now_iso()
    components: list[ComponentLog] = []
    requested_types = _resolve_requested_types(payload)

    prompt_component = _start_component("prompt_loader")
    template = load_prompt_template(payload.prompt)
    components.append(
        _finish_component(
            prompt_component,
            status="success",
            details={"prompt_name": payload.prompt},
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

    prompt_builder_component = _start_component("prompt_builder_v15")
    full_prompt, conditions_count, conditions_text_raw, conditions_text_de = _build_prompt(
        template=template,
        payload=payload,
        docs_text=docs_text,
        requested_types=requested_types,
    )
    components.append(
        _finish_component(
            prompt_builder_component,
            status="success",
            details={
                "prompt_length": len(full_prompt),
                "conditions_count": conditions_count,
                "has_conditions": conditions_count > 0,
                "requested_types_count": len(requested_types),
                "requested_types": requested_types,
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

    parser_component = _start_component("output_parser_boolean_map")
    confidence: float | None = None
    try:
        extracted_value, confidence = parse_extracted_boolean_map(
            llm_response.text,
            expected_keys=requested_types,
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
            details={"parsed": extracted_value is not None},
        )
    )

    is_match = evaluate_match(extracted_value, payload.expected_value)

    result = ExperimentResult(
        expected_value=payload.expected_value,
        extracted_value=extracted_value,
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