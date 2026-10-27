"""Prompt builder component v6 — Turtle/RDF condition parsing for KG-based experiments."""

import re

from app.services.components.prompt_builder_v5 import (
    VALUE_DESCRIPTIONS,
    SEARCH_TARGET_SENTENCES,
    describe_value,
    build_search_target_sentence,
)

# ---------------------------------------------------------------------------
# Turtle → human-readable condition extraction
# ---------------------------------------------------------------------------


def _parse_turtle_triples(turtle: str) -> list[tuple[str, str, str]]:
    """Parse Turtle text into a flat list of (subject, predicate, object) triples.

    Handles multi-line subjects: in Turtle, lines that start with a predicate
    (no subject) inherit the subject from the previous line.  Semicolons (``;``)
    continue the current subject, dots (``.``) close it.
    """
    triples: list[tuple[str, str, str]] = []
    current_subject: str | None = None

    for raw_line in turtle.splitlines():
        line = raw_line.strip().rstrip(";").rstrip(".").strip()
        if not line or line.startswith("#") or line.startswith("@prefix"):
            continue

        # Detect a new subject (URI or blank-node) at the start of the line
        subject_match = re.match(r'(<[^>]+>|_:\w+)\s*(.*)', line)
        if subject_match:
            current_subject = subject_match.group(1)
            rest = subject_match.group(2).strip()
        else:
            # Line starts with a predicate — inherits current_subject
            rest = line

        if not current_subject or not rest:
            continue

        # rest = "predicate object"
        pred_obj = re.match(r'([\w-]+:\w+)\s+(.+)', rest)
        if pred_obj:
            predicate = pred_obj.group(1)
            obj = pred_obj.group(2).strip().rstrip(";").rstrip(".").strip()
            triples.append((current_subject, predicate, obj))

    return triples


def _parse_turtle_names(turtle: str) -> dict[str, str]:
    """Extract URI → human-readable name mappings from ``fp-prop-*:name`` triples."""
    mapping: dict[str, str] = {}
    for subj, pred, obj in _parse_turtle_triples(turtle):
        if re.fullmatch(r'fp-prop-\w+:name', pred):
            # Strip surrounding quotes from the object
            name = obj.strip('"')
            mapping[subj] = name
    return mapping


def _parse_turtle_relations(turtle: str) -> dict[str, str]:
    """Extract relation edges from the location node (material_id, position_id, opening_type_id)."""
    relations: dict[str, str] = {}
    for subj, pred, obj in _parse_turtle_triples(turtle):
        if pred.startswith("fp-rel:"):
            rel_name = pred.split(":", 1)[1]
            relations[rel_name] = obj
    return relations


def _parse_pipe_type_rules(turtle: str) -> list[dict[str, str | float | None]]:
    """Parse blank-node pipe type rules into a list of constraint dicts.

    Each rule is emitted as::
        {"pipe_type_uri": "<...>", "min_diameter": 0.0, "max_diameter": 88.9, ...}
    """
    # Group triples by blank-node subject
    rule_triples: dict[str, list[tuple[str, str]]] = {}
    for subj, pred, obj in _parse_turtle_triples(turtle):
        if subj.startswith("_:pipe_type_rule"):
            rule_triples.setdefault(subj, []).append((pred, obj))

    rules: list[dict[str, str | float | None]] = []
    for _bnode, pairs in rule_triples.items():
        rule: dict[str, str | float | None] = {}
        for pred, obj in pairs:
            if pred == "fp-rel-ptr:pipe_type_id":
                rule["pipe_type_uri"] = obj
            elif pred.startswith("fp-prop-ptr:"):
                prop_name = pred.split(":", 1)[1]
                try:
                    rule[prop_name] = float(obj)
                except ValueError:
                    rule[prop_name] = obj
        rules.append(rule)

    return rules


# Human-readable relation labels
_RELATION_LABEL: dict[str, str] = {
    "material_id": "Material",
    "position_id": "Einbauposition",
    "opening_type_id": "Oeffnungsart",
}


def build_conditions_block_from_turtle(turtle: str) -> tuple[str, int]:
    """Convert a Turtle RDF snippet into a structured German condition block.

    Returns ``(condition_text, condition_count)`` exactly like the v5
    ``build_conditions_block_de`` function, so it can be used as a drop-in
    replacement inside the prompt template.
    """
    if not turtle or not turtle.strip():
        return "Keine zusaetzlichen Bedingungen vorgegeben.", 0

    names = _parse_turtle_names(turtle)
    relations = _parse_turtle_relations(turtle)
    pipe_rules = _parse_pipe_type_rules(turtle)

    lines: list[str] = ["Gegebene Bedingungen (alle muessen gleichzeitig erfuellt sein):"]
    idx = 0

    # Basic location conditions (material, position, opening_type)
    for rel_key, rel_uri in relations.items():
        label = _RELATION_LABEL.get(rel_key, rel_key)
        resolved_name = names.get(rel_uri, rel_uri)
        idx += 1
        lines.append(f"{idx}. {label}: {resolved_name}")

    # Pipe type rules
    if pipe_rules:
        idx += 1
        lines.append(f"{idx}. Erlaubte Rohrtypen:")
        for rule in pipe_rules:
            pipe_name = names.get(str(rule.get("pipe_type_uri", "")), "unbekannt")
            constraints: list[str] = []
            if "min_diameter" in rule:
                constraints.append(f"min. Durchmesser {rule['min_diameter']} mm")
            if "max_diameter" in rule:
                constraints.append(f"max. Durchmesser {rule['max_diameter']} mm")
            if "min_count" in rule:
                constraints.append(f"min. Anzahl {int(rule['min_count'])}")
            if "max_count" in rule:
                constraints.append(f"max. Anzahl {int(rule['max_count'])}")
            constraint_str = ", ".join(constraints) if constraints else "keine Einschraenkungen"
            lines.append(f"   - {pipe_name} ({constraint_str})")

    return "\n".join(lines), idx


def build_conditions_raw_from_turtle(turtle: str) -> str:
    """Return the raw Turtle snippet wrapped in a labelled block for traceability."""
    if not turtle or not turtle.strip():
        return "Keine zusaetzlichen Bedingungen vorgegeben (kein Turtle-Snippet)."
    return f"Bedingungen (Turtle/RDF):\n```turtle\n{turtle.strip()}\n```"


def build_prompt_v6(
    template: str,
    system: str,
    system_name: str,
    value: str,
    docs_text: str,
    conditions_turtle: str | None = None,
) -> str:
    """Build a complete prompt using the Turtle/RDF conditions format.

    Supports the same placeholder set as v5 (``{{CONDITIONS}}``,
    ``{{CONDITIONS_DE}}``) but fills them from the parsed Turtle graph
    instead of a ``list[Condition]``.
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
        "{{DOCUMENT_CONTENT}}": docs_text,
    }

    rendered = template
    for token, value_str in placeholders.items():
        rendered = rendered.replace(token, value_str)

    return rendered
