"""Direct Q&A pipeline v1: answer a question from a provided text chunk.

Design intent
-------------
This pipeline is designed for the ACCORD-NLP/CODE-ACCORD-Entities dataset and
similar pre-chunked datasets where the text passage (`content`) and the question
(`question`) are already provided as part of the experiment payload.

Instead of fetching and chunking PDFs, the pipeline:
  1. Loads a simple English prompt template (direct_qa_v1.txt).
  2. Substitutes {{QUESTION}} and {{CONTENT}} placeholders.
  3. Calls the LLM once.
  4. Parses the JSON response for `extracted_value`.
  5. Evaluates correctness with a soft matcher that accepts different numeric
     representations (e.g. "90" == "90%" == "90 percent").

Soft match rules
----------------
- Exact numeric equality (float comparison with epsilon 1e-9) always matches.
- If the LLM returns a string containing the expected number, it also matches
  (e.g. expected="90", extracted="90%" → match).
- Case-insensitive string containment is the final fallback for non-numeric values.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any, Callable

from app.models import ComponentLog, ExperimentRequest, ExperimentResponse, ExperimentResult
from app.services.components.llm_client_component import generate_text_component
from app.services.components.output_parser_component import parse_extracted_payload
from app.services.components.result_matcher_component import evaluate_match
from app.services.prompt_loader import load_prompt_template


# ---------------------------------------------------------------------------
# Helpers (copied from v9 to keep this module self-contained)
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
# Soft matcher
# ---------------------------------------------------------------------------

def _soft_evaluate_match(
    extracted_value: Any,
    expected_value: Any,
) -> bool:
    """Soft match that accepts different numeric representations.

    Matching order:
    1. Exact match via the standard ``evaluate_match`` (numeric epsilon + string casefold).
    2. Numeric containment: extract all numbers from the extracted string and
       check if the expected number appears among them.
    3. String containment: expected string appears inside the extracted string
       (case-insensitive).
    """
    # Level 1: standard exact match
    if evaluate_match(extracted_value, expected_value):
        return True

    if expected_value is None or extracted_value is None:
        return False

    expected_str = str(expected_value).strip()
    extracted_str = str(extracted_value).strip()

    # Level 2: numeric containment
    expected_nums = re.findall(r"[-+]?\d+(?:[.,]\d+)?", expected_str)
    extracted_nums = re.findall(r"[-+]?\d+(?:[.,]\d+)?", extracted_str)
    if expected_nums and extracted_nums:
        expected_f = float(expected_nums[0].replace(",", "."))
        for n in extracted_nums:
            if abs(float(n.replace(",", ".")) - expected_f) < 1e-9:
                return True

    # Level 3: string containment
    if expected_str and extracted_str:
        if expected_str.lower() in extracted_str.lower():
            return True

    return False


def _parse_confidence(raw_confidence: Any) -> float | None:
    """Parse confidence into a bounded float in the range [0.0, 1.0]."""
    if raw_confidence is None:
        return None

    if isinstance(raw_confidence, (int, float)):
        parsed = float(raw_confidence)
    elif isinstance(raw_confidence, str):
        normalized = raw_confidence.strip().replace(",", ".")
        if not normalized:
            return None
        try:
            parsed = float(normalized)
        except ValueError:
            return None
    else:
        return None

    if 0.0 <= parsed <= 1.0:
        return parsed
    return None


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_direct_qa_v1(payload: ExperimentRequest) -> ExperimentResponse:
    """Execute the direct Q&A pipeline."""
    return _run_direct_qa(payload, pipeline_name="direct_qa_v1")


def _run_direct_qa(
    payload: ExperimentRequest,
    *,
    pipeline_name: str,
    additional_match: Callable[[Any, Any], bool] | None = None,
) -> ExperimentResponse:
    """Execute direct Q&A extraction for a registered pipeline variant.

    Requires ``payload.content`` (the text chunk) and ``payload.question``
    (the question to answer).  Both fields must be non-empty strings.
    """
    pipeline_started_at = _now_iso()
    components: list[ComponentLog] = []

    content = payload.content or ""
    question = payload.question or ""

    if not content:
        raise ValueError(f"{pipeline_name} requires a non-empty 'content' field in the payload.")
    if not question:
        raise ValueError(f"{pipeline_name} requires a non-empty 'question' field in the payload.")

    # 1) Load prompt template
    prompt_component = _start_component("prompt_loader")
    template = load_prompt_template(payload.prompt)
    components.append(
        _finish_component(
            prompt_component,
            status="success",
            details={"prompt_name": payload.prompt},
        )
    )

    # 2) Build prompt
    builder_component = _start_component("prompt_builder")
    full_prompt = (
        template
        .replace("{{QUESTION}}", question)
        .replace("{{CONTENT}}", content)
    )
    components.append(
        _finish_component(
            builder_component,
            status="success",
            details={"prompt_length": len(full_prompt)},
        )
    )

    # 3) LLM call
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
                input_tokens=llm_response.input_tokens,
                output_tokens=llm_response.output_tokens,
                details={"model": payload.llm.value},
            )
        )
    except Exception as exc:
        components.append(
            _finish_component(llm_component, status="error", error=str(exc))
        )
        raise RuntimeError(f"LLM call failed: {exc}") from exc

    # 4) Parse extracted value and confidence
    parser_component = _start_component("output_parser")
    raw_output = llm_response.text
    parsed_data, _ = parse_extracted_payload(raw_output)
    raw_extracted = parsed_data.get("extracted_value")
    raw_confidence = parsed_data.get("confidence")

    # Normalise to float when the value is numeric, otherwise keep as string
    extracted_value: Any
    if isinstance(raw_extracted, (int, float)):
        extracted_value = float(raw_extracted)
    elif isinstance(raw_extracted, str):
        m = re.fullmatch(r"\s*[-+]?\d+(?:[.,]\d+)?\s*", raw_extracted)
        extracted_value = float(raw_extracted.replace(",", ".").strip()) if m else raw_extracted
    else:
        extracted_value = raw_extracted  # None or other type

    confidence = _parse_confidence(raw_confidence)

    components.append(
        _finish_component(
            parser_component,
            status="success",
            details={
                "raw_extracted": str(raw_extracted),
                "normalised": str(extracted_value),
                "raw_confidence": str(raw_confidence),
                "parsed_confidence": confidence,
            },
        )
    )

    # 5) Soft match
    is_match = _soft_evaluate_match(extracted_value, payload.expected_value)
    if not is_match and additional_match is not None:
        is_match = additional_match(extracted_value, payload.expected_value)

    pipeline_finished_at = _now_iso()

    total_input_tokens = sum(c.input_tokens for c in components)
    total_output_tokens = sum(c.output_tokens for c in components)

    result = ExperimentResult(
        expected_value=payload.expected_value,
        extracted_value=extracted_value,
        is_match=is_match,
        confidence=confidence,
        full_prompt=full_prompt,
        full_output=raw_output,
        input_tokens=total_input_tokens,
        output_tokens=total_output_tokens,
        temperature=payload.temperature,
        experiment_id=payload.experiment_id,
        pipeline_started_at=pipeline_started_at,
        pipeline_finished_at=pipeline_finished_at,
        experiment_description=payload.experiment_description,
        used_documents=[],
        system=payload.system or "",
        extracted_value_type="direct_qa",
        min_or_max=payload.min_or_max,
        used_llm=payload.llm.value,
        components=components,
    )

    return ExperimentResponse(
        status="success",
        experiment_id=payload.experiment_id,
        pipeline=pipeline_name,
        result=result,
    )
