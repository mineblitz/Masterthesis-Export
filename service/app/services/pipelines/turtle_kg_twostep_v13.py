"""Two-step Turtle KG pipeline v13 — locate then extract.

Step 1 (locate):  LLM scans the full document and returns relevant passages.
Step 2 (extract): A second LLM call receives only the located passages and
                  extracts the final numeric value.
"""

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.models import ComponentLog, ExperimentRequest, ExperimentResponse, ExperimentResult
from app.services.components.llm_client_component import generate_text_component
from app.services.components.output_parser_component import parse_extracted_value
from app.services.components.result_matcher_component import evaluate_match
from app.services.components.prompt_builder_v6 import (
    build_conditions_block_from_turtle,
    build_conditions_raw_from_turtle,
    build_prompt_v6,
    describe_value,
    build_search_target_sentence,
)
from app.services.prompt_loader import load_prompt_template


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Marker LLM markdown extraction (reused from v12)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Step-1 output parser: extract relevant_passages from LLM JSON
# ---------------------------------------------------------------------------

def _repair_json(text: str) -> str:
    """Attempt to repair common LLM JSON issues inside string values.

    Strategy: walk through the text and fix a few common issues that appear in
    LocalAI responses:
    - unescaped double-quotes inside string values
    - raw newlines / carriage returns / tabs inside string values
    """
    result: list[str] = []
    i = 0
    in_string = False
    escaped = False

    while i < len(text):
        ch = text[i]

        if escaped:
            result.append(ch)
            escaped = False
            i += 1
            continue

        if ch == "\\":
            escaped = True
            result.append(ch)
            i += 1
            continue

        if ch == '"':
            if not in_string:
                # Opening a string
                in_string = True
                result.append(ch)
            else:
                # Could be end-of-string or an unescaped interior quote.
                # Peek ahead: if next non-whitespace is a structural char
                # (, : } ] or another key start "), it's end-of-string.
                rest = text[i + 1:].lstrip()
                if not rest or rest[0] in (",", ":", "}", "]", '"'):
                    in_string = False
                    result.append(ch)
                else:
                    # Unescaped interior quote — escape it
                    result.append('\\"')
            i += 1
            continue

        if in_string and ch == "\n":
            result.append("\\n")
            i += 1
            continue

        if in_string and ch == "\r":
            i += 1
            continue

        if in_string and ch == "\t":
            result.append("\\t")
            i += 1
            continue

        result.append(ch)
        i += 1

    return "".join(result)


def _append_missing_closers(text: str) -> str:
    """Append missing closing brackets/braces for truncated JSON payloads."""
    closers: list[str] = []
    in_string = False
    escaped = False

    for ch in text:
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            closers.append("}")
        elif ch == "[":
            closers.append("]")
        elif ch in {"}", "]"} and closers and closers[-1] == ch:
            closers.pop()

    return text + "".join(reversed(closers))


def _salvage_relevant_passages(text: str) -> dict[str, list[dict[str, Any]]] | None:
    """Best-effort salvage of already well-formed passage objects from partial JSON."""
    match = re.search(r'"relevant_passages"\s*:\s*\[', text)
    if not match:
        return None

    decoder = json.JSONDecoder()
    passages: list[dict[str, Any]] = []
    remainder = text[match.end():]
    index = 0

    while index < len(remainder):
        while index < len(remainder) and remainder[index] in " \t\r\n,":
            index += 1
        if index >= len(remainder) or remainder[index] == "]":
            break

        try:
            item, consumed = decoder.raw_decode(remainder[index:])
        except json.JSONDecodeError:
            break

        if not isinstance(item, dict):
            break

        passages.append(item)
        index += consumed

    if not passages:
        return None

    return {"relevant_passages": passages}


