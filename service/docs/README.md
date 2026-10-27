# Documentation Hub — Experiments Brandschutz

This is the central navigation index for all project documentation.
All `.md` documentation files live under `docs/` organized by type and detail level.

---

## Structure Overview

```
docs/
├── README.md                   ← you are here
├── global/                     ← project-wide summaries and dashboards
├── research/                   ← literature, papers, and technical planning
├── pipelines/                  ← per-pipeline design, research, findings (family + version)
└── reviews/                    ← multi-agent regression reviews (paper trail)
```

---

## Global / Project Level

| Document | Description |
|---|---|
| [global/summary.md](global/summary.md) | High-level synthesis across all pipeline families |
| [global/experiment_results.md](global/experiment_results.md) | Experiment dashboard snapshot — all pipelines, all LLMs |
| [global/performance_guide.md](global/performance_guide.md) | Pipeline selection guide & tiered performance rankings |
| [global/improvement_plan.md](global/improvement_plan.md) | Analysis + 18-item improvement backlog with status |

---

## Research & Literature

| Document | Description |
|---|---|
| [research/README.md](research/README.md) | Research index — how to navigate literature |
| [research/paper_index.md](research/paper_index.md) | Curated master table of peer-reviewed papers (all approaches) |
| [research/literature_review.md](research/literature_review.md) | Deep literature review (~100 papers, 13+ research directions) |
| [research/library_replacement_plan.md](research/library_replacement_plan.md) | Custom vs library implementation plan (BM25, reranker, etc.) |

---

## Pipelines

| Document | Description |
|---|---|
| [pipelines/README.md](pipelines/README.md) | Full pipeline inventory + literature mapping (all families) |
| [pipelines/dataset_compatibility.md](pipelines/dataset_compatibility.md) | Dataset compatibility matrix (17 dataset families × all pipelines) |
| [pipelines/text_only/summary.md](pipelines/text_only/summary.md) | **Text-only family** — v18 to v33, performance trend, key decisions |
| [pipelines/multimodal/summary.md](pipelines/multimodal/summary.md) | **Multimodal family** — v21, v22 findings |
| [pipelines/kg_turtle/summary.md](pipelines/kg_turtle/summary.md) | **KG / Turtle family** — v2, v3, v15 findings |

### Text-Only Pipeline Versions (v18 → v33)

| Version | Docs | Key Theme |
|---|---|---|
| v18 | [plan](pipelines/text_only/v18/plan.md) · [research](pipelines/text_only/v18/research.md) · [summary](pipelines/text_only/v18/summary.md) | Multi-query expansion, diversity selection, evidence scoring |
| v20 | [findings](pipelines/text_only/v20/findings.md) | Adaptive narrow/broad retry, evidence consistency gate |
| v21 | [findings](pipelines/text_only/v21/findings.md) | Marker-aware cleaning, semantic reranking, contradiction penalty |
| v22 | [findings](pipelines/text_only/v22/findings.md) | Domain query expansion (EI/REI/F90), numeric normalization |
| v23 | [findings](pipelines/text_only/v23/findings.md) | Marker-noise-aware retrieval, artifact filtering |
| v24 | [findings](pipelines/text_only/v24/findings.md) | Adaptive consistency gating, modal-value acceptance |
| v25 | [findings](pipelines/text_only/v25/findings.md) | Compliance-routing prefilter (first Section 7 implementation) |
| v26 | [findings](pipelines/text_only/v26/findings.md) | Clause typing + semantic verifier gate |
| v29 | [findings](pipelines/text_only/v29/findings.md) | Deterministic IR compiler (subject/condition/operator/value) |
| v30 | [findings](pipelines/text_only/v30/findings.md) | Object-model bridge → KG/BIM entity mapping |
| v31 | [findings](pipelines/text_only/v31/findings.md) | Counterexample-aware constraint voting (recovery from v29/v30 collapse) |
| v32 | [findings](pipelines/text_only/v32/findings.md) | Scenario ensemble compliance simulation (MAD outlier rejection) |
| v33 | [design](pipelines/text_only/v33/design.md) · [research](pipelines/text_only/v33/research.md) · [findings](pipelines/text_only/v33/findings.md) · [impl. summary](pipelines/text_only/v33/implementation_summary.md) | **HybridRAG** — graph + vector retrieval, triple extraction, confidence weighting |
| v35 | [plan](pipelines/text_only/v35/plan.md) · [research](pipelines/text_only/v35/research.md) · [findings](pipelines/text_only/v35/findings.md) | **Lean consolidation** — v9 simplicity + v25 routing; all v26-v34 gates removed |
| v36 | [plan](pipelines/text_only/v36/plan.md) · [research](pipelines/text_only/v36/research.md) · [design](pipelines/text_only/v36/design.md) · [findings](pipelines/text_only/v36/findings.md) | **Agentic ReAct** — bounded LLM controller over v35 prep; 5 tools; v35 baseline as deterministic fallback |

### Multimodal Pipeline Versions

| Version | Docs | Key Theme |
|---|---|---|
| v21 | [findings](pipelines/multimodal/v21/findings.md) | Marker structure parser, logo image filter |
| v22 | [findings](pipelines/multimodal/v22/findings.md) | Compliance grounding, structured violation report |

### KG / Turtle Pipeline Versions

| Version | Docs | Key Theme |
|---|---|---|
| v2 | [findings](pipelines/kg_turtle/v2/findings.md) | Hierarchical schema extraction (presence → value → assembly) |
| v3 | [findings](pipelines/kg_turtle/v3/findings.md) | Schema extension + deterministic canonicalization |
| v15 | [findings](pipelines/kg_turtle/v15/findings.md) | 3-stage Extract→Normalize→Formalize, numeric canonicalization |

---

## Reviews & Regression Analyses (Paper Trail)

These documents record multi-agent reviews and are the reasoning trail for why pipeline iterations were made.

| Document | Scope | Key Findings |
|---|---|---|
| [reviews/README.md](reviews/README.md) | Index | — |
| [reviews/text_only_v21_v30.md](reviews/text_only_v21_v30.md) | v21–v30 (10 pipelines) | v29/v30 collapse to 0%; v22/v23 hard failures; v28 telemetry gap |
| [reviews/text_only_v26_v30.md](reviews/text_only_v26_v30.md) | v26–v30 (5 pipelines) | Confirms v29/v30 catastrophic collapse; validates v26–v27 gains |
| [reviews/turtle_kg_v15.md](reviews/turtle_kg_v15.md) | turtle_kg_v15 vs v14 | ~90% relative drop (29.71% → 2.84%); token collapse hypothesis |

---

## Navigation Conventions

- **Summary layer**: `**/summary.md` — one-page overview per family, links to versions
- **Findings layer**: `**/findings.md` — full implementation record per version
- **Research layer**: `**/research.md` or `research/` — literature anchoring every design decision
- **Review layer**: `reviews/` — all regression reviews preserved as paper trail
- **Plan layer**: `**/plan.md` or `**/design.md` — pre-implementation design documents

> **Maintained by**: Documentation Agent (`.github/agents/documentation-agent.agent.md`)  
> All agent workflows that produce or update pipelines are required to invoke this agent at the end of each run.
