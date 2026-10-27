"""Multimodal conversion pipeline v22 with hybrid compliance grounding and deterministic report scaffold."""

from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from app.models import ComponentLog, ExperimentRequest, ExperimentResponse, ExperimentResult, LLMProvider
from app.services.components.compliance_report_builder_v22 import build_compliance_report_v22
from app.services.components.context_expander import expand_ranked_chunks
from app.services.components.hybrid_context_ranker import rank_document_chunks
from app.services.components.llm_client_component import generate_multimodal_component
from app.services.components.logo_image_filter import filter_probable_logo_images
from app.services.components.marker_structure_parser import MarkerImageReference, parse_marker_structure
from app.services.components.marker_text_cleaner import clean_marker_markdown_text
from app.services.components.multimodal_evidence_selector_v19 import (
    collect_multimodal_image_candidates,
    infer_layout_priority_pages,
    select_diverse_image_evidence,
)
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
from app.services.prompt_loader import load_prompt_template


@dataclass(frozen=True)
class MarkerDocumentBundle:
    source_document_path: str
    marker_document_path: str
    raw_text: str


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


def _resolve_marker_markdown_path(document_path: str, base_dir: Path) -> tuple[Path, str, str]:
    source_path = (base_dir / document_path).resolve()

    if source_path.name.lower().endswith("_marker.md"):
        marker_path = source_path
    else:
        marker_path = source_path.with_name(f"{source_path.stem}_marker.md")

    if not marker_path.exists():
        raise FileNotFoundError(f"Marker markdown not found: {marker_path}")

    return (
        marker_path,
        marker_path.relative_to(base_dir.resolve()).as_posix(),
        source_path.as_posix(),
    )


def _load_marker_documents(paths: list[str], base_dir: Path) -> list[MarkerDocumentBundle]:
    documents: list[MarkerDocumentBundle] = []

    for document_path in paths:
        marker_path, relative_marker_path, source_document_path = _resolve_marker_markdown_path(document_path, base_dir)
        raw_text = marker_path.read_text(encoding="utf-8")
        documents.append(
            MarkerDocumentBundle(
                source_document_path=source_document_path,
                marker_document_path=relative_marker_path,
                raw_text=raw_text,
            )
        )

    return documents


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
    raw = extras.get(key, default)
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str):
        return raw.strip().lower() in {"1", "true", "yes", "on"}
    return bool(raw)


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


def _aggregate_evidence_quality(*, text_quality: float, text_evidence: float, image_evidence: float) -> float:
    score = text_quality * 0.45 + text_evidence * 0.3 + image_evidence * 0.25
    return round(min(1.0, max(0.0, score)), 4)


