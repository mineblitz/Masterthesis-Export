# Global Summary — All Pipeline Families

> **Navigation**: [Docs Hub](../README.md) | [Experiment Results](experiment_results.md) | [Performance Guide](performance_guide.md) | [Improvement Plan](improvement_plan.md)

Last meaningful update: May 2026 (v33 complete). Update this file after any new experiment batch or major pipeline milestone.

---

## Project Goal

Automated extraction of fire-protection compliance values from German building-approval PDFs using LLM-based retrieval-augmented generation (RAG) pipelines. Three pipeline families have been developed in parallel.

---

## Pipeline Families at a Glance

| Family | Versions | Best Result | Status |
|---|---|---|---|
| **Text-only** | v18–v33 | ~35-40% (v26) | Active, v33 complete |
| **Multimodal** | v21–v22 | ~10-15% | Experimental |
| **KG / Turtle** | v2, v3, v15 | ~30% (v14, regressed in v15) | Under investigation |

See [Performance Guide](performance_guide.md) for tier-based rankings and deployment recommendations.

---

## Text-Only Family — Trend

```
v18 (baseline) → v21 (reranking) → v25/v26 (compliance routing) → v31/v32 (ensemble) → v33 (HybridRAG)
     ~15%              ~22%                  ~32-40%                     TBD                  TBD
```

Key inflection points:
- **v21**: Semantic reranking + contradiction penalty → first meaningful gain above v18
- **v25/v26**: Compliance-routing prefilter / clause typing → best scores achieved
- **v29/v30**: Catastrophic collapse to ~0% (IR compiler + object-model bridge over-engineered hardgates) — documented in [reviews/text_only_v26_v30.md](../reviews/text_only_v26_v30.md)
- **v31/v32**: Recovery via soft ensemble voting
- **v33**: HybridRAG — graph + vector retrieval; results pending

Full per-version trail: [text_only/summary.md](../pipelines/text_only/summary.md)

---

## Multimodal Family — Summary

Built on Marker-parsed document structure (images + text blocks). V22 added a compliance grounding stage and structured violation reports. Performance consistently lower than text-only pipelines; cost/benefit not yet favourable.

Details: [multimodal/summary.md](../pipelines/multimodal/summary.md)

---

## KG / Turtle Family — Summary

Extracts Turtle RDF triples from fire-protection documents. V14 achieved ~30% but v15 regressed sharply (~3%); root cause: token collapse correlated with quality collapse. Under investigation.

Details: [kg_turtle/summary.md](../pipelines/kg_turtle/summary.md) | Review: [reviews/turtle_kg_v15.md](../reviews/turtle_kg_v15.md)

---

## Research Foundation

All pipeline improvements are anchored in peer-reviewed literature:
- [Paper Index](../research/paper_index.md) — master paper table with pipeline mapping
- [Literature Review](../research/literature_review.md) — 100-paper survey across 13 research directions
- Each pipeline version carries a `research.md` or inline research section linking design to papers

---

## Key Cross-Cutting Observations

1. **Compliance routing** (Section 7 literature) is the strongest signal — correctly weighting requirement-type chunks vs administrative text drives the biggest gains.
2. **Hard gates fail** — v29/v30 showed that deterministic gate logic collapses on noisy, varied real PDFs. Prefer soft margin-based or ensemble approaches.
3. **Marker noise** matters — raw Marker output contains significant line-level artifacts; filtering these (v23) improved recall.
4. **Numeric canonicalization** (hours↔minutes, EI/REI/F90 synonyms) is necessary for recall.
5. **Graph-augmented retrieval** (v33) is the next testable hypothesis for multi-hop compliance checking.
