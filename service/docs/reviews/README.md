# Reviews & Regression Analyses

> **Navigation**: [Docs Hub](../README.md) | [Global Summary](../global/summary.md) | [Improvement Plan](../global/improvement_plan.md)

---

## Purpose

This folder is the **paper trail** for why pipeline iterations were made. Every multi-agent regression review is preserved here permanently. Do not delete these files.

Reviews explain:
- Why a pipeline regressed or improved relative to its predecessor(s)
- What the root cause classification is (implementation defect / method mismatch / config mismatch / data mismatch)
- What next iteration proposals were generated

---

## Review Documents

| Document | Scope | Date | Key Finding |
|---|---|---|---|
| [text_only_v21_v30.md](text_only_v21_v30.md) | v21–v30 (10 pipelines) | 2026-05-18 | v29/v30 collapse to 0%; v22/v23 hard failures; v28 telemetry gap |
| [text_only_v26_v30.md](text_only_v26_v30.md) | v26–v30 (5 pipelines) | 2026-05-18 | Confirms v29/v30 catastrophic collapse; validates v26–v27 gradual gains |
| [turtle_kg_v15.md](turtle_kg_v15.md) | turtle_kg_keyword_v15 vs v14 | 2026-05-18 | ~90% relative drop (29.71% → 2.84%); token collapse hypothesis |

---

## How to Read a Review

Each review document follows a standard structure:
1. **Scope** — which pipelines were compared and what data was used
2. **Executive Summary** — severity-ordered findings (Critical → High → Medium)
3. **Per-Pipeline Summaries** — individual deep dives
4. **Root Cause Classification** — implementation defect / idea mismatch / config / data
5. **Proposed Next Iterations** — concrete next pipeline proposals with measurable targets

---

## Connecting Reviews to Next Pipelines

| Review Conclusion | Led To |
|---|---|
| v29/v30 collapse: hard gates fail on noisy PDFs | v31 soft constraint voting; v32 scenario ensemble |
| v26/v27 gradual gains from compliance routing | v33 HybridRAG (confirmed compliance routing is preserved) |
| turtle_kg_v15 token collapse hypothesis | KG family backlog — v16 design pending |

---

## Adding New Reviews

When the Pipeline Review Orchestrator completes a run, the Documentation Agent places the output here.
Naming convention: `<family>_v<start>_v<end>.md` or `<family>_v<version>_vs_predecessor.md`
