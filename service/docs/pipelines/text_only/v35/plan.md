# text_only_simple_conversion_v35 — Plan

**Pipeline name**: `text_only_simple_conversion_v35`  
**Theme**: Lean Compliance-Routed Single-Pass Extraction  
**Created**: 2026-06-01  
**Parent baseline**: v25 (compliance-routing prefilter) + v9 (prompt-simplicity discipline)

---

## Motivation

The text-only RAG lineage peaked at **v25/v26** (`~32-40%` on conditionBasedExtraction in the broader runs; `~7-8%` on the gemma-3-27b-it baseline) and every iteration after that either stayed flat or regressed sharply:

| Version | Status | Cause |
|---|---|---|
| v26 | flat–slight gain | semantic verifier gate; foundation still healthy |
| v27 | flat | rule-class router added complexity without lift |
| v28 | apparent gain, broken telemetry | token logging anomaly; hard to compare |
| **v29** | **0.00% across 1,076 runs** | deterministic IR compiler + hard gates |
| **v30** | **0.00% across 1,074 runs** | object-model bridge compounded v29 failures |
| v31, v32 | recovery attempts, TBD | constraint voter / scenario ensemble |
| v33 | TBD | HybridRAG (triple extraction + graph neighborhood) |
| v34 | TBD | calibration profile + semantic validation sandbox |

The clear pattern: **hard gates and speculative multi-pass reasoning suppress correct candidates faster than they suppress wrong ones**, especially on noisy fire-regulation PDFs run against a mid-tier local LLM. Simultaneously, the simplest production pipeline (`v9`) holds a 75.29% success rate on `systemTransferScopeExtraction` purely by trusting the LLM with full text and a clean prompt.

---

## Hypothesis

A pipeline that combines v9's *prompt simplicity discipline* with v25's *compliance-routing prefilter* — and **deliberately omits every gate/retry layer added in v20-v34** — will at least match v25/v26 on numeric extraction while being substantially cheaper and lower-variance.

---

## Design

### Preserved (proven gains)
1. **Structured document chunker** (v18+ baseline)
2. **Hybrid lexical + numeric ranker** (v18+ baseline)
3. **Multi-query expansion** (v24/v25 wrapper with EI/REI/F90 synonyms)
4. **Compliance-routing prefilter** (`select_consistent_diverse_chunks_v25`) — the single largest gain in the family (+8pp in v25 introduction)
5. **Numeric normalization** (v24 wrapper: hours↔minutes, EI/REI synonyms)
6. **Marker-aware document source resolution** (v21 helper; used only when payload requests it)
7. **v9-style flow shape**: build prompt → one LLM call → parse → match

### Removed (correlated with regressions)
- v20/v24 evidence consistency hard gate
- v26 semantic verifier hard gate
- v17–v26 corrective retry loops with adaptive replanning
- v29 deterministic IR compiler
- v30 object-model bridge
- v31 counterexample constraint voter
- v32 scenario ensemble resolver
- v33 triple extraction + graph neighborhood expansion + hybrid aggregator
- v34 calibration profile + exception adjudicator + semantic validation sandbox

### Pipeline shape

```
prompt_loader
   ↓
document_source_resolver  (pdf full text default; marker if requested)
   ↓
structured_document_chunker
   ↓
hybrid_context_ranker
   ↓
multi_query_expander (v25)
   ↓
compliance_routed_chunk_selector_v35   ← uses v25 prefilter, ignores consistency metadata
   ↓
prompt_builder_v5
   ↓
llm_client  ← single call, no retries
   ↓
output_parser  +  v24 numeric normalization
   ↓
result_matcher
```

### Configurable knobs (via `payload.extra`)
- `prefer_marker_markdown` (bool, default `True` per `_resolve_document_source`)
- `query_expansion_limit` (int, default 10)
- `top_k_chunks` (int, default **5**, slightly higher than v25's 3 to compensate for removing retry-based expansion)
- `diversity_max_per_document` (int, default 2)
- `diversity_max_per_heading` (int, default 1)
- `minimum_query_length` (int, default 4)

No verifier threshold, no retrieval threshold, no consistency threshold, no retry knobs.

---

## Acceptance criteria

For an A/B vs v25/v26 on `conditionBasedExtraction` + `localai:gemma-3-27b-it`:
- Success rate **≥ v25** within statistical noise.
- Average tokens per run **< v25** (no retry-based expansion).
- Zero pipeline-internal blocking gates (verified by unit test).

For an A/B vs v34 on the same dataset:
- Success rate **strictly greater** (recover from v29-v34 regression regime).

---

## Risks and caveats

- Trusts the LLM to handle exception/scope clauses without a deterministic verifier. Mitigation: compliance-routing prefilter already down-weights non-requirement chunks before they reach the LLM, so the prompt receives requirement-focused evidence.
- Loses the consistency-gate safety net for multi-valued variables. Mitigation: v25 modal-value metadata is no longer used; we accept that some recall comes back at the cost of slightly more numeric noise. Numeric normalization stays in place.
- No corrective retry means a single bad retrieval is final. Mitigation: top-K raised from 3 to 5; multi-query expansion still active.

---

## Files

- New: [`app/services/pipelines/text_only_simple_conversion_v35.py`](../../../../app/services/pipelines/text_only_simple_conversion_v35.py)
- Modified: [`app/services/experiment_runner.py`](../../../../app/services/experiment_runner.py)
- New: [`tests/test_text_only_simple_conversion_v35_flow.py`](../../../../tests/test_text_only_simple_conversion_v35_flow.py)
- Docs: [plan.md](plan.md) (this), [research.md](research.md), [findings.md](findings.md)
