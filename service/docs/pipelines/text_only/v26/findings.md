# Text-only Simple Conversion v26 Findings

Date: 2026-05-12
Pipeline: text_only_simple_conversion_v26

## Selected literature-driven finding
Section 7 in `pipeline_inventory_and_paper_mapping.md`, second finding:

- v5 structured text extraction lineage needs clause typing, semantic pattern support, and a verifier stage beyond prompt-only extraction.
- Relevant anchors: 2012, 2016, and 2021 compliance-IE papers in the El-Gohary lineage and follow-up deep IE work.

## Design choices
- Started from v25 (strongest text-only compliance retrieval baseline already implemented).
- Kept architecture additive: no schema changes, no external services, and no learned model dependency.
- Implemented a deterministic verifier as pragmatic substitute for a learned verifier to keep execution stable and testable offline.

## Implementation details

### New component: app/services/components/retrieval_enhancer_v26_text.py
- Extends v25 retrieval selection with clause typing metadata on selected chunks.
- Clause categories: `requirement`, `scope`, `exception`, `administrative`, `informational`.
- Adds semantic verification helper:
  - Builds semantic anchors from payload value and conditions.
  - Checks numeric support in selected chunks for extracted candidate values.
  - Requires requirement-like evidence support for acceptance.
  - Returns verifier score, support chunk IDs, and acceptance decision.

### New pipeline: app/services/pipelines/text_only_simple_conversion_v26.py
- Mirrors v25 execution flow.
- Uses `select_consistent_diverse_chunks_v26(...)` to include clause typing metadata.
- Adds `semantic_clause_verifier_v26` component after each extraction attempt (initial and retry).
- Applies combined acceptance gate:
  - extracted value present
  - semantic verifier passed and score above threshold
  - consistency gate passed (or adaptive modal acceptance)
- Writes verifier score into `ExperimentResult.confidence`.

### Registration
- Added import and dispatch for `text_only_simple_conversion_v26` in `app/services/experiment_runner.py`.
- Updated supported pipeline list accordingly.

### Tests
- `tests/test_retrieval_enhancer_v26.py` validates:
  - clause typing behavior (`requirement`, `exception`)
  - semantic verifier accepts value with requirement-like evidence support
  - semantic verifier rejects unsupported values
- `tests/test_api_contract.py` adds API-level contract test for `text_only_simple_conversion_v26` with mocked PDF extraction and LLM output.

## Expected impact
- Reduces false positives where numbers are present but not grounded in requirement clauses.
- Improves traceability by exposing explicit clause types and verifier diagnostics in component logs.
- Maintains v25 retrieval improvements while adding a post-extraction quality gate.

## Risks and caveats
- Deterministic verifier is heuristic and may be conservative on unusual document wording.
- Clause typing vocabulary is German-heavy and compliance-domain focused.
- This is a pragmatic substitute for learned verification, not a calibrated classifier.

## Validation
- Focused unit tests: `python -m pytest tests/test_retrieval_enhancer_v26.py -v`
- API-level focused test: `python -m pytest tests/test_api_contract.py -k "v26" -v`
- Import/registration sanity: `python -c "from app.services.experiment_runner import run_experiment; from app.services.pipelines.text_only_simple_conversion_v26 import run_text_only_simple_conversion_v26; print('ok')"`
