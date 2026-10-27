# Multi-Agent Review: Last 10 Text-Only Pipelines (v21-v30)

Date: 2026-05-18
Method: Parallel Pipeline Regression Reviewer agents (10)
Primary data policy: live backend via http://localhost:8050, snapshot fallback

## Scope
- text_only_simple_conversion_v21
- text_only_simple_conversion_v22
- text_only_simple_conversion_v23
- text_only_simple_conversion_v24
- text_only_simple_conversion_v25
- text_only_simple_conversion_v26
- text_only_simple_conversion_v27
- text_only_simple_conversion_v28
- text_only_simple_conversion_v29
- text_only_simple_conversion_v30

## Executive Summary
1. v21 and v20 comparison is currently blocked by missing/ambiguous text-only records in the available snapshot view.
2. v22 and v23 are in hard-failure mode (0.00% success) on conditionBasedExtraction, indicating major regression relative to earlier working baselines.
3. v24-v27 show gradual recovery (5.86% -> 8.02%) with mostly stable token cost, but absolute quality is still low.
4. v28 is the strongest observed performer (16.57%, done=true) but has broken token telemetry (reported 0 tokens).
5. v29 introduces a catastrophic collapse to 0.00%, and v30 remains in the same collapse regime (no recovery evidence yet).

## Severity-Ordered Findings

### Critical
1. v29 hard regression on conditionBasedExtraction.
- Pattern: 0.00% success across ~1,076 runs with substantial token usage.
- Likely class: implementation defect first, method mismatch second.

2. v30 remains at 0.00% and appears to inherit v29 failure behavior.
- Pattern: near-identical run count and token profile to v29; no quality recovery.

### High
1. v22/v23 hard-failure lineage.
- Pattern: both at 0.00% on conditionBasedExtraction with large run counts and non-trivial token budgets.

2. v28 observability regression (token telemetry invalid).
- Pattern: done=true with 1,080 runs but total_tokens and avg_tokens_per_run reported as zero.

### Medium
1. v24-v27 incremental recovery but low absolute ceiling.
- Pattern: success rises from 5.86% to 8.02%, but still below robust-operational level.

2. v27 efficiency tradeoff vs v26.
- Pattern: small success gain with notably higher avg tokens/run.

### Low
1. v21 baseline uncertainty in this sweep.
- Pattern: data naming/availability ambiguity in artifacts; direct text-only v21 regression call is blocked.

## Consolidated Evidence Snapshot

Primary matched dataset: ../datasets/conditionBasedExtraction

| Pipeline | Success % | Total Runs | Successful Runs | Done | LLM | Avg Tokens/Run |
|---|---:|---:|---:|---|---|---:|
| text_only_simple_conversion_v22 | 0.00 | 1,074 | 0 | false | localai:gemma-3-27b-it | 9,646.84 |
| text_only_simple_conversion_v23 | 0.00 | 1,075 | 0 | false | localai:gemma-3-27b-it | 9,582.95 |
| text_only_simple_conversion_v24 | 5.86 | 1,075 | 63 | false | localai:gemma-3-27b-it | 9,587.30 |
| text_only_simple_conversion_v25 | 7.37 | 1,072 | 79 | false | localai:gemma-3-27b-it | 9,667.73 |
| text_only_simple_conversion_v26 | 7.91 | 1,074 | 85 | false | localai:gemma-3-27b-it | 9,672.48 |
| text_only_simple_conversion_v27 | 8.02 | 1,072 | 86 | false | localai:gemma-3-27b-it | 10,326.50 |
| text_only_simple_conversion_v28 | 16.57 | 1,080 | 179 | true | localai:gemma-3-27b-it | 0.00 |
| text_only_simple_conversion_v29 | 0.00 | 1,076 | 0 | false | localai:gemma-3-27b-it | 10,774.14 |
| text_only_simple_conversion_v30 | 0.00 | 1,074 | 0 | false | localai:gemma-3-27b-it | 10,932.83 |

Notes:
- v28 token fields are likely invalid telemetry and should not be used for efficiency ranking.
- v21/v20 text-only rows were not reliably available in the reviewed snapshot artifacts for direct completed comparison.

## Per-Pipeline Diagnosis

### v21
- Status: insufficient reliable evidence in this sweep artifacts for final regression attribution.
- Risk: name collision with multimodal v21 can mislead comparisons.

### v22
- Status: severe failure regime.
- Likely class: v22-specific method/implementation issue, with model differences as confound in some comparisons.

### v23
- Status: still severe failure regime (no recovery vs v22).
- Likely class: inherited v22-lineage failure behavior.

### v24
- Status: first meaningful recovery from 0% baseline.
- Likely class: method correction works partially, not fully.

### v25
- Status: incremental improvement over v24.
- Likely class: useful method addition (routing prefilter), modest cost increase.

### v26
- Status: incremental non-regressive improvement over v25.
- Likely class: mild method improvement, still underpowered in absolute terms.

### v27
- Status: slight quality gain vs v26 with efficiency penalty.
- Likely class: method tradeoff, not collapse.

### v28
- Status: best observed quality.
- Likely class: strong method gain, but blocked by telemetry defect for cost analysis.

### v29
- Status: catastrophic regression onset.
- Likely class: implementation defect (primary), method mismatch (secondary).

### v30
- Status: no recovery from v29 collapse.
- Likely class: inherited unresolved v29 failure path.

## Recommended Action Plan (Immediate)
1. Prioritize v29/v30 failure isolation before any new text-only variants.
2. Repair v28 token telemetry to restore trusted efficiency/cost evaluation.
3. Completion-lock v24-v27-v29-v30 runs (done=true) for final ranked comparisons.
4. Run matched-slice A/B experiments for v28/v29/v30 under identical subset and settings.

## Bounded Experiments with Acceptance Criteria
1. Matched-slice triage (v28 vs v29 vs v30, same 216 samples)
- Acceptance: if v28 > 10% and v29/v30 < 1%, confirm v29-level regression onset.

2. v29/v30 stage-failure audit (first 100-300 runs)
- Acceptance: identify one dominant failing stage explaining >=70% of failures.

3. Completion parity for v24-v27-v29-v30
- Acceptance: all done=true; re-rank by success and by valid token efficiency metrics.

4. v28 telemetry integrity run
- Acceptance: >=99% runs with non-zero token totals and experiment total_tokens consistent with run-level sums.

## Agent Notes
- All agents were instructed to use live backend first and snapshot fallback.
- Some agents explicitly reported fallback-only evidence in this environment.
- This report consolidates agent conclusions and normalizes them into one decision artifact.
