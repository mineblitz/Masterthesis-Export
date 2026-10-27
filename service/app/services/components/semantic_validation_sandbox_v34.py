"""Non-blocking semantic validation sandbox for v34.

Computes bounded penalties for semantic quality signals without hard rejection.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


_NUMBER_WITH_UNIT_RE = re.compile(
    r"(?P<value>[-+]?\d+(?:[\.,]\d+)?)\s*(?P<unit>mm|cm|m|min|minute|minuten|h|std|stunden|stunde)?",
    re.IGNORECASE,
)

_CONTRADICTION_TERMS = (
    "nicht",
    "kein",
    "keine",
    "ausgenommen",
    "abweichend",
    "gilt nicht",
    "unzulaessig",
    "unzulassig",
)


@dataclass(frozen=True)
class SemanticValidationResultV34:
    total_penalty: float
    unit_penalty: float
    range_penalty: float
    contradiction_penalty: float
    provenance_penalty: float
    unit_compatible: bool
    range_sane: bool
    contradiction_density: float
    provenance_completeness: float
    max_semantic_penalty: float


def _normalize(text: str) -> str:
    return (
        text.casefold()
        .replace("ae", "a")
        .replace("oe", "o")
        .replace("ue", "u")
        .replace("\u00df", "ss")
        .replace("\u00e4", "a")
        .replace("\u00f6", "o")
        .replace("\u00fc", "u")
    )


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _chunk_attr(item: Any, key: str, default: Any) -> Any:
    chunk = getattr(item, "chunk", item)
    return getattr(chunk, key, default)


def _infer_family(value_name: str) -> str:
    norm = value_name.casefold().replace("_", " ")
    if any(term in norm for term in ("dicke", "thick", "durchmesser", "diameter")):
        return "thickness"
    if any(term in norm for term in ("dauer", "time", "minute", "stunden", "feuerwiderstand")):
        return "time"
    if any(term in norm for term in ("abstand", "distance", "breite", "width", "hoehe", "height")):
        return "distance"
    return "generic"


def _expected_units(value_family: str) -> set[str]:
    if value_family in {"thickness", "distance"}:
        return {"mm", "cm", "m"}
    if value_family == "time":
        return {"min", "minute", "minuten", "h", "std", "stunden", "stunde"}
    return set()


def _range_bounds(value_family: str) -> tuple[float, float]:
    if value_family == "thickness":
        return 1.0, 500.0
    if value_family == "distance":
        return 1.0, 2000.0
    if value_family == "time":
        return 5.0, 360.0
    return 0.0, 10000.0


def _supports_value(text: str, extracted_value: float | None, tolerance: float = 0.2) -> bool:
    if extracted_value is None:
        return False
    for match in _NUMBER_WITH_UNIT_RE.finditer(text):
        try:
            parsed = float(match.group("value").replace(",", "."))
        except ValueError:
            continue
        if abs(parsed - extracted_value) <= tolerance:
            return True
    return False


def run_semantic_validation_sandbox_v34(
    *,
    value_name: str,
    extracted_value: float | None,
    selected_chunks: list[Any],
    clause_type_by_chunk_id: dict[str, str] | None,
    max_semantic_penalty: float = 0.25,
) -> SemanticValidationResultV34:
    if extracted_value is None:
        bounded = round(min(0.14, max_semantic_penalty), 4)
        return SemanticValidationResultV34(
            total_penalty=bounded,
            unit_penalty=0.0,
            range_penalty=min(0.1, bounded),
            contradiction_penalty=0.0,
            provenance_penalty=max(0.0, round(bounded - min(0.1, bounded), 4)),
            unit_compatible=True,
            range_sane=False,
            contradiction_density=0.0,
            provenance_completeness=0.0,
            max_semantic_penalty=max_semantic_penalty,
        )

    family = _infer_family(value_name)
    expected_units = _expected_units(family)
    lower, upper = _range_bounds(family)
    clause_map = clause_type_by_chunk_id or {}

    observed_units: set[str] = set()
    contradiction_hits = 0
    supporting_chunks = 0
    requirement_support = 0

    for item in selected_chunks:
        text = str(_chunk_attr(item, "text", ""))
        norm = _normalize(text)
        chunk_id = str(_chunk_attr(item, "chunk_id", "unknown"))

        if any(term in norm for term in _CONTRADICTION_TERMS):
            contradiction_hits += 1

        if _supports_value(text, extracted_value):
            supporting_chunks += 1
            clause_type = clause_map.get(chunk_id, "informational")
            if clause_type in {"requirement", "scope"}:
                requirement_support += 1

        for match in _NUMBER_WITH_UNIT_RE.finditer(text):
            try:
                parsed = float(match.group("value").replace(",", "."))
            except ValueError:
                continue
            if abs(parsed - extracted_value) > 0.2:
                continue
            unit = (match.group("unit") or "").casefold().strip()
            if unit:
                observed_units.add(unit)

    unit_compatible = True
    unit_penalty = 0.0
    if expected_units and observed_units and expected_units.isdisjoint(observed_units):
        unit_compatible = False
        unit_penalty = 0.08

    range_sane = lower <= extracted_value <= upper
    range_penalty = 0.0 if range_sane else 0.11

    contradiction_density = contradiction_hits / max(1, len(selected_chunks))
    contradiction_penalty = min(0.1, round(contradiction_density * 0.12, 4))

    support_ratio = supporting_chunks / max(1, len(selected_chunks))
    requirement_ratio = requirement_support / max(1, len(selected_chunks))
    provenance_completeness = round(support_ratio * 0.6 + requirement_ratio * 0.4, 4)
    provenance_penalty = round(max(0.0, 0.12 * (1.0 - provenance_completeness)), 4)

    total_penalty = round(
        min(
            max_semantic_penalty,
            unit_penalty + range_penalty + contradiction_penalty + provenance_penalty,
        ),
        4,
    )

    return SemanticValidationResultV34(
        total_penalty=total_penalty,
        unit_penalty=round(unit_penalty, 4),
        range_penalty=round(range_penalty, 4),
        contradiction_penalty=round(contradiction_penalty, 4),
        provenance_penalty=round(provenance_penalty, 4),
        unit_compatible=unit_compatible,
        range_sane=range_sane,
        contradiction_density=round(_clamp(contradiction_density, 0.0, 1.0), 4),
        provenance_completeness=round(_clamp(provenance_completeness, 0.0, 1.0), 4),
        max_semantic_penalty=max_semantic_penalty,
    )
