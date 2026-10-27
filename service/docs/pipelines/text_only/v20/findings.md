# text_only_simple_conversion_v20 Findings

## What This Pipeline Does

`text_only_simple_conversion_v20` is a text-only extraction pipeline for numeric values (for example minimum thickness) from approval documents.

In simple terms, it does four things:
1. It builds better search queries from value, conditions, and system metadata to find relevant text more reliably.
2. It selects diverse context chunks and checks if numeric evidence is internally consistent before trusting the extraction.
3. It asks the LLM for the value using the selected context.
4. If confidence/consistency is weak, it retries with adaptive context windows (alternating narrow and broad expansion) before finalizing.

Result: v20 is designed to reduce wrong numeric picks caused by narrow retrieval or conflicting context snippets, while staying backward-compatible with existing request payloads.

## 1) Baseline Analysis: v17

### Strengths
- Uses structured chunking and hybrid ranking before prompting the LLM.
- Includes retrieval quality scoring and a corrective retry path.
- Keeps extraction parser semantics stable through `parse_extracted_value`.
- Preserves request schema flexibility by reading controls from `payload.model_extra`.

### Limitations observed in v17
- Query formulation is narrow (few normalized variants), so lexical drift can reduce recall.
- No explicit evidence-consistency gate before accepting extracted numeric values.
- Retry strategy is single-mode context expansion and can miss better narrow/broad alternation.
- Retrieval selection is top-k from ranker without stronger diversity + consistency balancing.

## 2) Implemented Improvements in v20

### A) Better query coverage and normalization
- Added `app/services/components/retrieval_enhancer_v20.py`.
- New `build_multi_query_variants_v20(...)` expands terms from:
  - canonical search terms
  - value key + readable value form
  - condition type/value + composite condition phrases
  - system and system name
- Added normalization-aware variants for underscores, hyphens, and umlaut/ascii alternatives.

### B) Evidence consistency checks before final extraction
- Added consistency-aware chunk selection via `select_consistent_diverse_chunks(...)`.
- Computes:
  - per-chunk evidence scores
  - average evidence score
  - numeric consistency score from extracted numeric candidates across selected chunks
- In pipeline `text_only_simple_conversion_v20`, parsed extraction is accepted only when consistency gate passes (or consistency is naturally high).
- Added component log `evidence_consistency_checker` with threshold, score, and conflicts.

### C) Adaptive retry strategy (narrow <-> broad)
- Added `choose_adaptive_retry_window(...)`.
- Retry alternates context growth mode:
  - odd retry index: `narrow_retry`
  - even retry index: `broad_retry`
- Logged per retry event: stage, expansion step, quality/evidence/consistency metrics.

### D) Backward compatibility and schema behavior
- No schema change in `ExperimentRequest`.
- New controls read via `payload.model_extra` only.
- Existing parse semantics retained by reusing `parse_extracted_value` (v17/v18 compatible numeric behavior).

## 3) New Optional model_extra Knobs (v20)

- `query_expansion_limit` (int, default `8`)
- `minimum_query_length` (int, default `4`)
- `top_k_chunks` (int, default `3`)
- `diversity_max_per_document` (int, default `2`)
- `diversity_max_per_heading` (int, default `1`)
- `retrieval_confidence_threshold` (float, default `0.58`)
- `evidence_score_threshold` (float, default `0.45`)
- `evidence_consistency_threshold` (float, default `0.62`)
- `enable_corrective_retry` (bool, default `true`)
- `max_corrective_retries` (int, default `2`)
- `narrow_retry_expansion_step` (int, default `1`)
- `broad_retry_multiplier` (int, default `2`)

## 4) Code Changes Delivered

- Added pipeline:
  - `app/services/pipelines/text_only_simple_conversion_v20.py`
- Added v20 component helpers:
  - `app/services/components/retrieval_enhancer_v20.py`
- Registered v19 dispatch:
  - `app/services/experiment_runner.py`
- Added focused API contract tests:
  - `tests/test_api_contract.py`
- Added component tests:
  - `tests/test_retrieval_enhancer_v20.py`

## 5) Validation and Observed Behavior Changes

### Validation run in this session
- Editor diagnostics (`get_errors`) on changed files: no errors.

### Focused tests added
- API tests validate:
  - v19 success path with consistency component and query expansion controls.
  - adaptive retry switching across `narrow_retry` then `broad_retry` stages.
- Component tests validate:
  - query normalization/coverage expansion
  - numeric inconsistency detection
  - alternating retry window policy

### Runtime execution note
- Direct pytest command execution was not available through the active tool interface in this session, so runtime test execution could not be performed here.

## 6) Known Risks / Deferred Items

- Consistency gating is heuristic and may be conservative on documents with mixed but valid numeric contexts.
- Numeric conflict detection currently uses simple bucketed values (rounded to one decimal) and may need domain-specific tolerance refinement.
- Adaptive retry alternation is deterministic; future work could make mode choice data-driven from retrieval diagnostics.
