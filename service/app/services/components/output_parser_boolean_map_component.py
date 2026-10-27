"""Output parser for strict boolean-map extraction experiments."""

import json
import re


def _repair_json(text: str) -> str:
    """Repair common LLM JSON issues inside string values."""
    result: list[str] = []
    index = 0
    in_string = False
    escaped = False

    while index < len(text):
        char = text[index]

        if escaped:
            result.append(char)
            escaped = False
            index += 1
            continue

        if char == "\\":
            escaped = True
            result.append(char)
            index += 1
            continue

        if char == '"':
            if not in_string:
                in_string = True
                result.append(char)
            else:
                remainder = text[index + 1 :].lstrip()
                if not remainder or remainder[0] in (",", ":", "}", "]"):
                    in_string = False
                    result.append(char)
                else:
                    result.append('\\"')
            index += 1
            continue

        if in_string and char == "\n":
            result.append("\\n")
            index += 1
            continue

        if in_string and char == "\r":
            index += 1
            continue

        if in_string and char == "\t":
            result.append("\\t")
            index += 1
            continue

        result.append(char)
        index += 1

    return "".join(result)


def _load_json_object(raw_output: str) -> dict:
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
        repaired_output = _repair_json(cleaned_output)
        try:
            data = json.loads(repaired_output)
        except json.JSONDecodeError:
            json_match = re.search(r"\{[\s\S]*\}", repaired_output)
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

    if not isinstance(data, dict):
        raise ValueError("LLM output root must be a JSON object")

    return data


def _coerce_boolean(value: bool | str, *, key: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
    raise ValueError(f"extracted_value['{key}'] must be a boolean")


def parse_extracted_boolean_map(
    raw_output: str,
    *,
    expected_keys: list[str] | None = None,
) -> tuple[dict[str, bool] | None, float | None]:
    """Parse strict JSON output and normalize extracted_value to a boolean map with confidence.
    
    Returns:
        Tuple of (extracted boolean map, confidence value or None)
    """
    data = _load_json_object(raw_output)

    extracted = data.get("extracted_value")
    confidence = data.get("confidence")
    
    if extracted is None:
        return None, None
    if not isinstance(extracted, dict):
        raise ValueError("extracted_value must be an object or null")

    normalized: dict[str, bool] = {}
    for key, value in extracted.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError("extracted_value keys must be non-empty strings")
        normalized[key] = _coerce_boolean(value, key=key)

    # Validate and normalize confidence
    if confidence is not None:
        try:
            confidence = float(confidence)
            if not (0.0 <= confidence <= 1.0):
                confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
        except (ValueError, TypeError):
            confidence = None

    if expected_keys is None:
        return normalized, confidence

    missing_keys = [key for key in expected_keys if key not in normalized]
    extra_keys = [key for key in normalized if key not in expected_keys]
    if missing_keys or extra_keys:
        raise ValueError(
            "extracted_value must contain exactly the requested keys. "
            f"Missing: {missing_keys}; Extra: {extra_keys}"
        )

    return {key: normalized[key] for key in expected_keys}, confidence