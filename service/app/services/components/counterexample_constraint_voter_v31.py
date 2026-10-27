"""Counterexample-aware soft constraint voting for scalar extraction.

This module scores numeric candidates by combining:
- supporting evidence from selected chunks
- contradicting/counterexample evidence
- soft symbolic checks (unit and inequality compatibility)

The result is intentionally soft-scored to avoid brittle all-or-nothing rejection.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from app.models import ExperimentRequest
from app.services.components.hybrid_context_ranker import RankedChunk
from app.services.components.retrieval_enhancer_v29_text import normalize_numeric_value_for_payload_v29


_NUMERIC_WITH_UNIT_PATTERN = re.compile(
    r"(?P<value>[-+]?\d+(?:[\.,]\d+)?)\s*(?P<unit>mm|cm|m|min|minute|minuten|h|std|stunden|stunde)?",
    re.IGNORECASE,
)

_NEGATION_CUES = (
    "nicht",
    "kein",
    "keine",
    "ausgenommen",
    "abweichend",
    "gilt nicht",
    "nicht zulaessig",
    "nicht zulassig",
)

_MIN_CUES = ("mindestens", "minimum", "min.", "min ", ">=")
_MAX_CUES = ("hoechstens", "hochstens", "maximal", "max.", "max ", "<=", "bis zu")


@dataclass
class CandidateScore:
    value: float
    support: float
    contradiction: float
    margin: float
    mentions: int
    source_chunk_ids: list[str]


@dataclass
class CounterexampleVotingDecision:
    selected_value: float | None
    confidence: float
    decision: str
    fallback_used: bool
    selected_from: str
    top_candidates: list[dict[str, float | int | list[str]]]


def _normalize_for_match(text: str) -> str:
    return (
        text.casefold()
        .replace("ae", "a")
        .replace("oe", "o")
        .replace("ue", "u")
        .replace("ß", "ss")
        .replace("ä", "a")
        .replace("ö", "o")
        .replace("ü", "u")
    )


def _anchor_terms(payload: ExperimentRequest) -> list[str]:
    anchors: list[str] = []
    anchors.extend(part for part in payload.value.replace("_", " ").split() if part)
    for condition in payload.conditions or []:
        if condition.type.strip():
            anchors.append(condition.type.strip())
        if condition.value.strip():
            anchors.append(condition.value.strip())

    seen: set[str] = set()
    normalized: list[str] = []
    for anchor in anchors:
        norm = _normalize_for_match(anchor)
        if len(norm) < 3 or norm in seen:
            continue
        seen.add(norm)
        normalized.append(norm)
    return normalized


def _infer_unit_family(value_key: str) -> str | None:
    normalized = _normalize_for_match(value_key)
    if any(token in normalized for token in ("dicke", "thickness", "abstand", "breite", "durchmesser", "hoehe")):
        return "length"
    if any(token in normalized for token in ("feuerwiderstand", "fire_resistance", "brandklasse", "widerstand")):
        return "time"
    return None


def _unit_family(unit: str | None) -> str | None:
    if unit is None:
        return None
    normalized = _normalize_for_match(unit)
    if normalized in {"mm", "cm", "m"}:
        return "length"
    if normalized in {"min", "minute", "minuten", "h", "std", "stunden", "stunde"}:
        return "time"
    return None


def _inequality_compatibility(context: str, payload: ExperimentRequest) -> float:
    norm = _normalize_for_match(context)
    has_min = any(cue in norm for cue in _MIN_CUES)
    has_max = any(cue in norm for cue in _MAX_CUES)

    mode = _normalize_for_match(payload.min_or_max or "")
    if "min" in mode:
        if has_min:
            return 0.16
        if has_max:
            return -0.12
    if "max" in mode:
        if has_max:
            return 0.16
        if has_min:
            return -0.12
    return 0.0


def _contains_negation(context: str) -> bool:
    norm = _normalize_for_match(context)
    return any(cue in norm for cue in _NEGATION_CUES)


def _extract_candidates_from_chunk(
    *,
    ranked_chunk: RankedChunk,
    payload: ExperimentRequest,
    anchors: list[str],
    clause_type: str,
    evidence_score: float,
) -> list[tuple[float, float, float]]:
    text = ranked_chunk.chunk.text
    normalized_text = _normalize_for_match(text)
    expected_unit_family = _infer_unit_family(payload.value)

    results: list[tuple[float, float, float]] = []
    for match in _NUMERIC_WITH_UNIT_PATTERN.finditer(text):
        raw = match.group("value")
        try:
            parsed = float(raw.replace(",", "."))
        except ValueError:
            continue

        normalized_value = normalize_numeric_value_for_payload_v29(parsed, payload, source_text=match.group("unit") or "")
        if normalized_value is None:
            continue

        start = max(0, match.start() - 72)
        end = min(len(text), match.end() + 72)
        local_context = text[start:end]
        normalized_local = _normalize_for_match(local_context)

        anchor_hits = sum(1 for anchor in anchors if anchor in normalized_local)
        relevance = min(0.28, anchor_hits * 0.07)

        clause_bonus = 0.0
        clause_penalty = 0.0
        if clause_type in {"requirement", "scope"}:
            clause_bonus += 0.08
        elif clause_type == "exception":
            clause_penalty += 0.08

        unit_score = 0.0
        unit_family = _unit_family(match.group("unit"))
        if expected_unit_family and unit_family:
            if unit_family == expected_unit_family:
                unit_score = 0.1
            else:
                unit_score = -0.14

        inequality_score = _inequality_compatibility(local_context, payload)
        contradiction = 0.0
        if _contains_negation(local_context):
            contradiction += 0.12
        contradiction += clause_penalty

        support = 0.32 + evidence_score * 0.42 + relevance + clause_bonus + unit_score + inequality_score
        results.append((float(round(normalized_value, 4)), support, contradiction))

    if not results and any(anchor in normalized_text for anchor in anchors):
        # Keep zero-candidate chunks from disappearing entirely in logs.
        return []
    return results


def _calibrate_confidence(*, top_margin: float, second_margin: float, support: float, mentions: int) -> float:
    margin_signal = min(1.0, max(0.0, (top_margin + 0.3) / 1.3))
    separation = min(1.0, max(0.0, top_margin - second_margin))
    support_signal = min(1.0, support / 2.5)
    mention_signal = min(1.0, mentions / 4.0)
    confidence = 0.22 + margin_signal * 0.35 + separation * 0.23 + support_signal * 0.12 + mention_signal * 0.08
    return round(min(0.98, max(0.05, confidence)), 4)


def resolve_value_with_counterexample_voting_v31(
    *,
    payload: ExperimentRequest,
    selected_chunks: list[RankedChunk],
    clause_type_by_chunk_id: dict[str, str] | None,
    chunk_evidence: dict[str, float] | None,
    llm_candidate: float | None,
    modal_candidate: float | None,
    min_margin_threshold: float = 0.12,
) -> CounterexampleVotingDecision:
    anchors = _anchor_terms(payload)
    clause_map = clause_type_by_chunk_id or {}
    evidence_map = chunk_evidence or {}

    accumulator: dict[float, CandidateScore] = {}
    for ranked_chunk in selected_chunks:
        chunk_id = ranked_chunk.chunk.chunk_id
        evidence_score = float(evidence_map.get(chunk_id, 0.0))
        clause_type = clause_map.get(chunk_id, "informational")

        for value, support, contradiction in _extract_candidates_from_chunk(
            ranked_chunk=ranked_chunk,
            payload=payload,
            anchors=anchors,
            clause_type=clause_type,
            evidence_score=evidence_score,
        ):
            if value not in accumulator:
                accumulator[value] = CandidateScore(
                    value=value,
                    support=0.0,
                    contradiction=0.0,
                    margin=0.0,
                    mentions=0,
                    source_chunk_ids=[],
                )

            entry = accumulator[value]
            entry.support += support
            entry.contradiction += contradiction
            entry.mentions += 1
            if chunk_id not in entry.source_chunk_ids:
                entry.source_chunk_ids.append(chunk_id)

    if llm_candidate is not None:
        llm_norm = normalize_numeric_value_for_payload_v29(llm_candidate, payload)
        if llm_norm is not None and llm_norm in accumulator:
            accumulator[llm_norm].support += 0.12

    if modal_candidate is not None:
        modal_norm = normalize_numeric_value_for_payload_v29(modal_candidate, payload)
        if modal_norm is not None and modal_norm in accumulator:
            accumulator[modal_norm].support += 0.08

    for candidate in accumulator.values():
        candidate.margin = round(candidate.support - candidate.contradiction, 4)

    ranked = sorted(accumulator.values(), key=lambda item: (-item.margin, -item.support, -item.mentions, item.value))
    top_candidates: list[dict[str, float | int | list[str]]] = []
    for item in ranked[:5]:
        top_candidates.append(
            {
                "value": item.value,
                "support": round(item.support, 4),
                "contradiction": round(item.contradiction, 4),
                "margin": item.margin,
                "mentions": item.mentions,
                "source_chunk_ids": item.source_chunk_ids,
            }
        )

    if not ranked:
        if llm_candidate is not None:
            llm_norm = normalize_numeric_value_for_payload_v29(llm_candidate, payload)
            return CounterexampleVotingDecision(
                selected_value=llm_norm,
                confidence=0.42,
                decision="bounded_fallback_llm_no_candidates",
                fallback_used=True,
                selected_from="llm",
                top_candidates=top_candidates,
            )
        if modal_candidate is not None:
            modal_norm = normalize_numeric_value_for_payload_v29(modal_candidate, payload)
            return CounterexampleVotingDecision(
                selected_value=modal_norm,
                confidence=0.36,
                decision="bounded_fallback_modal_no_candidates",
                fallback_used=True,
                selected_from="modal",
                top_candidates=top_candidates,
            )
        return CounterexampleVotingDecision(
            selected_value=None,
            confidence=0.08,
            decision="no_candidate_available",
            fallback_used=False,
            selected_from="none",
            top_candidates=top_candidates,
        )

    best = ranked[0]
    second_margin = ranked[1].margin if len(ranked) > 1 else 0.0
    confidence = _calibrate_confidence(
        top_margin=best.margin,
        second_margin=second_margin,
        support=best.support,
        mentions=best.mentions,
    )

    if best.margin < min_margin_threshold:
        if llm_candidate is not None:
            llm_norm = normalize_numeric_value_for_payload_v29(llm_candidate, payload)
            return CounterexampleVotingDecision(
                selected_value=llm_norm,
                confidence=max(0.34, round(confidence * 0.74, 4)),
                decision="bounded_fallback_llm_low_margin",
                fallback_used=True,
                selected_from="llm",
                top_candidates=top_candidates,
            )
        if modal_candidate is not None:
            modal_norm = normalize_numeric_value_for_payload_v29(modal_candidate, payload)
            return CounterexampleVotingDecision(
                selected_value=modal_norm,
                confidence=max(0.31, round(confidence * 0.7, 4)),
                decision="bounded_fallback_modal_low_margin",
                fallback_used=True,
                selected_from="modal",
                top_candidates=top_candidates,
            )

    return CounterexampleVotingDecision(
        selected_value=best.value,
        confidence=confidence,
        decision="voted_candidate",
        fallback_used=False,
        selected_from="counterexample_voting",
        top_candidates=top_candidates,
    )
