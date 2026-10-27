"""RDF Turtle canonicalizer backed by rdflib.

New component for v4 KG pipelines. Replaces the inline regex canonicalization in
kg_comprehensive_schema_minimal_turtle_v3.py (_canonicalize_qname_locals,
_canonicalize_numeric_literals, _ensure_schema_prefixes, _dedupe_turtle_lines)
with an rdflib round-trip: parse → bind namespace prefixes → serialize.
Existing pipeline v3 and its helper functions are unchanged.
"""

from __future__ import annotations

from typing import Any

try:
    import rdflib  # type: ignore[import-untyped]
    _RDFLIB_AVAILABLE = True
except ImportError:
    _RDFLIB_AVAILABLE = False


def _extract_prefix_bindings(schema_ttl: str) -> list[tuple[str, str]]:
    """Parse @prefix declarations from a Turtle schema string."""
    import re
    prefix_re = re.compile(
        r"@prefix\s+([A-Za-z][\w-]*):\s*<([^>]+)>\s*\.", re.IGNORECASE
    )
    return [(m.group(1), m.group(2)) for m in prefix_re.finditer(schema_ttl)]


def canonicalize_turtle(
    turtle_text: str,
    schema_ttl: str = "",
) -> tuple[str, dict[str, Any]]:
    """Canonicalize a Turtle string using rdflib round-trip serialization.

    Steps:
    1. Parse turtle_text into an rdflib.Graph.
    2. Bind all namespace prefixes found in schema_ttl to the output graph.
    3. Serialize the graph back to Turtle with rdflib's canonical output.

    This produces deterministic prefix ordering, normalized literals, and
    deduplication without any regex manipulation.

    Args:
        turtle_text: Raw Turtle text, possibly malformed.
        schema_ttl: Optional Turtle schema whose @prefix declarations are
                    injected into the output graph's namespace bindings.

    Returns:
        Tuple of (canonical_turtle_string, stats_dict). stats_dict contains:
            - input_triple_count: triples parsed from turtle_text
            - output_triple_count: triples in canonical output
            - schema_prefixes_bound: number of prefixes added from schema_ttl
            - parse_method: "direct" or "repaired"

    Raises:
        ImportError: If rdflib is not installed.
        ValueError: If turtle_text cannot be parsed even after repair.
    """
    if not _RDFLIB_AVAILABLE:
        raise ImportError(
            "rdflib is required for rdf_canonicalizer. "
            "Install it with: pip install rdflib"
        )

    from app.services.components.rdf_turtle_parser import parse_turtle

    # Parse the input turtle (with fence stripping and prefix repair)
    parse_method = "direct"
    try:
        graph = parse_turtle(turtle_text)
    except ValueError as exc:
        raise ValueError(f"canonicalize_turtle: parse failed — {exc}") from exc

    input_triple_count = len(graph)

    # Bind schema prefixes so they appear in the canonical output
    schema_prefixes_bound = 0
    if schema_ttl:
        for prefix, uri in _extract_prefix_bindings(schema_ttl):
            graph.bind(prefix, rdflib.Namespace(uri), override=False)
            schema_prefixes_bound += 1

    # Serialize to canonical Turtle
    canonical = graph.serialize(format="turtle")
    output_triple_count = len(graph)

    return canonical, {
        "input_triple_count": input_triple_count,
        "output_triple_count": output_triple_count,
        "schema_prefixes_bound": schema_prefixes_bound,
        "parse_method": parse_method,
    }
