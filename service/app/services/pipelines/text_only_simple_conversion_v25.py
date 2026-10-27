"""Text-only conversion pipeline v25 with compliance-routing prefilter."""

from pathlib import Path
from typing import Any

from app.models import ComponentLog, ExperimentRequest, ExperimentResponse, ExperimentResult
from app.services.components.context_expander import expand_ranked_chunks
from app.services.components.hybrid_context_ranker import rank_document_chunks
from app.services.components.llm_client_component import generate_text_component
from app.services.components.output_parser_component import parse_extracted_value
from app.services.components.prompt_builder_v5 import (
    build_conditions_block,
    build_conditions_block_de,
    build_prompt_v5,
)
from app.services.components.retrieval_enhancer_v25_text import (
    build_multi_query_variants_v25,
    choose_adaptive_retry_plan_v25,
    normalize_numeric_value_for_payload_v25,
    select_consistent_diverse_chunks_v25,
)
from app.services.components.retrieval_quality_component import assess_retrieval_quality
from app.services.components.result_matcher_component import evaluate_match
from app.services.components.structured_document_chunker import build_structured_document_chunks
from app.services.pipelines.text_only_simple_conversion_v21 import (
    _derive_retry_reason,
    _extract_text_from_marker_markdown_v21,
    _finish_component,
    _now_iso,
    _render_selected_context,
    _resolve_bool_extra,
    _resolve_document_source,
    _resolve_float_extra,
    _resolve_int_extra,
    _start_component,
    _value_family_defaults,
)
from app.services.pdf_text_extractor import extract_text_from_pdfs
from app.services.prompt_loader import load_prompt_template


