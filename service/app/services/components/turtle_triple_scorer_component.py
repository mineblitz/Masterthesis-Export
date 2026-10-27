"""Utilities for Turtle triple normalization and scoring."""

import re
from decimal import Decimal, InvalidOperation
from typing import Any


_RDF_TYPE_URI = "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>"
_PREFIX_RE = re.compile(r"@prefix\s+([A-Za-z][\w-]*):\s*<([^>]+)>\s*\.", re.IGNORECASE)
_NUMERIC_RE = re.compile(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")


def _strip_markdown_fence(text: str) -> str:
    cleaned = text.strip()
    if not cleaned.startswith("```"):
        return cleaned
    lines = cleaned.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip().endswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _remove_comments(text: str) -> str:
    result_lines: list[str] = []
    for line in text.splitlines():
        out: list[str] = []
        in_string = False
        escaped = False
        for char in line:
            if escaped:
                out.append(char)
                escaped = False
                continue
            if char == "\\":
                out.append(char)
                escaped = True
                continue
            if char == '"':
                in_string = not in_string
                out.append(char)
                continue
            if char == "#" and not in_string:
                break
            out.append(char)
        result_lines.append("".join(out))
    return "\n".join(result_lines)


def _split_outside_quotes(text: str, delimiter: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    in_string = False
    escaped = False
    depth_angle = 0

    for char in text:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            current.append(char)
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            current.append(char)
            continue
        if not in_string and char == "<":
            depth_angle += 1
            current.append(char)
            continue
        if not in_string and char == ">" and depth_angle > 0:
            depth_angle -= 1
            current.append(char)
            continue
        if not in_string and depth_angle == 0 and char == delimiter:
            part = "".join(current).strip()
            if part:
                parts.append(part)
            current = []
            continue
        current.append(char)

    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return parts


def _normalize_numeric(value: str) -> str:
    try:
        normalized = format(Decimal(value), "f")
        if "." in normalized:
            normalized = normalized.rstrip("0").rstrip(".")
        return normalized or "0"
    except (InvalidOperation, ValueError):
        return value


def _normalize_term(term: str, prefixes: dict[str, str]) -> str:
    token = term.strip()
    if not token:
        return token

    if token == "a":
        return _RDF_TYPE_URI

    if token.startswith("_:"):
        return "_:blank"

    if token.startswith("<") and token.endswith(">"):
        return token

    if token.startswith('"'):
        return token.strip()

    if _NUMERIC_RE.fullmatch(token):
        return _normalize_numeric(token)

    if ":" in token:
        prefix, local = token.split(":", 1)
        if prefix in prefixes:
            return f"<{prefixes[prefix]}{local}>"
    return token


def _parse_predicate_objects(
    subject: str,
    chunks: list[str],
    prefixes: dict[str, str],
) -> set[tuple[str, str, str]]:
    triples: set[tuple[str, str, str]] = set()
    for index, chunk in enumerate(chunks):
        if index == 0:
            first_space = chunk.find(" ")
            if first_space == -1:
                continue
            subject_token = chunk[:first_space].strip()
            remainder = chunk[first_space + 1 :].strip()
            subject = _normalize_term(subject_token, prefixes)
        else:
            remainder = chunk

        pred_space = remainder.find(" ")
        if pred_space == -1:
            continue
        pred_token = remainder[:pred_space].strip()
        object_segment = remainder[pred_space + 1 :].strip()
        predicate = _normalize_term(pred_token, prefixes)

        for obj in _split_outside_quotes(object_segment, ","):
            normalized_object = _normalize_term(obj, prefixes)
            triples.add((subject, predicate, normalized_object))

    return triples


def parse_turtle_to_normalized_triples(turtle_text: str) -> set[tuple[str, str, str]]:
    cleaned = _remove_comments(_strip_markdown_fence(turtle_text))
    prefixes = {prefix: uri for prefix, uri in _PREFIX_RE.findall(cleaned)}
    body = _PREFIX_RE.sub("", cleaned)

    triples: set[tuple[str, str, str]] = set()
    for statement in _split_outside_quotes(body, "."):
        chunks = _split_outside_quotes(statement, ";")
        if not chunks:
            continue
        triples.update(_parse_predicate_objects("", chunks, prefixes))

    if not triples:
        raise ValueError("No triples parsed from Turtle output")
    return triples


def score_triple_sets(
    predicted: set[tuple[str, str, str]],
    expected: set[tuple[str, str, str]],
) -> dict[str, Any]:
    correct = predicted & expected
    predicted_count = len(predicted)
    expected_count = len(expected)
    correct_count = len(correct)

    precision = (correct_count / predicted_count) if predicted_count else (1.0 if expected_count == 0 else 0.0)
    recall = (correct_count / expected_count) if expected_count else (1.0 if predicted_count == 0 else 0.0)
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)

    return {
        "predicted_triples": predicted_count,
        "expected_triples": expected_count,
        "correct_triples": correct_count,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def classify_triple_errors(
    predicted: set[tuple[str, str, str]],
    expected: set[tuple[str, str, str]],
    *,
    max_examples: int = 30,
) -> dict[str, Any]:
    missing = sorted(expected - predicted)
    hallucinated = sorted(predicted - expected)

    expected_by_so = {(s, o): p for s, p, o in expected}
    expected_by_sp = {(s, p): o for s, p, o in expected}

    wrong_relation_count = 0
    wrong_literal_count = 0
    wrong_entity_linkage_count = 0

    for s, p, o in hallucinated:
        exp_p = expected_by_so.get((s, o))
        if exp_p is not None and exp_p != p:
            wrong_relation_count += 1

        exp_o = expected_by_sp.get((s, p))
        if exp_o is not None and exp_o != o:
            if o.startswith('"') or exp_o.startswith('"'):
                wrong_literal_count += 1
            else:
                wrong_entity_linkage_count += 1

    def _format(triples: list[tuple[str, str, str]]) -> list[str]:
        return [f"{s} {p} {o}" for s, p, o in triples[:max_examples]]

    return {
        "missing_triples_count": len(missing),
        "hallucinated_triples_count": len(hallucinated),
        "wrong_relation_count": wrong_relation_count,
        "wrong_literal_count": wrong_literal_count,
        "wrong_entity_linkage_count": wrong_entity_linkage_count,
        "missing_triples_examples": _format(missing),
        "hallucinated_triples_examples": _format(hallucinated),
    }