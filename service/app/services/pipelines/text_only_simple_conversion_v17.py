"""Text-only conversion pipeline v17 with structured chunk ranking and corrective retry."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.models import ComponentLog, ExperimentRequest, ExperimentResponse, ExperimentResult
from app.services.components.context_expander import expand_ranked_chunks, select_ranked_chunks
from app.services.components.dataset_input_adapter import (
    append_question_to_prompt,
    resolve_dataset_search_terms,
    resolve_document_input,
)
from app.services.components.hybrid_context_ranker import rank_document_chunks
from app.services.components.output_parser_component import parse_extracted_value
from app.services.components.prompt_builder_v5 import (
    build_conditions_block,
    build_conditions_block_de,
    build_prompt_v5,
)
from app.services.components.retrieval_quality_component import assess_retrieval_quality
from app.services.components.structured_document_chunker import build_structured_document_chunks
from app.services.components.result_matcher_component import evaluate_match
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


def _resolve_top_k(payload: ExperimentRequest) -> int:
    extras = payload.model_extra or {}
    raw = extras.get("top_k_chunks", 3)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = 3
    return max(1, value)


def _resolve_retry_threshold(payload: ExperimentRequest) -> float:
    extras = payload.model_extra or {}
    raw = extras.get("retrieval_confidence_threshold", 0.55)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        value = 0.55
    return max(0.0, min(1.0, value))


def _resolve_enable_retry(payload: ExperimentRequest) -> bool:
    extras = payload.model_extra or {}
    return bool(extras.get("enable_corrective_retry", True))


def _render_selected_context(selected_chunks: list[Any]) -> str:
    blocks: list[str] = []
    for index, ranked in enumerate(selected_chunks, start=1):
        chunk = ranked.chunk
        heading_line = f"Heading: {chunk.heading}\n" if chunk.heading else ""
        blocks.append(
            "\n".join(
                [
                    f"## Selected Chunk {index}",
                    f"Document: {chunk.document_path}",
                    f"Lines: {chunk.start_line}-{chunk.end_line}",
                    f"Score: {ranked.score:.2f}",
                    heading_line.rstrip(),
                    chunk.text,
                ]
            ).strip()
        )
    return "\n\n".join(blocks)


def run_text_only_simple_conversion_v17(payload: ExperimentRequest) -> ExperimentResponse:
    pipeline_started_at = _now_iso()
    components: list[ComponentLog] = []

    prompt_component = _start_component("prompt_loader")
    template = load_prompt_template(payload.prompt)
    components.append(_finish_component(prompt_component, status="success", details={"prompt_name": payload.prompt}))

    source_component = _start_component("document_source_resolver")
    input_source = (payload.model_extra or {}).get("input_source")
    preferred_source = (
        "dataset_text"
        if input_source == "dataset_text"
        else _resolve_document_source(payload)
    )

    try:
        if (payload.model_extra or {}).get("input_source") == "dataset_text":
            document_input = resolve_document_input(payload, Path("."))
            docs_text = document_input.text
            used_documents = document_input.used_documents
            actual_source = "dataset_text"
            source_details = {
                **document_input.details,
                "preferred_source": preferred_source,
            }
        elif preferred_source == "marker":
            docs_text, used_documents = _extract_text_from_marker_markdown(payload.approval_links, Path("."))
            actual_source = "marker_markdown"
            source_details = {}
        else:
            docs_text, used_documents = extract_text_from_pdfs(payload.approval_links, Path("."))
            actual_source = "pdf_full_text"
            source_details = {}
        components.append(
            _finish_component(
                source_component,
                status="success",
                details={
                    "preferred_source": preferred_source,
                    "actual_source": actual_source,
                    "document_count": len(used_documents),
                    **source_details,
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
            details={
                "chunk_count": len(chunks),
                "document_count": len(used_documents),
                "source_text_chars": len(docs_text),
                "source_text_truncated": False,
            },
        )
    )

    ranker_component = _start_component("hybrid_context_ranker")
    ranked_chunks, search_terms = rank_document_chunks(
        chunks=chunks,
        payload=payload,
        search_terms=resolve_dataset_search_terms(payload),
    )
    top_k = _resolve_top_k(payload)
    selected_chunks = select_ranked_chunks(ranked_chunks, top_k=top_k)
    components.append(
        _finish_component(
            ranker_component,
            status="success",
            details={
                "candidate_count": len(ranked_chunks),
                "selected_chunk_count": len(selected_chunks),
                "top_k_chunks": top_k,
                "search_terms": search_terms,
                "selected_chunk_ids": [item.chunk.chunk_id for item in selected_chunks],
            },
        )
    )

    retrieval_component = _start_component("retrieval_quality_checker")
    retry_threshold = _resolve_retry_threshold(payload)
    quality = assess_retrieval_quality(
        selected_chunks=selected_chunks,
        available_ranked_chunks=ranked_chunks,
        search_terms=search_terms,
        threshold=retry_threshold,
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
            },
        )
    )

    conditions_text_raw, conditions_count = build_conditions_block(payload.conditions)
    conditions_text_de, _ = build_conditions_block_de(payload.conditions)

    llm_outputs: list[str] = []
    total_input_tokens = 0
    total_output_tokens = 0
    extracted_value: float | None = None
    selected_context = _render_selected_context(selected_chunks)
    fallback_stage = "initial"

    llm_component = _start_component("llm_client")
    full_prompt = append_question_to_prompt(
        build_prompt_v5(
            template=template,
            system=payload.system,
            system_name=payload.system_name,
            value=payload.value,
            conditions=payload.conditions,
            docs_text=selected_context,
        ),
        payload,
    )
    try:
        llm_response = generate_text_component(prompt=full_prompt, llm=payload.llm, temperature=payload.temperature)
        total_input_tokens += llm_response.input_tokens
        total_output_tokens += llm_response.output_tokens
        llm_outputs.append(f"### Attempt 1\n{llm_response.text}")
        extracted_value = parse_extracted_value(llm_response.text)
        components.append(
            _finish_component(
                llm_component,
                status="success",
                details={"model": llm_response.model, "attempt": 1, "fallback_stage": fallback_stage},
                input_tokens=llm_response.input_tokens,
                output_tokens=llm_response.output_tokens,
            )
        )
    except Exception as exc:
        components.append(_finish_component(llm_component, status="error", error=str(exc)))
        raise RuntimeError(f"LLM generation failed: {exc}") from exc

    if _resolve_enable_retry(payload) and (quality.should_retry or extracted_value is None) and len(selected_chunks) < len(ranked_chunks):
        retry_component = _start_component("corrective_retry")
        expanded_chunks = expand_ranked_chunks(ranked_chunks, current_count=len(selected_chunks), expansion_step=max(1, top_k))
        expanded_context = _render_selected_context(expanded_chunks)
        retry_prompt = append_question_to_prompt(
            build_prompt_v5(
                template=template,
                system=payload.system,
                system_name=payload.system_name,
                value=payload.value,
                conditions=payload.conditions,
                docs_text=expanded_context,
            ),
            payload,
        )
        fallback_stage = "expanded_chunks"
        retry_llm_component = _start_component("llm_client")
        try:
            retry_response = generate_text_component(prompt=retry_prompt, llm=payload.llm, temperature=payload.temperature)
            total_input_tokens += retry_response.input_tokens
            total_output_tokens += retry_response.output_tokens
            llm_outputs.append(f"### Attempt 2\n{retry_response.text}")
            retry_value = parse_extracted_value(retry_response.text)
            if retry_value is not None:
                extracted_value = retry_value
                full_prompt = retry_prompt
            components.append(
                _finish_component(
                    retry_llm_component,
                    status="success",
                    details={"model": retry_response.model, "attempt": 2, "fallback_stage": fallback_stage},
                    input_tokens=retry_response.input_tokens,
                    output_tokens=retry_response.output_tokens,
                )
            )
            components.append(
                _finish_component(
                    retry_component,
                    status="success",
                    details={
                        "triggered": True,
                        "reason": quality.reason if quality.should_retry else "null_extraction",
                        "previous_chunk_count": len(selected_chunks),
                        "expanded_chunk_count": len(expanded_chunks),
                    },
                )
            )
        except Exception as exc:
            components.append(_finish_component(retry_llm_component, status="error", error=str(exc)))
            components.append(_finish_component(retry_component, status="error", error=str(exc)))
            raise RuntimeError(f"Corrective retry failed: {exc}") from exc
    else:
        retry_component = _start_component("corrective_retry")
        components.append(
            _finish_component(
                retry_component,
                status="success",
                details={"triggered": False, "reason": "not_needed_or_no_more_context"},
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