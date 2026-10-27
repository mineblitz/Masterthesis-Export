"""Turtle KG conversion pipeline v12 — uses Turtle/RDF conditions from a Knowledge Graph."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.models import ComponentLog, ExperimentRequest, ExperimentResponse, ExperimentResult
from app.services.components.llm_client_component import generate_text_component
from app.services.components.output_parser_component import parse_extracted_value
from app.services.components.result_matcher_component import evaluate_match
from app.services.components.prompt_builder_v6 import (
    build_conditions_block_from_turtle,
    build_conditions_raw_from_turtle,
    build_prompt_v6,
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


def _resolve_marker_llm_markdown_path(document_path: str, base_dir: Path) -> tuple[Path, str]:
    """Resolve a PDF path to its sibling *_marker_llm.md file."""
    source_path = (base_dir / document_path).resolve()

    if source_path.name.lower().endswith("_marker_llm.md"):
        marker_path = source_path
    else:
        marker_path = source_path.with_name(f"{source_path.stem}_marker_llm.md")

    if not marker_path.exists():
        raise FileNotFoundError(f"Marker LLM markdown not found: {marker_path}")

    return marker_path, marker_path.relative_to(base_dir.resolve()).as_posix()


def _extract_text_from_marker_llm_markdown(paths: list[str], base_dir: Path) -> tuple[str, list[str]]:
    chunks: list[str] = []
    resolved_paths: list[str] = []

    for document_path in paths:
        marker_path, relative_marker_path = _resolve_marker_llm_markdown_path(document_path, base_dir)
        cleaned_text = marker_path.read_text(encoding="utf-8")
        chunks.append(f"## Document: {relative_marker_path}\n{cleaned_text}")
        resolved_paths.append(relative_marker_path)

    return "\n\n".join(chunks), resolved_paths


def run_turtle_kg_conversion_v12(payload: ExperimentRequest) -> ExperimentResponse:
    """
    Pipeline v12: Turtle KG condition extraction.

    Uses ``conditions_turtle`` (a Turtle/RDF snippet from a Knowledge Graph)
    instead of ``conditions`` (a flat list) to describe the filter criteria.
    Document input is Marker LLM-generated markdown (same as v7).
    """
    pipeline_started_at = _now_iso()
    components: list[ComponentLog] = []

    # --- 1. Load prompt template ------------------------------------------------
    prompt_component = _start_component("prompt_loader")
    template = load_prompt_template(payload.prompt)
    components.append(
        _finish_component(
            prompt_component,
            status="success",
            details={"prompt_name": payload.prompt},
        )
    )

    # --- 2. Extract document text (Marker LLM markdown) -------------------------
    marker_component = _start_component("marker_llm_markdown_extractor")
    try:
        docs_text, used_documents = _extract_text_from_marker_llm_markdown(
            paths=payload.approval_links,
            base_dir=Path("."),
        )
        components.append(
            _finish_component(
                marker_component,
                status="success",
                details={"document_count": len(used_documents), "method": "marker_llm_markdown"},
            )
        )
    except Exception as exc:
        components.append(
            _finish_component(
                marker_component,
                status="error",
                details={"document_count": 0},
                error=str(exc),
            )
        )
        raise RuntimeError(f"Marker LLM markdown extraction failed: {exc}") from exc

    # --- 3. Build prompt with Turtle conditions ----------------------------------
    prompt_builder_component = _start_component("prompt_builder_v6_turtle")
    turtle_snippet = payload.conditions_turtle or ""
    conditions_text_de, conditions_count = build_conditions_block_from_turtle(turtle_snippet)
    conditions_text_raw = build_conditions_raw_from_turtle(turtle_snippet)
    full_prompt = build_prompt_v6(
        template=template,
        system=payload.system,
        system_name=payload.system_name,
        value=payload.value,
        docs_text=docs_text,
        conditions_turtle=payload.conditions_turtle,
    )
    components.append(
        _finish_component(
            prompt_builder_component,
            status="success",
            details={
                "prompt_length": len(full_prompt),
                "conditions_count": conditions_count,
                "has_conditions_turtle": bool(turtle_snippet.strip()),
                "conditions_preview_de": conditions_text_de[:250],
                "conditions_preview_raw": conditions_text_raw[:250],
            },
        )
    )

    # --- 4. Call LLM -------------------------------------------------------------
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

    # --- 5. Parse output ----------------------------------------------------------
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

    # --- 6. Evaluate match --------------------------------------------------------
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
