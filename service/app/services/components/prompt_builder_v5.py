"""Prompt builder component v5 with German condition translation and search sentence."""

from app.models import ExperimentRequest


VALUE_DESCRIPTIONS: dict[str, str] = {
    "min_thickness": "minimale erlaubte Bauteildicke in mm",
    "max_thickness": "maximale erlaubte Bauteildicke in mm",
    "min_opening_width": "minimale erlaubte Oeffnungsbreite in mm",
    "max_opening_width": "maximale erlaubte Oeffnungsbreite in mm",
    "min_opening_height": "minimale erlaubte Oeffnungshoehe in mm",
    "max_opening_height": "maximale erlaubte Oeffnungshoehe in mm",
    "min_diameter": "minimaler erlaubter Oeffnungsdurchmesser in mm",
    "max_diameter": "maximaler erlaubter Oeffnungsdurchmesser in mm",
    "fire_resistance_class": "Feuerwiderstandsklasse, z. B. 30, 60, 90 oder 120",
    "thickness": "Bauteildicke in mm",
    "opening_width": "Oeffnungsbreite in mm",
    "opening_height": "Oeffnungshoehe in mm",
    "diameter": "Oeffnungsdurchmesser in mm",
}

CONDITION_TYPE_DE: dict[str, str] = {
    "material": "Material",
    "position": "Einbauposition",
    "position_type": "Einbauposition",
    "opening_type": "Oeffnungsart",
}

CONDITION_VALUE_DE: dict[str, str] = {
    "concrete": "Beton",
    "timberwork": "Holzbau",
    "brickwork": "Mauerwerk",
    "drywall": "Trockenbau",
    "plasterboard": "Gipskarton",
    "priowall": "PRIOWALL",
    "wall": "Wand",
    "ceiling": "Decke",
    "round": "rund",
    "rectangular": "rechteckig",
}

SEARCH_TARGET_SENTENCES: dict[str, str] = {
    "min_thickness": "Gesucht ist die minimale erlaubte Bauteildicke unter den folgenden Bedingungen.",
    "max_thickness": "Gesucht ist die maximale erlaubte Bauteildicke unter den folgenden Bedingungen.",
    "min_opening_width": "Gesucht ist die minimale erlaubte Oeffnungsbreite unter den folgenden Bedingungen.",
    "max_opening_width": "Gesucht ist die maximale erlaubte Oeffnungsbreite unter den folgenden Bedingungen.",
    "min_opening_height": "Gesucht ist die minimale erlaubte Oeffnungshoehe unter den folgenden Bedingungen.",
    "max_opening_height": "Gesucht ist die maximale erlaubte Oeffnungshoehe unter den folgenden Bedingungen.",
    "min_diameter": "Gesucht ist der minimale erlaubte Oeffnungsdurchmesser unter den folgenden Bedingungen.",
    "max_diameter": "Gesucht ist der maximale erlaubte Oeffnungsdurchmesser unter den folgenden Bedingungen.",
    "fire_resistance_class": "Gesucht ist die passende Feuerwiderstandsklasse unter den folgenden Bedingungen.",
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
            ExperimentRequest.Condition(
                id=condition.id,
                type=condition_type,
                value=condition_value,
            )
        )
    return normalized


def _translate_condition_type(condition_type: str) -> str:
    key = condition_type.strip().lower()
    return CONDITION_TYPE_DE.get(key, condition_type)


def _translate_condition_value(condition_value: str) -> str:
    key = condition_value.strip().lower()
    return CONDITION_VALUE_DE.get(key, condition_value)


def build_conditions_block(
    conditions: list[ExperimentRequest.Condition] | None,
) -> tuple[str, int]:
    """Build raw condition block for backward traceability in prompt."""
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


def build_conditions_block_de(
    conditions: list[ExperimentRequest.Condition] | None,
) -> tuple[str, int]:
    """Build translated German condition block for better model guidance."""
    normalized = _normalize_conditions(conditions)
    if not normalized:
        return "Keine zusaetzlichen Bedingungen vorgegeben.", 0

    lines = ["Gegebene Bedingungen (alle muessen gleichzeitig erfuellt sein):"]
    for idx, condition in enumerate(normalized, start=1):
        type_de = _translate_condition_type(condition.type)
        value_de = _translate_condition_value(condition.value)
        if condition.id is None:
            lines.append(f"{idx}. {type_de}: {value_de}")
        else:
            lines.append(f"{idx}. {type_de} (id={condition.id}): {value_de}")

    return "\n".join(lines), len(normalized)


def build_search_target_sentence(value: str) -> str:
    """Build a descriptive extraction goal sentence."""
    if value in SEARCH_TARGET_SENTENCES:
        return SEARCH_TARGET_SENTENCES[value]
    description = describe_value(value)
    return f"Gesucht ist der Wert '{value}' ({description}) unter den folgenden Bedingungen."


def build_prompt_v5(
    template: str,
    system: str,
    system_name: str,
    value: str,
    docs_text: str,
    conditions: list[ExperimentRequest.Condition] | None = None,
) -> str:
    """Build complete v5 prompt with translated conditions and descriptive target sentence."""
    value_description = describe_value(value)
    search_target_sentence = build_search_target_sentence(value)
    conditions_block_raw, _ = build_conditions_block(conditions)
    conditions_block_de, _ = build_conditions_block_de(conditions)

    placeholders = {
        "{{SYSTEM}}": system,
        "{{SYSTEM_NAME}}": system_name,
        "{{VALUE}}": value,
        "{{VALUE_DESCRIPTION}}": value_description,
        "{{SEARCH_TARGET_SENTENCE}}": search_target_sentence,
        "{{CONDITIONS}}": conditions_block_raw,
        "{{CONDITIONS_DE}}": conditions_block_de,
        "{{DOCUMENT_CONTENT}}": docs_text,
    }

    rendered = template
    for token, value_str in placeholders.items():
        rendered = rendered.replace(token, value_str)

    return rendered