def _build_text_grounding_records(selected_chunks: list[Any], evidence_map: dict[str, float]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for ranked in selected_chunks:
        chunk = ranked.chunk
        records.append(
            {
                "id": f"text::{chunk.chunk_id}",
                "document_path": chunk.document_path,
                "line_span": f"{chunk.start_line}-{chunk.end_line}",
                "score": round(evidence_map.get(chunk.chunk_id, 0.0), 4),
                "snippet": chunk.text[:220],
            }
        )
    return records


def _build_image_grounding_records(selected_images: list[Any], evidence_map: dict[str, float]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for image in selected_images:
        records.append(
            {
                "id": f"image::p{image.page_number}_r{image.region_index}",
                "image_path": image.image_path,
                "document_path": image.document_path,
                "page_number": image.page_number,
                "region_index": image.region_index,
                "score": round(evidence_map.get(image.image_path, 0.0), 4),
            }
        )
    return records


def run_text_image_multimodal_conversion_v22(payload: ExperimentRequest) -> ExperimentResponse:
    """
    Pipeline v22:
    1) Resolve Marker markdown and parse page/image structure metadata.
    2) Clean Marker markdown text (remove image embed lines/span tags, preserve page boundaries).
    3) Reuse v19 text/image evidence selection and bounded multimodal retries.
    4) Filter likely logo images using Marker metadata before multimodal image selection.
    5) Build deterministic grounded compliance report with evidence provenance fields.
    """
    provider, _ = payload.llm.value.split(":", 1)
    if provider != LLMProvider.OPENROUTER.value:
        raise ValueError(
            "Pipeline v22 requires an OpenRouter model (e.g. OPENROUTER_GEMMA_4_26B_A4B_IT_FREE)."
        )

    pipeline_started_at = _now_iso()
    components: list[ComponentLog] = []

    prompt_component = _start_component("prompt_loader")
    template = load_prompt_template(payload.prompt)
    components.append(
        _finish_component(
            prompt_component,
            status="success",
            details={"prompt_name": payload.prompt},
        )
    )

    marker_component = _start_component("marker_markdown_extractor")
    try:
        marker_documents = _load_marker_documents(payload.approval_links, Path("."))
        used_documents = [item.marker_document_path for item in marker_documents]
        components.append(
            _finish_component(
                marker_component,
                status="success",
                details={"document_count": len(used_documents), "method": "marker_markdown"},
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
        raise RuntimeError(f"Marker markdown extraction failed: {exc}") from exc

    parser_component = _start_component("marker_structure_parser")
    marker_refs: list[MarkerImageReference] = []
    marker_page_span_count = 0
    try:
        for document in marker_documents:
            parse_result = parse_marker_structure(document.raw_text)
            marker_refs.extend(parse_result.image_references)
            marker_page_span_count += len(parse_result.page_spans)

        components.append(
            _finish_component(
                parser_component,
                status="success",
                details={
                    "document_count": len(marker_documents),
                    "image_reference_count": len(marker_refs),
                    "page_span_count": marker_page_span_count,
                },
            )
        )
    except Exception as exc:
        components.append(_finish_component(parser_component, status="error", error=str(exc)))
        raise RuntimeError(f"Marker structure parsing failed: {exc}") from exc

    cleaner_component = _start_component("marker_text_cleaner")
    enable_cleaning = _resolve_bool_extra(payload, "mm_enable_marker_text_cleaning", True)
    remove_image_lines = _resolve_bool_extra(payload, "mm_remove_marker_image_lines", True)
    remove_page_spans = _resolve_bool_extra(payload, "mm_remove_marker_page_spans", True)
    preserve_page_markers = _resolve_bool_extra(payload, "mm_preserve_marker_page_boundaries", True)

    cleaned_chunks: list[str] = []
    try:
        for document in marker_documents:
            cleaned_text = document.raw_text
            if enable_cleaning:
                cleaned_text = clean_marker_markdown_text(
                    document.raw_text,
                    remove_image_lines=remove_image_lines,
                    remove_page_span_tags=remove_page_spans,
                    preserve_page_markers=preserve_page_markers,
                )
            cleaned_chunks.append(f"## Document: {document.marker_document_path}\n{cleaned_text}")

        docs_text = "\n\n".join(cleaned_chunks)
        components.append(
            _finish_component(
                cleaner_component,
                status="success",
                details={
                    "document_count": len(marker_documents),
                    "cleaning_enabled": enable_cleaning,
                    "remove_image_lines": remove_image_lines,
                    "remove_page_span_tags": remove_page_spans,
                    "preserve_page_markers": preserve_page_markers,
                    "cleaned_text_length": len(docs_text),
                },
            )
        )
    except Exception as exc:
        components.append(_finish_component(cleaner_component, status="error", error=str(exc)))
        raise RuntimeError(f"Marker text cleaning failed: {exc}") from exc

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
    query_limit = _resolve_int_extra(payload, "mm_query_expansion_limit", default=6, minimum=2)
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

    top_k_text = _resolve_int_extra(payload, "mm_top_k_text_chunks", default=3, minimum=1)
    text_max_per_document = _resolve_int_extra(payload, "mm_max_text_chunks_per_document", default=2, minimum=1)
    text_max_per_heading = _resolve_int_extra(payload, "mm_max_text_chunks_per_heading", default=1, minimum=1)

    text_diversity_component = _start_component("text_evidence_selector")
    text_selection = select_diverse_chunks(
        ranked_chunks=ranked_chunks,
        top_k=top_k_text,
        max_per_document=text_max_per_document,
        max_per_heading=text_max_per_heading,
        payload=payload,
        query_variants=query_variants,
    )
    selected_text_chunks = text_selection.selected_chunks
    components.append(
        _finish_component(
            text_diversity_component,
            status="success",
            details={
                "selected_chunk_count": len(selected_text_chunks),
                "top_k_text_chunks": top_k_text,
                "max_text_chunks_per_document": text_max_per_document,
                "max_text_chunks_per_heading": text_max_per_heading,
                "selected_chunk_ids": [item.chunk.chunk_id for item in selected_text_chunks],
                "average_text_evidence_score": text_selection.average_evidence_score,
                "skipped_for_document_cap": text_selection.skipped_for_document_cap,
                "skipped_for_heading_cap": text_selection.skipped_for_heading_cap,
                "skipped_for_redundancy": text_selection.skipped_for_redundancy,
            },
        )
    )

    image_component = _start_component("layout_aware_image_selector")
    image_candidate_limit = _resolve_int_extra(payload, "mm_max_image_candidates", default=20, minimum=1)
    image_candidates = collect_multimodal_image_candidates(
        payload.approval_links,
        Path("."),
        max_images_total=image_candidate_limit,
    )
    if not image_candidates:
        components.append(
            _finish_component(
                image_component,
                status="error",
                details={"image_candidate_count": 0},
                error="No images found for multimodal request",
            )
        )
        raise RuntimeError("No images found for multimodal request. Check system-information/<system>/img.")

    logo_component = _start_component("logo_image_filter")
    enable_logo_filter = _resolve_bool_extra(payload, "mm_logo_filter_enabled", True)
    logo_region_index_max = _resolve_int_extra(payload, "mm_logo_region_index_max", default=1, minimum=0)
    logo_repeat_page_threshold = _resolve_int_extra(payload, "mm_logo_repeat_page_threshold", default=2, minimum=1)

    filtered_image_candidates = image_candidates
    filtered_out_images_count = 0
    fallback_to_unfiltered = False

    if enable_logo_filter:
        filter_result = filter_probable_logo_images(
            candidates=image_candidates,
            marker_image_references=marker_refs,
            logo_region_index_max=logo_region_index_max,
            repeat_page_threshold=logo_repeat_page_threshold,
        )
        filtered_image_candidates = filter_result.filtered_candidates
        filtered_out_images_count = len(filter_result.filtered_out_candidates)
        if not filtered_image_candidates:
            filtered_image_candidates = image_candidates
            fallback_to_unfiltered = True

    components.append(
        _finish_component(
            logo_component,
            status="success",
            details={
                "enabled": enable_logo_filter,
                "input_candidate_count": len(image_candidates),
                "filtered_candidate_count": len(filtered_image_candidates),
                "filtered_out_count": filtered_out_images_count,
                "logo_region_index_max": logo_region_index_max,
                "logo_repeat_page_threshold": logo_repeat_page_threshold,
                "fallback_to_unfiltered": fallback_to_unfiltered,
            },
        )
    )

    layout_priority_count = _resolve_int_extra(payload, "mm_layout_priority_pages", default=4, minimum=1)
    prioritized_pages = infer_layout_priority_pages(
        selected_text_chunks=selected_text_chunks,
        query_variants=query_variants,
        max_pages=layout_priority_count,
    )

    top_k_images = _resolve_int_extra(payload, "mm_top_k_images", default=8, minimum=1)
    image_max_per_document = _resolve_int_extra(payload, "mm_max_images_per_document", default=4, minimum=1)
    image_max_per_page = _resolve_int_extra(payload, "mm_max_regions_per_page", default=2, minimum=1)

    image_selection = select_diverse_image_evidence(
        candidates=filtered_image_candidates,
        top_k=top_k_images,
        max_per_document=image_max_per_document,
        max_regions_per_page=image_max_per_page,
        prioritized_pages=prioritized_pages,
    )
    selected_images = image_selection.selected_images

    components.append(
        _finish_component(
            image_component,
            status="success",
            details={
                "image_candidate_count": len(image_candidates),
                "image_candidate_count_after_logo_filter": len(filtered_image_candidates),
                "selected_image_count": len(selected_images),
                "top_k_images": top_k_images,
                "max_images_per_document": image_max_per_document,
                "max_regions_per_page": image_max_per_page,
                "layout_priority_pages": prioritized_pages,
                "average_image_evidence_score": image_selection.average_evidence_score,
                "skipped_for_document_cap": image_selection.skipped_for_document_cap,
                "skipped_for_page_cap": image_selection.skipped_for_page_cap,
                "selected_images_sample": [item.image_path for item in selected_images[:3]],
            },
        )
    )

    retrieval_component = _start_component("evidence_quality_checker")
    retrieval_threshold = _resolve_float_extra(
        payload,
        "mm_retrieval_confidence_threshold",
        default=0.58,
        minimum=0.0,
        maximum=1.0,
    )
    retrieval_quality = assess_retrieval_quality(
        selected_chunks=selected_text_chunks,
        available_ranked_chunks=ranked_chunks,
        search_terms=query_variants,
        threshold=retrieval_threshold,
    )
    combined_evidence_score = _aggregate_evidence_quality(
        text_quality=retrieval_quality.quality_score,
        text_evidence=text_selection.average_evidence_score,
        image_evidence=image_selection.average_evidence_score,
    )
    evidence_threshold = _resolve_float_extra(
        payload,
        "mm_evidence_score_threshold",
        default=0.5,
        minimum=0.0,
        maximum=1.0,
    )
    evidence_low = combined_evidence_score < evidence_threshold
    components.append(
        _finish_component(
            retrieval_component,
            status="success",
            details={
                "retrieval_quality_score": retrieval_quality.quality_score,
                "retrieval_reason": retrieval_quality.reason,
                "keyword_coverage": retrieval_quality.keyword_coverage,
                "average_text_evidence_score": text_selection.average_evidence_score,
                "average_image_evidence_score": image_selection.average_evidence_score,
                "combined_evidence_score": combined_evidence_score,
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
    current_text_evidence_map = text_selection.chunk_evidence
    current_image_evidence_map = image_selection.evidence_by_image

    selected_context = _render_selected_context(selected_text_chunks, text_selection.chunk_evidence)
    full_prompt = build_prompt_v5(
        template=template,
        system=payload.system,
        system_name=payload.system_name,
        value=payload.value,
        conditions=payload.conditions,
        docs_text=selected_context,
    )

    selected_image_paths = [item.image_path for item in selected_images]
    attempt_number = 1
    llm_component = _start_component("llm_client_multimodal")
    try:
        llm_response = generate_multimodal_component(
            prompt=full_prompt,
            image_paths=selected_image_paths,
            llm=payload.llm,
            temperature=payload.temperature,
        )
        total_input_tokens += llm_response.input_tokens
        total_output_tokens += llm_response.output_tokens
        llm_outputs.append(f"### Attempt {attempt_number}\n{llm_response.text}")
        extracted_value = parse_extracted_value(llm_response.text)
        components.append(
            _finish_component(
                llm_component,
                status="success",
                details={
                    "model": llm_response.model,
                    "attempt": attempt_number,
                    "image_count": len(selected_image_paths),
                },
                input_tokens=llm_response.input_tokens,
                output_tokens=llm_response.output_tokens,
            )
        )
    except Exception as exc:
        components.append(_finish_component(llm_component, status="error", error=str(exc)))
        raise RuntimeError(f"Multimodal LLM generation failed: {exc}") from exc

    retry_events: list[dict[str, Any]] = []
    enable_retry = _resolve_bool_extra(payload, "mm_enable_corrective_retry", True)
    max_retries = _resolve_int_extra(payload, "mm_max_corrective_retries", default=1, minimum=0)

    current_text_count = len(selected_text_chunks)
    current_image_count = len(selected_images)
    image_step = _resolve_int_extra(payload, "mm_retry_image_expansion_step", default=2, minimum=1)

    while enable_retry and len(retry_events) < max_retries:
        extraction_missing = extracted_value is None
        retry_reason = _derive_retry_reason(
            quality_reason=retrieval_quality.reason,
            extraction_missing=extraction_missing,
            evidence_low=evidence_low,
        )

        can_expand_text = current_text_count < len(ranked_chunks)
        can_expand_images = current_image_count < len(filtered_image_candidates)
        should_retry = retry_reason != "not_needed" and (can_expand_text or can_expand_images)
        if not should_retry:
            break

        expanded_ranked = expand_ranked_chunks(
            ranked_chunks,
            current_count=current_text_count,
            expansion_step=max(1, top_k_text),
        )
        current_text_count = len(expanded_ranked)

        expanded_text_selection = select_diverse_chunks(
            ranked_chunks=expanded_ranked,
            top_k=current_text_count,
            max_per_document=text_max_per_document,
            max_per_heading=text_max_per_heading,
            payload=payload,
            query_variants=query_variants,
        )
        selected_text_chunks = expanded_text_selection.selected_chunks
        current_text_evidence_map = expanded_text_selection.chunk_evidence

        current_image_count = min(len(filtered_image_candidates), current_image_count + image_step)
        expanded_image_selection = select_diverse_image_evidence(
            candidates=filtered_image_candidates,
            top_k=current_image_count,
            max_per_document=image_max_per_document,
            max_regions_per_page=image_max_per_page,
            prioritized_pages=prioritized_pages,
        )
        selected_images = expanded_image_selection.selected_images
        current_image_evidence_map = expanded_image_selection.evidence_by_image
        selected_image_paths = [item.image_path for item in selected_images]

        selected_context = _render_selected_context(selected_text_chunks, expanded_text_selection.chunk_evidence)
        retry_prompt = build_prompt_v5(
            template=template,
            system=payload.system,
            system_name=payload.system_name,
            value=payload.value,
            conditions=payload.conditions,
            docs_text=selected_context,
        )

        attempt_number += 1
        retry_llm_component = _start_component("llm_client_multimodal")
        try:
            retry_response = generate_multimodal_component(
                prompt=retry_prompt,
                image_paths=selected_image_paths,
                llm=payload.llm,
                temperature=payload.temperature,
            )
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
                    details={
                        "model": retry_response.model,
                        "attempt": attempt_number,
                        "image_count": len(selected_image_paths),
                        "retry_reason": retry_reason,
                    },
                    input_tokens=retry_response.input_tokens,
                    output_tokens=retry_response.output_tokens,
                )
            )
        except Exception as exc:
            components.append(_finish_component(retry_llm_component, status="error", error=str(exc)))
            raise RuntimeError(f"Corrective multimodal retry failed: {exc}") from exc

        retrieval_quality = assess_retrieval_quality(
            selected_chunks=selected_text_chunks,
            available_ranked_chunks=ranked_chunks,
            search_terms=query_variants,
            threshold=retrieval_threshold,
        )
        combined_evidence_score = _aggregate_evidence_quality(
            text_quality=retrieval_quality.quality_score,
            text_evidence=expanded_text_selection.average_evidence_score,
            image_evidence=expanded_image_selection.average_evidence_score,
        )
        evidence_low = combined_evidence_score < evidence_threshold

        retry_events.append(
            {
                "attempt": attempt_number,
                "reason": retry_reason,
                "expanded_text_chunk_count": len(selected_text_chunks),
                "expanded_image_count": len(selected_images),
                "retrieval_quality_score": retrieval_quality.quality_score,
                "combined_evidence_score": combined_evidence_score,
            }
        )

    retry_component = _start_component("corrective_retry")
    final_reason = _derive_retry_reason(
        quality_reason=retrieval_quality.reason,
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
    components.append(
        _finish_component(
            parser_component,
            status="success",
            details={"parsed": extracted_value is not None},
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
            },
        )
    )

    text_grounding_records = _build_text_grounding_records(selected_text_chunks, current_text_evidence_map)
    image_grounding_records = _build_image_grounding_records(selected_images, current_image_evidence_map)

    grounding_component = _start_component("compliance_grounding_v22")
    compliance_report = build_compliance_report_v22(
        expected_value=payload.expected_value,
        extracted_value=extracted_value,
        min_or_max=payload.min_or_max,
        text_evidence=text_grounding_records,
        image_evidence=image_grounding_records,
    )
    components.append(
        _finish_component(
            grounding_component,
            status="success",
            details={
                "check_status": compliance_report["check_status"],
                "comparison_mode": compliance_report["comparison_mode"],
                "primary_text_evidence_id": compliance_report["evidence_provenance"]["primary_text_evidence_id"],
                "primary_image_evidence_id": compliance_report["evidence_provenance"]["primary_image_evidence_id"],
                "text_evidence_count": len(text_grounding_records),
                "image_evidence_count": len(image_grounding_records),
            },
        )
    )

    is_match = evaluate_match(extracted_value, payload.expected_value)
    compliance_report_json = json.dumps(compliance_report, ensure_ascii=True, sort_keys=True)
    result = ExperimentResult(
        expected_value=payload.expected_value,
        extracted_value=extracted_value,
        is_match=is_match,
        confidence=combined_evidence_score,
        full_prompt=full_prompt,
        full_output="\n\n".join(
            [
                *llm_outputs,
                "### Deterministic Compliance Report v22",
                compliance_report_json,
            ]
        ),
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
