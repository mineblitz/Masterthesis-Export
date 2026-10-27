# Research Index

> **Navigation**: [Docs Hub](../README.md) | [Paper Index](paper_index.md) | [Literature Review](literature_review.md) | [Library Replacement Plan](library_replacement_plan.md)

---

## Purpose

This folder contains all research material that underpins pipeline design decisions. Every pipeline version is traceable to one or more papers in this research base.

---

## Documents

### [paper_index.md](paper_index.md)
**Curated master table** of peer-reviewed papers used by all agents. Organized by approach class:
- Text-only RAG/IE pipelines
- Multimodal models
- KG extraction
- Compliance checking
- Surveys & benchmarks

Includes relevance scores and direct pipeline-mapping notes. **This is the canonical source of truth for literature** — update it whenever a new paper is used for a pipeline.

---

### [literature_review.md](literature_review.md)
**Deep literature survey** covering ~100 papers across 13+ research directions:
RAG, LLM-IE, Layout-Analysis, Multi-modal, KG-Extraction, Rule-Extraction, Compliance, BIM, etc.

Each entry includes: paper title, year, methodology tags, relevance score, key finding, and applicability notes.

---

### [library_replacement_plan.md](library_replacement_plan.md)
**Technical implementation plan** mapping current custom implementations to mature Python library alternatives:
- BM25 (rank_bm25)
- Cross-encoder reranker (sentence-transformers)
- Instructor schema parser (instructor, pydantic)
- Proposed library-backed pipelines (v28+) for A/B benchmarking

---

## Traceability Convention

When a pipeline version is implemented:
1. The **research document** (`docs/pipelines/<family>/<version>/research.md`) lists the exact papers used.
2. The **findings document** references these papers in a `## References` section.
3. The [paper_index.md](paper_index.md) is updated to note which pipeline(s) each paper influenced.

This ensures every design decision has a traceable academic justification.

---

## Key Research Directions and Pipeline Coverage

| Research Direction | Papers | Pipelines Influenced |
|---|---|---|
| CRAG / corrective RAG | CRAG 2024 | v18, v20 |
| Compliance routing / Section 7 | Regulatory IE papers | v25, v26 |
| Semantic reranking / cross-encoder | Reranker survey 2025 | v21, v28 |
| Noise-resilient retrieval | Layout-aware chunking | v23 |
| Graph-augmented retrieval | HybridRAG, KGRAG | v33 |
| Ensemble / voting methods | MAD ensemble papers | v32 |
| Numeric canonicalization | Regulatory normalization | v22, v24 |
| KG triple extraction | Open IE, Rebel | v2, v3, v15, v33 |
| BIM compliance checking | IFC compliance papers | v22 multimodal |