def run_text_only_simple_conversion_v25(payload: ExperimentRequest) -> ExperimentResponse:
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
            details={
                "candidate_count": len(ranked_chunks),
                "search_terms": search_terms,
            },
        )
    )

    query_component = _start_component("multi_query_expander")
    query_limit = _resolve_int_extra(payload, "query_expansion_limit", default=10, minimum=2)
    query_variants = build_multi_query_variants_v25(
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

    top_k = _resolve_int_extra(payload, "top_k_chunks", default=3, minimum=1)
    max_per_document = _resolve_int_extra(payload, "diversity_max_per_document", default=2, minimum=1)
    max_per_heading = _resolve_int_extra(payload, "diversity_max_per_heading", default=1, minimum=1)
    minimum_query_length = _resolve_int_extra(payload, "minimum_query_length", default=4, minimum=2)

    diversity_component = _start_component("retrieval_diversity_selector")
    selection = select_consistent_diverse_chunks_v25(
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
                "diversity_max_per_document": max_per_document,
                "diversity_max_per_heading": max_per_heading,
                "minimum_query_length": minimum_query_length,
                "selected_chunk_ids": [item.chunk.chunk_id for item in selected_chunks],
                "average_evidence_score": selection["average_evidence_score"],
                "contradiction_hit_count": selection["contradiction_hit_count"],
                "skipped_for_document_cap": selection["skipped_for_document_cap"],
                "skipped_for_heading_cap": selection["skipped_for_heading_cap"],
                "skipped_for_redundancy": selection["skipped_for_redundancy"],
                "marker_noise_mitigation": "line_filter_and_score_penalty_v23",
                "adaptive_consistency": "enabled_v24",
                "compliance_routing_prefilter": "enabled_v25",
                "route_focus": selection["route_focus"],
                "route_anchor_count": selection["route_anchor_count"],
                "route_boosted_chunk_ids": selection["route_boosted_chunk_ids"],
                "route_penalized_chunk_ids": selection["route_penalized_chunk_ids"],
            },
        )
    )

    default_quality, default_evidence, default_consistency = _value_family_defaults(payload)

    retrieval_component = _start_component("retrieval_quality_checker")
    retry_threshold = _resolve_float_extra(
        payload,
        "retrieval_confidence_threshold",
        default=default_quality,
        minimum=0.0,
        maximum=1.0,
    )
    quality = assess_retrieval_quality(
        selected_chunks=selected_chunks,
        available_ranked_chunks=ranked_chunks,
        search_terms=query_variants,
        threshold=retry_threshold,
    )
    evidence_threshold = _resolve_float_extra(
        payload,
        "evidence_score_threshold",
        default=default_evidence,
        minimum=0.0,
        maximum=1.0,
    )
    evidence_low = selection["average_evidence_score"] < evidence_threshold

    consistency_component = _start_component("evidence_consistency_checker_v25")
    consistency_threshold = _resolve_float_extra(
        payload,
        "evidence_consistency_threshold",
        default=default_consistency,
        minimum=0.0,
        maximum=1.0,
    )
    consistency_score = selection["evidence_consistency_score"]
    should_accept_modal = selection["should_accept_modal"]
    consistency_low = consistency_score < consistency_threshold

    components.append(
        _finish_component(
            consistency_component,
            status="success",
            details={
                "consistency_score": consistency_score,
                "consistency_threshold": consistency_threshold,
                "consistency_below_threshold": consistency_low,
                "modal_numeric_value": selection["modal_numeric_value"],
                "modal_candidate_frequency": selection["modal_candidate_frequency"],
                "is_multi_valued_variable": selection["is_multi_valued_variable"],
                "should_accept_modal": should_accept_modal,
                "conflicting_numeric_candidates": selection["conflicting_numeric_candidates"],
                "numeric_normalization": "enabled_v24_adaptive",
                "adaptive_gating_strategy": "modal_acceptance_for_multivalued",
                "compliance_routing_prefilter": "enabled_v25",
                "route_focus": selection["route_focus"],
            },
        )
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
                "average_evidence_score": selection["average_evidence_score"],
                "evidence_threshold": evidence_threshold,
                "evidence_below_threshold": evidence_low,
                "marker_noise_mitigation": "enabled_v23",
                "adaptive_consistency": "enabled_v24",
                "compliance_routing_prefilter": "enabled_v25",
            },
        )
    )

    conditions_text_raw, conditions_count = build_conditions_block(payload.conditions)
    conditions_text_de, _ = build_conditions_block_de(payload.conditions)

    llm_outputs: list[str] = []
    total_input_tokens = 0
    total_output_tokens = 0
    extracted_value: float | None = None
    selected_context = _render_selected_context(selected_chunks, selection["chunk_evidence"])
    full_prompt = build_prompt_v5(
        template=template,
        system=payload.system,
        system_name=payload.system_name,
        value=payload.value,
        conditions=payload.conditions,
        docs_text=selected_context,
    )
    fallback_stage = "initial"

    attempt_number = 1
    llm_component = _start_component("llm_client")
    try:
        llm_response = generate_text_component(prompt=full_prompt, llm=payload.llm, temperature=payload.temperature)
        total_input_tokens += llm_response.input_tokens
        total_output_tokens += llm_response.output_tokens
        llm_outputs.append(f"### Attempt {attempt_number}\n{llm_response.text}")
        candidate_value = parse_extracted_value(llm_response.text)
        normalized_candidate = normalize_numeric_value_for_payload_v25(candidate_value, payload, source_text=llm_response.text)

        gating_decision = (normalized_candidate is not None) and (not consistency_low or should_accept_modal)
        if gating_decision:
            extracted_value = normalized_candidate

        components.append(
            _finish_component(
                llm_component,
                status="success",
                details={
                    "model": llm_response.model,
                    "attempt": attempt_number,
                    "fallback_stage": fallback_stage,
                    "consistency_gate_blocked": normalized_candidate is not None and consistency_low and not should_accept_modal,
                    "adaptive_modal_accepted": normalized_candidate is not None and should_accept_modal,
                    "numeric_normalization": "enabled_v24_adaptive",
                    "compliance_routing_prefilter": "enabled_v25",
                },
                input_tokens=llm_response.input_tokens,
                output_tokens=llm_response.output_tokens,
            )
        )
    except Exception as exc:
        components.append(_finish_component(llm_component, status="error", error=str(exc)))
        raise RuntimeError(f"LLM generation failed: {exc}") from exc

    retry_events: list[dict[str, Any]] = []
    enable_retry = _resolve_bool_extra(payload, "enable_corrective_retry", True)
    max_retries = _resolve_int_extra(payload, "max_corrective_retries", default=3, minimum=0)
    narrow_expansion_step = _resolve_int_extra(payload, "narrow_retry_expansion_step", default=1, minimum=1)
    broad_expansion_multiplier = _resolve_int_extra(payload, "broad_retry_multiplier", default=2, minimum=1)
    current_count = len(selected_chunks)

    while enable_retry and len(retry_events) < max_retries:
        extraction_missing = extracted_value is None
        retry_reason = _derive_retry_reason(
            quality_reason=quality.reason,
            extraction_missing=extraction_missing,
            evidence_low=evidence_low,
            consistency_low=consistency_low and not should_accept_modal,
            contradiction_hits=selection["contradiction_hit_count"],
        )
        should_retry = retry_reason != "not_needed" and current_count < len(ranked_chunks)
        if not should_retry:
            break

        retry_index = len(retry_events) + 1
        retry_plan = choose_adaptive_retry_plan_v25(
            retry_index=retry_index,
            top_k=top_k,
            narrow_expansion_step=narrow_expansion_step,
            broad_expansion_multiplier=broad_expansion_multiplier,
        )
        fallback_stage = retry_plan["fallback_stage"]

        expanded_candidates = expand_ranked_chunks(
            ranked_chunks,
            current_count=current_count,
            expansion_step=retry_plan["expansion_step"],
        )
        current_count = len(expanded_candidates)

        selection = select_consistent_diverse_chunks_v25(
            ranked_chunks=expanded_candidates,
            top_k=current_count,
            max_per_document=max_per_document,
            max_per_heading=max_per_heading,
            payload=payload,
            query_variants=query_variants,
            minimum_query_length=minimum_query_length,
            rerank_strategy=retry_plan["rerank_strategy"],
        )
        selected_chunks = selection["selected_chunks"]
        selected_context = _render_selected_context(selected_chunks, selection["chunk_evidence"])
        retry_prompt = build_prompt_v5(
            template=template,
            system=payload.system,
            system_name=payload.system_name,
            value=payload.value,
            conditions=payload.conditions,
            docs_text=selected_context,
        )

        attempt_number += 1
        retry_llm_component = _start_component("llm_client")
        try:
            retry_response = generate_text_component(prompt=retry_prompt, llm=payload.llm, temperature=payload.temperature)
            total_input_tokens += retry_response.input_tokens
            total_output_tokens += retry_response.output_tokens
            llm_outputs.append(f"### Attempt {attempt_number}\n{retry_response.text}")
            retry_candidate = parse_extracted_value(retry_response.text)
            normalized_retry_candidate = normalize_numeric_value_for_payload_v25(
                retry_candidate,
                payload,
                source_text=retry_response.text,
            )

            retry_consistency_score = selection["evidence_consistency_score"]
            retry_should_accept_modal = selection["should_accept_modal"]
            retry_consistency_low = retry_consistency_score < consistency_threshold
            retry_gating_decision = (normalized_retry_candidate is not None) and (not retry_consistency_low or retry_should_accept_modal)
            if retry_gating_decision:
                extracted_value = normalized_retry_candidate
                full_prompt = retry_prompt

            components.append(
                _finish_component(
                    retry_llm_component,
                    status="success",
                    details={
                        "model": retry_response.model,
                        "attempt": attempt_number,
                        "fallback_stage": fallback_stage,
                        "rerank_strategy": retry_plan["rerank_strategy"],
                        "consistency_gate_blocked": normalized_retry_candidate is not None and retry_consistency_low and not retry_should_accept_modal,
                        "adaptive_modal_accepted": normalized_retry_candidate is not None and retry_should_accept_modal,
                        "numeric_normalization": "enabled_v24_adaptive",
                        "compliance_routing_prefilter": "enabled_v25",
                    },
                    input_tokens=retry_response.input_tokens,
                    output_tokens=retry_response.output_tokens,
                )
            )
        except Exception as exc:
            components.append(_finish_component(retry_llm_component, status="error", error=str(exc)))
            raise RuntimeError(f"Corrective retry failed: {exc}") from exc

        quality = assess_retrieval_quality(
            selected_chunks=selected_chunks,
            available_ranked_chunks=ranked_chunks,
            search_terms=query_variants,
            threshold=retry_threshold,
        )
        evidence_low = selection["average_evidence_score"] < evidence_threshold
        consistency_low = selection["evidence_consistency_score"] < consistency_threshold
        should_accept_modal = selection["should_accept_modal"]

        retry_events.append(
            {
                "attempt": attempt_number,
                "retry_index": retry_index,
                "reason": retry_reason,
                "fallback_stage": fallback_stage,
                "rerank_strategy": retry_plan["rerank_strategy"],
                "expansion_step": retry_plan["expansion_step"],
                "expanded_chunk_count": len(selected_chunks),
                "quality_score": quality.quality_score,
                "average_evidence_score": selection["average_evidence_score"],
                "consistency_score": selection["evidence_consistency_score"],
                "should_accept_modal": should_accept_modal,
                "contradiction_hit_count": selection["contradiction_hit_count"],
                "route_focus": selection["route_focus"],
            }
        )

    retry_component = _start_component("corrective_retry")
    final_reason = _derive_retry_reason(
        quality_reason=quality.reason,
        extraction_missing=extracted_value is None,
        evidence_low=evidence_low,
        consistency_low=consistency_low and not should_accept_modal,
        contradiction_hits=selection["contradiction_hit_count"],
    )
    components.append(
        _finish_component(
            retry_component,
            status="success",
            details={
                "triggered": bool(retry_events),
                "retry_count": len(retry_events),
                "max_corrective_retries": max_retries,
                "retry_events": retry_events,
                "adaptive_strategy": "semantic_and_contradiction_aware_v25",
                "narrow_retry_expansion_step": narrow_expansion_step,
                "broad_retry_multiplier": broad_expansion_multiplier,
                "final_retry_reason_state": final_reason,
                "bounded_stop": len(retry_events) >= max_retries and final_reason != "not_needed",
                "adaptive_consistency_gating": "enabled_v24",
                "compliance_routing_prefilter": "enabled_v25",
            },
        )
    )

    parser_component = _start_component("output_parser")
    components.append(
        _finish_component(
            parser_component,
            status="success",
            details={
                "parsed": extracted_value is not None,
                "numeric_normalization": "enabled_v24_adaptive",
                "compliance_routing_prefilter": "enabled_v25",
            },
        )
    )

    prompt_builder_component = _start_component("prompt_builder_v5")
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
                "fallback_stage": fallback_stage,
                "adaptive_consistency_gating": "enabled_v24",
                "compliance_routing_prefilter": "enabled_v25",
            },
        )
    )

    normalized_expected = payload.expected_value
    if isinstance(payload.expected_value, (int, float)):
        normalized_expected = normalize_numeric_value_for_payload_v25(payload.expected_value, payload)

    is_match = evaluate_match(extracted_value, normalized_expected)
    result = ExperimentResult(
        expected_value=payload.expected_value,
        extracted_value=extracted_value,
        is_match=is_match,
        full_prompt=full_prompt,
        full_output="\n\n".join(llm_outputs),
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