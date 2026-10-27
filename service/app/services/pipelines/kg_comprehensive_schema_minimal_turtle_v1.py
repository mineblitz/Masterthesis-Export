"""Comprehensive KG extraction pipeline for minimal schema to full Turtle output."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.models import ComponentLog, ExperimentRequest, ExperimentResponse, ExperimentResult
from app.services.components.llm_client_component import generate_text_component
from app.services.components.pdf_text_extractor_v2 import extract_text_from_pdfs_v2
from app.services.components.turtle_triple_scorer_component import (
    classify_triple_errors,
    parse_turtle_to_normalized_triples,
    score_triple_sets,
)
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


def _get_extra(payload: ExperimentRequest, key: str, default: Any = None) -> Any:
    extras = payload.model_extra or {}
    return extras.get(key, default)


def _build_prompt(
    *,
    template: str,
    payload: ExperimentRequest,
    input_kg_schema_ttl: str,
    docs_text: str,
) -> str:
    placeholders = {
        "{{SYSTEM}}": payload.system,
        "{{SYSTEM_NAME}}": payload.system_name,
        "{{VALUE}}": payload.value,
        "{{INPUT_KG_SCHEMA_TTL}}": input_kg_schema_ttl.strip(),
        "{{DOCUMENT_CONTENT}}": docs_text,
    }

    rendered = template
    for token, value in placeholders.items():
        rendered = rendered.replace(token, value)
    return rendered


def run_kg_comprehensive_schema_minimal_turtle_v1(
    payload: ExperimentRequest,
) -> ExperimentResponse:
    pipeline_started_at = _now_iso()
    components: list[ComponentLog] = []

    input_kg_schema_ttl = str(_get_extra(payload, "input_kg_schema_ttl", "")).strip()
    expected_turtle_filled = str(_get_extra(payload, "expected_turtle_filled", "")).strip()
    if not input_kg_schema_ttl:
        raise ValueError("input_kg_schema_ttl is required for comprehensive KG pipeline")
    if not expected_turtle_filled:
        raise ValueError("expected_turtle_filled is required for comprehensive KG pipeline")

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

    prompt_builder_component = _start_component("prompt_builder_comprehensive_kg")
    full_prompt = _build_prompt(
        template=template,
        payload=payload,
        input_kg_schema_ttl=input_kg_schema_ttl,
        docs_text=docs_text,
    )
    components.append(
        _finish_component(
            prompt_builder_component,
            status="success",
            details={
                "prompt_length": len(full_prompt),
                "schema_chars": len(input_kg_schema_ttl),
                "document_chars": len(docs_text),
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
        components.append(_finish_component(llm_component, status="error", error=str(exc)))
        raise RuntimeError(f"LLM generation failed: {exc}") from exc

    scoring_component = _start_component("turtle_triple_scorer")
    syntax_failure = False
    syntax_error: str | None = None

    try:
        expected_triples = parse_turtle_to_normalized_triples(expected_turtle_filled)
    except Exception as exc:
        components.append(
            _finish_component(
                scoring_component,
                status="error",
                error=f"Expected turtle parsing failed: {exc}",
            )
        )
        raise RuntimeError(f"Expected turtle parsing failed: {exc}") from exc

    try:
        predicted_triples = parse_turtle_to_normalized_triples(llm_response.text)
        metrics = score_triple_sets(predicted_triples, expected_triples)
        errors = classify_triple_errors(predicted_triples, expected_triples)
    except Exception as exc:
        syntax_failure = True
        syntax_error = str(exc)
        metrics = {
            "predicted_triples": 0,
            "expected_triples": len(expected_triples),
            "correct_triples": 0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
        }
        errors = {
            "missing_triples_count": len(expected_triples),
            "hallucinated_triples_count": 0,
            "wrong_relation_count": 0,
            "wrong_literal_count": 0,
            "wrong_entity_linkage_count": 0,
            "missing_triples_examples": [],
            "hallucinated_triples_examples": [],
            "syntax_failure": True,
            "syntax_error": syntax_error,
        }

    components.append(
        _finish_component(
            scoring_component,
            status="success",
            details={
                **metrics,
                **errors,
                "syntax_failure": syntax_failure,
            },
        )
    )

    is_match = (not syntax_failure) and (metrics["f1"] == 1.0)

    extracted_value = {
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1": metrics["f1"],
        "predicted_triples": metrics["predicted_triples"],
        "expected_triples": metrics["expected_triples"],
        "correct_triples": metrics["correct_triples"],
        "syntax_failure": syntax_failure,
    }

    result = ExperimentResult(
        expected_value=payload.expected_value,
        extracted_value=extracted_value,
        is_match=is_match,
        confidence=metrics["f1"],
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