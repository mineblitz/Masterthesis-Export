"""Calibration profiles for text-only pipeline v34.

Applies soft, family-aware confidence and acceptance adjustments.
All adjustments are bounded and never force a hard rejection.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CalibrationProfileV34:
    name: str
    global_confidence_shift: float
    global_acceptance_shift: float
    family_confidence_shift: dict[str, float]
    family_acceptance_shift: dict[str, float]


@dataclass(frozen=True)
class CalibrationResultV34:
    profile_name: str
    variable_family: str
    calibrated_confidence: float
    calibrated_acceptance: float
    confidence_shift: float
    acceptance_shift: float
    ab_mode: str


_PROFILES: dict[str, CalibrationProfileV34] = {
    "default": CalibrationProfileV34(
        name="default",
        global_confidence_shift=0.0,
        global_acceptance_shift=0.0,
        family_confidence_shift={
            "thickness": 0.04,
            "time": 0.03,
            "distance": 0.02,
            "generic": 0.01,
        },
        family_acceptance_shift={
            "thickness": 0.03,
            "time": 0.02,
            "distance": 0.015,
            "generic": 0.0,
        },
    ),
    "conservative": CalibrationProfileV34(
        name="conservative",
        global_confidence_shift=-0.03,
        global_acceptance_shift=-0.04,
        family_confidence_shift={
            "thickness": 0.01,
            "time": 0.0,
            "distance": -0.01,
            "generic": -0.015,
        },
        family_acceptance_shift={
            "thickness": 0.0,
            "time": -0.01,
            "distance": -0.02,
            "generic": -0.03,
        },
    ),
    "high_recall": CalibrationProfileV34(
        name="high_recall",
        global_confidence_shift=0.02,
        global_acceptance_shift=0.035,
        family_confidence_shift={
            "thickness": 0.05,
            "time": 0.04,
            "distance": 0.03,
            "generic": 0.02,
        },
        family_acceptance_shift={
            "thickness": 0.04,
            "time": 0.03,
            "distance": 0.02,
            "generic": 0.02,
        },
    ),
}


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def infer_variable_family_v34(value_name: str) -> str:
    normalized = value_name.casefold().replace("_", " ")
    if any(term in normalized for term in ("dicke", "thick", "diameter", "durchmesser")):
        return "thickness"
    if any(term in normalized for term in ("time", "dauer", "minute", "feuerwiderstand", "resistance")):
        return "time"
    if any(term in normalized for term in ("abstand", "distance", "width", "breite", "hoehe", "hohe", "height")):
        return "distance"
    return "generic"


def apply_calibration_profile_v34(
    *,
    base_confidence: float,
    acceptance_score: float,
    value_name: str,
    profile_name: str = "default",
    ab_mode: str = "v34_calibrated",
) -> CalibrationResultV34:
    profile = _PROFILES.get(profile_name, _PROFILES["default"])
    family = infer_variable_family_v34(value_name)

    mode_conf_shift = 0.0
    mode_accept_shift = 0.0
    if ab_mode == "v34_calibrated_soft":
        mode_conf_shift = -0.01
        mode_accept_shift = -0.015
    elif ab_mode == "v34_calibrated_aggressive":
        mode_conf_shift = 0.015
        mode_accept_shift = 0.02

    confidence_shift = (
        profile.global_confidence_shift
        + profile.family_confidence_shift.get(family, 0.0)
        + mode_conf_shift
    )
    acceptance_shift = (
        profile.global_acceptance_shift
        + profile.family_acceptance_shift.get(family, 0.0)
        + mode_accept_shift
    )

    calibrated_confidence = round(_clamp(base_confidence + confidence_shift, 0.05, 0.98), 4)
    calibrated_acceptance = round(_clamp(acceptance_score + acceptance_shift, 0.0, 1.0), 4)

    return CalibrationResultV34(
        profile_name=profile.name,
        variable_family=family,
        calibrated_confidence=calibrated_confidence,
        calibrated_acceptance=calibrated_acceptance,
        confidence_shift=round(confidence_shift, 4),
        acceptance_shift=round(acceptance_shift, 4),
        ab_mode=ab_mode,
    )
