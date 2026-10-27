"""Deterministic compliance-report scaffold builder for multimodal pipeline v22."""

from __future__ import annotations

from typing import Any


def _try_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        raw = value.strip().replace(",", ".")
        if not raw:
            return None
        try:
            return float(raw)
        except ValueError:
            return None
    return None


def _normalize_mode(min_or_max: str | None) -> str:
    if not min_or_max:
        return "exact"
    normalized = min_or_max.strip().lower()
    if "min" in normalized or "klein" in normalized:
        return "minimum"
    if "max" in normalized or "gro" in normalized:
        return "maximum"
    return "exact"


def _sort_evidence(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: (
            -float(item.get("score", 0.0)),
            str(item.get("id", "")),
        ),
    )


def _determine_status(*, expected_value: Any, extracted_value: Any, mode: str) -> tuple[str, float | None]:
    expected_num = _try_float(expected_value)
    extracted_num = _try_float(extracted_value)

    if expected_num is None or extracted_num is None:
        return "undetermined", None

    deviation = round(extracted_num - expected_num, 4)

    if mode == "minimum":
        return ("compliant" if extracted_num >= expected_num else "violation"), deviation
    if mode == "maximum":
        return ("compliant" if extracted_num <= expected_num else "violation"), deviation
    return ("compliant" if abs(deviation) < 1e-9 else "violation"), deviation


def build_compliance_report_v22(
    *,
    expected_value: Any,
    extracted_value: Any,
    min_or_max: str | None,
    text_evidence: list[dict[str, Any]],
    image_evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a deterministic violation-report style scaffold from selected evidence."""
    mode = _normalize_mode(min_or_max)
    sorted_text = _sort_evidence(text_evidence)
    sorted_images = _sort_evidence(image_evidence)
    check_status, deviation = _determine_status(
        expected_value=expected_value,
        extracted_value=extracted_value,
        mode=mode,
    )

    text_ids = [item["id"] for item in sorted_text]
    image_ids = [item["id"] for item in sorted_images]

    return {
        "report_type": "compliance_violation_report_v22",
        "check_status": check_status,
        "comparison_mode": mode,
        "expected_value": expected_value,
        "extracted_value": extracted_value,
        "deviation": deviation,
        "evidence_provenance": {
            "text_evidence_ids": text_ids,
            "image_evidence_ids": image_ids,
            "primary_text_evidence_id": text_ids[0] if text_ids else None,
            "primary_image_evidence_id": image_ids[0] if image_ids else None,
        },
        "grounded_evidence": {
            "text": sorted_text,
            "images": sorted_images,
        },
    }
