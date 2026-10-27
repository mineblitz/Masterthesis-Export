"""Turtle KG pipeline v15 with staged Extract -> Normalize -> Formalize flow."""

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.models import ComponentLog, ExperimentRequest, ExperimentResponse, ExperimentResult
from app.services.components.keyword_context_extractor import (
    extract_keyword_context_chunks,
    resolve_search_terms,
)
from app.services.components.llm_client_component import generate_text_component
from app.services.components.output_parser_component import parse_extracted_value
from app.services.components.prompt_builder_v6 import build_prompt_v6
from app.services.components.result_matcher_component import evaluate_match
from app.services.prompt_loader import load_prompt_template


_NUMERIC_WITH_UNIT_RE = re.compile(r"(?P<number>\d+(?:[.,]\d+)?)\s*(?P<unit>mm|cm|m)\b", re.IGNORECASE)


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


def _resolve_marker_llm_markdown_path(document_path: str, base_dir: Path) -> tuple[Path, str]:
    source_path = (base_dir / document_path).resolve()
    if source_path.name.lower().endswith("_marker_llm.md"):
        marker_path = source_path
    else:
        marker_path = source_path.with_name(f"{source_path.stem}_marker_llm.md")
    if not marker_path.exists():
        raise FileNotFoundError(f"Marker LLM markdown not found: {marker_path}")
    return marker_path, marker_path.relative_to(base_dir.resolve()).as_posix()


def _extract_text_from_marker_llm_markdown(
    paths: list[str], base_dir: Path
) -> tuple[str, list[str]]:
    chunks: list[str] = []
    resolved_paths: list[str] = []
    for document_path in paths:
        marker_path, rel = _resolve_marker_llm_markdown_path(document_path, base_dir)
        cleaned_text = marker_path.read_text(encoding="utf-8")
        chunks.append(f"## Document: {rel}\n{cleaned_text}")
        resolved_paths.append(rel)
    return "\n\n".join(chunks), resolved_paths


def _resolve_context_window(payload: ExperimentRequest) -> tuple[int, int]:
    raw_common = getattr(payload, "context_window_lines", None)
    raw_before = getattr(payload, "context_lines_before", None)
    raw_after = getattr(payload, "context_lines_after", None)

    if raw_before is not None or raw_after is not None:
        raise ValueError(
            "Bitte nur 'context_window_lines' verwenden. "
            "Separate Werte 'context_lines_before' und 'context_lines_after' sind in v15 nicht erlaubt."
        )

    default_window = 5
    common = int(raw_common) if raw_common is not None else default_window
    return common, common


def _parse_keywords_output(raw_output: str) -> list[str]:
    cleaned = raw_output.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().endswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        json_match = re.search(r"\{[\s\S]*\}", cleaned)
        if not json_match:
            return []
        try:
            data = json.loads(json_match.group(0))
        except json.JSONDecodeError:
            return []

    keywords = data.get("keywords", [])
    if not isinstance(keywords, list):
        return []

    normalized: list[str] = []
    seen: set[str] = set()
    for keyword in keywords:
        candidate = str(keyword).strip()
        if not candidate:
            continue
        folded = candidate.casefold()
        if folded in seen:
            continue
        seen.add(folded)
        normalized.append(candidate)
    return normalized


def _parse_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", ".").strip())
        except ValueError:
            return None
    return None


def _is_dimensional_value(value_name: str) -> bool:
    lowered = value_name.casefold()
    return any(token in lowered for token in ("thickness", "diameter", "width", "height", "depth", "distance"))


def _unit_to_mm(value: float, unit: str) -> float:
    normalized_unit = unit.casefold()
    if normalized_unit == "mm":
        return value
    if normalized_unit == "cm":
        return value * 10.0
    if normalized_unit == "m":
        return value * 1000.0
    return value


def _extract_numeric_candidates(
    docs_text: str,
    *,
    search_terms: list[str],
    value_name: str,
) -> list[dict[str, Any]]:
    value_hints = [part for part in value_name.split("_") if part]
    normalized_terms = [term.casefold() for term in [*search_terms, *value_hints]]
    candidates: list[dict[str, Any]] = []

    for line in docs_text.splitlines():
        lowered = line.casefold()
        if normalized_terms and not any(term in lowered for term in normalized_terms):
            continue

        for match in _NUMERIC_WITH_UNIT_RE.finditer(line):
            parsed = _parse_float(match.group("number"))
            if parsed is None:
                continue
            unit = match.group("unit").lower()
            candidates.append(
                {
                    "raw_value": parsed,
                    "unit": unit,
                    "normalized_mm": _unit_to_mm(parsed, unit),
                    "line": line[:200],
                }
            )

    return candidates


