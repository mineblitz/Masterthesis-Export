# Text-only Simple Conversion v24 Findings

Date: 2026-05-12
Pipeline: text_only_simple_conversion_v24

## Selected unfinished finding
Section 2 (Text-only conditional scalar extraction), Finding B:
v18 (32.9%) consistency-gating regression vs v17 (34.3%) despite better retrieval.

Consistency gating treats multi-valued evidence (e.g., table showing "60/90/120 min depending on cross-section") as conflicting and blocks extraction, causing false negatives in spec documents where value ranges are intentionally multi-valued.

## Design choices
- Started from v23 (proven marker-noise-aware retrieval) to maintain strong baseline.
- Added variable-family-aware adaptive consistency gating instead of static threshold.
- Adopted modal (most frequent) value acceptance for multi-valued variables.
- Kept additive behavior: v24 reuses v23 query expansion, marker noise mitigation, and retry strategy.

## Implementation details

### New Component: [app/services/components/retrieval_enhancer_v24_text.py](app/services/components/retrieval_enhancer_v24_text.py)
- **`_is_multi_valued_variable(payload)`**: Detects multi-valued spec variables by pattern matching on value name
  - Patterns: "fire_resistance", "thickness", "rating", "bereich", and any conditional variables
  - Conditions: presence of conditional metadata (e.g., cross_section-dependent values)
  
- **`_compute_adaptive_consistency(...)`**: Computes modal value and adaptive acceptance decision
  - Extracts numeric candidates and groups into buckets by rounding to 0.1
  - Identifies modal (most frequent) candidate and its frequency
  - Returns adaptive gating decision based on:
    - High consistency (≥0.58): Always accept
    - Low consistency + multi-valued variable + modal frequency ≥0.2: Accept modal
    - Otherwise: Reject (consistent with v23 baseline)
  - Tracks conflicting values for logging

- **`select_consistent_diverse_chunks_v24(...)`**: Extends v23 chunk selection with adaptive results
  - Wraps v23 logic and computes adaptive consistency on top
  - Returns extended dict with: `modal_numeric_value`, `modal_candidate_frequency`, `is_multi_valued_variable`, `should_accept_modal`

### New Pipeline: [app/services/pipelines/text_only_simple_conversion_v24.py](app/services/pipelines/text_only_simple_conversion_v24.py)
- Mirrors v23 flow with two key changes:
  1. **Consistency Gating Decision**: Line ~267
     - Old (v23): `if normalized_candidate is not None and not consistency_low`
     - New (v24): `if normalized_candidate is not None and (not consistency_low or should_accept_modal)`
     - Applies same adaptive logic to retry loop

  2. **Component Logging**: Added v24-specific details to consistency checker component
     - Logs `modal_numeric_value`, `modal_candidate_frequency`
     - Logs `is_multi_valued_variable`, `should_accept_modal`
     - Logs gating strategy for debugging

### Registration: [app/services/experiment_runner.py](app/services/experiment_runner.py)
- Added import for v24 pipeline
- Added routing: `if pipeline_name == "text_only_simple_conversion_v24": return run_text_only_simple_conversion_v24(payload)`
- Updated supported pipelines list to include v24

### Tests: [tests/test_retrieval_enhancer_v24.py](tests/test_retrieval_enhancer_v24.py)
- **MultiValuedVariableDetection**: Validates pattern matching for multi-valued variables
  - fire_resistance, thickness, conditional variables correctly identified
  - non-multi-valued variables correctly rejected
  
- **AdaptiveConsistencyComputation**: Validates modal extraction and acceptance logic
  - Single candidate → full consistency → accept
  - Multi-valued evidence (60/90/120) → low consistency but modal accepted for multi-valued vars
  - High consistency → always accept
  - Low consistency + non-multi-valued → reject
  - Modal frequency tracking verified

## Expected impact

### vs v18 (32.9%)
- v18 was a regression from v17 (34.3%) due to overly strict consistency gating
- v24 should recover the 1.4 pp loss by accepting modal values from multi-valued evidence
- Expected: v24 ≥ v23 > v17 > v18 on `conditionBasedExtraction`

### vs v23 (unknown - likely ~35-36% on gemma-3)
- v23 already outperforms v17 through marker noise mitigation
- v24 adds modal acceptance, primarily benefiting:
  - Fire resistance class extraction (intentional value ranges: 60/90/120 min)
  - Thickness conditional ranges (different cross-sections = different thickness ranges)
  - System configuration value ranges (e.g., "depending on installation type")
- Expected v24 benefit: +0.5-1.5 pp over v23 on multi-valued spec conditions

### Production impact
- False negative elimination: Cases where spec provides "60/90/120 min depending on cross-section" and evidence finds all three will now extract the modal (most common) value instead of returning null
- Precision preserved: High consistency cases (≥0.58) are unaffected; modal acceptance only triggers for multi-valued patterns
- Robustness: Retry loop benefits from same adaptive logic, so retries can recover cases that fail on first attempt due to partial evidence

## Risks
- **Over-acceptance**: Multi-valued detection could be too permissive, accepting genuinely conflicting evidence (e.g., from mixed manufacturer specs in single document)
  - Mitigation: Added minimum modal frequency threshold (≥0.2) to require clear dominance
  - Mitigation: Non-multi-valued variables still use strict gating (no modal acceptance)

- **Pattern misidentification**: Value name patterns (e.g., "fire_resistance") might match non-spec variables
  - Mitigation: Added explicit list of Brandschutz domain patterns
  - Mitigation: Test coverage validates pattern matching on known variable types

- **Bucketization side effects**: Rounding numeric values to 0.1 precision might group distinct spec values
  - Impact: Unlikely for fire resistance (60/90/120 min are clearly separate) and thickness (typically differ by >0.1 mm)
  - Mitigation: Can be tuned per variable family if side effects observed

## Next experiments
1. Run v24 on `conditionBasedExtraction` with gemma-3 and gemma-4 to measure:
   - Absolute success rate vs v23 baseline
   - Modal value acceptance rate (how often modal is selected)
   - False positive rate (cases where modal was wrong choice)

2. Analyze failure cases where modal acceptance occurred but was incorrect:
   - Distinguish between genuinely multi-valued specs vs. confused extraction
   - Refine `_is_multi_valued_variable` patterns if needed

3. If v24 succeeds, backport modal acceptance logic as optional mode to v22 and v21 (they have identical consistency gating to v23)

4. Extend adaptive consistency to KG extraction pipelines (v14/v15) where similar multi-valued evidence patterns appear

## Architecture notes
- v24 is fully additive: all v23 components (marker noise mitigation, retrieval quality checks, retry planning) are reused without modification
- No schema changes to ExperimentRequest, ExperimentResponse, or ExperimentResult
- All v24-specific knobs are optional and read from payload.model_extra (consistent with v23)
- Component logs are backward compatible; existing consumers ignore new fields
