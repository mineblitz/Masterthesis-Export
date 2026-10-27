"""Output parser for strict label extraction experiments."""

import json
import re


_ALLOWED_VALUES = {
    "beides": "Beides",
    "beide": "Beides",
    "kabel": "Kabel",
    "rohre": "Rohre",
    "rohr": "Rohre",
}


def parse_extracted_label(raw_output: str) -> str | None:
    """Parse strict JSON output and normalize extracted_value to one of 3 labels."""
    cleaned_output = raw_output.strip()

    if cleaned_output.startswith("```"):
        lines = cleaned_output.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().endswith("```"):
            lines = lines[:-1]
        cleaned_output = "\n".join(lines).strip()

    try:
        data = json.loads(cleaned_output)
    except json.JSONDecodeError:
        json_match = re.search(r"\{[\s\S]*\}", cleaned_output)
        if not json_match:
            preview = cleaned_output[:250]
            raise ValueError(
                "LLM output did not contain valid JSON. "
                f"Output preview: {preview!r}"
            )
        try:
            data = json.loads(json_match.group(0))
        except json.JSONDecodeError as exc:
            preview = cleaned_output[:250]
            raise ValueError(
                "LLM output contained JSON-like text but parsing failed. "
                f"Output preview: {preview!r}"
            ) from exc

    extracted = data.get("extracted_value")
    if extracted is None:
        return None

    if not isinstance(extracted, str):
        raise ValueError("extracted_value must be a string or null")

    normalized = extracted.strip().casefold()
    normalized = re.sub(r"\s+", " ", normalized)
    if not normalized:
        return None

    if normalized in _ALLOWED_VALUES:
        return _ALLOWED_VALUES[normalized]

    raise ValueError(
        "Invalid extracted_value for label experiment. "
        "Allowed: Beides, Kabel, Rohre, null"
    )