def normalize_extracted_value_v15(
    *,
    extracted_value: Any,
    docs_text: str,
    search_terms: list[str],
    value_name: str,
) -> tuple[float | None, dict[str, Any]]:
    parsed_extracted = _parse_float(extracted_value)
    candidates = _extract_numeric_candidates(
        docs_text,
        search_terms=search_terms,
        value_name=value_name,
    )

    selected_candidate: dict[str, Any] | None = None
    if candidates and parsed_extracted is not None:
        selected_candidate = min(
            candidates,
            key=lambda item: min(
                abs(item["raw_value"] - parsed_extracted),
                abs(item["normalized_mm"] - parsed_extracted),
            ),
        )
    elif candidates:
        selected_candidate = candidates[0]

    normalized_value = parsed_extracted
    normalization_applied = False

    if selected_candidate and _is_dimensional_value(value_name):
        raw_diff = float("inf") if parsed_extracted is None else abs(selected_candidate["raw_value"] - parsed_extracted)
        normalized_diff = (
            float("inf")
            if parsed_extracted is None
            else abs(selected_candidate["normalized_mm"] - parsed_extracted)
        )

        if parsed_extracted is None or raw_diff <= normalized_diff:
            normalized_value = selected_candidate["normalized_mm"]
            normalization_applied = selected_candidate["raw_value"] != selected_candidate["normalized_mm"]

    details = {
        "candidate_count": len(candidates),
        "selected_candidate": selected_candidate,
        "normalization_applied": normalization_applied,
        "raw_extracted_value": parsed_extracted,
        "normalized_extracted_value": normalized_value,
    }
    return normalized_value, details


def _slugify(text: str) -> str:
    lowered = text.casefold()
    cleaned = re.sub(r"[^a-z0-9]+", "_", lowered)
    cleaned = cleaned.strip("_")
    return cleaned or "unknown"


def _format_decimal(value: float) -> str:
    rendered = f"{value:.6f}".rstrip("0").rstrip(".")
    if "." not in rendered:
        rendered = f"{rendered}.0"
    return rendered


def build_formalized_turtle_v15(
    *,
    payload: ExperimentRequest,
    extracted_value: float | None,
    used_documents: list[str],
) -> str:
    subject = f"system_{_slugify(payload.system)}_{_slugify(payload.system_name)}"
    predicate = _slugify(payload.value)
    source = used_documents[0] if used_documents else "unknown_source"

    if extracted_value is None:
        return (
            "@prefix bs: <https://example.org/brandschutz/> .\n"
            "@prefix prov: <http://www.w3.org/ns/prov#> .\n\n"
            f"bs:{subject} prov:wasDerivedFrom \"{source}\" ."
        )

    literal = _format_decimal(extracted_value)
    return (
        "@prefix bs: <https://example.org/brandschutz/> .\n"
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n"
        "@prefix prov: <http://www.w3.org/ns/prov#> .\n\n"
        f"bs:{subject} bs:{predicate} \"{literal}\"^^xsd:decimal .\n"
        f"bs:{subject} prov:wasDerivedFrom \"{source}\" ."
    )


