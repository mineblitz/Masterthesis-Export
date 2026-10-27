# text_only_simple_conversion_v31 Findings

Date: 2026-05-18
Pipeline: text_only_simple_conversion_v31
Theme: Counterexample-Aware Constraint Voting (soft validation, no hard collapse gate)

## 1) New method idea

v31 introduces a new post-extraction decision stage inspired by building-code validation and explainable evidence aggregation:

1. Generate a first LLM scalar candidate from retrieved context (same retrieval family as v29 lineage).
2. Build numeric candidate pool directly from selected chunks.
3. Score each candidate by weighted support minus contradiction margin:
   - support terms: chunk evidence strength, clause relevance, requirement/scope clause bonus
   - contradiction terms: negation/exception cues, explicit exception clause penalty
   - soft symbolic checks: unit-family compatibility and inequality cue compatibility (min/max)
4. Select the best candidate by margin with calibrated confidence.
5. Apply bounded fallback when margin is too low:
   - fallback to LLM candidate first
   - then fallback to retrieval modal candidate

This is intentionally soft-scored and avoids brittle all-or-nothing gating.

## 2) Why this addresses observed regressions

From the multi-agent review (`pipeline_review_text_only_v21_to_v30_multi_agent.md`):

- v28 is strongest quality baseline, but explainable validation was limited.
- v29/v30 collapsed to 0.00%, consistent with hard gating brittleness.

v31 design response:

1. Keep retrieval and evidence diversity from the strong lineage.
2. Replace strict reject gates with support-contradiction margin voting.
3. Keep explainability through candidate-level voting logs (`top_candidates`, selected source, fallback reason).
4. Keep graceful fallback behavior so uncertain cases do not collapse to null-only outcomes.

## 3) Files changed

Code:
- app/services/components/counterexample_constraint_voter_v31.py
- app/services/pipelines/text_only_simple_conversion_v31.py
- app/services/experiment_runner.py

Prompt:
- prompts/text_only_v12.txt

Tests:
- tests/test_counterexample_constraint_voter_v31.py
- tests/test_text_only_simple_conversion_v31_flow.py

## 4) Implementation notes

Component `counterexample_constraint_voter_v31` outputs:

- `selected_value`
- `confidence`
- `decision` (`voted_candidate`, `bounded_fallback_llm_low_margin`, etc.)
- `selected_from` (`counterexample_voting`, `llm`, `modal`, `none`)
- `top_candidates` with support/contradiction/margin and source chunk IDs

Pipeline v31 component log focus:

- retrieval quality is observed but not used as a hard reject gate
- voter stage performs final selection
- parser and prompt builder logs remain compatible with existing dashboard conventions

## 5) Literature alignment

Aligned with the repository literature strategy in:

- experiment_analysis_and_improvement_plan.md
- pipeline_inventory_and_paper_mapping.md
- literature_review_auto_ie_construction.md

Relevant mapped ideas combined in v31:

1. Compliance-style clause semantics from v25/v26 lineage.
2. Explainable, evidence-grounded selection instead of strict binary acceptance.
3. Graceful bounded fallback to avoid regression collapse seen in v29/v30.

## 6) Expected behavior change

Compared to v29/v30, v31 should:

1. Reduce catastrophic null/wrong rejection cases caused by over-constrained hard gates.
2. Preserve evidence-grounded correctness by penalizing contradictory/exception signals.
3. Keep extraction alive under ambiguity by selecting a bounded fallback value with explicit decision trace.
