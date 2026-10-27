# text_only_simple_conversion_v36 — Findings (post-implementation)

**Date**: 2026-06-01
**Pipeline**: `text_only_simple_conversion_v36`
**Lineage**: v35 lean baseline + agentic ReAct controller
**Status**: Implemented and unit-tested. Runtime A/B benchmark vs v35 pending experiment runner.

## What was built

A two-stage pipeline that wraps an LLM-driven ReAct controller around the
proven v35 deterministic prep:

1. **Stage A (v35 prep)**: prompt load → document source resolution →
   structured chunking → hybrid ranking → v25 multi-query expansion →
   v25 compliance-routed chunk selection. **Identical to v35.**
2. **Stage B (v35 baseline)**: prompt_builder_v5 → single LLM call → parse +
   v24 numeric normalization. The baseline value is persisted as the
   deterministic fallback for the agent loop.
3. **Stage C (agent loop)**: bounded ReAct controller with five tools
   (`inspect_chunk`, `expand_query`, `retrieve_more_context`,
   `refine_extraction`, `finalize_answer`), step budget 4, token budget
   6000 cumulative output tokens, consecutive-malformed cap 3.
4. **Stage D**: if the agent finalized, use that value; otherwise fall back
   to the baseline. Apply the same v24 normalization as v35 and match.

No new retrieval mechanism, no hard gate, no IR compiler, no object-model
bridge, no constraint voter, no scenario ensemble, no triple extraction,
no graph neighborhood, no calibration sandbox.

## Files

- `app/services/pipelines/text_only_simple_conversion_v36.py` (new)
- `app/services/experiment_runner.py` (import + dispatch + supported-list)
- `tests/test_text_only_simple_conversion_v36_flow.py` (new; 4 tests)
- `docs/pipelines/text_only/v36/plan.md` (new)
- `docs/pipelines/text_only/v36/research.md` (new)
- `docs/pipelines/text_only/v36/design.md` (new)
- `docs/pipelines/text_only/v36/findings.md` (this file)
- `docs/pipelines/text_only/summary.md` (entry appended)
- `docs/pipelines/README.md` (Section 1 row appended)
- `docs/README.md` (text-only versions table row appended)

No new prompt template was added; the v36 agent system prompt is embedded
in the pipeline module and the v5 template is reused for baseline + refine
calls.

## Test coverage

| Test | What it asserts |
|---|---|
| `test_v36_agent_finalizes_within_budget` | Happy path: agent finalizes at step 1 with the baseline value; exactly 2 LLM calls (baseline + 1 agent step); trace contains the finalize entry; **forbidden-component invariant** — all v26–v34 gating components absent. |
| `test_v36_budget_exhaustion_falls_back_to_baseline` | Agent never finalizes; loop terminates after `agent_step_budget` steps; v35 baseline value is returned; `output_parser.source == "v35_baseline_fallback"`. |
| `test_v36_malformed_tool_calls_are_handled_without_crash` | Three consecutive malformed responses trigger `termination_reason == "consecutive_malformed_limit"`; no exception is raised; baseline value is returned. |
| `test_v36_agent_can_override_baseline_via_finalize` | Agent inspects a chunk and then finalizes with a value different from the baseline; `output_parser.source == "agent_finalize"`. |

Run with:
```
c:/Users/m.mager/Documents/GitHub/Experiments_Brandschutz/venv/Scripts/python.exe -m pytest tests/test_text_only_simple_conversion_v36_flow.py -v
```

## Design decisions

### Why a v35-equivalent baseline first?

The agent loop is non-deterministic. To guarantee that v36 **cannot regress
below v35**, we compute the v35 result first and use it as the fallback for
every non-finalize termination path (budget exhaustion, malformed cap, LLM
error, tool exception). The worst case for v36 is therefore *equal to v35
plus the cost of the failed agent calls*.

### Why a small fixed toolset?