def _parse_locate_output(raw_output: str) -> list[dict[str, str]]:
    """Parse the Step-1 LLM output into a list of passage dicts.

    Expected format::

        {"relevant_passages": [{"section": "...", "text": "...", "relevance": "..."}]}

    Returns the list (may be empty). Raises ``ValueError`` on parse failure.
    """
    cleaned = raw_output.strip()

    # Strip markdown fences
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().endswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    # Try direct parse first
    data = _try_parse_json(cleaned)
    if data is None:
        # Extract JSON block from mixed text
        json_match = re.search(r"\{[\s\S]*\}", cleaned)
        if not json_match:
            raise ValueError(
                f"Step-1 LLM output did not contain valid JSON. Preview: {cleaned[:250]!r}"
            )
        data = _try_parse_json(json_match.group(0))
        if data is None:
            raise ValueError(
                f"Step-1 JSON parsing failed even after repair. Preview: {cleaned[:250]!r}"
            )

    passages = data.get("relevant_passages", [])
    if not isinstance(passages, list):
        raise ValueError(
            f"'relevant_passages' is not a list. Got: {type(passages).__name__}"
        )
    return passages


def _try_parse_json(text: str) -> dict | None:
    """Try to parse JSON, with automatic repair on failure."""
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    repaired = _repair_json(text)

    # Attempt repair and retry
    try:
        data = json.loads(repaired)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    # If the payload is truncated, append the missing structural closers.
    try:
        balanced = _append_missing_closers(repaired)
        data = json.loads(balanced)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    salvaged = _salvage_relevant_passages(repaired)
    if salvaged is not None:
        return salvaged

    return None


def _format_passages_for_extraction(passages: list[dict[str, str]]) -> str:
    """Render located passages into a text block for the Step-2 prompt."""
    if not passages:
        return "(Keine relevanten Stellen gefunden.)"

    lines: list[str] = []
    for idx, p in enumerate(passages, start=1):
        section = p.get("section", "unbekannt")
        text = p.get("text", "")
        lines.append(f"--- Stelle {idx} (Abschnitt: {section}) ---")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Step-2 prompt builder
# ---------------------------------------------------------------------------

def _build_extract_prompt(
    template: str,
    system: str,
    system_name: str,
    value: str,
    conditions_turtle: str | None,
    passages_text: str,
) -> str:
    """Build the Step-2 extraction prompt.

    The template may use the standard v6 placeholders plus
    ``{{RELEVANT_PASSAGES}}``.
    """
    value_description = describe_value(value)
    search_target_sentence = build_search_target_sentence(value)
    conditions_block_de, _ = build_conditions_block_from_turtle(conditions_turtle or "")
    conditions_block_raw = build_conditions_raw_from_turtle(conditions_turtle or "")

    placeholders = {
        "{{SYSTEM}}": system,
        "{{SYSTEM_NAME}}": system_name,
        "{{VALUE}}": value,
        "{{VALUE_DESCRIPTION}}": value_description,
        "{{SEARCH_TARGET_SENTENCE}}": search_target_sentence,
        "{{CONDITIONS}}": conditions_block_raw,
        "{{CONDITIONS_DE}}": conditions_block_de,
        "{{CONDITIONS_TURTLE}}": (conditions_turtle or "").strip(),
        "{{RELEVANT_PASSAGES}}": passages_text,
    }

    rendered = template
    for token, val in placeholders.items():
        rendered = rendered.replace(token, val)
    return rendered


# ---------------------------------------------------------------------------
# Pipeline entry point
# ---------------------------------------------------------------------------

