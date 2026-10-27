"""KG comprehensive schema extraction pipeline v4 with rdflib-backed canonicalization and scoring.

New pipeline that replaces:
- Inline regex canonicalization (kg_comprehensive_schema_minimal_turtle_v3) with
  rdf_canonicalizer.canonicalize_turtle (rdflib round-trip).
- Custom Turtle parser + set scorer (turtle_triple_scorer_component) with
  rdf_turtle_parser + rdf_turtle_scorer (rdflib N-Triples serialization).
- Optional: pyshacl structural validation gate.

All other stages (schema extension merge, PDF extraction, hierarchical LLM extraction,
assembly) are carried over from v3 unchanged. Compare against v3 for A/B benchmarking.
"""

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
from app.services.components.rdf_canonicalizer import canonicalize_turtle
from app.services.components.rdf_turtle_parser import parse_turtle, parse_turtle_to_triple_set
from app.services.components.rdf_turtle_scorer import score_graphs, validate_with_shacl
from app.services.components.turtle_triple_scorer_component import classify_triple_errors
from app.services.prompt_loader import load_prompt_template

# Reuse all prompt builder helpers from v3 (unchanged)
from app.services.pipelines.kg_comprehensive_schema_minimal_turtle_v3 import (
    _build_assembly_prompt,
    _build_base_prompt,
    _build_fallback_extraction_prompt,
    _build_presence_prompt,
    _build_subtype_prompt,
    _build_value_extraction_prompt,
    _merge_schema_with_extension,
)


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


