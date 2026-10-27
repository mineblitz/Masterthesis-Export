# Text-only Simple Conversion v29 Findings

Date: 2026-05-15
Pipeline: text_only_simple_conversion_v29

## Selected literature-driven finding
From item 15 in `experiment_analysis_and_improvement_plan.md`:

- Build a regulation-to-executable IR compiler stage before scalar extraction.
- Main paper anchor: Translating building legislation into a computer-executable format for evaluating compliance of design models (2014).

## Design choices
- Started from v27 to preserve retrieval/ranking/retry and semantic-verifier strengths.
- Added deterministic IR compilation between retrieval selection and scalar acceptance.
- Kept changes additive: no API schema change, no new external service requirement.

## Implementation details

### New component: app/services/components/ir_compiler_v29.py
- Deterministic clause IR compiler with fixed schema:
  - `subject`, `condition`, `operator`, `value`, `unit`, `exception`
- Extracts operator/value/unit from selected clause text using deterministic regex and keyword patterns.
- Provides IR-aware scalar resolver (`select_scalar_using_ir_v29`) that combines LLM candidate and IR candidate with deterministic rules:
  - use IR as fallback when LLM output is null
  - keep LLM when aligned with IR
  - override with IR on mismatch

### New component: app/services/components/retrieval_enhancer_v29_text.py
- Re-exports v27 retrieval/retry/verifier functions under v29 names.
- Keeps v29 self-contained while preserving known-good v27 behavior.

### New pipeline: app/services/pipelines/text_only_simple_conversion_v29.py
- Mirrors v27 flow:
  - structured chunking
  - hybrid ranking
  - multi-query expansion
  - diversity selection
  - corrective retries
  - semantic verifier gate
- Adds `ir_compiler_v29` stage before each extraction attempt (initial + retries).
- Injects compiled IR JSON into prompt context and uses IR-aware scalar decision before semantic verification.
- Logs IR compilation and IR decision metadata in component traces.

### Prompt template update
- Added `prompts/text_only_v10.txt` with explicit IR usage instructions and strict JSON output contract.

### Registration
- Added v29 import/dispatch in `app/services/experiment_runner.py`.

## Expected impact
- Reduces null/missed outputs by allowing deterministic IR fallback when the LLM fails to emit a number.
- Increases traceability through explicit intermediate representation in component logs.
- Keeps v27 retrieval/verifier strengths unchanged while extending execution semantics.

## Risks and caveats
- IR compiler is heuristic and currently regex-based, so unusual phrasings may still require retries.
- Unit/operator detection is optimized for common fire-regulation scalar patterns and should be extended as new variable families are added.

## Validation (focused)
- `python -m pytest tests/test_ir_compiler_v29.py -v`
- `python -m pytest tests/test_text_only_simple_conversion_v29_flow.py -v`
- `python -c "from app.services.experiment_runner import run_experiment; from app.services.pipelines.text_only_simple_conversion_v29 import run_text_only_simple_conversion_v29; print('ok')"`
