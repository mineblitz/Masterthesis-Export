"""Text-only conversion pipeline v18 with expanded retrieval and bounded corrective retries."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.models import ComponentLog, ExperimentRequest, ExperimentResponse, ExperimentResult
from app.services.components.context_expander import expand_ranked_chunks
from app.services.components.hybrid_context_ranker import rank_document_chunks
from app.services.components.output_parser_component import parse_extracted_value
from app.services.components.prompt_builder_v5 import (
    build_conditions_block,
    build_conditions_block_de,
    build_prompt_v5,
)
from app.services.components.retrieval_enhancer_v18 import (
    build_multi_query_variants,
    select_diverse_chunks,
)
from app.services.components.retrieval_quality_component import assess_retrieval_quality
from app.services.components.result_matcher_component import evaluate_match
from app.services.components.structured_document_chunker import build_structured_document_chunks
from app.services.components.llm_client_component import generate_text_component
from app.services.pdf_text_extractor import extract_text_from_pdfs
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


def _resolve_marker_markdown_path(document_path: str, base_dir: Path) -> tuple[Path, str]:
    source_path = (base_dir / document_path).resolve()
    if source_path.name.lower().endswith("_marker.md"):
        marker_path = source_path
    else:
        marker_path = source_path.with_name(f"{source_path.stem}_marker.md")

    if not marker_path.exists():
        raise FileNotFoundError(f"Marker markdown not found: {marker_path}")

    return marker_path, marker_path.relative_to(base_dir.resolve()).as_posix()


def _extract_text_from_marker_markdown(paths: list[str], base_dir: Path) -> tuple[str, list[str]]:
    chunks: list[str] = []
    resolved_paths: list[str] = []

    for document_path in paths:
        marker_path, relative_marker_path = _resolve_marker_markdown_path(document_path, base_dir)
        cleaned_text = marker_path.read_text(encoding="utf-8")
        chunks.append(f"## Document: {relative_marker_path}\n{cleaned_text}")
        resolved_paths.append(relative_marker_path)

    return "\n\n".join(chunks), resolved_paths


def _resolve_document_source(payload: ExperimentRequest) -> str:
    extras = payload.model_extra or {}
    prefer_marker = extras.get("prefer_marker_markdown", True)
    return "marker" if prefer_marker else "pdf"


def _resolve_int_extra(payload: ExperimentRequest, key: str, default: int, minimum: int) -> int:
    extras = payload.model_extra or {}
    raw = extras.get(key, default)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = default
    return max(minimum, value)


def _resolve_float_extra(
    payload: ExperimentRequest,
    key: str,
    default: float,
    minimum: float,
    maximum: float,
) -> float:
    extras = payload.model_extra or {}
    raw = extras.get(key, default)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


def _resolve_bool_extra(payload: ExperimentRequest, key: str, default: bool) -> bool:
    extras = payload.model_extra or {}
    return bool(extras.get(key, default))


def _render_selected_context(selected_chunks: list[Any], evidence_map: dict[str, float]) -> str:
    blocks: list[str] = []
    for index, ranked in enumerate(selected_chunks, start=1):
        chunk = ranked.chunk
        heading_line = f"Heading: {chunk.heading}\n" if chunk.heading else ""
        evidence = evidence_map.get(chunk.chunk_id, 0.0)
        blocks.append(
            "\n".join(
                [
                    f"## Selected Chunk {index}",
                    f"Document: {chunk.document_path}",
                    f"Lines: {chunk.start_line}-{chunk.end_line}",
                    f"Score: {ranked.score:.2f}",
                    f"Evidence: {evidence:.2f}",
                    heading_line.rstrip(),
                    chunk.text,
                ]
            ).strip()
        )
    return "\n\n".join(blocks)


def _derive_retry_reason(*, quality_reason: str, extraction_missing: bool, evidence_low: bool) -> str:
    reasons: list[str] = []
    if quality_reason == "quality_below_threshold":
        reasons.append("retrieval_quality")
    if extraction_missing:
        reasons.append("null_extraction")
    if evidence_low:
        reasons.append("low_evidence")
    if not reasons:
        return "not_needed"
    return "+".join(reasons)


def run_text_only_simple_conversion_v18(payload: ExperimentRequest) -> ExperimentResponse:
    pipeline_started_at = _now_iso()
    components: list[ComponentLog] = []

    prompt_component = _start_component("prompt_loader")
    template = load_prompt_template(payload.prompt)
    components.append(_finish_component(prompt_component, status="success", details={"prompt_name": payload.prompt}))

    source_component = _start_component("document_source_resolver")
    preferred_source = _resolve_document_source(payload)

    try:
        if preferred_source == "marker":
            docs_text, used_documents = _extract_text_from_marker_markdown(payload.approval_links, Path("."))
            actual_source = "marker_markdown"
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
    query_limit = _resolve_int_extra(payload, "query_expansion_limit", default=6, minimum=2)
    query_variants = build_multi_query_variants(
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

    diversity_component = _start_component("retrieval_diversity_selector")
    diversity = select_diverse_chunks(
        ranked_chunks=ranked_chunks,
        top_k=top_k,
        max_per_document=max_per_document,
        max_per_heading=max_per_heading,
        payload=payload,
        query_variants=query_variants,
    )
    selected_chunks = diversity.selected_chunks
    components.append(
        _finish_component(
            diversity_component,
            status="success",
            details={
                "selected_chunk_count": len(selected_chunks),
                "top_k_chunks": top_k,
                "diversity_max_per_document": max_per_document,
                "diversity_max_per_heading": max_per_heading,
                "selected_chunk_ids": [item.chunk.chunk_id for item in selected_chunks],
                "average_evidence_score": diversity.average_evidence_score,
                "skipped_for_document_cap": diversity.skipped_for_document_cap,
                "skipped_for_heading_cap": diversity.skipped_for_heading_cap,
                "skipped_for_redundancy": diversity.skipped_for_redundancy,
            },
        )
    )

    retrieval_component = _start_component("retrieval_quality_checker")
    retry_threshold = _resolve_float_extra(
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
        threshold=retry_threshold,
    )
    evidence_threshold = _resolve_float_extra(
        payload,
        "evidence_score_threshold",
        default=0.42,
        minimum=0.0,
        maximum=1.0,
    )
    evidence_low = diversity.average_evidence_score < evidence_threshold
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
                "average_evidence_score": diversity.average_evidence_score,
                "evidence_threshold": evidence_threshold,
                "evidence_below_threshold": evidence_low,
            },
        )
    )

    conditions_text_raw, conditions_count = build_conditions_block(payload.conditions)
    conditions_text_de, _ = build_conditions_block_de(payload.conditions)

    llm_outputs: list[str] = []
    total_input_tokens = 0
    total_output_tokens = 0
    extracted_value: float | None = None
    selected_context = _render_selected_context(selected_chunks, diversity.chunk_evidence)
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
        extracted_value = parse_extracted_value(llm_response.text)
        components.append(
            _finish_component(
                llm_component,
                status="success",
                details={"model": llm_response.model, "attempt": attempt_number, "fallback_stage": fallback_stage},
                input_tokens=llm_response.input_tokens,
                output_tokens=llm_response.output_tokens,
            )
        )
    except Exception as exc:
        components.append(_finish_component(llm_component, status="error", error=str(exc)))
        raise RuntimeError(f"LLM generation failed: {exc}") from exc

    retry_events: list[dict[str, Any]] = []
    enable_retry = _resolve_bool_extra(payload, "enable_corrective_retry", True)
    max_retries = _resolve_int_extra(payload, "max_corrective_retries", default=1, minimum=0)
    current_count = len(selected_chunks)

    while enable_retry and len(retry_events) < max_retries:
        extraction_missing = extracted_value is None
        retry_reason = _derive_retry_reason(
            quality_reason=quality.reason,
            extraction_missing=extraction_missing,
            evidence_low=evidence_low,
        )
        should_retry = retry_reason != "not_needed" and current_count < len(ranked_chunks)
        if not should_retry:
            break

        fallback_stage = "expanded_chunks"
        expanded_candidates = expand_ranked_chunks(
            ranked_chunks,
            current_count=current_count,
            expansion_step=max(1, top_k),
        )
        current_count = min(len(ranked_chunks), current_count + max(1, top_k))
        expanded_selection = select_diverse_chunks(
            ranked_chunks=expanded_candidates,
            top_k=current_count,
            max_per_document=max_per_document,
            max_per_heading=max_per_heading,
            payload=payload,
            query_variants=query_variants,
        )
        selected_chunks = expanded_selection.selected_chunks
        selected_context = _render_selected_context(selected_chunks, expanded_selection.chunk_evidence)
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
            retry_value = parse_extracted_value(retry_response.text)
            if retry_value is not None:
                extracted_value = retry_value
                full_prompt = retry_prompt
            components.append(
                _finish_component(
                    retry_llm_component,
                    status="success",
                    details={"model": retry_response.model, "attempt": attempt_number, "fallback_stage": fallback_stage},
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
        evidence_low = expanded_selection.average_evidence_score < evidence_threshold
        retry_events.append(
            {
                "attempt": attempt_number,
                "reason": retry_reason,
                "expanded_chunk_count": len(selected_chunks),
                "quality_score": quality.quality_score,
                "average_evidence_score": expanded_selection.average_evidence_score,
            }
        )

    retry_component = _start_component("corrective_retry")
    final_reason = _derive_retry_reason(
        quality_reason=quality.reason,
        extraction_missing=extracted_value is None,
        evidence_low=evidence_low,
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
                "final_retry_reason_state": final_reason,
                "bounded_stop": len(retry_events) >= max_retries and final_reason != "not_needed",
            },
        )
    )

    parser_component = _start_component("output_parser")
    components.append(_finish_component(parser_component, status="success", details={"parsed": extracted_value is not None}))

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
            },
        )
    )

    is_match = evaluate_match(extracted_value, payload.expected_value)
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