def run_turtle_kg_twostep_v13(payload: ExperimentRequest) -> ExperimentResponse:
    """
    Pipeline v13: Two-step Turtle KG extraction.

    1. **Locate** — an LLM scans the full Marker LLM document and identifies
       all passages relevant to the query conditions.
    2. **Extract** — a second LLM call receives *only* the located passages
       and extracts the final numeric value.

    Prompt templates are specified via ``payload.prompt`` as a comma-separated
    pair: ``"turtle_locate_v1.txt,turtle_extract_v1.txt"``.  If only one
    template is given it is used for both steps (backward-compatible fallback,
    though typically you want two distinct templates).
    """
    pipeline_started_at = _now_iso()
    components: list[ComponentLog] = []
    total_input_tokens = 0
    total_output_tokens = 0

    # --- 0. Resolve prompt templates -------------------------------------------
    prompt_names = [p.strip() for p in payload.prompt.split(",")]
    locate_prompt_name = prompt_names[0]
    extract_prompt_name = prompt_names[1] if len(prompt_names) > 1 else prompt_names[0]

    prompt_component = _start_component("prompt_loader")
    locate_template = load_prompt_template(locate_prompt_name)
    extract_template = load_prompt_template(extract_prompt_name)
    components.append(
        _finish_component(
            prompt_component,
            status="success",
            details={
                "locate_prompt": locate_prompt_name,
                "extract_prompt": extract_prompt_name,
            },
        )
    )

    # --- 1. Extract document text (Marker LLM markdown) -------------------------
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

    # --- 2. Step 1: LOCATE — find relevant passages ----------------------------
    turtle_snippet = payload.conditions_turtle or ""
    conditions_de, cond_count = build_conditions_block_from_turtle(turtle_snippet)

    locate_prompt = build_prompt_v6(
        template=locate_template,
        system=payload.system,
        system_name=payload.system_name,
        value=payload.value,
        docs_text=docs_text,
        conditions_turtle=payload.conditions_turtle,
    )

    locate_llm_component = _start_component("llm_locate")
    try:
        locate_response = generate_text_component(
            prompt=locate_prompt,
            llm=payload.llm,
            temperature=payload.temperature,
        )
        total_input_tokens += locate_response.input_tokens
        total_output_tokens += locate_response.output_tokens
        components.append(
            _finish_component(
                locate_llm_component,
                status="success",
                details={"model": locate_response.model, "step": "locate"},
                input_tokens=locate_response.input_tokens,
                output_tokens=locate_response.output_tokens,
            )
        )
    except Exception as exc:
        components.append(
            _finish_component(locate_llm_component, status="error", error=str(exc))
        )
        raise RuntimeError(f"Step-1 LLM (locate) failed: {exc}") from exc

    # --- 3. Parse locate output -------------------------------------------------
    locate_parser_component = _start_component("locate_output_parser")
    try:
        passages = _parse_locate_output(locate_response.text)
        passages_text = _format_passages_for_extraction(passages)
        components.append(
            _finish_component(
                locate_parser_component,
                status="success",
                details={
                    "passage_count": len(passages),
                    "passages_preview": passages_text[:500],
                },
            )
        )
    except Exception as exc:
        components.append(
            _finish_component(
                locate_parser_component, status="error", error=str(exc)
            )
        )
        raise RuntimeError(f"Step-1 output parsing failed: {exc}") from exc

    # --- 4. Step 2: EXTRACT — extract value from passages ----------------------
    extract_prompt = _build_extract_prompt(
        template=extract_template,
        system=payload.system,
        system_name=payload.system_name,
        value=payload.value,
        conditions_turtle=payload.conditions_turtle,
        passages_text=passages_text,
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

    # --- 5. Parse extract output -----------------------------------------------
    extract_parser_component = _start_component("output_parser")
    try:
        extracted_value = parse_extracted_value(extract_response.text)
    except Exception as exc:
        components.append(
            _finish_component(
                extract_parser_component, status="error", error=str(exc)
            )
        )
        raise RuntimeError(f"Step-2 output parsing failed: {exc}") from exc

    components.append(
        _finish_component(
            extract_parser_component,
            status="success",
            details={"parsed": extracted_value is not None},
        )
    )

    # --- 6. Evaluate match ------------------------------------------------------
    is_match = evaluate_match(extracted_value, payload.expected_value)

    # Combine prompts for traceability
    full_prompt = (
        f"=== STEP 1: LOCATE ===\n{locate_prompt}\n\n"
        f"=== STEP 1 RESPONSE ===\n{locate_response.text}\n\n"
        f"=== STEP 2: EXTRACT ===\n{extract_prompt}"
    )

    result = ExperimentResult(
        expected_value=payload.expected_value,
        extracted_value=extracted_value,
        is_match=is_match,
        full_prompt=full_prompt,
        full_output=extract_response.text,
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
