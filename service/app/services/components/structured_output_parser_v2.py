"""Structured output parser backed by instructor + Pydantic schema enforcement.

New component for v27+ pipelines. Replaces the regex/json.loads repair pattern in
output_parser_component.py with instructor-enforced schema decoding and automatic
retry on validation failure. Existing output parsers are unchanged.
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, field_validator

from app.models import LLMModel, LLMProvider
from app.settings import settings

logger = logging.getLogger("app.components.structured_output_parser_v2")


# ---------------------------------------------------------------------------
# Output schemas
# ---------------------------------------------------------------------------

class ScalarExtractionOutput(BaseModel):
    """Schema for a single numeric extraction result."""
    extracted_value: float | None = None
    confidence: float | None = None
    evidence_summary: str | None = None

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, v: Any) -> float | None:
        if v is None:
            return None
        try:
            clamped = max(0.0, min(1.0, float(v)))
            return round(clamped, 4)
        except (TypeError, ValueError):
            return None


# ---------------------------------------------------------------------------
# Provider client resolution
# ---------------------------------------------------------------------------

def _get_instructor_client(llm: LLMModel) -> Any:
    """Build an instructor-patched OpenAI client for the given LLMModel.

    Raises:
        ImportError: If instructor is not installed.
        ValueError: If the provider from LLMModel is not recognised.
    """
    try:
        import instructor  # type: ignore[import-untyped]
        from openai import OpenAI
    except ImportError as exc:
        raise ImportError(
            "instructor and openai are required for structured_output_parser_v2. "
            "Install with: pip install instructor"
        ) from exc

    provider_value, model_id = llm.value.split(":", 1)
    provider = LLMProvider(provider_value)

    if provider == LLMProvider.LOCALAI:
        raw_client = OpenAI(
            base_url=settings.localai_base_url,
            api_key=settings.localai_api_key,
        )
    elif provider == LLMProvider.OPENROUTER:
        api_key = settings.openrouter_api_key or settings.open_router_api_key or ""
        raw_client = OpenAI(
            base_url=settings.openrouter_base_url,
            api_key=api_key,
        )
    elif provider == LLMProvider.HAWKI:
        raw_client = OpenAI(
            base_url=settings.hawki_base_url,
            api_key=settings.hawki_api_key,
        )
    elif provider == LLMProvider.OPENAI:
        raw_client = OpenAI(api_key=settings.openai_api_key or "")
    else:
        raise ValueError(f"Unsupported provider for structured_output_parser_v2: {provider}")

    # Use JSON mode — compatible with all OpenAI-compatible endpoints.
    # Mode.JSON instructs instructor to ask the model for a JSON object and
    # validates it against the Pydantic schema, retrying on failure.
    return instructor.from_openai(raw_client, mode=instructor.Mode.JSON), model_id


# ---------------------------------------------------------------------------
# Public parse functions
# ---------------------------------------------------------------------------

def parse_scalar_v2(
    *,
    prompt: str,
    llm: LLMModel,
    temperature: float | None = None,
    max_retries: int = 3,
) -> ScalarExtractionOutput:
    """Extract a single numeric value from the LLM using instructor schema enforcement.

    The LLM is asked to return JSON that matches ScalarExtractionOutput.
    If the output fails Pydantic validation, instructor automatically feeds
    the validation error back to the model and retries up to max_retries times.

    Args:
        prompt: The full prompt string to send.
        llm: Which LLM model to use.
        temperature: Sampling temperature (None = provider default).
        max_retries: Maximum instructor retry attempts on schema violations.

    Returns:
        ScalarExtractionOutput with extracted_value and confidence.

    Raises:
        ImportError: If instructor is not installed.
        RuntimeError: If the LLM call fails after all retries.
    """
    client, model_id = _get_instructor_client(llm)

    messages = [{"role": "user", "content": prompt}]
    kwargs: dict[str, Any] = {
        "model": model_id,
        "response_model": ScalarExtractionOutput,
        "messages": messages,
        "max_retries": max_retries,
    }
    if temperature is not None:
        kwargs["temperature"] = temperature

    try:
        result: ScalarExtractionOutput = client.chat.completions.create(**kwargs)
        return result
    except Exception as exc:
        logger.warning("instructor extraction failed: %s — returning empty result", exc)
        raise RuntimeError(f"structured_output_parser_v2 failed: {exc}") from exc