def run_turtle_kg_keyword_v15(payload: ExperimentRequest) -> ExperimentResponse:
    """
    Pipeline v15:
    1) Extract: LLM keyword expansion + keyword context chunk extraction + numeric extraction.
    2) Normalize: deterministic numeric canonicalization (unit-aware for dimensional values).
    3) Formalize: deterministic Turtle snippet rendering from normalized value.
    """
    pipeline_started_at = _now_iso()
    components: list[ComponentLog] = []
    total_input_tokens = 0
    total_output_tokens = 0

    prompt_names = [p.strip() for p in payload.prompt.split(",") if p.strip()]
    if not prompt_names:
        raise ValueError("payload.prompt muss mindestens einen Promptnamen enthalten")
    keyword_prompt_name = prompt_names[0]
    extract_prompt_name = prompt_names[1] if len(prompt_names) > 1 else prompt_names[0]

    prompt_component = _start_component("prompt_loader")
    keyword_template = load_prompt_template(keyword_prompt_name)
    extract_template = load_prompt_template(extract_prompt_name)
    components.append(
        _finish_component(
            prompt_component,
            status="success",
            details={
                "keyword_prompt": keyword_prompt_name,
                "extract_prompt": extract_prompt_name,
            },
        )
    )

    marker_component = _start_component("marker_llm_markdown_extractor")
    try:
        docs_text, used_documents = _extract_text_from_marker_llm_markdown(
            paths=payload.approval_links,
            base_dir=Path("."),
        )
        components.append(
            _finish_component(
                marker_component,
                status="success",
                details={
                    "document_count": len(used_documents),
                    "method": "marker_llm_markdown",
                },
            )
        )
    except Exception as exc:
        components.append(
            _finish_component(marker_component, status="error", error=str(exc))
        )
        raise RuntimeError(f"Marker LLM markdown extraction failed: {exc}") from exc

    keyword_prompt = build_prompt_v6(
        template=keyword_template,
        system=payload.system,
        system_name=payload.system_name,
        value=payload.value,
        docs_text="",
        conditions_turtle=payload.conditions_turtle,
    )

    keyword_llm_component = _start_component("llm_keyword_expand")
    try:
        keyword_response = generate_text_component(
            prompt=keyword_prompt,
            llm=payload.llm,
            temperature=payload.temperature,
        )
        total_input_tokens += keyword_response.input_tokens
        total_output_tokens += keyword_response.output_tokens
        components.append(
            _finish_component(
                keyword_llm_component,
                status="success",
                details={"model": keyword_response.model, "step": "keyword_expand"},
                input_tokens=keyword_response.input_tokens,
                output_tokens=keyword_response.output_tokens,
            )
        )
    except Exception as exc:
        components.append(
            _finish_component(keyword_llm_component, status="error", error=str(exc))
        )
        raise RuntimeError(f"Step-1 LLM (keyword expand) failed: {exc}") from exc

    keyword_parser_component = _start_component("keyword_output_parser")
    expanded_keywords = _parse_keywords_output(keyword_response.text)
    if not expanded_keywords:
        expanded_keywords = resolve_search_terms(payload.value, None)
        fallback_mode = True
    else:
        fallback_mode = False
    components.append(
        _finish_component(
            keyword_parser_component,
            status="success",
            details={
                "keyword_count": len(expanded_keywords),
                "keywords": expanded_keywords,
                "fallback_to_default_keywords": fallback_mode,
                "response_preview": keyword_response.text[:300],
            },
        )
    )

    keyword_chunk_component = _start_component("keyword_context_extractor")
    try:
        lines_before, lines_after = _resolve_context_window(payload)
        keyword_result = extract_keyword_context_chunks(
            docs_text,
            value=payload.value,
            search_terms=expanded_keywords,
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
            _finish_component(keyword_chunk_component, status="error", error=str(exc))
        )
        raise RuntimeError(f"Keyword context extraction failed: {exc}") from exc

    extract_prompt = build_prompt_v6(
        template=extract_template,
        system=payload.system,
        system_name=payload.system_name,
        value=payload.value,
        docs_text=docs_for_prompt,
        conditions_turtle=payload.conditions_turtle,
    )

    extract_llm_component = _start_component("llm_extract")
    try:
        extract_response = generate_text_component(
            prompt=extract_prompt,
            llm=payload.llm,
            temperature=payload.temperature,
        )
        total_input_tokens += extract_response.input_tokens
        total_output_tokens += extract_response.output_tokens
        components.append(
            _finish_component(
                extract_llm_component,
                status="success",
                details={"model": extract_response.model, "step": "extract"},
                input_tokens=extract_response.input_tokens,
                output_tokens=extract_response.output_tokens,
            )
        )
    except Exception as exc:
        components.append(
            _finish_component(extract_llm_component, status="error", error=str(exc))
        )
        raise RuntimeError(f"Step-2 LLM (extract) failed: {exc}") from exc

    parser_component = _start_component("output_parser")
    try:
        extracted_value = parse_extracted_value(extract_response.text)
    except Exception as exc:
        components.append(
            _finish_component(
                parser_component,
                status="error",
                details={"parsed": False},
                error=str(exc),
            )
        )
        raise RuntimeError(f"Step-2 output parsing failed: {exc}") from exc

    components.append(
        _finish_component(
            parser_component,
            status="success",
            details={"parsed": extracted_value is not None},
        )
    )

    normalize_component = _start_component("normalization_stage_v15")
    normalized_value, normalization_details = normalize_extracted_value_v15(
        extracted_value=extracted_value,
        docs_text=docs_for_prompt,
        search_terms=expanded_keywords,
        value_name=payload.value,
    )
    components.append(
        _finish_component(
            normalize_component,
            status="success",
            details=normalization_details,
        )
    )

    formalize_component = _start_component("turtle_formalization_v15")
    formalized_turtle = build_formalized_turtle_v15(
        payload=payload,
        extracted_value=normalized_value,
        used_documents=used_documents,
    )
    components.append(
        _finish_component(
            formalize_component,
            status="success",
            details={
                "formalized_turtle_preview": formalized_turtle[:600],
                "has_extracted_value": normalized_value is not None,
            },
        )
    )

    is_match = evaluate_match(normalized_value, payload.expected_value)

    full_prompt = (
        f"=== STEP 1: KEYWORD EXPANSION ===\n{keyword_prompt}\n\n"
        f"=== STEP 1 RESPONSE ===\n{keyword_response.text}\n\n"
        f"=== EXPANDED KEYWORDS ===\n{json.dumps(expanded_keywords, ensure_ascii=False)}\n\n"
        f"=== STEP 2: EXTRACT ===\n{extract_prompt}"
    )

    full_output = (
        f"=== EXTRACT RESPONSE ===\n{extract_response.text}\n\n"
        f"=== FORMALIZED TURTLE v15 ===\n{formalized_turtle}"
    )

    result = ExperimentResult(
        expected_value=payload.expected_value,
        extracted_value=normalized_value,
        is_match=is_match,
        full_prompt=full_prompt,
        full_output=full_output,
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
