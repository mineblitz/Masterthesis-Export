"""Multimodal conversion pipeline v11 using Marker markdown plus related images."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.models import ComponentLog, ExperimentRequest, ExperimentResponse, ExperimentResult, LLMProvider
from app.services.components.keyword_context_extractor import extract_keyword_context_chunks
from app.services.components.llm_client_component import generate_multimodal_component
from app.services.components.output_parser_component import parse_extracted_value
from app.services.components.prompt_builder_v5 import (
    build_conditions_block,
    build_conditions_block_de,
    build_prompt_v5,
)
from app.services.components.result_matcher_component import evaluate_match
from app.services.prompt_loader import load_prompt_template

_ALLOWED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
_DEFAULT_MAX_IMAGES = 20


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
        chunks.append(f"## Document: {relative_marker_path}\\n{cleaned_text}")
        resolved_paths.append(relative_marker_path)

    return "\\n\\n".join(chunks), resolved_paths


def _collect_multimodal_images(paths: list[str], base_dir: Path, max_images: int = _DEFAULT_MAX_IMAGES) -> list[str]:
    resolved: list[str] = []

    for document_path in paths:
        source_path = (base_dir / document_path).resolve()
        files_dir = source_path.parent

        # Collect extracted page images from the same directory as the markdown file.
        # Exclude per-page logo images: files whose stem ends with "_Picture_1" are
        # always the first (logo) image on each page and carry no technical content.
        if files_dir.exists() and files_dir.is_dir():
            candidates: list[Path] = sorted(
                p
                for p in files_dir.iterdir()
                if p.is_file()
                and p.suffix.lower() in _ALLOWED_IMAGE_SUFFIXES
                and p.name.startswith("_page_")
                and not p.stem.endswith("_Picture_1")
            )

            for image_path in candidates:
                resolved.append(image_path.as_posix())
                if len(resolved) >= max_images:
                    return resolved

    return resolved


def _resolve_context_window(payload: ExperimentRequest) -> tuple[int, int]:
    raw_common = getattr(payload, "context_window_lines", None)
    raw_before = getattr(payload, "context_lines_before", None)
    raw_after = getattr(payload, "context_lines_after", None)

    if raw_before is not None or raw_after is not None:
        raise ValueError(
            "Bitte nur 'context_window_lines' verwenden. "
            "Separate Werte 'context_lines_before' und 'context_lines_after' sind in v11 nicht erlaubt."
        )

    default_window = 3
    common = int(raw_common) if raw_common is not None else default_window
    return common, common


def run_text_image_multimodal_conversion_v11(payload: ExperimentRequest) -> ExperimentResponse:
    """
    Pipeline v11:
    1) Resolve Marker markdown from approval_links for text context.
    2) Select relevant chunks via keyword context extraction.
    3) Collect related images and run multimodal extraction (text + images) via OpenRouter model.
    """
    provider, _ = payload.llm.value.split(":", 1)
    if provider != LLMProvider.OPENROUTER.value:
        raise ValueError(
            "Pipeline v11 requires an OpenRouter model (e.g. OPENROUTER_GEMMA_4_26B_A4B_IT_FREE)."
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
        docs_text, used_documents = _extract_text_from_marker_markdown(
            paths=payload.approval_links,
            base_dir=Path("."),
        )
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

    keyword_chunk_component = _start_component("keyword_context_extractor")
    try:
        lines_before, lines_after = _resolve_context_window(payload)
        keyword_result = extract_keyword_context_chunks(
            docs_text,
            value=payload.value,
            search_terms=getattr(payload, "search_terms", None),
            lines_before=lines_before,
            lines_after=lines_after,
        )
        docs_for_prompt = keyword_result.filtered_documents_text
        if not docs_for_prompt.strip():
            docs_for_prompt = docs_text

        components.append(
            _finish_component(
                keyword_chunk_component,
                status="success",
                details={
                    "search_terms": keyword_result.search_terms,
                    "lines_before": lines_before,
                    "lines_after": lines_after,
                    "document_count": keyword_result.document_count,
                    "chunk_count": keyword_result.chunk_count,
                    "hit_count": keyword_result.hit_count,
                    "fallback_to_full_text": keyword_result.chunk_count == 0,
                },
            )
        )
    except Exception as exc:
        components.append(
            _finish_component(
                keyword_chunk_component,
                status="error",
                error=str(exc),
            )
        )
        raise RuntimeError(f"Keyword context extraction failed: {exc}") from exc

    images_component = _start_component("image_collector")
    image_paths = _collect_multimodal_images(payload.approval_links, Path("."))
    if not image_paths:
        components.append(
            _finish_component(
                images_component,
                status="error",
                details={"image_count": 0},
                error="No images found for multimodal request",
            )
        )
        raise RuntimeError("No images found for multimodal request. Check system-information/<system>/img.")

    components.append(
        _finish_component(
            images_component,
            status="success",
            details={
                "image_count": len(image_paths),
                "sample_images": image_paths[:3],
                "max_images": _DEFAULT_MAX_IMAGES,
            },
        )
    )

    prompt_builder_component = _start_component("prompt_builder_v5")
    conditions_text_raw, conditions_count = build_conditions_block(payload.conditions)
    conditions_text_de, _ = build_conditions_block_de(payload.conditions)
    full_prompt = build_prompt_v5(
        template=template,
        system=payload.system,
        system_name=payload.system_name,
        value=payload.value,
        conditions=payload.conditions,
        docs_text=docs_for_prompt,
    )
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

    llm_component = _start_component("llm_client_multimodal")
    try:
        llm_response = generate_multimodal_component(
            prompt=full_prompt,
            image_paths=image_paths,
            llm=payload.llm,
            temperature=payload.temperature,
        )
        components.append(
            _finish_component(
                llm_component,
                status="success",
                details={"model": llm_response.model, "image_count": len(image_paths)},
                input_tokens=llm_response.input_tokens,
                output_tokens=llm_response.output_tokens,
            )
        )
    except Exception as exc:
        components.append(
            _finish_component(
                llm_component,
                status="error",
                error=str(exc),
            )
        )
        raise RuntimeError(f"Multimodal LLM generation failed: {exc}") from exc

    parser_component = _start_component("output_parser")
    try:
        extracted_value = parse_extracted_value(llm_response.text)
    except Exception as exc:
        components.append(
            _finish_component(
                parser_component,
                status="error",
                details={"parsed": False},
                error=str(exc),
            )
        )
        raise RuntimeError(f"Output parsing failed: {exc}") from exc

    components.append(
        _finish_component(
            parser_component,
            status="success",
            details={"parsed": extracted_value is not None},
        )
    )

    is_match = evaluate_match(extracted_value, payload.expected_value)

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