def run_kg_comprehensive_schema_minimal_turtle_v4(
    payload: ExperimentRequest,
) -> ExperimentResponse:
    """Pipeline v4: hierarchical KG extraction with rdflib canonicalization and scoring.

    Stages:
    1. Schema extension merge (same as v3).
    2. PDF text extraction (same as v3).
    3. Hierarchical presence detection (same as v3).
    4. Subtype detection (same as v3).
    5. Value/detail extraction (same as v3).
    6. Turtle assembly (same as v3).
    7. rdflib canonicalization — replaces regex canonicalization from v3.
    8. rdflib scoring — replaces custom triple parser + set scorer from v3.
    9. Optional SHACL validation gate (new in v4).
    """
    pipeline_started_at = _now_iso()
    components: list[ComponentLog] = []

    input_kg_schema_ttl = str(_get_extra(payload, "input_kg_schema_ttl", "")).strip()
    schema_extension_ttl = str(_get_extra(payload, "schema_extension_ttl", "")).strip()
    expected_turtle_filled = str(_get_extra(payload, "expected_turtle_filled", "")).strip()
    shacl_shapes_ttl = str(_get_extra(payload, "shacl_shapes_ttl", "")).strip()
    run_shacl = bool(_get_extra(payload, "run_shacl_validation", False))

    if not input_kg_schema_ttl:
        raise ValueError("input_kg_schema_ttl is required for comprehensive KG pipeline")
    if not expected_turtle_filled:
        raise ValueError("expected_turtle_filled is required for comprehensive KG pipeline")

    # ---- Stage 1: schema extension merge (identical to v3) ----
    schema_extension_component = _start_component("schema_extension_v4")
    merged_schema_ttl = _merge_schema_with_extension(input_kg_schema_ttl, schema_extension_ttl)
    components.append(
        _finish_component(
            schema_extension_component,
            status="success",
            details={
                "base_schema_chars": len(input_kg_schema_ttl),
                "extension_schema_chars": len(schema_extension_ttl),
                "merged_schema_chars": len(merged_schema_ttl),
                "schema_extension_applied": bool(schema_extension_ttl),
            },
        )
    )

    # ---- Stage 2: prompt loader ----
    prompt_component = _start_component("prompt_loader")
    template = load_prompt_template(payload.prompt)
    components.append(_finish_component(prompt_component, status="success", details={"prompt_name": payload.prompt}))

    # ---- Stage 3: PDF extraction ----
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
        components.append(_finish_component(pdf_component, status="error", error=str(exc)))
        raise RuntimeError(f"PDF extraction failed: {exc}") from exc

    # ---- Build base prompt ----
    base_prompt_component = _start_component("prompt_builder_comprehensive_kg_hierarchical_v4")
    base_prompt = _build_base_prompt(
        template=template,
        payload=payload,
        input_kg_schema_ttl=merged_schema_ttl,
        docs_text=docs_text,
    )
    components.append(
        _finish_component(
            base_prompt_component,
            status="success",
            details={"prompt_length": len(base_prompt), "schema_chars": len(merged_schema_ttl)},
        )
    )

    # ---- Stage 4: candidate branch detection ----
    candidates_component = _start_component("hierarchical_candidate_extractor")
    candidate_branches = extract_schema_top_level_branches(merged_schema_ttl, max_branches=12)
    components.append(
        _finish_component(
            candidates_component,
            status="success",
            details={"candidate_branch_count": len(candidate_branches), "candidate_branches": candidate_branches},
        )
    )

    # ---- Stage 5: presence detection ----
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

    # ---- Stage 6: subtype detection ----
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
            },
        )
    )

    # ---- Stage 7: value/detail extraction ----
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
            details={"extracted_chunk_count": len(extracted_chunks), "fallback_used": not bool(branch_to_subtypes)},
        )
    )

    # ---- Stage 8: Turtle assembly ----
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
            details={"assembled_chars": len(assembled_turtle)},
        )
    )

    # ---- Stage 9: rdflib canonicalization (replaces regex v3 approach) ----
    canonicalization_component = _start_component("rdf_canonicalization_v4")
    try:
        canonical_turtle, canonicalization_stats = canonicalize_turtle(assembled_turtle, merged_schema_ttl)
        components.append(
            _finish_component(
                canonicalization_component,
                status="success",
                details={**canonicalization_stats, "canonical_turtle_chars": len(canonical_turtle), "method": "rdflib_roundtrip"},
            )
        )
    except (ImportError, ValueError) as exc:
        # On parse failure fall back to raw assembled turtle for scoring
        canonical_turtle = assembled_turtle
        components.append(
            _finish_component(
                canonicalization_component,
                status="error",
                details={"fallback_to_raw": True},
                error=str(exc),
            )
        )

    # ---- Stage 10: optional SHACL validation (new in v4) ----
    shacl_result: dict[str, Any] = {"run": False}
    if run_shacl and shacl_shapes_ttl:
        shacl_component = _start_component("shacl_validation_v4")
        try:
            predicted_graph = parse_turtle(canonical_turtle)
            shapes_graph = parse_turtle(shacl_shapes_ttl)
            shacl_result = {**validate_with_shacl(predicted_graph, shapes_graph), "run": True}
            components.append(
                _finish_component(
                    shacl_component,
                    status="success",
                    details=shacl_result,
                )
            )
        except Exception as exc:
            shacl_result = {"run": True, "error": str(exc)}
            components.append(_finish_component(shacl_component, status="error", error=str(exc)))

    # ---- Stage 11: rdflib scoring (replaces custom triple parser + scorer) ----
    scoring_component = _start_component("rdf_triple_scorer_v4")
    syntax_failure = False
    syntax_error: str | None = None

    try:
        expected_graph = parse_turtle(expected_turtle_filled)
    except Exception as exc:
        components.append(_finish_component(scoring_component, status="error", error=f"Expected turtle parse failed: {exc}"))
        raise RuntimeError(f"Expected turtle parse failed: {exc}") from exc

    try:
        predicted_graph = parse_turtle(canonical_turtle)
        metrics = score_graphs(predicted_graph, expected_graph)
        # Use classify_triple_errors from existing component for detailed diagnostics
        predicted_triples = parse_turtle_to_triple_set(canonical_turtle)
        expected_triples = parse_turtle_to_triple_set(expected_turtle_filled)
        errors = classify_triple_errors(predicted_triples, expected_triples)
    except Exception as exc:
        syntax_failure = True
        syntax_error = str(exc)
        expected_count = len(expected_graph) if expected_graph else 0
        metrics = {
            "predicted_triples": 0,
            "expected_triples": expected_count,
            "correct_triples": 0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
        }
        errors = {
            "missing_triples_count": expected_count,
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
                "scorer": "rdflib_ntriples",
                "shacl": shacl_result,
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
        full_output=canonical_turtle,
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
