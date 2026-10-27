# text_only_simple_conversion_v32 Findings

Date: 2026-05-18
Pipeline: text_only_simple_conversion_v32
Theme: Scenario Ensemble Compliance Simulation (multi-scenario consensus with outlier rejection)

## 1) New method idea

v32 introduces a scenario-based decision method that is structurally different from v31:

1. Build multiple condition-constrained evidence scenarios over the same retrieved chunks.
2. Produce one candidate per scenario (strict requirement, balanced requirement, broad coverage, exception stress test).
3. Aggregate scenario candidates by inter-scenario agreement instead of single-pass candidate scoring.
4. Apply robust outlier rejection (median/MAD style) before final aggregation.
5. Use bounded fallback only when scenario agreement is low or no scenario yields a candidate.

This is not a minor tweak of v31 voting. v31 evaluates one pooled candidate space once. v32 performs explicit scenario simulation and then consensus selection across scenario outputs.

## 2) Why this addresses known issues

From the review context:

- Avoid brittle collapse patterns.
- Improve evidence-grounded reliability under contradictory snippets and exception-heavy text.

v32 response:

1. No hard reject gate: disagreement lowers confidence, but does not force null collapse.
2. Agreement signal is computed across independent scenarios, reducing single-path failure risk.
3. Outlier rejection suppresses exception-driven spikes or isolated noisy values.
4. Final decision includes scenario-level traces and selected scenario IDs for explainability.

## 3) Files changed

Code:
- app/services/components/scenario_ensemble_resolver_v32.py
- app/services/pipelines/text_only_simple_conversion_v32.py
- app/services/experiment_runner.py

Prompt:
- prompts/text_only_v13.txt

Tests:
- tests/test_scenario_ensemble_resolver_v32.py
- tests/test_text_only_simple_conversion_v32_flow.py

## 4) Implementation notes

Component `scenario_ensemble_resolver_v32` outputs:

- `selected_value`
- `confidence`
- `decision` (`scenario_agreement_consensus`, `fallback_llm_low_agreement`, etc.)
- `selected_from` (`scenario_ensemble`, `llm`, `modal`, `none`)
- `agreement_score`
- `outlier_rejections`
- `selected_scenarios`
- `scenario_candidates` (one record per scenario)

Pipeline v32 behavior:

- Reuses strong retrieval lineage (v29-style multi-query + diversity selection)
- Adds a dedicated scenario-ensemble resolver stage for final value selection
- Keeps bounded fallback behavior to avoid catastrophic null-only failure modes

## 5) Literature and plan alignment

Aligned with repository guidance in:

- experiment_analysis_and_improvement_plan.md
- pipeline_inventory_and_paper_mapping.md
- literature_review_auto_ie_construction.md

Most relevant mapping themes for v32:

1. Agentic/multi-path IE for complex regulatory documents (scenario simulation over one-shot extraction).
2. Evidence-grounded robustness through structured aggregation, not hard binary gating.
3. Reliability under long-document contradictions via consensus and outlier controls.

## 6) Why v32 is different from v31

v31:

- One pooled candidate set
- Support-minus-contradiction margin scoring in one pass
- Counterexample-aware weighted voting

v32:

- Multiple explicit scenario runs over condition-constrained evidence subsets
- Cross-scenario consensus as primary selection signal
- Outlier rejection before aggregation
- Confidence primarily derived from inter-scenario agreement and scenario coverage

This creates a genuinely new method family rather than a parameter variant of v31.
