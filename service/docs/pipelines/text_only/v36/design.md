# text_only_simple_conversion_v36 — Design

**Date**: 2026-06-01
**Pipeline**: `text_only_simple_conversion_v36`

## Component graph

```
┌───────────────────────────────────────────────────────────────────────┐
│ STAGE A — DETERMINISTIC PREP (identical to v35)                       │
├───────────────────────────────────────────────────────────────────────┤
│ prompt_loader                                                          │
│ document_source_resolver  (pdf default, marker if prefer_marker)       │
│ structured_document_chunker                                            │
│ hybrid_context_ranker                                                  │
│ multi_query_expander  (v25 wrapper)                                    │
│ compliance_routed_chunk_selector_v36  (v25 prefilter, top_k=5)         │
└───────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────────────┐
│ STAGE B — BASELINE SINGLE-PASS (v35 equivalent, fallback anchor)      │
├───────────────────────────────────────────────────────────────────────┤
│ prompt_builder_v5  → llm_client_baseline (1 LLM call)                  │
│ → parse_extracted_value → normalize_numeric_value_for_payload_v25      │
│ baseline_value: float | None  (persisted in agent state)               │
└───────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────────────┐
│ STAGE C — AGENT LOOP  (agent_controller_v36)                          │
├───────────────────────────────────────────────────────────────────────┤
│ for step in 1..agent_step_budget (default 4):                          │
│   if cumulative_output_tokens >= agent_token_budget: break             │
│   build_agent_prompt → llm call                                        │
│   decision = parse_extracted_payload(response)                         │
│     - tool ∈ {inspect_chunk, expand_query,                             │
│               retrieve_more_context, refine_extraction,                │
│               finalize_answer}                                         │
│     - malformed → step counted, consecutive_malformed++                │
│       if consecutive_malformed >= 3: break                             │
│   execute_tool(decision)                                               │
│     - finalize_answer → set final_value/reason, break                  │
│ if not finalize_called:                                                │
│   final_value = baseline_value  (v35 fallback)                         │
└───────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────────────┐
│ STAGE D — RESULT                                                       │
├───────────────────────────────────────────────────────────────────────┤
│ output_parser (records source=agent_finalize | v35_baseline_fallback)  │
│ result_matcher (evaluate_match)                                        │
└───────────────────────────────────────────────────────────────────────┘
```

## Tool schema (strict JSON, one tool per step)

```jsonc
// inspect_chunk
{"thought":"...","tool":"inspect_chunk","args":{"chunk_id":"<id>"}}

// expand_query
{"thought":"...","tool":"expand_query","args":{"extra_terms":["t1","t2"]}}

// retrieve_more_context
{"thought":"...","tool":"retrieve_more_context","args":{"k":3}}

// refine_extraction
{"thought":"...","tool":"refine_extraction",
 "args":{"focus_chunk_ids":["<id1>","<id2>"],"hint":"..."}}

// finalize_answer
{"thought":"...","tool":"finalize_answer",
 "args":{"value": <number|null>, "reason":"..."}}
```

Any response that does not parse into one of these five shapes is counted
as a malformed step. Three consecutive malformed steps abort the loop and
trigger the v35 baseline fallback.

## Tool semantics

| Tool | Effect on agent state | LLM cost |
|---|---|---|
| `inspect_chunk` | Pure read; returns chunk heading + 600-char preview + score. | 0 extra LLM call |
| `expand_query` | Merges extra terms into `query_variants`, re-runs `select_consistent_diverse_chunks_v25`. Updates `selected_chunks` and `chunk_evidence`. | 0 extra LLM call |
| `retrieve_more_context` | Re-runs selection with `top_k + k`. | 0 extra LLM call |
| `refine_extraction` | Builds a focused `prompt_builder_v5` prompt over given chunk IDs + hint, calls the LLM once, returns the parsed numeric value as observation. | **1 extra LLM call** (counted in `agent_token_budget`) |
| `finalize_answer` | Terminates the loop with `value`. | 0 extra LLM call |

## Budgets

| Parameter | Default | Configurable via | Rationale |
|---|---|---|---|
| `agent_step_budget` | 4 | payload extra `agent_step_budget` | Enough room for inspect→refine→finalize plus one wildcard, while keeping cost bounded. |
| `agent_token_budget` | 6000 cumulative output tokens | payload extra `agent_token_budget` | Hard upper cost guard, independent of step budget. |
| Consecutive malformed cap | 3 | not configurable | Surfaces a model that cannot follow the schema fast, then falls back. |

## Trace structure

Each loop iteration appends a dict to `agent_controller_v36.details["agent_trace"]`:

```jsonc
{
  "step": 1,
  "status": "ok | malformed | finalize | tool_error | llm_error | not_found",
  "tool": "inspect_chunk",            // omitted for malformed
  "args": {"chunk_id": "..."},        // truncated/safe summary
  "observation": "heading=... text=...",
  "thought": "agent's free-form thought"
}
```

`tool_call_counts` is a per-tool histogram plus a `"malformed"` bucket.

## Determinism guarantees

- Stage A is deterministic (no LLM).
- Stage B is one LLM call (identical to v35), parameterized by
  `payload.temperature`.
- Stage C is non-deterministic by design (agent decides) but bounded by the
  step and token budgets and falls back to the deterministic Stage B value
  on any failure (budget exhaustion, malformed cap, LLM error, exception
  in a tool).
- The pipeline therefore **upper-bounds the worst case at the v35 result**.

## What is explicitly **not** reintroduced

| Removed mechanism | First introduced | Why not re-added |
|---|---|---|
| Hard verifier gate | v26 | Can suppress a valid candidate. v36 has no gate; agent commits via `finalize_answer`. |
| Hard consistency gate | v20/v24 | Same; suppresses multi-valued correct answers. |
| Deterministic IR compiler | v29 | 0% collapse on real PDFs. |
| Object-model bridge | v30 | Compounded v29 failure. |
| Constraint voter / scenario ensemble / triple+graph / calibration | v31-v34 | Unproven on production LLM. |
| Blind corrective retry loop | v17–v26 | Replaced by LLM-decided agent loop with hard budget. |
