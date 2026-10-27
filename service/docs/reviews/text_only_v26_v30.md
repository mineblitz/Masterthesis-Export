# Multi-Agent Review: Last 5 Text-Only Pipelines (v26-v30)

Date: 2026-05-18
Method: Parallel reviews with 5 Pipeline Regression Reviewer agents
Data source priority: live backend on http://localhost:8050, snapshot fallback

## Scope
- text_only_simple_conversion_v26
- text_only_simple_conversion_v27
- text_only_simple_conversion_v28
- text_only_simple_conversion_v29
- text_only_simple_conversion_v30

## Executive Findings
1. v26 vs v25/v24: no regression detected; small upward trend in success and token-normalized yield.
2. v27 vs v26/v25: no hard regression; slight success gain vs v26 but lower token efficiency than v26.
3. v28 vs v27/v26: clear success gain on available dataset, but token telemetry appears broken (reported as zero).
4. v29 vs v28/v27: catastrophic regression signal to 0.00% success across ~1,076 runs on same dataset/LLM.
5. v30 vs v29/v28: no additional drop vs v29 (both 0.00% so far), indicating the failure regime likely already entered in v29.

## Severity-Ordered Review Findings

### Critical
1. v29 hard-failure pattern on conditionBasedExtraction.
- Observed: v29 at 0.00% over 1,076 runs while v28 previously achieved 16.57% on same dataset and LLM.
- Likely class: implementation defect first, method mismatch second.

2. v30 remains in same hard-failure regime as v29.
- Observed: v30 also at 0.00% with near-identical run count and token profile.
- Interpretation: no evidence yet that v30 recovers v29 failure behavior.

### High
1. v28 token telemetry inconsistency.
- Observed: completed run with 1,080 runs but total_tokens=0 and avg_tokens_per_run=0.0.
- Risk: cost/efficiency decisions are unreliable until instrumentation is fixed.

### Medium
1. v27 efficiency tradeoff vs v26.
- Observed: slight success uptick but lower successes per 1M tokens than v26.
- Likely class: method tradeoff, not model/config mismatch.

### Low
1. v26 baseline status.
- Observed: no regression vs v25/v24 on available in-progress evidence.

## Consolidated Evidence Snapshot

Dataset overlap used by agents: ../datasets/conditionBasedExtraction

| Pipeline | Success % | Total Runs | Successful Runs | Done | LLM | Avg Tokens/Run |
|---|---:|---:|---:|---|---|---:|
| text_only_simple_conversion_v24 | 5.86 | 1,075 | 63 | false | localai:gemma-3-27b-it | 9,587.30 |
| text_only_simple_conversion_v25 | 7.37 | 1,072 | 79 | false | localai:gemma-3-27b-it | 9,667.73 |
| text_only_simple_conversion_v26 | 7.91 | 1,074 | 85 | false | localai:gemma-3-27b-it | 9,672.48 |
| text_only_simple_conversion_v27 | 8.02 | 1,072 | 86 | false | localai:gemma-3-27b-it | 10,326.50 |
| text_only_simple_conversion_v28 | 16.57 | 1,080 | 179 | true | localai:gemma-3-27b-it | 0.00 |
| text_only_simple_conversion_v29 | 0.00 | 1,076 | 0 | false | localai:gemma-3-27b-it | 10,774.14 |
| text_only_simple_conversion_v30 | 0.00 | 1,074 | 0 | false | localai:gemma-3-27b-it | 10,932.83 |

Note: v28 token metrics are likely invalid due to telemetry anomaly.

## Diagnosis by Pipeline

### v26
- Classification: no regression event detected.
- Likely residual issue: method ceiling on current dataset/model.

### v27
- Classification: mild method tradeoff (success up slightly, efficiency down vs v26).

### v28
- Classification: method appears improved on success, but measurement defect in token logging.

### v29
- Classification: likely implementation defect (or severe method mismatch) due to abrupt collapse to 0% on unchanged dataset/LLM.

### v30
- Classification: inherits unresolved v29 failure regime; no evidence of recovery yet.

## Recommended Immediate Next Actions
1. Finish v29 and v30 runs to done=true and re-evaluate with completed-only comparisons.
2. Run a matched-slice replay (same 216-sample subset) for v28/v29/v30 to isolate pipeline logic effects.
3. Run an ablation for v29 features (especially IR/gating path) to locate the failure trigger.
4. Repair/verify token instrumentation for v28 lineage so efficiency/cost comparisons are trustworthy.

## Agent Method Notes
Each review agent was instructed to:
- use live backend first via query_dashboard_backend.py and base URL http://localhost:8050,
- compare target pipeline to predecessors,
- classify likely cause as implementation defect, method mismatch, or config/model mismatch,
- propose bounded experiments with measurable acceptance criteria.
