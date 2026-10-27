"""Prompt builder component v3 with flexible extraction conditions."""

from app.models import ExperimentRequest


VALUE_DESCRIPTIONS: dict[str, str] = {
    "thickness": "Bauteildicke in mm",
    "opening_width": "Oeffnungsbreite in mm",
    "opening_height": "Oeffnungshoehe in mm",
    "diameter": "Oeffnungsdurchmesser in mm",
    "fire_resistance_class": "Feuerwiderstandsklasse, z. B. 30, 60, 90 oder 120",
}


def describe_value(value: str) -> str:
    """Get German description for a value key."""
    return VALUE_DESCRIPTIONS.get(value, f"Gesuchter Wert: {value}")


def _normalize_conditions(
    conditions: list[ExperimentRequest.Condition] | None,
) -> list[ExperimentRequest.Condition]:
    if not conditions:
        return []

    normalized: list[ExperimentRequest.Condition] = []
    for condition in conditions:
        condition_type = condition.type.strip()
        condition_value = condition.value.strip()
        if not condition_type or not condition_value:
            continue
        normalized.append(
            ExperimentRequest.Condition(type=condition_type, value=condition_value)
        )
    return normalized


def build_conditions_block(
    conditions: list[ExperimentRequest.Condition] | None,
) -> tuple[str, int]:
    """Build a stable, readable condition block for prompt injection."""
    normalized = _normalize_conditions(conditions)
    if not normalized:
        return "Keine zusaetzlichen Bedingungen vorgegeben.", 0

    lines = ["Gegebene Bedingungen (alle muessen gleichzeitig erfuellt sein):"]
    for idx, condition in enumerate(normalized, start=1):
        if condition.id is None:
            lines.append(f"{idx}. {condition.type} = {condition.value}")
        else:
            lines.append(f"{idx}. {condition.type} (id={condition.id}) = {condition.value}")

    return "\n".join(lines), len(normalized)


def build_prompt_v3(
    template: str,
    system: str,
    system_name: str,
    value: str,
    docs_text: str,
    conditions: list[ExperimentRequest.Condition] | None = None,
) -> str:
    """
    Build a complete prompt for value extraction with explicit conditions.

    Unlike previous versions this does not rely on min/max selection; it requests
    the concrete value that matches all provided conditions.
    """
    value_description = describe_value(value)
    conditions_block, _ = build_conditions_block(conditions)

    placeholders = {
        "{{SYSTEM}}": system,
        "{{SYSTEM_NAME}}": system_name,
        "{{VALUE}}": value,
        "{{VALUE_DESCRIPTION}}": value_description,
        "{{CONDITIONS}}": conditions_block,
        "{{DOCUMENT_CONTENT}}": docs_text,
    }

    rendered = template
    for token, value_str in placeholders.items():
        rendered = rendered.replace(token, value_str)

    return rendered
