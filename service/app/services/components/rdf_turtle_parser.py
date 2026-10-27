"""RDF Turtle parser backed by rdflib.

New component for v4 KG pipelines. Replaces the custom regex-based Turtle parser in
turtle_triple_scorer_component.py with rdflib's full Turtle 1.1 parser.
Existing turtle_triple_scorer_component.py is unchanged.
"""

from __future__ import annotations

import re

try:
    import rdflib  # type: ignore[import-untyped]
    _RDFLIB_AVAILABLE = True
except ImportError:
    _RDFLIB_AVAILABLE = False


_FENCE_RE = re.compile(r"^```[a-zA-Z]*\s*\n?", re.MULTILINE)
_FENCE_CLOSE_RE = re.compile(r"\n?```\s*$", re.MULTILINE)

_COMMON_MISSING_PREFIXES = (
    "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n",
    "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n",
    "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n",
    "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n",
)


def _strip_markdown_fences(text: str) -> str:
    text = _FENCE_RE.sub("", text)
    text = _FENCE_CLOSE_RE.sub("", text)
    return text.strip()


def _inject_missing_prefixes(turtle_text: str) -> str:
    """Prepend commonly missing standard prefixes that the model often omits."""
    header_lines: list[str] = []
    for prefix_line in _COMMON_MISSING_PREFIXES:
        prefix_decl = prefix_line.split("<")[0].lower()
        if prefix_decl.strip() not in turtle_text.lower():
            header_lines.append(prefix_line.rstrip())
    if not header_lines:
        return turtle_text
    return "\n".join(header_lines) + "\n\n" + turtle_text


def parse_turtle(turtle_text: str) -> "rdflib.Graph":
    """Parse a Turtle string into an rdflib Graph.

    Applies a repair pre-pass (markdown fence stripping, missing common prefix
    injection) before parsing. On the first parse error, injects all standard
    prefixes and retries once.

    Args:
        turtle_text: Raw Turtle text, possibly with markdown fences.

    Returns:
        rdflib.Graph with the parsed triples.

    Raises:
        ImportError: If rdflib is not installed.
        ValueError: If the text cannot be parsed as valid Turtle after repair.
    """
    if not _RDFLIB_AVAILABLE:
        raise ImportError(
            "rdflib is required for rdf_turtle_parser. "
            "Install it with: pip install rdflib"
        )

    cleaned = _strip_markdown_fences(turtle_text)
    if not cleaned.strip():
        raise ValueError("Empty Turtle text after stripping markdown fences")

    graph = rdflib.Graph()

    # First attempt — parse as-is
    try:
        graph.parse(data=cleaned, format="turtle")
        return graph
    except Exception:
        pass

    # Second attempt — inject missing standard prefixes
    repaired = _inject_missing_prefixes(cleaned)
    try:
        graph.parse(data=repaired, format="turtle")
        return graph
    except Exception as exc:
        preview = cleaned[:400].replace("\n", " ")
        raise ValueError(
            f"rdflib could not parse Turtle text after repair attempt. "
            f"Preview: {preview!r}. Error: {exc}"
        ) from exc


def parse_turtle_to_triple_set(turtle_text: str) -> set[tuple[str, str, str]]:
    """Parse Turtle text and return a normalized set of (subject, predicate, object) strings.

    Uses rdflib N-Triples serialization to produce canonical triple strings,
    which is more robust than the custom regex approach in turtle_triple_scorer_component.py.

    Args:
        turtle_text: Raw Turtle text.

    Returns:
        Set of (subject, predicate, object) string tuples in N-Triples notation.

    Raises:
        ImportError: If rdflib is not installed.
        ValueError: If parsing fails.
    """
    graph = parse_turtle(turtle_text)
    triples: set[tuple[str, str, str]] = set()
    nt_lines = graph.serialize(format="nt").strip().splitlines()
    for line in nt_lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # N-Triples format: <subj> <pred> <obj> .
        # Split carefully on whitespace, keeping object (which may contain spaces)
        parts = line.rstrip(" .").split(None, 2)
        if len(parts) == 3:
            triples.add((parts[0], parts[1], parts[2]))
    return triples
