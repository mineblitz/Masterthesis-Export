"""Scenario-ensemble resolver for text-only pipeline v32.

v32 introduces condition-constrained scenario simulation over retrieved evidence.
Each scenario proposes one candidate value, then a robust agreement stage applies
outlier rejection before selecting the final value.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from statistics import median

from app.models import ExperimentRequest
from app.services.components.hybrid_context_ranker import RankedChunk
from app.services.components.retrieval_enhancer_v29_text import normalize_numeric_value_for_payload_v29


_NUMERIC_WITH_UNIT_PATTERN = re.compile(
    r"(?P<value>[-+]?\d+(?:[\.,]\d+)?)\s*(?P<unit>mm|cm|m|min|minute|minuten|h|std|stunden|stunde)?",
    re.IGNORECASE,
)

_EXCEPTION_TERMS = (
    "ausgenommen",
    "abweichend",
    "gilt nicht",
    "nicht zulaessig",
    "nicht zulassig",
    "nur wenn",
)


@dataclass
class ScenarioSpec:
    scenario_id: str
    label: str
    include_clause_types: set[str]
    exclude_exception_terms: bool
    require_anchor_match: bool
    prior_weight: float


@dataclass
class ScenarioCandidate:
    scenario_id: str
    label: str
    candidate_value: float | None
    support_score: float
    evidence_count: int
    confidence: float
    source_chunk_ids: list[str]


@dataclass
class ScenarioEnsembleDecision:
    selected_value: float | None
    confidence: float
    decision: str
    selected_from: str
    fallback_used: bool
    agreement_score: float
    outlier_rejections: int
    selected_scenarios: list[str]
    scenario_candidates: list[dict[str, object]]


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


def _build_scenarios() -> list[ScenarioSpec]:
    return [
        ScenarioSpec(
            scenario_id="strict_requirement",
            label="Strict requirement evidence",
            include_clause_types={"requirement", "scope"},
            exclude_exception_terms=True,
            require_anchor_match=True,
            prior_weight=1.0,
        ),
        ScenarioSpec(
            scenario_id="balanced_requirement",
            label="Balanced requirement and informational evidence",
            include_clause_types={"requirement", "scope", "informational"},
            exclude_exception_terms=False,
            require_anchor_match=True,
            prior_weight=0.92,
        ),
        ScenarioSpec(
            scenario_id="broad_coverage",
            label="Broad coverage evidence",
            include_clause_types={"requirement", "scope", "informational", "exception"},
            exclude_exception_terms=False,
            require_anchor_match=False,
            prior_weight=0.86,
        ),
        ScenarioSpec(
            scenario_id="exception_stress_test",
            label="Exception stress test",
            include_clause_types={"requirement", "scope", "exception"},
            exclude_exception_terms=False,
            require_anchor_match=False,
            prior_weight=0.74,
        ),
    ]


def _contains_exception_signal(text: str) -> bool:
    norm = _normalize_for_match(text)
    return any(term in norm for term in _EXCEPTION_TERMS)


def _extract_scenario_candidate(
    *,
    scenario: ScenarioSpec,
    payload: ExperimentRequest,
    selected_chunks: list[RankedChunk],
    clause_type_by_chunk_id: dict[str, str],
    chunk_evidence: dict[str, float],
    anchors: list[str],
) -> ScenarioCandidate:
    value_support: dict[float, float] = {}
    value_sources: dict[float, list[str]] = {}
    evidence_count = 0

    for ranked in selected_chunks:
        chunk = ranked.chunk
        clause_type = clause_type_by_chunk_id.get(chunk.chunk_id, "informational")
        if clause_type not in scenario.include_clause_types:
            continue

        norm_chunk = _normalize_for_match(chunk.text)
        if scenario.require_anchor_match and anchors and not any(anchor in norm_chunk for anchor in anchors):
            continue
        if scenario.exclude_exception_terms and _contains_exception_signal(chunk.text):
            continue

        evidence = float(chunk_evidence.get(chunk.chunk_id, 0.0))
        clause_weight = 1.0
        if clause_type == "requirement":
            clause_weight = 1.12
        elif clause_type == "scope":
            clause_weight = 1.06
        elif clause_type == "exception":
            clause_weight = 0.68

        for match in _NUMERIC_WITH_UNIT_PATTERN.finditer(chunk.text):
            raw_value = match.group("value")
            try:
                parsed = float(raw_value.replace(",", "."))
            except ValueError:
                continue

            normalized = normalize_numeric_value_for_payload_v29(
                parsed,
                payload,
                source_text=match.group("unit") or "",
            )
            if normalized is None:
                continue

            local_start = max(0, match.start() - 64)
            local_end = min(len(chunk.text), match.end() + 64)
            local = _normalize_for_match(chunk.text[local_start:local_end])
            anchor_hits = sum(1 for anchor in anchors if anchor in local)
            local_weight = 0.22 + evidence * 0.55 + min(0.18, anchor_hits * 0.06)
            if _contains_exception_signal(local):
                local_weight *= 0.72

            support = scenario.prior_weight * clause_weight * local_weight
            bucket = float(round(normalized, 4))
            value_support[bucket] = value_support.get(bucket, 0.0) + support
            value_sources.setdefault(bucket, [])
            if chunk.chunk_id not in value_sources[bucket]:
                value_sources[bucket].append(chunk.chunk_id)
            evidence_count += 1

    if not value_support:
        return ScenarioCandidate(
            scenario_id=scenario.scenario_id,
            label=scenario.label,
            candidate_value=None,
            support_score=0.0,
            evidence_count=evidence_count,
            confidence=0.0,
            source_chunk_ids=[],
        )

    ranked_values = sorted(value_support.items(), key=lambda item: (-item[1], item[0]))
    best_value, best_support = ranked_values[0]
    second_support = ranked_values[1][1] if len(ranked_values) > 1 else 0.0
    margin = max(0.0, best_support - second_support)
    confidence = min(0.98, 0.2 + min(0.55, best_support) + min(0.23, margin))

    return ScenarioCandidate(
        scenario_id=scenario.scenario_id,
        label=scenario.label,
        candidate_value=best_value,
        support_score=round(best_support, 4),
        evidence_count=evidence_count,
        confidence=round(confidence, 4),
        source_chunk_ids=value_sources.get(best_value, []),
    )


def _mad_outlier_mask(values: list[float], threshold: float) -> list[bool]:
    if len(values) < 3:
        return [False] * len(values)

    med = median(values)
    deviations = [abs(value - med) for value in values]
    mad = median(deviations)
    if mad <= 1e-6:
        return [abs(value - med) > 1.5 for value in values]

    robust_scale = 1.4826 * mad
    return [abs(value - med) / robust_scale > threshold for value in values]


def _cluster_value(value: float, tolerance: float) -> float:
    if tolerance <= 0:
        return value
    return round(round(value / tolerance) * tolerance, 4)


def resolve_value_with_scenario_ensemble_v32(
    *,
    payload: ExperimentRequest,
    selected_chunks: list[RankedChunk],
    clause_type_by_chunk_id: dict[str, str] | None,
    chunk_evidence: dict[str, float] | None,
    llm_candidate: float | None,
    modal_candidate: float | None,
    outlier_threshold: float = 2.9,
    agreement_tolerance: float = 2.0,
) -> ScenarioEnsembleDecision:
    anchors = _anchor_terms(payload)
    clause_map = clause_type_by_chunk_id or {}
    evidence_map = chunk_evidence or {}

    scenario_candidates: list[ScenarioCandidate] = []
    for scenario in _build_scenarios():
        scenario_candidates.append(
            _extract_scenario_candidate(
                scenario=scenario,
                payload=payload,
                selected_chunks=selected_chunks,
                clause_type_by_chunk_id=clause_map,
                chunk_evidence=evidence_map,
                anchors=anchors,
            )
        )

    non_null = [item for item in scenario_candidates if item.candidate_value is not None]
    candidate_logs: list[dict[str, object]] = [
        {
            "scenario_id": item.scenario_id,
            "label": item.label,
            "candidate_value": item.candidate_value,
            "support_score": item.support_score,
            "evidence_count": item.evidence_count,
            "confidence": item.confidence,
            "source_chunk_ids": item.source_chunk_ids,
        }
        for item in scenario_candidates
    ]

    if not non_null:
        if llm_candidate is not None:
            llm_norm = normalize_numeric_value_for_payload_v29(llm_candidate, payload)
            return ScenarioEnsembleDecision(
                selected_value=llm_norm,
                confidence=0.4,
                decision="fallback_llm_no_scenarios",
                selected_from="llm",
                fallback_used=True,
                agreement_score=0.0,
                outlier_rejections=0,
                selected_scenarios=[],
                scenario_candidates=candidate_logs,
            )
        if modal_candidate is not None:
            modal_norm = normalize_numeric_value_for_payload_v29(modal_candidate, payload)
            return ScenarioEnsembleDecision(
                selected_value=modal_norm,
                confidence=0.35,
                decision="fallback_modal_no_scenarios",
                selected_from="modal",
                fallback_used=True,
                agreement_score=0.0,
                outlier_rejections=0,
                selected_scenarios=[],
                scenario_candidates=candidate_logs,
            )
        return ScenarioEnsembleDecision(
            selected_value=None,
            confidence=0.08,
            decision="no_candidate_available",
            selected_from="none",
            fallback_used=False,
            agreement_score=0.0,
            outlier_rejections=0,
            selected_scenarios=[],
            scenario_candidates=candidate_logs,
        )

    values = [item.candidate_value for item in non_null if item.candidate_value is not None]
    outlier_mask = _mad_outlier_mask(values, threshold=outlier_threshold)
    surviving: list[ScenarioCandidate] = []
    outliers = 0
    for item, is_outlier in zip(non_null, outlier_mask):
        if is_outlier:
            outliers += 1
            continue
        surviving.append(item)

    if not surviving:
        surviving = [max(non_null, key=lambda item: (item.support_score, item.confidence))]

    bucket_support: dict[float, float] = {}
    bucket_values: dict[float, list[float]] = {}
    bucket_scenarios: dict[float, list[str]] = {}
    total_support = 0.0

    for item in surviving:
        assert item.candidate_value is not None
        bucket = _cluster_value(item.candidate_value, tolerance=agreement_tolerance)
        score = max(0.0001, item.support_score * (0.65 + item.confidence * 0.35))
        total_support += score
        bucket_support[bucket] = bucket_support.get(bucket, 0.0) + score
        bucket_values.setdefault(bucket, []).append(item.candidate_value)
        bucket_scenarios.setdefault(bucket, []).append(item.scenario_id)

    best_bucket = max(bucket_support.items(), key=lambda item: item[1])[0]
    cluster_values = bucket_values.get(best_bucket, [])
    if cluster_values:
        weighted_sum = 0.0
        weighted_den = 0.0
        for item in surviving:
            if _cluster_value(item.candidate_value or 0.0, tolerance=agreement_tolerance) != best_bucket:
                continue
            weight = max(0.0001, item.support_score)
            weighted_sum += (item.candidate_value or 0.0) * weight
            weighted_den += weight
        selected_value = weighted_sum / weighted_den if weighted_den > 0 else cluster_values[0]
    else:
        selected_value = best_bucket

    selected_value = normalize_numeric_value_for_payload_v29(selected_value, payload)
    agreement = bucket_support.get(best_bucket, 0.0) / max(1e-6, total_support)
    scenario_coverage = len(surviving) / max(1, len(scenario_candidates))
    outlier_ratio = outliers / max(1, len(non_null))

    confidence = 0.22 + agreement * 0.46 + scenario_coverage * 0.24 + (1.0 - outlier_ratio) * 0.08
    confidence = round(min(0.98, max(0.08, confidence)), 4)

    decision = "scenario_agreement_consensus"
    selected_from = "scenario_ensemble"
    fallback_used = False

    if agreement < 0.45:
        if llm_candidate is not None:
            selected_value = normalize_numeric_value_for_payload_v29(llm_candidate, payload)
            confidence = max(0.33, round(confidence * 0.74, 4))
            decision = "fallback_llm_low_agreement"
            selected_from = "llm"
            fallback_used = True
        elif modal_candidate is not None:
            selected_value = normalize_numeric_value_for_payload_v29(modal_candidate, payload)
            confidence = max(0.3, round(confidence * 0.7, 4))
            decision = "fallback_modal_low_agreement"
            selected_from = "modal"
            fallback_used = True

    return ScenarioEnsembleDecision(
        selected_value=selected_value,
        confidence=confidence,
        decision=decision,
        selected_from=selected_from,
        fallback_used=fallback_used,
        agreement_score=round(agreement, 4),
        outlier_rejections=outliers,
        selected_scenarios=bucket_scenarios.get(best_bucket, []),
        scenario_candidates=candidate_logs,
    )
