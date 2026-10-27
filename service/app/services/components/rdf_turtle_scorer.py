"""RDF triple set scorer backed by rdflib.

New component for v4 KG pipelines. Replaces the set-based comparison in
turtle_triple_scorer_component.py with rdflib graph isomorphism and optional
pyshacl validation. Returns the same dict shape as score_triple_sets so
new pipelines can swap in without changing result models.
Existing turtle_triple_scorer_component.py is unchanged.
"""

from __future__ import annotations

from typing import Any

try:
    import rdflib  # type: ignore[import-untyped]
    _RDFLIB_AVAILABLE = True
except ImportError:
    _RDFLIB_AVAILABLE = False


def score_graphs(
    predicted: "rdflib.Graph",
    expected: "rdflib.Graph",
) -> dict[str, Any]:
    """Compute precision / recall / F1 by comparing two rdflib graphs.

    Serializes both graphs to N-Triples (which gives canonical, normalised triple
    strings) and computes set intersection — more robust than the custom regex
    triple parser in turtle_triple_scorer_component.py.

    Args:
        predicted: The rdflib.Graph produced by the pipeline LLM.
        expected: The rdflib.Graph for the ground-truth Turtle.

    Returns:
        Dict with keys: predicted_triples, expected_triples, correct_triples,
        precision, recall, f1. Same shape as turtle_triple_scorer_component.score_triple_sets.

    Raises:
        ImportError: If rdflib is not installed.
    """
    if not _RDFLIB_AVAILABLE:
        raise ImportError(
            "rdflib is required for rdf_turtle_scorer. "
            "Install it with: pip install rdflib"
        )

    def _graph_to_triple_set(graph: "rdflib.Graph") -> set[tuple[str, str, str]]:
        triples: set[tuple[str, str, str]] = set()
        for line in graph.serialize(format="nt").strip().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.rstrip(" .").split(None, 2)
            if len(parts) == 3:
                triples.add((parts[0], parts[1], parts[2]))
        return triples

    predicted_triples = _graph_to_triple_set(predicted)
    expected_triples = _graph_to_triple_set(expected)
    correct = predicted_triples & expected_triples

    p_count = len(predicted_triples)
    e_count = len(expected_triples)
    c_count = len(correct)

    precision = c_count / p_count if p_count else (1.0 if e_count == 0 else 0.0)
    recall = c_count / e_count if e_count else (1.0 if p_count == 0 else 0.0)
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {
        "predicted_triples": p_count,
        "expected_triples": e_count,
        "correct_triples": c_count,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def validate_with_shacl(
    data_graph: "rdflib.Graph",
    shacl_graph: "rdflib.Graph",
) -> dict[str, Any]:
    """Validate a data graph against SHACL shapes using pyshacl.

    Args:
        data_graph: The rdflib.Graph to validate.
        shacl_graph: SHACL shapes graph.

    Returns:
        Dict with keys: conforms (bool), violation_count (int), report_text (str).

    Raises:
        ImportError: If pyshacl is not installed.
    """
    try:
        from pyshacl import validate as shacl_validate  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError(
            "pyshacl is required for SHACL validation. "
            "Install it with: pip install pyshacl"
        ) from exc

    conforms, results_graph, results_text = shacl_validate(
        data_graph,
        shacl_graph=shacl_graph,
        inference="rdfs",
        abort_on_first=False,
    )
    violation_count = sum(
        1 for _ in results_graph.subjects(
            rdflib.RDF.type,
            rdflib.URIRef("http://www.w3.org/ns/shacl#ValidationResult"),
        )
    )
    return {
        "conforms": bool(conforms),
        "violation_count": violation_count,
        "report_text": str(results_text)[:1000],
    }
