# text_only_simple_conversion_v35 — Research

**Status**: consolidation iteration based on existing literature anchors  
**Date**: 2026-06-01

## Note on research scope

v35 is an explicit **simplification** iteration motivated by *negative results* in v29-v34 and the dashboard-observed plateau at v25/v26. It does not introduce any new external mechanism; instead, it re-applies already-anchored techniques from the repository's existing paper index with stricter discipline (no hard gates, no multi-pass retries).

Because no new component is introduced, the paper anchors below are drawn from the existing `docs/research/paper_index.md` and `docs/pipelines/README.md` Section 7 (compliance-checking extraction mapping). All papers were previously vetted for the text-only lineage.

## Anchoring papers

### Group A: compliance-routing prefilter (the *preserved* core)
1. Zhang & El-Gohary (2016) — *Semantic NLP-Based Information Extraction from Construction Regulatory Documents for Automated Compliance Checking* — supports requirement-first routing.
2. *A platform-based Natural Language processing-driven strategy for digitalising regulatory compliance processes for the built environment* (2024) — supports clause-type prefiltering for IE pipelines.
3. Hjelseth & Janssen (2012) — *Extraction of Construction Regulatory Requirements from Textual Documents Using NLP Techniques* — classical clause-aware extraction.

### Group B: single-pass extraction with LLMs (the *v9 discipline*)
4. Dunn et al. (2024) — *Structured information extraction from scientific text with large language models* — single-pass prompt-only structured IE.
5. *Understanding Tradeoffs in Clinical Text Extraction: Prompting, Retrieval-Augmented Generation, and Supervised Learning on EHRs* (2026) — direct comparison showing prompt+retrieval often matches or beats heavier supervised stacks.
6. Chong et al. (2024) — *Using Large Language Models for the Interpretation of Building Regulations* — direct LLM extraction with light grounding works on building regulations.
7. *Retrieval augmented generation-driven information retrieval and question answering in construction management* (2025) — RAG-only pipelines (no verifier loops) perform well in this domain.

### Group C: why over-engineered retry/gating loops hurt
8. Yan et al. (2024) — *Corrective Retrieval Augmented Generation (CRAG)* — corrective retrieval helps **only when the initial retriever is systematically wrong**; otherwise repeated retries compound bias. v17–v26 corrective retry was justified by this paper but the dashboard shows it plateaued and the v29+ extensions of it collapsed.
9. *Enhancing Retrieval-Augmented Generation* (2025) — multi-query expansion is the cheap component; iterative replanning is the expensive one. v35 keeps the former and drops the latter.
10. *Longtriever* (2023) — long-context retrieval lessons; query expansion alone explains most of the gain.

### Group D: hard-gate failure mode (the *negative evidence*)
11. Internal regression review: [`docs/reviews/text_only_v26_v30.md`](../../../reviews/text_only_v26_v30.md) — documents the v29 0% collapse correlating with deterministic IR gate introduction.
12. Internal regression review: [`docs/reviews/text_only_v21_v30.md`](../../../reviews/text_only_v21_v30.md) — 10-pipeline comparison; v25/v26 plateau as text-only ceiling on gemma-3-27b-it.

## Synthesis

The literature points consistently in two directions for v35:

- **Keep**: routing/prefilter (Group A) and single-pass LLM extraction (Group B). These map directly to the components retained in v35.
- **Drop**: heavy multi-pass verifier loops unless the *base* retriever is provably broken (Group C, CRAG's own scoping caveat). Combined with the internal negative evidence (Group D) showing the v29+ hard-gate cascade, this justifies removing every gate added after v25.

## Open questions for future work (not in v35)

- Calibrated soft verifier (not a hard gate) per variable family — would extend v35 toward v34's intent without re-introducing v34's blocking behaviour.
- Library-backed retrieval stack (BM25 + cross-encoder) as in v28 — already tested in v28 with promising telemetry but token-instrumented inconsistently; deserves a clean re-run.
