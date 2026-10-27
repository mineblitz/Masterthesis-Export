"""Text-only conversion pipeline v28 using library-backed retrieval and structured parsing.

This pipeline is intended as the new-generation successor to v27 and focuses on
library-backed components instead of custom heuristics:
- structured_document_chunker_v2 (langchain-text-splitters)
- bm25_context_ranker (rank-bm25)
- embedding_reranker (sentence-transformers CrossEncoder)
- structured_output_parser_v2 (instructor + Pydantic schema)
"""

from pathlib import Path

from app.models import ComponentLog, ExperimentRequest, ExperimentResponse, ExperimentResult
from app.services.components.bm25_context_ranker import rank_bm25
from app.services.components.embedding_reranker import rerank
from app.services.components.prompt_builder_v5 import build_prompt_v5
from app.services.components.result_matcher_component import evaluate_match
from app.services.components.structured_document_chunker_v2 import build_structured_document_chunks_v2
from app.services.components.structured_output_parser_v2 import parse_scalar_v2
from app.services.pdf_text_extractor import extract_text_from_pdfs
from app.services.prompt_loader import load_prompt_template
from app.services.pipelines.text_only_simple_conversion_v21 import (
    _extract_text_from_marker_markdown_v21,
    _finish_component,
    _resolve_document_source,
    _resolve_int_extra,
    _start_component,
    _now_iso,
)

_BM25_POOL_DEFAULT = 24
_TOP_K_DEFAULT = 5
_CROSS_ENCODER_DEFAULT = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def _render_selected_context(selected_chunks: list) -> str:
    blocks: list[str] = []
    for index, ranked in enumerate(selected_chunks, start=1):
        chunk = ranked.chunk
        lines = [
            f"## Selected Chunk {index}",
            f"Document: {chunk.document_path}",
            f"Lines: {chunk.start_line}-{chunk.end_line}",
            f"Score: {ranked.score:.4f}",
        ]
        if chunk.heading:
            lines.append(f"Heading: {chunk.heading}")
        lines.append(chunk.text)
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _build_query(payload: ExperimentRequest) -> str:
    parts = [payload.value.strip()]
    for condition in payload.conditions or []:
        cond_type = condition.type.strip()
        cond_value = condition.value.strip()
        if cond_type and cond_value:
            parts.append(f"{cond_type} {cond_value}")
        elif cond_type:
            parts.append(cond_type)
        elif cond_value:
            parts.append(cond_value)
    return " ".join(part for part in parts if part)


def run_text_only_simple_conversion_v28(payload: ExperimentRequest) -> ExperimentResponse:
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
        components.append(_finish_component(source_component, status="error", error=str(exc)))
        raise RuntimeError(f"Document source resolution failed: {exc}") from exc

    chunk_component = _start_component("structured_document_chunker_v2")
    chunks = build_structured_document_chunks_v2(docs_text)
    components.append(
        _finish_component(
            chunk_component,
            status="success",
            details={"chunk_count": len(chunks), "document_count": len(used_documents)},
        )
    )

    bm25_pool = _resolve_int_extra(payload, "bm25_candidate_pool", default=_BM25_POOL_DEFAULT, minimum=5)
    ranker_component = _start_component("bm25_context_ranker")
    ranked_chunks, search_terms = rank_bm25(
        chunks=chunks,
        payload=payload,
        search_terms=getattr(payload, "search_terms", None),
        max_results=bm25_pool,
    )
    components.append(
        _finish_component(
            ranker_component,
            status="success",
            details={
                "candidate_count": len(ranked_chunks),
                "bm25_candidate_pool": bm25_pool,
                "search_terms": search_terms,
            },
        )
    )

    top_k = _resolve_int_extra(payload, "top_k_chunks", default=_TOP_K_DEFAULT, minimum=1)
    cross_encoder_model = (payload.model_extra or {}).get("cross_encoder_model", _CROSS_ENCODER_DEFAULT)
    reranker_component = _start_component("embedding_reranker")
    selected_chunks = rerank(
        ranked_chunks,
        query=_build_query(payload),
        top_n=top_k,
        model_name=str(cross_encoder_model),
    )
    components.append(
        _finish_component(
            reranker_component,
            status="success",
            details={
                "selected_chunk_count": len(selected_chunks),
                "top_k_chunks": top_k,
                "cross_encoder_model": cross_encoder_model,
                "selected_chunk_ids": [item.chunk.chunk_id for item in selected_chunks],
            },
        )
    )

    selected_context = _render_selected_context(selected_chunks)
    full_prompt = build_prompt_v5(
        template=template,
        system=payload.system,
        system_name=payload.system_name,
        value=payload.value,
        conditions=payload.conditions,
        docs_text=selected_context,
    )

    parse_retries = _resolve_int_extra(payload, "instructor_max_retries", default=3, minimum=1)
    llm_component = _start_component("llm_client_instructor")
    extraction = parse_scalar_v2(
        prompt=full_prompt,
        llm=payload.llm,
        temperature=payload.temperature,
        max_retries=parse_retries,
    )
    extracted_value = extraction.extracted_value
    confidence = extraction.confidence
    components.append(
        _finish_component(
            llm_component,
            status="success",
            details={
                "extracted_value": extracted_value,
                "confidence": confidence,
                "evidence_summary": extraction.evidence_summary,
                "instructor_max_retries": parse_retries,
                "output_schema": "ScalarExtractionOutput",
            },
        )
    )

    is_match = evaluate_match(extracted_value, payload.expected_value)

    result = ExperimentResult(
        expected_value=payload.expected_value,
        extracted_value=extracted_value,
        is_match=is_match,
        confidence=confidence,
        full_prompt=full_prompt,
        full_output=str(extraction.model_dump()),
        input_tokens=0,
        output_tokens=0,
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
