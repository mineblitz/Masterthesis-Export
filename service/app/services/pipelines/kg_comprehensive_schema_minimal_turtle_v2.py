"""Hierarchical comprehensive KG extraction pipeline for minimal schema to Turtle output."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.models import ComponentLog, ExperimentRequest, ExperimentResponse, ExperimentResult
from app.services.components.kg_hierarchical_extraction_component import (
    extract_schema_top_level_branches,
    normalize_presence_output,
    normalize_subtype_output,
    parse_json_object_best_effort,
)
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


def _build_base_prompt(
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


def _build_presence_prompt(base_prompt: str, candidates: list[str]) -> str:
    branch_block = "\n".join(f"- {branch}" for branch in candidates)
    return (
        f"{base_prompt}\n\n"
        "Hierarchical stage 1 - presence and scope detection:\n"
        "Given the candidate top-level branches below, determine which branches are explicitly present in the document context.\n"
        "Candidate branches:\n"
        f"{branch_block}\n\n"
        "Return ONLY JSON in this exact format:\n"
        '{"detected_branches": ["BranchA", "BranchB"], "reason": "short evidence summary"}'
    )


def _build_subtype_prompt(base_prompt: str, branch: str) -> str:
    return (
        f"{base_prompt}\n\n"
        "Hierarchical stage 2 - subtype detection:\n"
        f"Focus only on branch '{branch}'. Identify present subtypes/categories for this branch.\n"
        "Return ONLY JSON in this exact format:\n"
        f'{{"branch": "{branch}", "detected_subtypes": ["SubtypeA", "SubtypeB"], "reason": "short evidence summary"}}'
    )


def _build_value_extraction_prompt(base_prompt: str, branch: str, subtype: str) -> str:
    return (
        f"{base_prompt}\n\n"
        "Hierarchical stage 3 - value/detail extraction:\n"
        f"Extract Turtle triples only for branch '{branch}' and subtype '{subtype}'.\n"
        "Use only explicitly supported information and keep namespace prefixes consistent with schema context.\n"
        "Return ONLY Turtle triples, no markdown fences and no prose."
    )


def _build_fallback_extraction_prompt(base_prompt: str, branches: list[str]) -> str:
    branch_block = ", ".join(branches) if branches else "none"
    return (
        f"{base_prompt}\n\n"
        "Hierarchical fallback extraction:\n"
        f"No subtypes were confidently detected. Extract Turtle triples only for these detected branches: {branch_block}.\n"
        "Return ONLY Turtle triples, no markdown fences and no prose."
    )


def _build_assembly_prompt(base_prompt: str, chunks: list[str], detected_branches: list[str]) -> str:
    chunk_block = "\n\n".join(
        f"### Chunk {index + 1}\n{chunk.strip()}" for index, chunk in enumerate(chunks) if chunk.strip()
    )
    branch_text = ", ".join(detected_branches) if detected_branches else "none"
    return (
        f"{base_prompt}\n\n"
        "Hierarchical stage 4 - final assembly:\n"
        f"Detected branches: {branch_text}\n"
        "Merge, deduplicate and normalize the extracted Turtle chunks below into one consistent Turtle graph.\n"
        "Do not invent missing facts. Keep only evidence-backed triples.\n\n"
        f"{chunk_block}\n\n"
        "Return ONLY final Turtle, no markdown fences and no prose."
    )


def run_kg_comprehensive_schema_minimal_turtle_v2(
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

    base_prompt_component = _start_component("prompt_builder_comprehensive_kg_hierarchical_v2")
    base_prompt = _build_base_prompt(
        template=template,
        payload=payload,
        input_kg_schema_ttl=input_kg_schema_ttl,
        docs_text=docs_text,
    )
    components.append(
        _finish_component(
            base_prompt_component,
            status="success",
            details={
                "prompt_length": len(base_prompt),
                "schema_chars": len(input_kg_schema_ttl),
                "document_chars": len(docs_text),
            },
        )
    )

    candidates_component = _start_component("hierarchical_candidate_extractor")
    candidate_branches = extract_schema_top_level_branches(input_kg_schema_ttl, max_branches=12)
    components.append(
        _finish_component(
            candidates_component,
            status="success",
            details={
                "candidate_branch_count": len(candidate_branches),
                "candidate_branches": candidate_branches,
            },
        )
    )

    stage1_component = _start_component("hierarchical_presence_detection")
    stage1_response = generate_text_component(
        prompt=_build_presence_prompt(base_prompt, candidate_branches),
        llm=payload.llm,
        temperature=payload.temperature,
    )
    stage1_data = parse_json_object_best_effort(stage1_response.text)
    detected_branches = normalize_presence_output(stage1_data, candidate_branches)
    if not detected_branches:
        detected_branches = candidate_branches[:2]
    components.append(
        _finish_component(
            stage1_component,
            status="success",
            input_tokens=stage1_response.input_tokens,
            output_tokens=stage1_response.output_tokens,
            details={
                "detected_branch_count": len(detected_branches),
                "detected_branches": detected_branches,
                "fallback_used": not bool(normalize_presence_output(stage1_data, candidate_branches)),
            },
        )
    )

    stage2_component = _start_component("hierarchical_subtype_detection")
    branch_to_subtypes: dict[str, list[str]] = {}
    stage2_in_tokens = 0
    stage2_out_tokens = 0

    for branch in detected_branches[:8]:
        subtype_response = generate_text_component(
            prompt=_build_subtype_prompt(base_prompt, branch),
            llm=payload.llm,
            temperature=payload.temperature,
        )
        stage2_in_tokens += subtype_response.input_tokens
        stage2_out_tokens += subtype_response.output_tokens
        subtype_data = parse_json_object_best_effort(subtype_response.text)
        subtypes = normalize_subtype_output(subtype_data, branch, max_subtypes=6)
        if subtypes:
            branch_to_subtypes[branch] = subtypes

    components.append(
        _finish_component(
            stage2_component,
            status="success",
            input_tokens=stage2_in_tokens,
            output_tokens=stage2_out_tokens,
            details={
                "branches_processed": len(detected_branches[:8]),
                "branches_with_subtypes": len(branch_to_subtypes),
                "branch_to_subtypes": branch_to_subtypes,
            },
        )
    )

    stage3_component = _start_component("hierarchical_value_extraction")
    extracted_chunks: list[str] = []
    stage3_in_tokens = 0
    stage3_out_tokens = 0

    for branch, subtypes in branch_to_subtypes.items():
        for subtype in subtypes[:6]:
            extraction_response = generate_text_component(
                prompt=_build_value_extraction_prompt(base_prompt, branch, subtype),
                llm=payload.llm,
                temperature=payload.temperature,
            )
            stage3_in_tokens += extraction_response.input_tokens
            stage3_out_tokens += extraction_response.output_tokens
            if extraction_response.text.strip():
                extracted_chunks.append(extraction_response.text.strip())

    if not extracted_chunks:
        fallback_response = generate_text_component(
            prompt=_build_fallback_extraction_prompt(base_prompt, detected_branches),
            llm=payload.llm,
            temperature=payload.temperature,
        )
        stage3_in_tokens += fallback_response.input_tokens
        stage3_out_tokens += fallback_response.output_tokens
        if fallback_response.text.strip():
            extracted_chunks.append(fallback_response.text.strip())

    components.append(
        _finish_component(
            stage3_component,
            status="success",
            input_tokens=stage3_in_tokens,
            output_tokens=stage3_out_tokens,
            details={
                "extracted_chunk_count": len(extracted_chunks),
                "fallback_used": len(branch_to_subtypes) == 0,
            },
        )
    )

    stage4_component = _start_component("hierarchical_turtle_assembly")
    assembly_response = generate_text_component(
        prompt=_build_assembly_prompt(base_prompt, extracted_chunks, detected_branches),
        llm=payload.llm,
        temperature=payload.temperature,
    )
    assembled_turtle = assembly_response.text.strip()
    components.append(
        _finish_component(
            stage4_component,
            status="success",
            input_tokens=assembly_response.input_tokens,
            output_tokens=assembly_response.output_tokens,
            details={
                "detected_branch_count": len(detected_branches),
                "assembled_chars": len(assembled_turtle),
            },
        )
    )

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
        predicted_triples = parse_turtle_to_normalized_triples(assembled_turtle)
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

    total_input_tokens = (
        stage1_response.input_tokens
        + stage2_in_tokens
        + stage3_in_tokens
        + assembly_response.input_tokens
    )
    total_output_tokens = (
        stage1_response.output_tokens
        + stage2_out_tokens
        + stage3_out_tokens
        + assembly_response.output_tokens
    )

    result = ExperimentResult(
        expected_value=payload.expected_value,
        extracted_value=extracted_value,
        is_match=is_match,
        confidence=metrics["f1"],
        full_prompt=base_prompt,
        full_output=assembled_turtle,
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
