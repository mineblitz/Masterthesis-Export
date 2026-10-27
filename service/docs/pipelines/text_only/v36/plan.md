# text_only_simple_conversion_v36 — Plan

**Date**: 2026-06-01
**Pipeline**: `text_only_simple_conversion_v36`
**Lineage**: v35 lean baseline (v9 single-pass + v25 compliance routing + v18 chunker/ranker + v24 numeric normalization) + agentic ReAct controller
**Status**: planning → research → implementation → review → documentation

## Motivation

v35 closed the regression that started at v29 by stripping all hard gates and
multi-pass retries and trusting a single LLM call on v25-routed evidence.
v35 is the **proven lean baseline** but it is **deterministic and rigid**:
every request follows the same pipeline regardless of how clear or muddled
the evidence actually is.

The agentic direction is the natural next step: keep the v35 prep verbatim,
but let the LLM itself decide *when to look more carefully* (inspect a chunk),
*when to broaden the search* (expand query, retrieve more context), *when to
re-extract on a focused window* (refine_extraction), or *when to commit*
(finalize_answer).

## Goals

1. Improve over v35 on requests where the baseline single-pass is wrong but
   the correct answer is reachable with one or two additional targeted steps.
2. **Never regress below v35**: the v35-equivalent single-pass result is
   always computed first and used as deterministic fallback.
3. Stay strictly inside the failure budget of the previous regressions: no
   unbounded retry, no hard gate that can suppress a valid answer, no
   re-introduction of v29 IR compiler / v30 object-model bridge / v31-v34
   voter/ensemble/graph/calibration components.

## Non-goals

- No new retrieval mechanism; reuse v18/v25 chunker/ranker/routing as-is.
- No multimodal extension; text-only family only.
- No external orchestration framework (LangChain, AutoGen, etc.); the loop
  is a small native Python state machine to keep the failure surface low and
  the trace auditable.
- No persistent agent memory across requests.

## Design

### Stage A — Deterministic prep (identical to v35)

1. Prompt template load
2. Document source resolution (PDF default, marker if requested)
3. Structured chunking
4. Hybrid context ranking
5. Multi-query expansion (v24/v25)
6. Compliance-routed diverse chunk selection (v25 prefilter)

### Stage B — Baseline single-pass (v35-equivalent)

7. Build the v5 prompt over the selected chunks.
8. Single LLM call. Parse + normalize numeric value. **Persist as fallback.**

### Stage C — Agentic ReAct loop

9. Run the controller with:
   - **Step budget**: 4 (configurable via `agent_step_budget`)
   - **Token budget**: 6000 cumulative output tokens (configurable via
     `agent_token_budget`)
   - **Consecutive-malformed cap**: 3 (hard-coded)
10. Tools:
    - `inspect_chunk(chunk_id)` — return heading + 600-char preview + score
    - `expand_query(extra_terms)` — extend query anchors, re-run selector
    - `retrieve_more_context(k)` — bump `top_k` and add `k` more chunks
    - `refine_extraction(focus_chunk_ids, hint)` — focused re-extraction
      with a narrow prompt over selected chunks
    - `finalize_answer(value, reason)` — terminate the loop with a value
11. Strict JSON tool-call schema parsed via the existing
    `parse_extracted_payload`. Malformed responses count as failed steps;
    three in a row aborts the loop.

### Stage D — Result selection

12. If `finalize_answer` was called, use that value. Otherwise, fall back to
    the baseline value from stage B.
13. Apply the same `normalize_numeric_value_for_payload_v25` as v35.
14. Match against `expected_value`.

## Risks

- **Token cost**: even with a tight budget, agent prompts include a chunk
  summary table; each step is ~1500-2500 input tokens. Mitigated by the
  4-step cap and the 6000-output-token cap.
- **Agent gets distracted on easy requests**: if the baseline is already
  correct, the agent might waste steps before finalizing. Mitigated by
  prompting it to finalize immediately when baseline is plausible.
- **Tool-call schema drift on smaller LLMs**: gemma-3-27b-it is the
  production target; if it cannot follow the strict schema, malformed-step
  abort kicks in and v35 baseline is returned. This is the same outcome as
  v35 (no regression), only at higher cost.

## Success criteria

- All four flow tests green.
- `tests/test_api_contract.py` still green.
- Dashboard A/B (post-implementation) shows v36 ≥ v35 on
  `conditionBasedExtraction` (success rate); cost increase ≤ 4×.

## Out of scope for v36 (future work)

- Per-variable-family calibration of step/token budget.
- Soft confidence scoring on the finalize value.
- Multi-LLM agent (planner LLM ≠ refine LLM).