Per Toolformer (Schick et al., 2023) and ReAct (Yao et al., 2023): a small
well-defined toolset gives the agent enough freedom to self-correct without
risking exploration into components that were already shown to fail in
v29–v34. All five tools map to operations on the already-proven v18/v25
substrate; none of them can re-introduce a hard gate.

### Why the consecutive-malformed cap?

Some LLMs (especially smaller ones) cannot reliably follow a strict JSON
tool-call schema. Without a cap, a model that drifts off-schema would
exhaust the full step budget producing nothing useful. The cap of 3
surfaces this failure fast and falls back to the baseline.

### Why no separate prompt file?

The v36 agent system prompt is short, self-contained, and tightly coupled
to the tool schema enumerated in code. Moving it to `prompts/text_only_v36.txt`
would split the schema across two files and increase the chance of drift.
The v5 prompt template is still reused (via `load_prompt_template(payload.prompt)`)
for the baseline single-pass and for the `refine_extraction` tool's
focused prompt.

## Expected impact

- **Success rate** on `conditionBasedExtraction` (gemma-3-27b-it baseline):
  expected ≥ v35 (`~7-8%`); upper bound depends on how often the agent
  correctly self-corrects vs how often it confidently finalizes a wrong
  baseline value (the only failure mode that can lose v35 ground).
- **Tokens per run**: expected 2–4× v35 in the average case (baseline + 1–2
  agent steps + occasional refine call). Hard-capped by `agent_token_budget`.
- **Variance**: expected higher than v35 by construction (agent
  non-determinism). The trace logs are designed so that an A/B regression
  review can attribute variance to specific tools.

These predictions need confirmation via the dashboard once experiments
run. Use:
```
python PipelineEvalutator/query_dashboard_backend.py --ask completed-experiments \
  --pipeline text_only_simple_conversion_v36 \
  --snapshot-file experiment_dashboard_snapshot.json
```
and the [pipeline-regression-review skill](../../../../.github/skills/pipeline-regression-review/SKILL.md) for the post-run analysis.

## Risks and caveats

- **Agent overrides a correct baseline with a wrong refine**: the agent
  could call `refine_extraction` and trust a focused window that happens to
  contain an exception clause. Mitigated by: (i) the system prompt instructs
  the agent to finalize the baseline when plausible; (ii) the trace
  records both `baseline_value` and `final_value` for dashboard diffing.
- **Cost amplification on schema-drifting LLMs**: caps mitigate but do not
  eliminate. Watch token telemetry on the first dashboard run.
- **Tool surface is fixed**: the agent cannot, for example, call an
  external numeric calculator or invoke the multimodal pipeline. This is
  deliberate (text-only family) but limits the kinds of corrections the
  agent can make.

## A/B comparison plan vs v35

1. Run the same `conditionBasedExtraction` request set against
   `text_only_simple_conversion_v35` and `text_only_simple_conversion_v36`
   on `LOCALAI_GEMMA_3_27B_IT` (production baseline).
2. Compute, per experiment:
   - delta success rate (v36 − v35);
   - delta total tokens;
   - fraction of v36 runs where `output_parser.source == "agent_finalize"`
     vs `"v35_baseline_fallback"`;
   - within agent_finalize: fraction where `final_value == baseline_value`
     (no-op finalize) vs where `final_value != baseline_value`
     (self-correction).
3. Use the pipeline-regression-review skill to classify any per-experiment
   regression as: (a) agent overrode correct baseline,
   (b) agent failed to override wrong baseline, or
   (c) malformed-cap abort + same baseline.

## Follow-up ideas (out of scope for v36)

1. Per-variable-family budget tuning (e.g., higher step budget for
   multi-valued variables).
2. Soft confidence on `finalize_answer` for dashboard segmentation.
3. Multi-LLM agentic variant: planner LLM ≠ refine LLM.
4. Reflexion-style self-critique step before finalize.
