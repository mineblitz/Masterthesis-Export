# KG / Turtle Pipeline Family — Summary

> **Navigation**: [Docs Hub](../../README.md) | [Pipeline Inventory](../README.md) | [Global Summary](../../global/summary.md) | [Reviews](../../reviews/README.md)

---

## Family Overview

The KG/Turtle family (`kg_comprehensive_schema_minimal_turtle_vX`, `turtle_kg_keyword_vXX`) extracts RDF triples in Turtle syntax from fire-protection approval documents. The goal is structured knowledge-graph output for downstream compliance reasoning and BIM integration.

**Lineage**: v2 → v3 → ... → v14 → v15 (regression)

---

## Performance

| Version | Success Rate (approx.) | Change | Key Theme |
|---|---|---|---|
| v2 | ~15% | — | Hierarchical schema extraction |
| v3 | ~18% | +3pp | Schema extension + canonicalization |
| v14 | ~30% | (predecessor) | Best result achieved |
| v15 | ~3% | **–27pp COLLAPSE** | Token collapse — see regression review |

> v15 regression is documented in [reviews/turtle_kg_v15.md](../../reviews/turtle_kg_v15.md). Root cause hypothesis: implementation defect causing token collapse that correlates with quality collapse.

---

## Version Details

### [v2](v2/findings.md) — Hierarchical Schema Extraction
- 4-stage extraction: presence → subtype → value → assembly
- Builds a hierarchical rather than flat extraction approach
- New component: `kg_hierarchical_extraction_component.py`

### [v3](v3/findings.md) — Schema Extension + Canonicalization
- Adds schema extension stage: discovers entity types not in base schema
- Adds deterministic canonicalization stage: normalizes values before Turtle serialization
- Implements Section 7 KG canonicalization finding

### [v15](v15/findings.md) — 3-Stage Extract→Normalize→Formalize
- 3-stage pipeline: Extract entities → Normalize numeric values → Formalize as Turtle
- Deterministic numeric canonicalization (F90 → fire rating 90min, etc.)
- **Status**: Severely regressed (~3% vs v14's ~30%)
- **Root cause**: Under investigation — see [regression review](../../reviews/turtle_kg_v15.md)

---

## Open Issues

1. **v15 regression not resolved** — token collapse hypothesis needs implementation audit.
2. **v14 baseline not documented** — no findings file exists for v14; understanding v14's design is a prerequisite for diagnosing v15.
3. **KG output quality not measured separately** — Turtle syntax validity and triple completeness are not tracked in the current dashboard.

---

## Related Documents

- [Pipeline Inventory](../README.md) — paper mapping for KG family
- [Review: turtle_kg_v15](../../reviews/turtle_kg_v15.md) — regression analysis
- [Research: Paper Index](../../research/paper_index.md) — KG extraction section
- [Research: Literature Review](../../research/literature_review.md) — KG-Extraction, Rule-Extraction sections
- [Global Improvement Plan](../../global/improvement_plan.md) — KG family items in backlog
