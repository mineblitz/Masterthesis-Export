"""Text-only conversion pipeline v34 with calibrated soft validation.

v34 extends v33 with:
- calibration profiles by variable family
- exception-aware soft adjudication
- non-blocking semantic validation penalties

All adjustments are bounded and never hard-reject by themselves.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.models import ComponentLog, ExperimentRequest, ExperimentResponse, ExperimentResult
from app.services.components.calibration_profile_v34 import apply_calibration_profile_v34
from app.services.components.exception_adjudicator_v34_clean import adjudicate_exceptions_v34
from app.services.components.hybrid_context_ranker import rank_document_chunks
from app.services.components.llm_client_component import generate_text_component
from app.services.components.output_parser_component import parse_extracted_value
from app.services.components.prompt_builder_v5 import build_conditions_block, build_conditions_block_de, build_prompt_v5
from app.services.components.retrieval_enhancer_v29_text import (
    build_multi_query_variants_v29,
    normalize_numeric_value_for_payload_v29,
    select_consistent_diverse_chunks_v29,
)
from app.services.components.retrieval_quality_component import assess_retrieval_quality
from app.services.components.result_matcher_component import evaluate_match
from app.services.components.scenario_ensemble_resolver_v32 import resolve_value_with_scenario_ensemble_v32
from app.services.components.semantic_validation_sandbox_v34 import run_semantic_validation_sandbox_v34
from app.services.components.structured_document_chunker import build_structured_document_chunks
from app.services.components.triple_extractor_v33 import TripleExtractorV33
from app.services.components.graph_neighborhood_retriever_v33 import GraphNeighborhoodRetrieverV33
from app.services.components.hybrid_chunk_aggregator_v33 import HybridChunkAggregatorV33
from app.services.pdf_text_extractor import extract_text_from_pdfs
from app.services.pipelines.text_only_simple_conversion_v21 import (
    _extract_text_from_marker_markdown_v21,
    _finish_component,
    _now_iso,
    _render_selected_context,
    _resolve_document_source,
    _resolve_float_extra,
    _resolve_int_extra,
    _resolve_bool_extra,
    _start_component,
)
from app.services.prompt_loader import load_prompt_template


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def run_text_only_simple_conversion_v34(payload: ExperimentRequest) -> ExperimentResponse:
    pipeline_started_at = _now_iso()
    components: list[ComponentLog] = []

    prompt_component = _start_component("prompt_loader")
    template = load_prompt_template(payload.prompt)
    components.append(_finish_component(prompt_component, status="success", details={"prompt_name": payload.prompt}))

    source_component = _start_component("document_source_resolver")
    preferred_source = _resolve_document_source(payload)
    try:
        if preferred_source == "marker":
            docs_text, used_documents = _extract_text_from_marker_markdown_v21(payload.approval_links, Path("."), payload)
            actual_source = "marker_markdown_cleaned"
        else:
            docs_text, used_documents = extract_text_from_pdfs(payload.approval_links, Path("."))
            actual_source = "pdf_full_text"
        components.append(
            _finish_component(
                source_component,
                status="success",
                details={
                    "preferred_source": preferred_source,
                    "actual_source": actual_source,
                    "document_count": len(used_documents),
                },
            )
        )
    except Exception as exc:
        if preferred_source == "marker":
            try:
                docs_text, used_documents = extract_text_from_pdfs(payload.approval_links, Path("."))
                components.append(
                    _finish_component(
                        source_component,
                        status="success",
                        details={
                            "preferred_source": preferred_source,
                            "actual_source": "pdf_full_text_fallback",
                            "document_count": len(used_documents),
                            "fallback_reason": str(exc),
                        },
                    )
                )
            except Exception as nested_exc:
                components.append(_finish_component(source_component, status="error", error=str(nested_exc)))
                raise RuntimeError(f"Document source resolution failed: {nested_exc}") from nested_exc
        else:
            components.append(_finish_component(source_component, status="error", error=str(exc)))
            raise RuntimeError(f"Document source resolution failed: {exc}") from exc

    chunk_component = _start_component("structured_document_chunker")
    chunks = build_structured_document_chunks(docs_text)
    components.append(
        _finish_component(
            chunk_component,
            status="success",
            details={"chunk_count": len(chunks), "document_count": len(used_documents)},
        )
    )

    ranker_component = _start_component("hybrid_context_ranker")
    ranked_chunks, search_terms = rank_document_chunks(
        chunks=chunks,
        payload=payload,
        search_terms=getattr(payload, "search_terms", None),
    )
    components.append(
        _finish_component(
            ranker_component,
            status="success",
            details={"candidate_count": len(ranked_chunks), "search_terms": search_terms},
        )
    )

    query_component = _start_component("multi_query_expander")
    query_limit = _resolve_int_extra(payload, "query_expansion_limit", default=10, minimum=2)
    query_variants = build_multi_query_variants_v29(
        payload=payload,
        base_search_terms=search_terms,
        query_limit=query_limit,
    )
    components.append(
        _finish_component(
            query_component,
            status="success",
            details={"query_count": len(query_variants), "queries": query_variants},
        )
    )

    top_k = _resolve_int_extra(payload, "top_k_chunks", default=5, minimum=1)
    max_per_document = _resolve_int_extra(payload, "diversity_max_per_document", default=2, minimum=1)
    max_per_heading = _resolve_int_extra(payload, "diversity_max_per_heading", default=1, minimum=1)
    minimum_query_length = _resolve_int_extra(payload, "minimum_query_length", default=4, minimum=2)

    diversity_component = _start_component("retrieval_diversity_selector")
    selection = select_consistent_diverse_chunks_v29(
        ranked_chunks=ranked_chunks,
        top_k=top_k,
        max_per_document=max_per_document,
        max_per_heading=max_per_heading,
        payload=payload,
        query_variants=query_variants,
        minimum_query_length=minimum_query_length,
        rerank_strategy="balanced",
    )
    selected_chunks = selection["selected_chunks"]
    components.append(
        _finish_component(
            diversity_component,
            status="success",
            details={
                "top_k": top_k,
                "selected_chunk_ids": [item.chunk.chunk_id for item in selected_chunks],
                "average_evidence_score": selection["average_evidence_score"],
                "contradiction_hit_count": selection["contradiction_hit_count"],
                "clause_type_distribution": selection["clause_type_distribution"],
            },
        )
    )

    hybrid_rag_enabled = _resolve_bool_extra(payload, "hybrid_rag_enabled", default=False)
    if hybrid_rag_enabled:
        triple_extraction_component = _start_component("triple_extraction_v33")
        triple_confidence_threshold = _resolve_float_extra(
            payload, "triple_extraction_confidence_threshold", default=0.3, minimum=0.0, maximum=1.0
        )
        extractor = TripleExtractorV33(confidence_threshold=triple_confidence_threshold)
        chunks_for_extraction = [item.chunk for item in selected_chunks]
        extraction_result = extractor.extract(chunks_for_extraction)
        components.append(
            _finish_component(
                triple_extraction_component,
                status="success",
                details={
                    "triple_count": len(extraction_result.triples),
                    "entity_count": len(extraction_result.entity_set),
                    "confidence_threshold": triple_confidence_threshold,
                    "extraction_time_ms": extraction_result.extraction_time_ms,
                },
            )
        )

        neighborhood_component = _start_component("neighborhood_expansion_v33")
        entity_expansion_alpha = _resolve_float_extra(
            payload, "entity_expansion_alpha", default=0.5, minimum=0.1, maximum=2.0
        )
        retriever = GraphNeighborhoodRetrieverV33(expansion_alpha=entity_expansion_alpha)

        condition_keywords = set()
        if payload.conditions:
            for condition in payload.conditions:
                condition_keywords.update(str(condition).lower().split())

        expansion_result = retriever.expand(
            entity_set=extraction_result.entity_set,
            selected_chunks=selected_chunks,
            all_chunks=chunks,
            payload=payload,
            condition_keywords=condition_keywords if condition_keywords else None,
        )
        components.append(
            _finish_component(
                neighborhood_component,
                status="success",
                details={
                    "expansion_count": expansion_result.expansion_count,
                    "average_expansion_score": expansion_result.average_expansion_score,
                    "expansion_alpha": entity_expansion_alpha,
                    "entity_coverage": expansion_result.entity_coverage,
                    "expansion_time_ms": expansion_result.expansion_time_ms,
                },
            )
        )

        aggregation_component = _start_component("hybrid_aggregation_v33")
        neighborhood_discount_factor = _resolve_float_extra(
            payload, "neighborhood_discount_factor", default=0.6, minimum=0.2, maximum=1.0
        )
        max_aggregated_chunks = _resolve_int_extra(
            payload, "max_aggregated_chunks", default=15, minimum=5
        )
        aggregator = HybridChunkAggregatorV33(
            neighborhood_discount_factor=neighborhood_discount_factor,
            max_aggregated_chunks=min(30, max_aggregated_chunks),
        )
        agg_result = aggregator.aggregate(
            selected_chunks=selected_chunks,
            neighborhood_chunks=expansion_result.neighborhood_chunks,
        )
        selected_chunks = agg_result.aggregated_chunks
        components.append(
            _finish_component(
                aggregation_component,
                status="success",
                details={
                    "original_chunk_count": agg_result.original_chunk_count,
                    "expansion_chunk_count": agg_result.expansion_chunk_count,
                    "deduplication_count": agg_result.deduplication_count,
                    "final_chunk_count": len(agg_result.aggregated_chunks),
                    "average_combined_weight": agg_result.average_weight,
                    "weight_distribution": agg_result.weight_distribution,
                    "neighborhood_discount_factor": neighborhood_discount_factor,
                    "aggregation_time_ms": agg_result.aggregation_time_ms,
                },
            )
        )

    retrieval_component = _start_component("retrieval_quality_checker")
    quality_threshold = _resolve_float_extra(
        payload,
        "retrieval_confidence_threshold",
        default=0.58,
        minimum=0.0,
        maximum=1.0,
    )
    quality = assess_retrieval_quality(
        selected_chunks=selected_chunks,
        available_ranked_chunks=ranked_chunks,
        search_terms=query_variants,
        threshold=quality_threshold,
    )
    components.append(
        _finish_component(
            retrieval_component,
            status="success",
            details={
                "quality_score": quality.quality_score,
                "keyword_coverage": quality.keyword_coverage,
                "selected_chunk_count": quality.selected_chunk_count,
                "should_retry": quality.should_retry,
                "reason": quality.reason,
                "hybrid_rag_enabled": hybrid_rag_enabled,
            },
        )
    )

    selected_chunks_for_context = []
    for agg in selected_chunks:
        if hasattr(agg, "chunk"):
            score = getattr(agg, "combined_weight", getattr(agg, "score", 0.0))
            selected_chunks_for_context.append(type("obj", (object,), {"chunk": agg.chunk, "score": score})())
        else:
            selected_chunks_for_context.append(agg)
    selected_context = _render_selected_context(selected_chunks_for_context, selection.get("chunk_evidence", {}))
    full_prompt = build_prompt_v5(
        template=template,
        system=payload.system,
        system_name=payload.system_name,
        value=payload.value,
        conditions=payload.conditions,
        docs_text=selected_context,
    )

    llm_outputs: list[str] = []
    total_input_tokens = 0
    total_output_tokens = 0

    llm_component = _start_component("llm_client")
    llm_candidate: float | None = None
    parse_error: str | None = None
    try:
        llm_response = generate_text_component(prompt=full_prompt, llm=payload.llm, temperature=payload.temperature)
        total_input_tokens += llm_response.input_tokens
        total_output_tokens += llm_response.output_tokens
        llm_outputs.append(llm_response.text)
        try:
            parsed_candidate = parse_extracted_value(llm_response.text)
            llm_candidate = normalize_numeric_value_for_payload_v29(
                parsed_candidate,
                payload,
                source_text=llm_response.text,
            )
        except ValueError as exc:
            parse_error = str(exc)

        components.append(
            _finish_component(
                llm_component,
                status="success",
                details={
                    "model": llm_response.model,
                    "llm_candidate": llm_candidate,
                    "parser_error": parse_error,
                },
                input_tokens=llm_response.input_tokens,
                output_tokens=llm_response.output_tokens,
            )
        )
    except Exception as exc:
        components.append(_finish_component(llm_component, status="error", error=str(exc)))
        raise RuntimeError(f"LLM generation failed: {exc}") from exc

    scenario_component = _start_component("scenario_ensemble_resolver_v32")
    outlier_threshold = _resolve_float_extra(
        payload,
        "scenario_outlier_threshold",
        default=2.9,
        minimum=1.0,
        maximum=6.0,
    )
    agreement_tolerance = _resolve_float_extra(
        payload,
        "scenario_agreement_tolerance",
        default=2.0,
        minimum=0.1,
        maximum=20.0,
    )
    scenario_decision = resolve_value_with_scenario_ensemble_v32(
        payload=payload,
        selected_chunks=selected_chunks,
        clause_type_by_chunk_id=selection.get("clause_type_by_chunk_id", {}),
        chunk_evidence=selection.get("chunk_evidence", {}),
        llm_candidate=llm_candidate,
        modal_candidate=selection.get("modal_numeric_value"),
        outlier_threshold=outlier_threshold,
        agreement_tolerance=agreement_tolerance,
    )
    extracted_value = scenario_decision.selected_value
    components.append(
        _finish_component(
            scenario_component,
            status="success",
            details={
                "decision": scenario_decision.decision,
                "fallback_used": scenario_decision.fallback_used,
                "selected_from": scenario_decision.selected_from,
                "selected_value": scenario_decision.selected_value,
                "confidence": scenario_decision.confidence,
                "agreement_score": scenario_decision.agreement_score,
                "outlier_rejections": scenario_decision.outlier_rejections,
                "selected_scenarios": scenario_decision.selected_scenarios,
                "scenario_candidates": scenario_decision.scenario_candidates,
                "outlier_threshold": outlier_threshold,
                "agreement_tolerance": agreement_tolerance,
            },
        )
    )

    exception_pass_enabled = _resolve_bool_extra(payload, "exception_pass_enabled", default=True)
    contradiction_window_lines = _resolve_int_extra(payload, "contradiction_window_lines", default=2, minimum=1)
    exception_component = _start_component("exception_adjudicator_v34")
    if exception_pass_enabled:
        exception_result = adjudicate_exceptions_v34(
            selected_chunks=selected_chunks,
            extracted_value=extracted_value,
            contradiction_window_lines=contradiction_window_lines,
        )
        components.append(
            _finish_component(
                exception_component,
                status="success",
                details={
                    "exception_hits": exception_result.exception_hits,
                    "override_hits": exception_result.override_hits,
                    "matched_chunk_ids": exception_result.matched_chunk_ids,
                    "exception_penalty": exception_result.exception_penalty,
                    "override_bonus": exception_result.override_bonus,
                    "net_adjustment": exception_result.net_adjustment,
                    "non_blocking": True,
                },
            )
        )
    else:
        exception_result = adjudicate_exceptions_v34(
            selected_chunks=[],
            extracted_value=extracted_value,
            contradiction_window_lines=contradiction_window_lines,
        )
        components.append(
            _finish_component(
                exception_component,
                status="success",
                details={
                    "disabled": True,
                    "net_adjustment": 0.0,
                    "non_blocking": True,
                },
            )
        )

    semantic_penalty_enabled = _resolve_bool_extra(payload, "semantic_penalty_enabled", default=True)
    max_semantic_penalty = _resolve_float_extra(
        payload,
        "max_semantic_penalty",
        default=0.25,
        minimum=0.0,
        maximum=0.6,
    )
    semantic_component = _start_component("semantic_validation_sandbox_v34")
    if semantic_penalty_enabled:
        semantic_result = run_semantic_validation_sandbox_v34(
            value_name=payload.value,
            extracted_value=extracted_value,
            selected_chunks=selected_chunks,
            clause_type_by_chunk_id=selection.get("clause_type_by_chunk_id", {}),
            max_semantic_penalty=max_semantic_penalty,
        )
        components.append(
            _finish_component(
                semantic_component,
                status="success",
                details={
                    "total_penalty": semantic_result.total_penalty,
                    "unit_penalty": semantic_result.unit_penalty,
                    "range_penalty": semantic_result.range_penalty,
                    "contradiction_penalty": semantic_result.contradiction_penalty,
                    "provenance_penalty": semantic_result.provenance_penalty,
                    "unit_compatible": semantic_result.unit_compatible,
                    "range_sane": semantic_result.range_sane,
                    "contradiction_density": semantic_result.contradiction_density,
                    "provenance_completeness": semantic_result.provenance_completeness,
                    "max_semantic_penalty": semantic_result.max_semantic_penalty,
                    "non_blocking": True,
                },
            )
        )
    else:
        semantic_result = run_semantic_validation_sandbox_v34(
            value_name=payload.value,
            extracted_value=extracted_value,
            selected_chunks=selected_chunks,
            clause_type_by_chunk_id=selection.get("clause_type_by_chunk_id", {}),
            max_semantic_penalty=0.0,
        )
        components.append(
            _finish_component(
                semantic_component,
                status="success",
                details={
                    "disabled": True,
                    "total_penalty": 0.0,
                    "non_blocking": True,
                },
            )
        )

    base_confidence = scenario_decision.confidence
    soft_adjusted_confidence = _clamp(base_confidence + exception_result.net_adjustment - semantic_result.total_penalty * 0.85)
    soft_acceptance = _clamp(base_confidence + exception_result.net_adjustment - semantic_result.total_penalty)

    calibration_enabled = _resolve_bool_extra(payload, "calibration_enabled", default=True)
    calibration_profile_name = str((payload.model_extra or {}).get("calibration_profile_name", "default"))
    ab_mode = str((payload.model_extra or {}).get("ab_mode", "v34_calibrated"))

    calibration_component = _start_component("calibration_profile_v34")
    if calibration_enabled:
        calibration = apply_calibration_profile_v34(
            base_confidence=soft_adjusted_confidence,
            acceptance_score=soft_acceptance,
            value_name=payload.value,
            profile_name=calibration_profile_name,
            ab_mode=ab_mode,
        )
        final_confidence = calibration.calibrated_confidence
        final_acceptance = calibration.calibrated_acceptance
        components.append(
            _finish_component(
                calibration_component,
                status="success",
                details={
                    "profile_name": calibration.profile_name,
                    "variable_family": calibration.variable_family,
                    "confidence_shift": calibration.confidence_shift,
                    "acceptance_shift": calibration.acceptance_shift,
                    "calibrated_confidence": calibration.calibrated_confidence,
                    "calibrated_acceptance": calibration.calibrated_acceptance,
                    "ab_mode": calibration.ab_mode,
                    "non_blocking": True,
                },
            )
        )
    else:
        final_confidence = round(soft_adjusted_confidence, 4)
        final_acceptance = round(soft_acceptance, 4)
        components.append(
            _finish_component(
                calibration_component,
                status="success",
                details={
                    "disabled": True,
                    "calibrated_confidence": final_confidence,
                    "calibrated_acceptance": final_acceptance,
                    "ab_mode": ab_mode,
                    "non_blocking": True,
                },
            )
        )

    fallback_margin_threshold = _resolve_float_extra(
        payload,
        "fallback_margin_threshold",
        default=0.1,
        minimum=0.0,
        maximum=0.5,
    )
    bounded_fallback_used = False
    if final_acceptance < fallback_margin_threshold and extracted_value is not None:
        bounded_fallback_used = True
        final_confidence = round(max(final_confidence, 0.18), 4)

    parser_component = _start_component("output_parser")
    components.append(
        _finish_component(
            parser_component,
            status="success",
            details={
                "parsed": extracted_value is not None,
                "llm_candidate": llm_candidate,
                "selected_value": extracted_value,
                "selection_decision": scenario_decision.decision,
                "final_acceptance": final_acceptance,
                "bounded_fallback_used": bounded_fallback_used,
            },
        )
    )

    prompt_builder_component = _start_component("prompt_builder_v5")
    conditions_text_raw, conditions_count = build_conditions_block(payload.conditions)
    conditions_text_de, _ = build_conditions_block_de(payload.conditions)
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
                "hybrid_rag_enabled": hybrid_rag_enabled,
                "ab_mode": ab_mode,
            },
        )
    )

    normalized_expected = payload.expected_value
    if isinstance(payload.expected_value, (int, float)):
        normalized_expected = normalize_numeric_value_for_payload_v29(payload.expected_value, payload)

    is_match = evaluate_match(extracted_value, normalized_expected)

    final_output: dict[str, Any] = {
        "llm_output": llm_outputs[-1] if llm_outputs else "",
        "scenario_decision": {
            "decision": scenario_decision.decision,
            "selected_value": scenario_decision.selected_value,
            "confidence": scenario_decision.confidence,
            "fallback_used": scenario_decision.fallback_used,
            "selected_from": scenario_decision.selected_from,
            "agreement_score": scenario_decision.agreement_score,
            "outlier_rejections": scenario_decision.outlier_rejections,
            "selected_scenarios": scenario_decision.selected_scenarios,
        },
        "soft_validation_v34": {
            "exception_net_adjustment": exception_result.net_adjustment,
            "semantic_penalty": semantic_result.total_penalty,
            "final_acceptance": final_acceptance,
            "bounded_fallback_used": bounded_fallback_used,
        },
        "hybrid_rag": {
            "enabled": hybrid_rag_enabled,
        },
    }

    result = ExperimentResult(
        expected_value=payload.expected_value,
        extracted_value=extracted_value,
        is_match=is_match,
        confidence=final_confidence,
        full_prompt=full_prompt,
        full_output=json.dumps(final_output, ensure_ascii=True),
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
    return ExperimentResponse(status="success", experiment_id=payload.experiment_id, pipeline=payload.pipeline, result=result)
