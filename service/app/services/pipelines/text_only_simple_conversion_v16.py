"""Text-only conversion pipeline v16 for batched cable/pipe boolean-map extraction."""

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
    """Extract and validate the list of requested types from expected_value."""
    if not isinstance(payload.expected_value, dict) or not payload.expected_value:
        raise ValueError(
            "Pipeline v16 requires expected_value to be a non-empty object of {type: boolean}."
        )
    return list(payload.expected_value.keys())


def _resolve_number_of_variables_per_request(payload: ExperimentRequest, total_types: int) -> int:
    """Determine the number of variables per LLM request for splitting requested types."""
    if payload.number_of_variables_per_request is None:
        return total_types
    if payload.number_of_variables_per_request < 1:
        raise ValueError("number_of_variables_per_request must be >= 1")
    return payload.number_of_variables_per_request


def _split_into_batches(items: list[str], batch_size: int) -> list[list[str]]:
    """Split a list into batches of at most batch_size (number_of_variables_per_request)."""
    return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]


def _build_prompt(
    *,
    template: str,
    payload: ExperimentRequest,
    docs_text: str,
    requested_types: list[str],
) -> tuple[str, int, str, str]:
    """Build Step-1 prompt with the requested types list."""
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


def _parse_batch_boolean_map_with_fallback(
    *,
    raw_output: str,
    batch_types: list[str],
) -> tuple[dict[str, bool], float | None, bool, str | None]:
    """Parse batch output strictly first, then recover missing keys with False if needed.

    Recovery keeps the pipeline running when the model omits requested keys in one batch.
    """
    try:
        parsed, confidence = parse_extracted_boolean_map(
            raw_output,
            expected_keys=batch_types,
        )
        if parsed is None:
            return {key: False for key in batch_types}, confidence, True, "extracted_value was null"
        return parsed, confidence, False, None
    except ValueError as strict_error:
        # Attempt a tolerant parse and fill missing requested keys with False.
        parsed, confidence = parse_extracted_boolean_map(raw_output, expected_keys=None)
        parsed = parsed or {}

        recovered: dict[str, bool] = {key: parsed.get(key, False) for key in batch_types}
        missing = [key for key in batch_types if key not in parsed]
        extra = [key for key in parsed if key not in batch_types]
        issue = (
            f"Recovered from strict key mismatch. Missing defaulted to False: {missing}; "
            f"Ignored extra keys: {extra}; strict_error={strict_error}"
        )
        return recovered, confidence, True, issue


def run_text_only_simple_conversion_v16(payload: ExperimentRequest) -> ExperimentResponse:
    """
    Pipeline v16:
    1) Extract full text from PDFs using cleaner v2.
    2) Split requested cable/pipe type list into batches of number_of_variables_per_request.
    3) For each batch, ask the LLM for strict true/false values.
    4) Collect results from all batches into a single boolean map.
    5) Compare against the full expected_value.
    """
    pipeline_started_at = _now_iso()
    components: list[ComponentLog] = []
    total_input_tokens = 0
    total_output_tokens = 0

    requested_types = _resolve_requested_types(payload)
    number_of_variables_per_request = _resolve_number_of_variables_per_request(payload, len(requested_types))
    batches = _split_into_batches(requested_types, number_of_variables_per_request)

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

    batching_component = _start_component("batching_split")
    components.append(
        _finish_component(
            batching_component,
            status="success",
            details={
                "total_types": len(requested_types),
                "number_of_variables_per_request": number_of_variables_per_request,
                "batch_count": len(batches),
            },
        )
    )

    extracted_value: dict[str, bool] = {}
    all_full_outputs: list[str] = []
    batch_confidences: list[float] = []

    for batch_idx, batch_types in enumerate(batches, start=1):
        batch_component = _start_component(f"batch_{batch_idx}_prompt_builder")
        full_prompt, conditions_count, conditions_text_raw, conditions_text_de = _build_prompt(
            template=template,
            payload=payload,
            docs_text=docs_text,
            requested_types=batch_types,
        )
        components.append(
            _finish_component(
                batch_component,
                status="success",
                details={
                    "prompt_length": len(full_prompt),
                    "batch_types_count": len(batch_types),
                    "batch_types": batch_types,
                    "conditions_count": conditions_count,
                    "conditions_preview": conditions_text_raw[:250],
                },
            )
        )

        llm_component = _start_component(f"batch_{batch_idx}_llm_client")
        try:
            llm_response = generate_text_component(
                prompt=full_prompt,
                llm=payload.llm,
                temperature=payload.temperature,
            )
            total_input_tokens += llm_response.input_tokens
            total_output_tokens += llm_response.output_tokens
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
            raise RuntimeError(f"Batch {batch_idx} LLM generation failed: {exc}") from exc

        parser_component = _start_component(f"batch_{batch_idx}_output_parser_boolean_map")
        try:
            batch_result, batch_confidence, recovered, parse_issue = _parse_batch_boolean_map_with_fallback(
                raw_output=llm_response.text,
                batch_types=batch_types,
            )
            if batch_result:
                extracted_value.update(batch_result)
                if batch_confidence is not None:
                    batch_confidences.append(batch_confidence)
        except Exception as exc:
            components.append(
                _finish_component(
                    parser_component,
                    status="error",
                    details={"parsed": False},
                    error=str(exc),
                )
            )
            raise RuntimeError(f"Batch {batch_idx} output parsing failed: {exc}") from exc

        components.append(
            _finish_component(
                parser_component,
                status="success",
                details={
                    "parsed": batch_result is not None,
                    "batch_types": batch_types,
                    "confidence": batch_confidence,
                    "recovered": recovered,
                    "parse_issue": parse_issue,
                },
            )
        )

        all_full_outputs.append(f"### Batch {batch_idx}\n{llm_response.text}")

    is_match = evaluate_match(extracted_value, payload.expected_value)
    
    # Calculate average confidence from all batches
    average_confidence = (sum(batch_confidences) / len(batch_confidences)) if batch_confidences else None

    result = ExperimentResult(
        expected_value=payload.expected_value,
        extracted_value=extracted_value,
        is_match=is_match,
        confidence=average_confidence,
        full_prompt=f"Batches: {len(batches)} (number_of_variables_per_request={number_of_variables_per_request})\n\n" + "\n\n".join(all_full_outputs),
        full_output="\n\n".join(all_full_outputs),
        input_tokens=total_input_tokens,
        output_tokens=total_output_tokens,
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
