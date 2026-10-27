# text_only_simple_conversion_v35 — Findings (post-implementation)

**Date**: 2026-06-01  
**Pipeline**: `text_only_simple_conversion_v35`  
**Lineage**: v25 (compliance-routing prefilter) + v9 (prompt-simplicity discipline)  
**Status**: Implemented and unit-tested; runtime A/B benchmark pending experiment runner.

## What was built

A single-pass text-only pipeline that:

1. Resolves the document source (PDF full text by default; marker markdown if the payload requests it via `prefer_marker_markdown`).
2. Builds structured chunks and ranks them via the proven hybrid lexical/numeric ranker.
3. Expands the query set via the v24/v25 helpers (EI/REI/F90 synonyms, hours↔minutes etc.).
4. Selects evidence chunks via `select_consistent_diverse_chunks_v25` to preserve the v25 compliance-routing prefilter — but the selection's `evidence_consistency_score`, `should_accept_modal`, and `contradiction_hit_count` are **not** used as gates.
5. Builds one prompt with `prompt_builder_v5` and makes a **single** LLM call.
6. Parses + soft-normalizes the numeric output and matches.

No retry, no verifier gate, no consistency gate, no IR compiler, no object-model bridge, no constraint voter, no scenario ensemble, no triple extraction, no graph neighborhood, no calibration sandbox.

## Files

- `app/services/pipelines/text_only_simple_conversion_v35.py` (new)
- `app/services/experiment_runner.py` (import + dispatch + supported-list line added)
- `tests/test_text_only_simple_conversion_v35_flow.py` (new; 3 tests)

## Test coverage

| Test | What it asserts |
|---|---|
| `test_v35_single_pass_returns_extracted_value_and_components` | End-to-end success path; extracted value matches; **forbidden-component invariant** — verifies absence of all 13 components introduced in v25 consistency, v26, v29-v34 |
| `test_v35_single_pass_no_retry_when_extraction_missing` | LLM returning null does not trigger a second call |
| `test_v35_compliance_routing_metadata_present` | v25 routing metadata is exposed; `gates_disabled` log clearly enumerates what was removed |

Run with:
```
c:/Users/m.mager/Documents/GitHub/Experiments_Brandschutz/venv/Scripts/python.exe -m pytest tests/test_text_only_simple_conversion_v35_flow.py -v
```

## Design decisions vs failed recent versions

| Removed from | Reason |
|---|---|
| v26 semantic verifier | Hard gate; became part of v29 cascade. v35 trusts the routed evidence + LLM. |
| v20/v24 consistency gate | Suppresses valid multi-valued answers; documented in pipelines/README Section 6 finding 4. |
| v17-v26 corrective retry | Per CRAG, retries amplify bias when initial retrieval is fine; here the prefilter is already strong. |
| v29 IR compiler | Catastrophic 0% on real PDFs — documented in `reviews/text_only_v26_v30.md`. |
| v30 object-model bridge | Inherited v29 failure regime. |
| v31 constraint voter, v32 ensemble, v33 graph/triple, v34 calibration | Unproven on production LLM; added complexity without dashboard evidence of recovery. |

## Expected impact

- **Success rate** on `conditionBasedExtraction` (gemma-3-27b-it baseline): expected at or slightly above v25 (~7-8%), substantially above v29-v30 (0%).
- **Tokens per run**: expected lower than v25 (no retry expansion).
- **Variance**: expected lower (no scenario ensemble averaging, no verifier rejection randomness).

These predictions need confirmation via the dashboard once experiments run. Use:
```
python PipelineEvalutator/query_dashboard_backend.py --ask completed-experiments \
  --pipeline text_only_simple_conversion_v35 \
  --snapshot-file experiment_dashboard_snapshot.json
```
and the [pipeline-regression-review skill](../../../../.github/skills/pipeline-regression-review/SKILL.md) for the post-run analysis.

## Risks and caveats

- The compliance-routing prefilter is German-fire-protection-specific (heading/text term lists in `retrieval_enhancer_v25_text.py`). Cross-domain generalization is not claimed.
- Without a verifier, numerically plausible but contextually wrong answers (e.g. picking a number from an exception clause) are returned as-is. The prefilter penalty on administrative chunks reduces this risk but does not eliminate it.
- Single-pass means a single bad LLM response is final. Acceptable trade-off given documented retry-loop failure modes; revisit only if the dashboard shows lower success than v25.

## Follow-up ideas (out of scope for v35)

1. Calibrated **soft** verifier (penalty only, never reject) — recover v26's intent without v29's failure mode.
2. Re-validate the v28 library-backed retrieval stack with fixed token instrumentation.
3. Re-run v17 multi-LLM study on v35 to confirm the LLM ranking still holds.
