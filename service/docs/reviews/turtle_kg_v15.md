# Pipeline Review: turtle_kg_keyword_v15 vs Previous Pipelines

Date: 2026-05-18
Data source: `PipelineEvalutator/query_dashboard_backend.py` in snapshot mode
Snapshot: `experiment_dashboard_snapshot.json`

## Why this pipeline was selected
`turtle_kg_keyword_v15` is completed and shows a severe drop versus its direct predecessor lineage. This makes it the highest-priority candidate for failure diagnosis and iteration planning.

## Queries used
- `python PipelineEvalutator/query_dashboard_backend.py --ask completed-pipelines --snapshot-file experiment_dashboard_snapshot.json`
- `python PipelineEvalutator/query_dashboard_backend.py --ask completed-experiments --pipeline turtle_kg_keyword_v15 --snapshot-file experiment_dashboard_snapshot.json`
- `python PipelineEvalutator/query_dashboard_backend.py --ask completed-experiments --pipeline turtle_kg_keyword_v14 --snapshot-file experiment_dashboard_snapshot.json`
- `python PipelineEvalutator/query_dashboard_backend.py --ask completed-experiments --pipeline turtle_kg_twostep_v13 --snapshot-file experiment_dashboard_snapshot.json`
- `python PipelineEvalutator/query_dashboard_backend.py --ask completed-experiments --pipeline turtle_kg_conversion_v12 --snapshot-file experiment_dashboard_snapshot.json`

## Compared pipeline metrics (completed experiments)

| Pipeline | Experiment | Dataset | LLM | Success % | Total Runs | Successful Runs | Avg Tokens/Run |
|---|---|---|---|---:|---:|---:|---:|
| turtle_kg_keyword_v15 | exp_059 | conditionKGExtraction | localai:gemma-3-27b-it | 2.84 | 4500 | 128 | 4082.61 |
| turtle_kg_keyword_v14 | exp_019 | conditionKGExtraction | localai:gemma-3-27b-it | 29.71 | 4500 | 1337 | 15891.23 |
| turtle_kg_twostep_v13 | exp_0018 | conditionKGExtraction | localai:gemma-3-27b-it | 22.56 | 900 | 203 | 23098.63 |
| turtle_kg_conversion_v12 | exp_0017 | conditionKGExtraction | localai:gemma-3-27b-it | 23.78 | 900 | 214 | 21198.39 |

## Key findings
1. **Critical regression from v14 to v15**
- Success dropped from 29.71% to 2.84%.
- Absolute delta: -26.87 percentage points.
- Relative drop: ~90.4%.

2. **Regression happened with same dataset and same LLM**
- Dataset unchanged: `../datasets/conditionKGExtraction`.
- LLM unchanged: `localai:gemma-3-27b-it`.
- This strongly reduces likelihood that the drop is caused by data or model change.

3. **Token usage collapsed while quality collapsed**
- Avg tokens/run dropped from 15,891 (v14) to 4,083 (v15).
- This suggests v15 is likely producing much shorter outputs and/or skipping extraction paths.
- Lower token usage here is not efficiency gain; it correlates with missing output quality.

4. **v15 underperforms all earlier baselines by a wide margin**
- v12: 23.78%
- v13: 22.56%
- v14: 29.71%
- v15: 2.84%

## Cause classification

### Most likely: implementation defect (high confidence)
Evidence:
- Massive one-version regression on unchanged dataset and unchanged LLM.
- Output-length proxy (tokens/run) suggests truncated/bypassed processing.
- The drop is too abrupt for normal algorithmic drift.

### Possible secondary factor: idea mismatch (low-medium confidence)
Evidence:
- v15 introduced additional deterministic normalization/formalization stages.
- If these stages are too strict, valid outputs might be filtered out.
- Still, the abruptness points more to implementation quality than concept invalidity.

### Unlikely primary factor: model/config mismatch (low confidence)
Evidence:
- No model change in this comparison.
- No indication from completed data that parameter sweeps caused this specific collapse.

## What probably failed in v15
1. A gating condition in normalization/formalization path likely rejects most candidates.
2. Serialization/parse path may drop extracted values before final scoring.
3. A fallback branch likely does not trigger when upstream extraction fails.

## Recommended next iterations (v16 proposal set)

1. **v16-A: rollback-control variant**
- Change: start from v14 logic and add only minimal instrumentation (no behavior changes).
- Goal: re-confirm baseline around >=27% success.
- Go/no-go: if <25%, stop and verify experiment parity assumptions.

2. **v16-B: normalization-only variant**
- Change: add v15 normalization stage only, keep v14 extraction+scoring unchanged.
- Goal: avoid >3 pp degradation from v14.
- Go/no-go: if success <26%, disable normalization by default.

3. **v16-C: formalization-only variant**
- Change: add formalization output as non-blocking side artifact (must not affect matching/scoring path).
- Goal: success remains within 2 pp of v14 while producing formalized artifact.
- Go/no-go: if success falls below 27%, keep formalization optional/debug only.

4. **v16-D: strictness sweep**
- Change: run threshold sweep for any deterministic filter introduced in v15.
- Goal: locate threshold region where success recovers toward v14.
- Go/no-go: if no threshold recovers >24%, remove the filter entirely.

5. **v16-E: failure-path telemetry hardening**
- Change: explicit counters for: candidate generated, candidate normalized, candidate discarded, candidate scored.
- Goal: make drop-off stage visible in one run.
- Go/no-go: required before promoting any v16 variant.

## Minimal experiment matrix

| Variant | Dataset | Runs | Target Success % |
|---|---|---:|---:|
| v16-A | conditionKGExtraction | 900 | >=27 |
| v16-B | conditionKGExtraction | 900 | >=26 |
| v16-C | conditionKGExtraction | 900 | >=27 |
| v16-D | conditionKGExtraction | 900 x 3 thresholds | >=24 at least one |

## Decision recommendation
- **Do not continue with v15 as-is.**
- Use v14 as operational fallback.
- Promote only a v16 variant that demonstrates >=26% success on 900-run validation.
