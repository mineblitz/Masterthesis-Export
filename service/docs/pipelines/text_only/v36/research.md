# text_only_simple_conversion_v36 — Research

**Status**: agentic-LLM extension of the v35 lean baseline.
**Date**: 2026-06-01

## Scope

v36 introduces an LLM-driven controller (ReAct-style plan-act-observe loop
with tool use) on top of the proven v35 deterministic prep. The literature
anchors below were selected for direct relevance to **bounded agentic LLM
loops for information extraction**, with explicit guardrails against the
failure patterns the family already encountered in v29-v34 (rigid gates,
unbounded retries, IR compiler collapse).

Per the prompt's research budget guidance (2–4 grounding papers, prefer
items already in `docs/research/paper_index.md`), we cite four anchors,
two from the existing index and two that are well-established in the
agentic-LLM literature but not previously needed in the text-only family.

## Anchoring papers

### A1 — ReAct: Synergizing Reasoning and Acting in Language Models
- Yao et al., ICLR 2023.
- **Why relevant**: defines the canonical plan-act-observe loop with strict
  JSON tool schemas. v36's controller is a direct, minimal implementation
  of this pattern: one tool per step, observation injected into next prompt,
  bounded by an external step budget.
- **What we adopt**: the prompt structure (thought → action → observation),
  per-step single-tool discipline, and the principle that *the LLM, not a
  hard-coded planner, decides when to stop*.
- **What we discard**: the open-ended "no budget" variant. v36 enforces a
  hard step budget (4) and a hard token budget (6000) — see C1 below.

### A2 — Toolformer: Language Models Can Teach Themselves to Use Tools
- Schick et al., NeurIPS 2023.
- **Why relevant**: motivates the small, well-defined toolset over generic
  function-calling. v36 exposes exactly 5 tools (inspect_chunk, expand_query,
  retrieve_more_context, refine_extraction, finalize_answer) so the agent
  cannot wander outside the proven v18/v25 retrieval surface.
- **What we adopt**: tool surface minimalism.
- **What we discard**: any fine-tuning step — v36 is prompt-only on top of
  the production gemma-3-27b-it baseline.

### A3 — Corrective Retrieval Augmented Generation (CRAG)
- Yan et al., 2024 — already in `docs/research/paper_index.md` Section 1
  and 4.
- **Why relevant (and why we use it as a *negative anchor*)**: CRAG's own
  scoping note — "corrective retrieval helps **only when the initial
  retriever is systematically wrong**" — is the lesson v35 distilled and
  v36 must continue to respect. The v17–v26 corrective retry loop *was*
  justified by CRAG but plateaued at v25/v26 and the v29+ extensions
  collapsed to 0%.
- **What we adopt**: a bounded agentic loop that includes a
  retrieve-more-context tool but is **gated by an LLM decision**, not a
  deterministic confidence threshold.
- **What we discard**: any deterministic retrieval-quality gate that can
  force a retry; the agent decides, and the budget bounds it.

### A4 — Enhancing Retrieval-Augmented Generation: a Study of Best Practices
- COLING 2025 — already in `docs/research/paper_index.md` Section 1 update.
- **Why relevant**: empirically shows that *multi-query expansion is the
  cheap component and iterative replanning is the expensive one*. v36 keeps
  v35's deterministic multi-query expansion (cheap), and exposes
  `expand_query` as an agent tool only for the case where the deterministic
  expansion missed a relevant term.
- **What we adopt**: the cheap-first, agent-as-last-resort architecture.

## Synthesis

The literature points to a clear architecture for v36:

- **Use ReAct's loop structure** (A1), but with an external hard step budget
  to avoid the runaway behaviour that A1's open-ended formulation can
  produce on long-tail inputs.
- **Use Toolformer's minimal-tool discipline** (A2): expose only the tools
  that map to already-proven v18/v25 components. No general tool surface.
- **Respect CRAG's scoping caveat** (A3): the agent loop is opt-in *by the
  agent itself* for each request, with the deterministic v35 result as
  fallback. This avoids the v29 hard-gate failure mode while preserving the
  opportunity for self-correction when the agent judges it useful.
- **Keep deterministic multi-query expansion** (A4); use the agent's
  `expand_query` only for targeted last-resort term injection.

## Negative anchors (failure-mode references)

- Internal regression review: [`docs/reviews/text_only_v26_v30.md`](../../../reviews/text_only_v26_v30.md)
  — v29 IR-compiler 0% collapse. v36 explicitly does **not** add any
  deterministic gate that can reject a candidate; the only commit point is
  `finalize_answer` called by the agent.
- v35 findings: [`docs/pipelines/text_only/v35/findings.md`](../v35/findings.md)
  — establishes the lean baseline whose result v36 must never regress
  below.

## Open questions for follow-up work

- **Multi-LLM agentic**: separating planner LLM from refine LLM (relates
  to A1 follow-ups Reflexion / Self-Refine).
- **Calibrated soft confidence**: rather than a binary finalize, attach an
  agent-reported confidence and use it for dashboard segmentation.
- **Tool-call telemetry**: which tool yields the best correction rate per
  variable family? Answer requires dashboard runs across multiple PDFs.
