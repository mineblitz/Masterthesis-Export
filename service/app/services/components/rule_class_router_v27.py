"""Rule-class classifier and prompt/scoring profiles for v27.

Classifies each extraction variable into one of four rule classes and returns
the corresponding prompt injection string and scoring weight adjustments.
"""

from __future__ import annotations

from app.models import ExperimentRequest

# ---------------------------------------------------------------------------
# Classification keyword sets
# ---------------------------------------------------------------------------

_THRESHOLD_VALUE_KEYWORDS = (
    "min",
    "max",
    "thickness",
    "distance",
    "abstand",
    "dicke",
    "mindest",
    "hoechst",
    "mm",
    "cm",
    "widerstand",
)

_THRESHOLD_CONDITION_EXCLUDE_KEYWORDS = (
    "tabelle",
    "table",
    "abschnitt",
    "section",
    "gemäß",
    "gemaess",
    "nach abschnitt",
    "laut",
    "verweis",
)

_EXCEPTION_VALUE_KEYWORDS = ("exception",)

_EXCEPTION_CONDITION_KEYWORDS = (
    "ausgenommen",
    "abweichend",
    "gilt nicht",
    "nicht zulaessig",
    "nicht zulässig",
    "nur wenn",
    "ausnahme",
)

_CROSS_REFERENCE_KEYWORDS = (
    "tabelle",
    "table",
    "abschnitt",
    "section",
    "gemäß",
    "gemaess",
    "nach abschnitt",
    "laut",
    "verweis",
)

_TABLE_LOOKUP_VALUE_KEYWORDS = ("type", "kategorie", "klasse")

_TABLE_LOOKUP_VALUE_SUFFIXES = ("_class", "_type")

_TABLE_LOOKUP_CONDITION_KEYWORDS = ("tabelle", "table")


def _condition_texts(payload: ExperimentRequest) -> list[str]:
    """Return lowercased condition value strings from the payload."""
    if not payload.conditions:
        return []
    return [c.value.lower() for c in payload.conditions if c.value]


def classify_rule_class(*, payload: ExperimentRequest) -> str:
    """Classify the extraction variable into one of four rule classes.

    Returns one of: ``"threshold"``, ``"exception"``, ``"cross_reference"``,
    ``"table_lookup"``.  Defaults to ``"threshold"`` when no signal is found.
    """
    value_lower = (payload.value or "").lower()
    conditions = _condition_texts(payload)

    # --- exception check (highest priority after explicit signals) ----------
    if any(k in value_lower for k in _EXCEPTION_VALUE_KEYWORDS):
        return "exception"
    if any(kw in cond for cond in conditions for kw in _EXCEPTION_CONDITION_KEYWORDS):
        return "exception"

    # --- table_lookup check -------------------------------------------------
    is_table_lookup_value = (
        any(k in value_lower for k in _TABLE_LOOKUP_VALUE_KEYWORDS)
        or any(value_lower.endswith(sfx) for sfx in _TABLE_LOOKUP_VALUE_SUFFIXES)
    )
    has_table_condition = any(
        kw in cond for cond in conditions for kw in _TABLE_LOOKUP_CONDITION_KEYWORDS
    )
    if is_table_lookup_value and has_table_condition:
        return "table_lookup"

    # --- cross_reference check ----------------------------------------------
    if any(kw in value_lower for kw in _CROSS_REFERENCE_KEYWORDS):
        return "cross_reference"
    if any(kw in cond for cond in conditions for kw in _CROSS_REFERENCE_KEYWORDS):
        return "cross_reference"

    # --- threshold check (default, but only when no cross-ref in conditions)
    if any(k in value_lower for k in _THRESHOLD_VALUE_KEYWORDS):
        has_cross_ref_condition = any(
            kw in cond for cond in conditions for kw in _THRESHOLD_CONDITION_EXCLUDE_KEYWORDS
        )
        if not has_cross_ref_condition:
            return "threshold"

    # --- default ------------------------------------------------------------
    return "threshold"


# ---------------------------------------------------------------------------
# Prompt injections
# ---------------------------------------------------------------------------

_PROMPT_INJECTIONS: dict[str, str] = {
    "threshold": (
        "Extrahiere den genauen numerischen Grenzwert (Minimum oder Maximum). "
        "Ignoriere Ausnahmen und Nebenaussagen. Gib nur die Zahl aus."
    ),
    "exception": (
        "Der gesuchte Wert steht möglicherweise in einer Ausnahme- oder "
        "Einschränkungsklausel. Beachte Verneinungen und Ausnahmen ('ausgenommen', "
        "'gilt nicht für', 'nur wenn'). Extrahiere den Wert, der für die gegebene "
        "Bedingung gilt."
    ),
    "cross_reference": (
        "Der gesuchte Wert könnte in einer Querverweis-Klausel oder Tabelle stehen. "
        "Folge Verweisen auf andere Abschnitte oder Tabellen und extrahiere den dort "
        "genannten Wert."
    ),
    "table_lookup": (
        "Der gesuchte Wert steht wahrscheinlich in einer Tabelle. Suche nach "
        "Tabellenzeilen oder -spalten, die die Bedingung und den Wert gemeinsam "
        "nennen."
    ),
}


def get_rule_class_prompt_injection(rule_class: str) -> str:
    """Return the German-language prompt injection for the given rule class."""
    return _PROMPT_INJECTIONS.get(rule_class, _PROMPT_INJECTIONS["threshold"])


# ---------------------------------------------------------------------------
# Scoring weights
# ---------------------------------------------------------------------------

_SCORING_WEIGHTS: dict[str, dict] = {
    "threshold": {
        "verifier_threshold_delta": 0.0,
        "top_k_delta": 0,
        "rerank_strategy": "balanced",
        "prefer_table_chunks": False,
    },
    "exception": {
        "verifier_threshold_delta": -0.05,
        "top_k_delta": 1,
        "rerank_strategy": "exception_aware",
        "prefer_table_chunks": False,
    },
    "cross_reference": {
        "verifier_threshold_delta": -0.05,
        "top_k_delta": 2,
        "rerank_strategy": "broad",
        "prefer_table_chunks": False,
    },
    "table_lookup": {
        "verifier_threshold_delta": -0.05,
        "top_k_delta": 2,
        "rerank_strategy": "balanced",
        "prefer_table_chunks": True,
    },
}


def get_rule_class_scoring_weights(rule_class: str) -> dict:
    """Return scoring weight adjustments for the given rule class."""
    return dict(_SCORING_WEIGHTS.get(rule_class, _SCORING_WEIGHTS["threshold"]))
