"""Prompt builder component for text extraction with value descriptions."""


VALUE_DESCRIPTIONS: dict[str, str] = {
    "min_thickness": "Bauteildicke: die untere zulässige Grenze der Bauteildicke",
    "max_thickness": "Bauteildicke: die obere zulässige Grenze der Bauteildicke",
    "min_opening_width": "Oeffnungsbreite: die kleinste zulaessige Breite einer rechteckigen Oeffnung",
    "max_opening_width": "Oeffnungsbreite: die groesste zulaessige Breite einer rechteckigen Oeffnung",
    "min_opening_height": "Oeffnungshoehe: die kleinste zulaessige Hoehe einer rechteckigen Oeffnung",
    "max_opening_height": "Oeffnungshoehe: die groesste zulaessige Hoehe einer rechteckigen Oeffnung",
    "min_diameter": "Oeffnungsdurchmesser: der kleinste zulaessige Durchmesser einer runden Oeffnung",
    "max_diameter": "Oeffnungsdurchmesser: der groesste zulaessige Durchmesser einer runden Oeffnung",
    "fire_resistance_class": "Feuerwiderstand: die im Dokument genannte Feuerwiderstandsklasse, z. B. 30, 60, 90 oder 120",
}

VALUE_GLOSSARY_ORDER = [
    "min_thickness",
    "max_thickness",
    "min_opening_width",
    "max_opening_width",
    "min_opening_height",
    "max_opening_height",
    "min_diameter",
    "max_diameter",
    "fire_resistance_class",
]


def describe_value(value: str) -> str:
    """Get German description for a value key."""
    return VALUE_DESCRIPTIONS.get(value, f"Gesuchter Wert: {value}")


def build_value_glossary() -> str:
    """Build a formatted glossary of all supported values."""
    glossary_lines = []
    for value_key in VALUE_GLOSSARY_ORDER:
        description = VALUE_DESCRIPTIONS.get(value_key, value_key)
        glossary_lines.append(f"- {value_key}: {description}")
    return "\n".join(glossary_lines)


def build_prompt(
    template: str,
    system: str,
    system_name: str,
    min_or_max: str,
    value: str,
    docs_text: str,
) -> str:
    """
    Build a complete prompt with all placeholders replaced.
    
    Args:
        template: Prompt template with {{PLACEHOLDER}} tokens.
        system: System identifier (e.g., "B2").
        system_name: Human-readable system name (e.g., "Kabel-Roehre").
        min_or_max: Either "groesste" or "kleinste".
        value: Value key to extract (e.g., "min_thickness").
        docs_text: Full extracted document text.
        
    Returns:
        Complete prompt ready for LLM.
    """
    value_description = describe_value(value)
    selection_instruction = (
        "Es koennen mehrere passende Werte vorkommen. "
        f"Wenn {min_or_max} gefordert ist, waehle immer den passenden Extremwert unter allen passenden Kandidaten."
    )

    placeholders = {
        "{{SYSTEM}}": system,
        "{{SYSTEM_NAME}}": system_name,
        "{{MIN_OR_MAX}}": min_or_max,
        "{{VALUE}}": value,
        "{{VALUE_DESCRIPTION}}": value_description,
        "{{VALUE_GLOSSARY}}": build_value_glossary(),
        "{{SELECTION_INSTRUCTION}}": selection_instruction,
        "{{DOCUMENT_CONTENT}}": docs_text,
    }

    rendered = template
    for token, value_str in placeholders.items():
        rendered = rendered.replace(token, value_str)

    return rendered
