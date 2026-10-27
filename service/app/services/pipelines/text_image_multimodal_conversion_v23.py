"""Multimodal conversion pipeline v23 with layout-model evidence selection.

New pipeline that replaces:
- marker_structure_parser + filename/position heuristics (multimodal_evidence_selector_v19)
  with layout_document_parser (docling/Marker markdown) + multimodal_evidence_selector_v23
  (BM25 for text blocks, rapidfuzz for figure/table blocks).
- hybrid_context_ranker with bm25_context_ranker (rank-bm25).

All other stages (Marker markdown loading, text cleaning, multimodal LLM call,
compliance report builder v22) are carried over unchanged.
Compare against v22 for A/B benchmarking.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.models import ComponentLog, ExperimentRequest, ExperimentResponse, ExperimentResult, LLMProvider
from app.services.components.bm25_context_ranker import rank_bm25
from app.services.components.compliance_report_builder_v22 import build_compliance_report_v22
from app.services.components.layout_document_parser import LayoutBlock, parse_document
from app.services.components.llm_client_component import generate_multimodal_component
from app.services.components.marker_text_cleaner import clean_marker_markdown_text
from app.services.components.multimodal_evidence_selector_v23 import select_evidence_v23
from app.services.components.output_parser_component import parse_extracted_value
from app.services.components.prompt_builder_v5 import (
    build_conditions_block,
    build_conditions_block_de,
    build_prompt_v5,
)
from app.services.components.result_matcher_component import evaluate_match
from app.services.components.structured_document_chunker_v2 import build_structured_document_chunks_v2
from app.services.prompt_loader import load_prompt_template

# Reuse helpers from v22 (unchanged)
from app.services.pipelines.text_image_multimodal_conversion_v22 import (
    MarkerDocumentBundle,
    _aggregate_evidence_quality,
    _derive_retry_reason,
    _finish_component,
    _load_marker_documents,
    _now_iso,
    _render_selected_context,
    _resolve_bool_extra,
    _resolve_float_extra,
    _resolve_int_extra,
    _start_component,
)


def _build_context_from_layout_blocks(text_blocks: list[LayoutBlock]) -> str:
    """Render selected text/heading layout blocks as a context string for the LLM prompt."""
    parts: list[str] = []
    for index, block in enumerate(text_blocks, start=1):
        heading_line = f"Heading: {block.heading}" if block.heading else ""
        block_lines = [
            f"## Selected Block {index}",
            f"Document: {block.document_path}",
            f"Page: {block.page_number}",
            f"Type: {block.block_type}",
        ]
        if heading_line:
            block_lines.append(heading_line)
        block_lines.append(block.text)
        parts.append("\n".join(block_lines))
    return "\n\n".join(parts)


def _resolve_image_paths(
    evidence_items: list[Any],
    document_paths: list[str],
    base_dir: Path,
) -> list[str]:
    """Extract resolved image file paths from evidence items.

    Falls back to searching for _page_*.jpg files if no image paths are found
    from the layout blocks (e.g. pure-text documents without figures).
    """
    image_paths: list[str] = []
    for item in evidence_items:
        block = item.block
        if block.block_type in {"figure"} and block.image_path:
            candidate = (base_dir / block.image_path).resolve()
            if candidate.exists():
                image_paths.append(str(candidate))

    if not image_paths:
        # Fallback: collect _page_*.{jpg,png,webp} files next to the source documents
        import glob
        for doc_path in document_paths:
            doc_dir = (base_dir / doc_path).resolve().parent
            for pattern in ["_page_*.jpg", "_page_*.png", "_page_*.webp", "_page_*.jpeg"]:
                image_paths.extend(glob.glob(str(doc_dir / pattern)))

    return sorted(set(image_paths))[:20]  # cap at 20 images


def run_text_image_multimodal_conversion_v23(payload: ExperimentRequest) -> ExperimentResponse:
    """Pipeline v23: layout-model-backed evidence selection for multimodal extraction.

    Flow:
    1. Load Marker markdown documents.
    2. Clean Marker markdown text.
    3. Parse documents into typed layout blocks via layout_document_parser (docling/Marker).
    4. BM25-rank text blocks; embed-rerank top candidates.
    5. Score figure/table blocks via rapidfuzz caption matching.
    6. Select diverse text + image evidence with multimodal_evidence_selector_v23.
    7. Build prompt from selected text blocks.
    8. Call multimodal LLM with selected image paths.
    9. Parse output and build compliance report.
    """
    provider, _ = payload.llm.value.split(":", 1)
    if provider != LLMProvider.OPENROUTER.value:
        raise ValueError(
            "Pipeline v23 requires an OpenRouter model (e.g. OPENROUTER_GEMMA_4_26B_A4B_IT_FREE)."
        )

    pipeline_started_at = _now_iso()
    components: list[ComponentLog] = []

    # 1 — Prompt template
    prompt_component = _start_component("prompt_loader")
    template = load_prompt_template(payload.prompt)
    components.append(_finish_component(prompt_component, status="success", details={"prompt_name": payload.prompt}))

    # 2 — Load Marker markdown documents
    marker_component = _start_component("marker_markdown_extractor")
    try:
        marker_documents = _load_marker_documents(payload.approval_links, Path("."))
        used_documents = [d.marker_document_path for d in marker_documents]
        source_document_paths = [d.source_document_path for d in marker_documents]
        components.append(
            _finish_component(
                marker_component,
                status="success",
                details={"document_count": len(used_documents), "method": "marker_markdown"},
            )
        )
    except Exception as exc:
        components.append(_finish_component(marker_component, status="error", error=str(exc)))
        raise RuntimeError(f"Marker markdown loading failed: {exc}") from exc

    # 3 — Clean Marker markdown
    cleaner_component = _start_component("marker_text_cleaner")
    enable_cleaning = _resolve_bool_extra(payload, "mm_enable_marker_text_cleaning", True)
    cleaned_chunks: list[str] = []
    try:
        for document in marker_documents:
            cleaned_text = (
                clean_marker_markdown_text(document.raw_text, remove_image_lines=True,
                                           remove_page_span_tags=True, preserve_page_markers=True)
                if enable_cleaning
                else document.raw_text
            )
            cleaned_chunks.append(f"## Document: {document.marker_document_path}\n{cleaned_text}")
        docs_text = "\n\n".join(cleaned_chunks)
        components.append(
            _finish_component(
                cleaner_component,
                status="success",
                details={"document_count": len(marker_documents), "cleaning_enabled": enable_cleaning},
            )
        )
    except Exception as exc:
        components.append(_finish_component(cleaner_component, status="error", error=str(exc)))
        raise RuntimeError(f"Marker text cleaning failed: {exc}") from exc

    # 4 — Layout block parsing (docling or Marker markdown fallback)
    layout_component = _start_component("layout_document_parser_v23")
    all_blocks: list[LayoutBlock] = []
    try:
        for doc in marker_documents:
            blocks = parse_document(
                doc.marker_document_path,
                base_dir=Path("."),
                prefer_pdf=False,  # use Marker markdown since we already have it cleaned
            )
            all_blocks.extend(blocks)
        components.append(
            _finish_component(
                layout_component,
                status="success",
                details={
                    "total_block_count": len(all_blocks),
                    "text_blocks": sum(1 for b in all_blocks if b.block_type == "text"),
                    "figure_blocks": sum(1 for b in all_blocks if b.block_type == "figure"),
                    "table_blocks": sum(1 for b in all_blocks if b.block_type == "table"),
                    "heading_blocks": sum(1 for b in all_blocks if b.block_type == "heading"),
                    "parser": "layout_document_parser_v23",
                },
            )
        )
    except (ImportError, FileNotFoundError) as exc:
        components.append(_finish_component(layout_component, status="error", error=str(exc)))
        raise

    # 5 — BM25 text ranking on text/heading blocks
    bm25_component = _start_component("bm25_context_ranker_v23")
    query_variants = [payload.value] + [
        f"{c.type} {c.value}" for c in (payload.conditions or [])
    ]
    try:
        # Build temporary DocumentChunks from the layout text blocks using the v2 chunker
        chunks = build_structured_document_chunks_v2(docs_text)
        bm25_candidates, search_terms = rank_bm25(
            chunks=chunks,
            payload=payload,
            max_results=20,
        )
        components.append(
            _finish_component(
                bm25_component,
                status="success",
                details={"bm25_candidate_count": len(bm25_candidates), "search_terms": search_terms},
            )
        )
    except ImportError as exc:
        components.append(_finish_component(bm25_component, status="error", error=str(exc)))
        raise

    # 6 — Evidence selection via multimodal_evidence_selector_v23 (BM25 + rapidfuzz)
    top_k_text = _resolve_int_extra(payload, "mm_top_k_text_chunks", default=4, minimum=1)
    top_k_images = _resolve_int_extra(payload, "mm_top_k_images", default=4, minimum=1)
    max_per_page = _resolve_int_extra(payload, "mm_max_evidence_per_page", default=2, minimum=1)

    evidence_component = _start_component("multimodal_evidence_selector_v23")
    try:
        evidence = select_evidence_v23(
            blocks=all_blocks,
            query_variants=query_variants,
            top_text=top_k_text,
            top_figures=top_k_images,
            max_per_page=max_per_page,
        )
        components.append(
            _finish_component(
                evidence_component,
                status="success",
                details={
                    "selected_text_blocks": len(evidence.text_blocks),
                    "selected_figure_blocks": len(evidence.figure_blocks),
                    "selected_table_blocks": len(evidence.table_blocks),
                    "total_selected": len(evidence.all_items),
                    "scorer": "bm25_and_rapidfuzz",
                },
            )
        )
    except ImportError as exc:
        components.append(_finish_component(evidence_component, status="error", error=str(exc)))
        raise

    # 7 — Build text context from selected text blocks
    selected_text_blocks = [item.block for item in evidence.text_blocks]
    selected_context = _build_context_from_layout_blocks(selected_text_blocks)

    # Resolve actual image file paths for the multimodal call
    image_paths = _resolve_image_paths(
        evidence.figure_blocks + evidence.table_blocks,
        document_paths=source_document_paths,
        base_dir=Path("."),
    )

    conditions_text_raw, conditions_count = build_conditions_block(payload.conditions)
    conditions_text_de, _ = build_conditions_block_de(payload.conditions)

    full_prompt = build_prompt_v5(
        template=template,
        system=payload.system,
        system_name=payload.system_name,
        value=payload.value,
        conditions=payload.conditions,
        docs_text=selected_context,
    )

    # 8 — Multimodal LLM call
    llm_outputs: list[str] = []
    total_input_tokens = 0
    total_output_tokens = 0
    extracted_value: float | None = None

    llm_component = _start_component("llm_client_multimodal_v23")
    try:
        llm_response = generate_multimodal_component(
            prompt=full_prompt,
            image_paths=image_paths,
            llm=payload.llm,
            temperature=payload.temperature,
        )
        total_input_tokens += llm_response.input_tokens
        total_output_tokens += llm_response.output_tokens
        llm_outputs.append(f"### Attempt 1\n{llm_response.text}")
        extracted_value = parse_extracted_value(llm_response.text)
        components.append(
            _finish_component(
                llm_component,
                status="success",
                details={
                    "model": llm_response.model,
                    "text_block_count": len(selected_text_blocks),
                    "image_path_count": len(image_paths),
                },
                input_tokens=llm_response.input_tokens,
                output_tokens=llm_response.output_tokens,
            )
        )
    except Exception as exc:
        components.append(_finish_component(llm_component, status="error", error=str(exc)))
        raise RuntimeError(f"Multimodal LLM call failed: {exc}") from exc

    # 9 — Build grounding records for compliance report (reuse v22 builder)
    text_grounding = [
        {
            "id": f"text::block_{index}",
            "document_path": item.block.document_path,
            "page_number": item.block.page_number,
            "score": round(item.score, 4),
            "snippet": item.block.text[:220],
        }
        for index, item in enumerate(evidence.text_blocks)
    ]
    image_grounding = [
        {
            "id": f"image::block_{index}",
            "image_path": item.block.image_path or "",
            "document_path": item.block.document_path,
            "page_number": item.block.page_number,
            "score": round(item.score, 4),
        }
        for index, item in enumerate(evidence.figure_blocks + evidence.table_blocks)
    ]

    report_component = _start_component("compliance_report_builder_v22")
    report = build_compliance_report_v22(
        expected_value=payload.expected_value,
        extracted_value=extracted_value,
        min_or_max=payload.min_or_max,
        text_evidence=text_grounding,
        image_evidence=image_grounding,
    )
    is_match = report.get("check_status") == "compliant"
    components.append(
        _finish_component(
            report_component,
            status="success",
            details=report,
        )
    )

    # Final match
    is_match = evaluate_match(extracted_value, payload.expected_value)

    result = ExperimentResult(
        expected_value=payload.expected_value,
        extracted_value=extracted_value,
        is_match=is_match,
        confidence=None,
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
    return ExperimentResponse(
        status="success",
        experiment_id=payload.experiment_id,
        pipeline=payload.pipeline,
        result=result,
    )
