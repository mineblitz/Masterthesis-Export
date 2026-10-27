# Text-Only Pipeline Family — Summary

> **Navigation**: [Docs Hub](../../README.md) | [Pipeline Inventory](../README.md) | [Global Summary](../../global/summary.md) | [Reviews](../../reviews/README.md)

---

## Family Overview

The text-only family (`text_only_simple_conversion_vXX`) is the primary pipeline family. It processes Marker-parsed text from fire-protection approval PDFs and extracts compliance values using LLM-based RAG.

**Lineage**: v18 → v20 → v21 → v22 → v23 → v24 → v25 → v26 → [v27, v28 — no docs] → v29 → v30 → v31 → v32 → v33 → v34 → **v35 (consolidation)** → **v36 (agentic)**

---

## Performance Trend

| Version | Success Rate (approx.) | Change | Key Driver |
|---|---|---|---|
| v18 | ~15% | baseline | Multi-query expansion, retry |
| v20 | ~18% | +3pp | Evidence consistency gate |
| v21 | ~22% | +4pp | Semantic reranking, contradiction penalty |
| v22 | ~22% | ~0pp | Domain synonyms, numeric norm |
| v23 | ~24% | +2pp | Noise-aware retrieval |
| v24 | ~24% | ~0pp | Modal-value acceptance |
| v25 | ~32% | +8pp | Compliance routing prefilter |
| v26 | ~35-40% | +3-8pp | Clause typing + semantic verifier |
| v29 | ~0% | **COLLAPSE** | IR compiler + hard gates broke on real data |
| v30 | ~0% | **COLLAPSE** | Object-model bridge compounded hard gates |
| v31 | TBD | recovery attempt | Soft constraint voting |
| v32 | TBD | recovery attempt | Scenario ensemble (MAD) |
| v33 | TBD | new approach | HybridRAG (graph + vector) |
| v35 | TBD | **consolidation** | Lean compliance-routed single-pass — v9 simplicity + v25 routing, all v26-v34 gates removed |
| v36 | TBD | **agentic** | ReAct-style controller over v35 prep; 5 tools, step+token budget, v35-baseline fallback |

> Why did v29/v30 collapse? See the review: [reviews/text_only_v26_v30.md](../../reviews/text_only_v26_v30.md)

---

## Version Details

### [v18](v18/plan.md) — Foundation
Three-document set: pre-implementation [plan](v18/plan.md), [research](v18/research.md) distillation, and post-implementation [summary](v18/summary.md).
- Research: CRAG 2024, RAG best practices 2025, Longtriever
- Key additions: multi-query expansion, diversity selection, evidence scoring, bounded corrective retry

### [v20](v20/findings.md) — Evidence Gating
- Adaptive narrow/broad retry strategy
- Evidence consistency gate (multi-pass agreement)

### [v21](v21/findings.md) — Semantic Reranking
- Marker-aware text cleaning
- Semantic reranking via cross-encoder
- Contradiction-aware penalty
- Adaptive retry strategy switching

### [v22](v22/findings.md) — Domain Synonyms
- Fire-class query expansion: EI/REI/F90 synonym variants
- Numeric normalization (hours↔minutes)
- Addresses simpleMinMaxExtraction recall gap

### [v23](v23/findings.md) — Noise Filtering
- Line-level Marker artifact detection
- Noise-penalty scoring
- Hard suppression of high-noise chunks

### [v24](v24/findings.md) — Consistency Gating
- Adaptive consistency gating using modal-value acceptance
- Fixes false negatives from multi-valued spec variables

### [v25](v25/findings.md) — Compliance Routing ⭐
- Compliance-routing prefilter: boosts requirement headings, penalizes administrative text
- First implementation anchored in Section 7 compliance-checking literature
- Biggest single-version gain in the family

### [v26](v26/findings.md) — Clause Typing ⭐
- Clause type classification: requirement / scope / exception
- Semantic verifier gate: acceptance requires numeric support from requirement-type chunks only
- Further refines compliance routing from v25

### [v29](v29/findings.md) — IR Compiler ⚠️ COLLAPSED
- Deterministic regulation-to-IR compiler (subject/condition/operator/value/unit/exception schema)
- Hard gates caused catastrophic 0% performance on noisy real PDFs
- See [regression review](../../reviews/text_only_v26_v30.md)

### [v30](v30/findings.md) — Object-Model Bridge ⚠️ COLLAPSED
- Object-model bridge → canonical KG/BIM entity mapping
- Compounded the v29 hard gate failures
- See [regression review](../../reviews/text_only_v26_v30.md)

### [v31](v31/findings.md) — Constraint Voting (Recovery)
- Replaces hard gates with soft support-vs-contradiction margin voting
- Designed to recover from v29/v30 collapse

### [v32](v32/findings.md) — Scenario Ensemble (Recovery)
- Multi-scenario consensus: strict / balanced / broad / exception-stress
- MAD-style outlier rejection
- Evidence-grounded robustness improvement over v31

### [v33](v33/findings.md) — HybridRAG (New Approach) 🆕
- Triple extraction from chunks (59-predicate lexicon)
- Graph neighborhood retrieval: entity-hop expansion
- Hybrid chunk aggregator: graph + dense vector fusion
- Confidence-weighted aggregation
- Docs: [design](v33/design.md) · [research](v33/research.md) · [findings](v33

### [v35](v35/findings.md) — Lean Compliance-Routed Single-Pass (Consolidation) 🧹
- Built on the **proven** combination of v9 prompt simplicity + v25 compliance-routing prefilter
- **Removes** every gate / retry / ensemble layer added in v20-v34 that correlated with the v29-v34 regressions
- Single LLM call; no verifier, no consistency gate, no IR compiler, no object-model bridge, no triple/graph expansion, no calibration sandbox
- Docs: [plan](v35/plan.md) · [research](v35/research.md) · [findings](v35/findings.md)/findings.md) · [implementation summary](v33/implementation_summary.md)
- Research anchor: 12 papers; graph+vector hybrids +12-18% multi-hop precision

---

## Related Documents

- [Pipeline Inventory & Paper Mapping](../README.md) — all pipelines with direct paper anchors
- [Review: v21–v30](../../reviews/text_only_v21_v30.md) — 10-pipeline regression analysis
- [Review: v26–v30](../../reviews/text_only_v26_v30.md) — focused collapse diagnosis
- [Improvement Plan](../../global/improvement_plan.md) — ranked backlog of pending improvements
- [Research: Paper Index](../../research/paper_index.md) — all papers by approach class
