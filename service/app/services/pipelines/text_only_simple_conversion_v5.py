"""Text-only conversion pipeline v5 with translated conditional guidance."""

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.models import ComponentLog, ExperimentRequest, ExperimentResponse, ExperimentResult
from app.services.components.llm_client_component import generate_text_component
from app.services.components.output_parser_component import parse_extracted_value
from app.services.components.result_matcher_component import evaluate_match
from app.services.components.pdf_text_extractor_v2 import extract_text_from_pdfs_v2
from app.services.components.prompt_builder_v5 import (
    build_conditions_block,
    build_conditions_block_de,
    build_prompt_v5,
)
from app.services.prompt_loader import load_prompt_template


logger = logging.getLogger("app.pipeline.v5")
logger.setLevel(logging.DEBUG)


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


def run_text_only_simple_conversion_v5(payload: ExperimentRequest) -> ExperimentResponse:
    """
    Pipeline v5: Conditional extraction with German translated condition context.

    This keeps v4 behavior intact and adds richer prompt guidance in v5.
    """
    pipeline_started_at = _now_iso()
    components: list[ComponentLog] = []
    logger.debug(
        "Pipeline v5 started: experiment_id=%s prompt=%s llm=%s links=%d value=%s",
        payload.experiment_id,
        payload.prompt,
        payload.llm.value,
        len(payload.approval_links),
        payload.value,
    )

    prompt_component = _start_component("prompt_loader")
    template = load_prompt_template(payload.prompt)
    logger.debug(
        "Prompt template loaded: experiment_id=%s prompt=%s template_length=%d",
        payload.experiment_id,
        payload.prompt,
        len(template),
    )
    components.append(
        _finish_component(
            prompt_component,
            status="success",
            details={"prompt_name": payload.prompt},
        )
    )

    pdf_component = _start_component("pdf_text_extractor_v2")
    try:
        logger.debug(
            "Starting PDF extraction: experiment_id=%s links=%s",
            payload.experiment_id,
            payload.approval_links,
        )
        docs_text, used_documents = extract_text_from_pdfs_v2(
            paths=payload.approval_links,
            base_dir=Path("."),
        )
        logger.debug(
            "PDF extraction finished: experiment_id=%s used_documents=%d docs_text_length=%d",
            payload.experiment_id,
            len(used_documents),
            len(docs_text),
        )
        components.append(
            _finish_component(
                pdf_component,
                status="success",
                details={"document_count": len(used_documents), "method": "pypdf_filtered_text"},
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
        logger.exception(
            "PDF extraction failed: experiment_id=%s links=%s",
            payload.experiment_id,
            payload.approval_links,
        )
        raise RuntimeError(f"PDF extraction failed: {exc}") from exc

    prompt_builder_component = _start_component("prompt_builder_v5")
    conditions_text_raw, conditions_count = build_conditions_block(payload.conditions)
    conditions_text_de, _ = build_conditions_block_de(payload.conditions)
    full_prompt = build_prompt_v5(
        template=template,
        system=payload.system,
        system_name=payload.system_name,
        value=payload.value,
        conditions=payload.conditions,
        docs_text=docs_text,
    )
    logger.debug(
        "Prompt built: experiment_id=%s full_prompt_length=%d conditions_count=%d",
        payload.experiment_id,
        len(full_prompt),
        conditions_count,
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
        logger.debug(
            "Starting LLM generation: experiment_id=%s llm=%s temperature=%s",
            payload.experiment_id,
            payload.llm.value,
            payload.temperature,
        )
        llm_response = generate_text_component(
            prompt=full_prompt,
            llm=payload.llm,
            temperature=payload.temperature,
        )
        logger.debug(
            "LLM generation finished: experiment_id=%s model=%s input_tokens=%d output_tokens=%d text_length=%d",
            payload.experiment_id,
            llm_response.model,
            llm_response.input_tokens,
            llm_response.output_tokens,
            len(llm_response.text),
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
        logger.exception(
            "LLM generation failed: experiment_id=%s llm=%s",
            payload.experiment_id,
            payload.llm.value,
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
        logger.exception("Output parsing failed: experiment_id=%s", payload.experiment_id)
        raise RuntimeError(f"Output parsing failed: {exc}") from exc

    logger.debug(
        "Output parsing finished: experiment_id=%s extracted_value=%s",
        payload.experiment_id,
        extracted_value,
    )

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

    logger.debug(
        "Pipeline v5 finished: experiment_id=%s is_match=%s expected_value=%s extracted_value=%s",
        payload.experiment_id,
        is_match,
        payload.expected_value,
        extracted_value,
    )

    return ExperimentResponse(
        status="success",
        experiment_id=payload.experiment_id,
        pipeline=payload.pipeline,
        result=result,
    )
