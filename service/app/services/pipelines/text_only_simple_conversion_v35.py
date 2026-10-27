"""Text-only conversion pipeline v35: lean compliance-routed single-pass extraction.

Design intent
-------------
v35 is a deliberate consolidation iteration. It is built on the **proven** strengths
of the text-only family (v9 prompt simplicity and v25 compliance-routing prefilter)
and **explicitly removes** the layers that correlated with the v29-v34 regressions:

Preserved (proven gains):
  - v18 structured chunking + hybrid lexical/numeric ranker
  - v24 numeric normalization (units, EI/REI synonyms via v25 wrapper)
  - v25 compliance-routing prefilter (requirement-first reweighting) -- the
    single largest text-only gain in the family
  - v9 discipline: build one prompt -> one LLM call -> parse -> match

Removed (correlated with regressions):
  - v26 semantic verifier hard gate
  - v20/v24 evidence consistency hard gate
  - corrective retry loops with adaptive replanning
  - v29 IR compiler (catastrophic 0% collapse on real PDFs)
  - v30 object-model bridge (compounded v29 failure regime)
  - v31 constraint voter, v32 scenario ensembles, v33 graph/triple expansion,
    v34 calibration sandbox (all unproven or not converged on the gemma-3-27b-it
    baseline used for production runs)

Rationale: Dashboard snapshot shows v25/v26 plateauing at the top of the
RAG-based text-only lineage and every subsequent iteration either flat
or regressed. v35 keeps the proven retrieval reweighting, drops every
gate/retry that can suppress a correct candidate, and trusts the LLM to
extract in one pass with the cleanest possible evidence window.
"""

from __future__ import annotations

from pathlib import Path

from app.models import ComponentLog, ExperimentRequest, ExperimentResponse, ExperimentResult
from app.services.components.hybrid_context_ranker import rank_document_chunks
from app.services.components.llm_client_component import generate_text_component
from app.services.components.output_parser_component import parse_extracted_value
from app.services.components.prompt_builder_v5 import (
    build_conditions_block,
    build_conditions_block_de,
    build_prompt_v5,
)
from app.services.components.result_matcher_component import evaluate_match
from app.services.components.retrieval_enhancer_v25_text import (
    build_multi_query_variants_v25,
    normalize_numeric_value_for_payload_v25,
    select_consistent_diverse_chunks_v25,
)
from app.services.components.structured_document_chunker import build_structured_document_chunks
from app.services.pdf_text_extractor import extract_text_from_pdfs
from app.services.pipelines.text_only_simple_conversion_v21 import (
    _extract_text_from_marker_markdown_v21,
    _finish_component,
    _now_iso,
    _render_selected_context,
    _resolve_document_source,
    _resolve_int_extra,
    _start_component,
)
from app.services.prompt_loader import load_prompt_template


def run_text_only_simple_conversion_v35(payload: ExperimentRequest) -> ExperimentResponse:
    pipeline_started_at = _now_iso()
    components: list[ComponentLog] = []

    # 1) Prompt template
    prompt_component = _start_component("prompt_loader")
    template = load_prompt_template(payload.prompt)
    components.append(
        _finish_component(prompt_component, status="success", details={"prompt_name": payload.prompt})
    )

    # 2) Document source resolution (pdf default, marker if requested)
    source_component = _start_component("document_source_resolver")
    preferred_source = _resolve_document_source(payload)
    try:
        if preferred_source == "marker":
            docs_text, used_documents = _extract_text_from_marker_markdown_v21(
                payload.approval_links, Path("."), payload
            )
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

    # 3) Chunk + rank
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

    # 4) Query expansion (v25 / v24 family)
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

    # 5) Compliance-routed diverse chunk selection (v25 prefilter).
    #    We deliberately ignore the consistency/contradiction metadata as a gate
    #    and use the routed top-K chunks directly. This is the key difference
    #    from v25/v26.
    top_k = _resolve_int_extra(payload, "top_k_chunks", default=5, minimum=1)
    max_per_document = _resolve_int_extra(payload, "diversity_max_per_document", default=2, minimum=1)
    max_per_heading = _resolve_int_extra(payload, "diversity_max_per_heading", default=1, minimum=1)
    minimum_query_length = _resolve_int_extra(payload, "minimum_query_length", default=4, minimum=2)

    diversity_component = _start_component("compliance_routed_chunk_selector_v35")
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
                "selected_chunk_ids": [item.chunk.chunk_id for item in selected_chunks],
                "average_evidence_score": selection["average_evidence_score"],
                "route_focus": selection["route_focus"],
                "route_anchor_count": selection["route_anchor_count"],
                "route_boosted_chunk_ids": selection["route_boosted_chunk_ids"],
                "route_penalized_chunk_ids": selection["route_penalized_chunk_ids"],
                "gates_disabled": ["consistency_gate", "verifier_gate", "corrective_retry"],
                "design_intent": "lean_v9_simplicity_with_v25_routing",
            },
        )
    )

    # 6) Prompt build
    conditions_text_raw, conditions_count = build_conditions_block(payload.conditions)
    conditions_text_de, _ = build_conditions_block_de(payload.conditions)
    selected_context = _render_selected_context(selected_chunks, selection["chunk_evidence"])
    full_prompt = build_prompt_v5(
        template=template,
        system=payload.system,
        system_name=payload.system_name,
        value=payload.value,
        conditions=payload.conditions,
        docs_text=selected_context,
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
            },
        )
    )

    # 7) Single LLM call (no retries, no ensembles)
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
                    "single_pass": True,
                    "design_intent": "no_retry_no_ensemble_no_gate",
                },
                input_tokens=llm_response.input_tokens,
                output_tokens=llm_response.output_tokens,
            )
        )
    except Exception as exc:
        components.append(_finish_component(llm_component, status="error", error=str(exc)))
        raise RuntimeError(f"LLM generation failed: {exc}") from exc

    # 8) Parse + soft numeric normalization
    parser_component = _start_component("output_parser")
    try:
        candidate_value = parse_extracted_value(llm_response.text)
    except Exception as exc:
        components.append(_finish_component(parser_component, status="error", error=str(exc)))
        raise RuntimeError(f"Output parsing failed: {exc}") from exc
    extracted_value = normalize_numeric_value_for_payload_v25(
        candidate_value, payload, source_text=llm_response.text
    )
    components.append(
        _finish_component(
            parser_component,
            status="success",
            details={
                "raw_candidate": candidate_value,
                "normalized_value": extracted_value,
                "normalization": "v24_unit_and_synonym_normalization",
            },
        )
    )

    # 9) Match
    normalized_expected = payload.expected_value
    if isinstance(payload.expected_value, (int, float)):
        normalized_expected = normalize_numeric_value_for_payload_v25(payload.expected_value, payload)
    is_match = evaluate_match(extracted_value, normalized_expected)

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
