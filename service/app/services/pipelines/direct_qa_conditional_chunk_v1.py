"""Direct Q&A pipeline for conditional-dataset records with a ``chunk`` field."""

import math
from typing import Any

from app.models import ExperimentRequest, ExperimentResponse
from app.services.pipelines.direct_qa_v1 import _run_direct_qa


def _is_tenfold_numeric_match(extracted_value: Any, expected_value: Any) -> bool:
    """Accept a one-decimal-place extraction when it is one tenth of expected."""
    if isinstance(extracted_value, bool) or isinstance(expected_value, bool):
        return False

    try:
        extracted_number = float(str(extracted_value).strip().replace(",", "."))
        expected_number = float(str(expected_value).strip().replace(",", "."))
    except (TypeError, ValueError):
        return False

    if not math.isfinite(extracted_number) or not math.isfinite(expected_number):
        return False

    tolerance = max(1e-9, abs(expected_number) * 1e-9)
    return abs(expected_number - extracted_number * 10) <= tolerance


def run_direct_qa_conditional_chunk_v1(
    payload: ExperimentRequest,
) -> ExperimentResponse:
    """Extract the expected value, allowing a one-place decimal shift."""
    return _run_direct_qa(
        payload,
        pipeline_name="direct_qa_conditional_chunk_v1",
        additional_match=_is_tenfold_numeric_match,
    )
