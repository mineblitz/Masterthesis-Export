"""Text-only conversion pipeline v36: agentic ReAct-style extractor.

Design intent
-------------
v36 is the first **agentic** member of the text-only family. It builds directly
on the v35 lean baseline (v9 simplicity + v25 compliance-routing prefilter +
v18 chunker/ranker + v24 numeric normalization) and adds an LLM-driven
controller that can call a small, deterministic toolset before committing to a
final answer.

Key properties:
  * Reuses v35's prep (chunking, ranking, query expansion, compliance routing)
    verbatim. No re-implementation of those proven components.
  * The agent operates in a **ReAct-style plan-act-observe loop** with hard
    ceilings of 2 controller steps and 750 cumulative controller output tokens.
    Lower request values are honored; larger values are capped. The extra
    refinement LLM call is disabled.
  * A v35-equivalent single-pass extraction is run **first** and persisted as
    the deterministic fallback. If the agent fails to finalize within budget,
    or every step is malformed, we return the baseline value. Finalized agent
    revisions can still improve or harm the baseline and are reported separately.
  * Malformed tool calls are counted as failed steps (logged and surfaced to
    the agent as an observation), not crashes. The hard step ceiling bounds
    malformed retries as well.
  * The four active tools are:
      - inspect_chunk(chunk_id)
      - expand_query(extra_terms)
      - retrieve_more_context(k)
      - finalize_answer(value, reason)
    The additional refine_extraction generation call is disabled.
  * Structured trace logged under the `agent_controller_v36` component for
    later A/B analysis vs v35.

Failure modes explicitly avoided:
  * No unbounded loop (hard step + token + consecutive-malformed caps).
  * No hard gates that can suppress a valid candidate (baseline is always
    available as a fallback).
  * No re-introduction of v29 IR compiler, v30 object-model bridge, v31-v34
    voter/ensemble/graph/calibration components.
"""

from __future__ import annotations

import math
from pathlib import Path
import time
from typing import Any

from app.models import ComponentLog, ExperimentRequest, ExperimentResponse, ExperimentResult, LLMTextResponse
from app.services.components.dataset_input_adapter import (
    append_question_to_prompt,
    resolve_dataset_search_terms,
    resolve_document_input,
)
from app.services.components.hybrid_context_ranker import RankedChunk, rank_document_chunks
from app.services.components.llm_client_component import generate_text_component
from app.services.components.output_parser_component import (
    parse_extracted_answer,
    parse_extracted_payload,
    parse_extracted_value,
)
from app.services.components.prompt_builder_v5 import (
    build_conditions_block,
    build_conditions_block_de,
    build_prompt_v5,
)
from app.services.components.result_matcher_component import evaluate_match
from app.services.components.retrieval_enhancer_v25_text import (
    build_multi_query_variants_v25,
    normalize_numeric_value_for_payload_v25,
    select_consistent_diverse_chunks_v25,
)
from app.services.components.structured_document_chunker import build_structured_document_chunks
from app.services.pdf_text_extractor import extract_text_from_pdfs
from app.services.pipelines.text_only_simple_conversion_v21 import (
    _extract_text_from_marker_markdown_v21,
    _finish_component,
    _now_iso,
    _render_selected_context,
    _resolve_document_source,
    _resolve_int_extra,
    _start_component,
)
from app.services.prompt_loader import load_prompt_template


# ---------------------------------------------------------------------------
# Agent constants
# ---------------------------------------------------------------------------

_DEFAULT_STEP_BUDGET = 2
_DEFAULT_TOKEN_BUDGET = 750
_MAX_STEP_BUDGET = 2
_MAX_TOKEN_BUDGET = 750
_MAX_REFINE_EXTRACTION_CALLS = 0
_MAX_CONSECUTIVE_MALFORMED = 3

_TOOL_NAMES = (
    "inspect_chunk",
    "expand_query",
    "retrieve_more_context",
    "refine_extraction",
    "finalize_answer",
)


_AGENT_SYSTEM_PROMPT = """Du bist ein ReAct-Agent fuer die Extraktion eines Zielwerts
aus deutschen Brandschutz-Zulassungsdokumenten.

Du hast eine Baseline-Antwort eines einzelnen LLM-Durchlaufs und einen
deterministisch vorgefilterten Kontext. Du darfst pro Schritt **genau ein
Werkzeug** aufrufen, um die Antwort zu verbessern, oder die Baseline mit
finalize_answer bestaetigen.

Verfuegbare Werkzeuge (strict JSON, ein Werkzeug pro Schritt):

1. inspect_chunk    {"tool":"inspect_chunk","args":{"chunk_id":"..."}}
2. expand_query     {"tool":"expand_query","args":{"extra_terms":["...","..."]}}
3. retrieve_more_context {"tool":"retrieve_more_context","args":{"k":5}}
4. refine_extraction is disabled; do not call it.
5. finalize_answer  {"tool":"finalize_answer","args":{"value": <number|null>, "reason":"kurze Begruendung"}}

Regeln:
- Antworte **ausschliesslich** mit einem einzigen JSON-Objekt mit den Feldern
  "thought" (kurze Begruendung deines Schritts), "tool" und "args".
- Keine Markdown-Codefences, keinen Text vor oder nach dem JSON.
- Wenn die Baseline plausibel ist und nichts zu pruefen bleibt: rufe direkt
  finalize_answer mit dem Baseline-Wert auf.
- Wenn du unsicher bist: nutze hoechstens ein Kontextwerkzeug und finalize im
  naechsten Schritt.
- refine_extraction ist deaktiviert, um eine zusaetzliche LLM-Neuextraktion
  zu vermeiden.
- Bei Erreichen des Step-Budgets wird die Baseline verwendet.
"""

_AGENT_VERBATIM_SYSTEM_PROMPT = """You are a source-grounded answer review agent.

You receive a baseline answer and retrieved document context. Use at most one
tool per step, then either finalize the answer or use the baseline fallback.
The question and source document may be in English or German.

Available tools (strict JSON, one tool per step):
1. inspect_chunk {"tool":"inspect_chunk","args":{"chunk_id":"..."}}
2. expand_query {"tool":"expand_query","args":{"extra_terms":["...","..."]}}
3. retrieve_more_context {"tool":"retrieve_more_context","args":{"k":5}}
4. finalize_answer {"tool":"finalize_answer","args":{"value":"complete answer text or null","reason":"brief explanation","evidence":"short exact source quotation"}}

Return exactly one JSON object with "thought", "tool", and "args".
For a final answer, preserve the complete answer as stated in the source:
include units, percentage signs, both bounds of a range, and class or category
prefixes such as EI. Do not convert ratios, omit units, round, or return only
the first number in a range. Use null only when the supplied evidence does not
support an answer. The final value must be a JSON string or null, never a
number. Do not treat the model's prior answer as evidence; check the retrieved
source context before changing it. refine_extraction is disabled in this
version; do not call it.
"""


def _normalize_numeric_answer(
    value: float | str | None,
    payload: ExperimentRequest,
    *,
    source_text: str | None = None,
) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("Numeric answer mode produced a non-numeric value")
    return normalize_numeric_value_for_payload_v25(
        value,
        payload,
        source_text=source_text,
    )


def _parse_finalized_verbatim_answer(value: Any) -> str | None:
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return None


# ---------------------------------------------------------------------------
# Pipeline entry point
# ---------------------------------------------------------------------------


def run_text_only_simple_conversion_v36(payload: ExperimentRequest) -> ExperimentResponse:
    pipeline_clock_start = time.perf_counter()
    pipeline_started_at = _now_iso()
    components: list[ComponentLog] = []

    # 1) Prompt template (re-used for baseline + refine_extraction calls).
    prompt_component = _start_component("prompt_loader")
    template = load_prompt_template(payload.prompt)
    components.append(
        _finish_component(prompt_component, status="success", details={"prompt_name": payload.prompt})
    )

    # 2) Document source resolution (pdf default, marker if requested).
    source_component = _start_component("document_source_resolver")
    preferred_source = _resolve_document_source(payload)
    try:
        if (payload.model_extra or {}).get("input_source") == "dataset_text":
            document_input = resolve_document_input(payload, Path("."))
            docs_text = document_input.text
            used_documents = document_input.used_documents
            actual_source = "dataset_text"
            source_details = {
                **document_input.details,
                "preferred_source": preferred_source,
            }
        elif preferred_source == "marker":
            docs_text, used_documents = _extract_text_from_marker_markdown_v21(
                payload.approval_links, Path("."), payload
            )
            actual_source = "marker_markdown_cleaned"
            source_details = {}
        else:
            docs_text, used_documents = extract_text_from_pdfs(payload.approval_links, Path("."))
            actual_source = "pdf_full_text"
            source_details = {}
        components.append(
            _finish_component(
                source_component,
                status="success",
                details={
                    "preferred_source": preferred_source,
                    "actual_source": actual_source,
                    "document_count": len(used_documents),
                    **source_details,
                },
            )
        )
    except Exception as exc:
        if preferred_source == "marker":
            try:
                docs_text, used_documents = extract_text_from_pdfs(payload.approval_links, Path("."))
                components.append(
                    _finish_component(
                        source_component,
                        status="success",
                        details={
                            "preferred_source": preferred_source,
                            "actual_source": "pdf_full_text_fallback",
                            "document_count": len(used_documents),
                            "fallback_reason": str(exc),
                        },
                    )
                )
            except Exception as nested_exc:
                components.append(_finish_component(source_component, status="error", error=str(nested_exc)))
                raise RuntimeError(f"Document source resolution failed: {nested_exc}") from nested_exc
        else:
            components.append(_finish_component(source_component, status="error", error=str(exc)))
            raise RuntimeError(f"Document source resolution failed: {exc}") from exc

    # 3) Chunk + rank (v18 lineage).
    chunk_component = _start_component("structured_document_chunker")
    chunks = build_structured_document_chunks(docs_text)
    components.append(
        _finish_component(
            chunk_component,
            status="success",
            details={
                "chunk_count": len(chunks),
                "document_count": len(used_documents),
                "source_text_chars": len(docs_text),
                "source_text_truncated": False,
            },
        )
    )

    ranker_component = _start_component("hybrid_context_ranker")
    ranked_chunks, search_terms = rank_document_chunks(
        chunks=chunks,
        payload=payload,
        search_terms=resolve_dataset_search_terms(payload),
    )
    components.append(
        _finish_component(
            ranker_component,
            status="success",
            details={"candidate_count": len(ranked_chunks), "search_terms": search_terms},
        )
    )

    # 4) Query expansion (v25/v24 family).
    query_component = _start_component("multi_query_expander")
    query_limit = _resolve_int_extra(payload, "query_expansion_limit", default=10, minimum=2)
    query_variants = build_multi_query_variants_v25(
        payload=payload,
        base_search_terms=search_terms,
        query_limit=query_limit,
    )
    components.append(
        _finish_component(
            query_component,
            status="success",
            details={"query_count": len(query_variants), "queries": query_variants},
        )
    )

    # 5) Compliance-routed diverse chunk selection (v25 prefilter, same as v35).
    top_k = _resolve_int_extra(payload, "top_k_chunks", default=5, minimum=1)
    max_per_document = _resolve_int_extra(payload, "diversity_max_per_document", default=2, minimum=1)
    max_per_heading = _resolve_int_extra(payload, "diversity_max_per_heading", default=1, minimum=1)
    minimum_query_length = _resolve_int_extra(payload, "minimum_query_length", default=4, minimum=2)

    diversity_component = _start_component("compliance_routed_chunk_selector_v36")
    selection = select_consistent_diverse_chunks_v25(
        ranked_chunks=ranked_chunks,
        top_k=top_k,
        max_per_document=max_per_document,
        max_per_heading=max_per_heading,
        payload=payload,
        query_variants=query_variants,
        minimum_query_length=minimum_query_length,
        rerank_strategy="balanced",
    )
    selected_chunks: list[RankedChunk] = selection["selected_chunks"]
    chunk_evidence: dict[str, float] = selection["chunk_evidence"]
    components.append(
        _finish_component(
            diversity_component,
            status="success",
            details={
                "top_k": top_k,
                "diversity_max_per_document": max_per_document,
                "diversity_max_per_heading": max_per_heading,
                "selected_chunk_ids": [item.chunk.chunk_id for item in selected_chunks],
                "average_evidence_score": selection["average_evidence_score"],
                "route_focus": selection["route_focus"],
                "route_anchor_count": selection["route_anchor_count"],
                "route_boosted_chunk_ids": selection["route_boosted_chunk_ids"],
                "route_penalized_chunk_ids": selection["route_penalized_chunk_ids"],
                "gates_disabled": ["consistency_gate", "verifier_gate", "corrective_retry"],
                "design_intent": "v35_prep_for_agent_v36",
            },
        )
    )

    # 6) Baseline single-pass extraction (v35 equivalent). Always available
    #    as deterministic fallback for the agent loop.
    conditions_text_raw, conditions_count = build_conditions_block(payload.conditions)
    conditions_text_de, _ = build_conditions_block_de(payload.conditions)
    selected_context = _render_selected_context(selected_chunks, chunk_evidence)
    baseline_prompt = append_question_to_prompt(
        build_prompt_v5(
            template=template,
            system=payload.system,
            system_name=payload.system_name,
            value=payload.value,
            conditions=payload.conditions,
            docs_text=selected_context,
        ),
        payload,
    )

    prompt_builder_component = _start_component("prompt_builder_v5")
    components.append(
        _finish_component(
            prompt_builder_component,
            status="success",
            details={
                "prompt_length": len(baseline_prompt),
                "selected_context_chars": len(selected_context),
                "conditions_count": conditions_count,
                "has_conditions": conditions_count > 0,
                "conditions_preview_raw": conditions_text_raw[:250],
                "conditions_preview_de": conditions_text_de[:250],
            },
        )
    )

    baseline_component = _start_component("llm_client_baseline")
    baseline_clock_start = time.perf_counter()
    try:
        baseline_response = generate_text_component(
            prompt=baseline_prompt,
            llm=payload.llm,
            temperature=payload.temperature,
        )
        components.append(
            _finish_component(
                baseline_component,
                status="success",
                details={
                    "model": baseline_response.model,
                    "design_intent": "v35_equivalent_baseline_for_agent_fallback",
                    "baseline_runtime_ms": round(
                        (time.perf_counter() - baseline_clock_start) * 1000,
                        3,
                    ),
                },
                input_tokens=baseline_response.input_tokens,
                output_tokens=baseline_response.output_tokens,
            )
        )
    except Exception as exc:
        components.append(_finish_component(baseline_component, status="error", error=str(exc)))
        raise RuntimeError(f"Baseline LLM generation failed: {exc}") from exc

    baseline_output, _ = parse_extracted_payload(baseline_response.text)
    baseline_supporting_evidence = baseline_output.get("supporting_evidence")
    baseline_exception_evidence = baseline_output.get("exception_evidence")
    preserve_text = payload.answer_output_mode == "verbatim"
    if preserve_text:
        baseline_value = parse_extracted_answer(
            baseline_response.text,
            preserve_text=True,
        )
    else:
        baseline_raw_value = parse_extracted_value(baseline_response.text)
        baseline_value = _normalize_numeric_answer(
            baseline_raw_value,
            payload,
            source_text=baseline_response.text,
        )

    # 7) Agent loop (ReAct-style).
    requested_step_budget = _resolve_int_extra(
        payload,
        "agent_step_budget",
        default=_DEFAULT_STEP_BUDGET,
        minimum=1,
    )
    step_budget = min(requested_step_budget, _MAX_STEP_BUDGET)
    requested_token_budget = _resolve_int_extra(
        payload, "agent_token_budget", default=_DEFAULT_TOKEN_BUDGET, minimum=256
    )
    token_budget = min(requested_token_budget, _MAX_TOKEN_BUDGET)

    agent_component = _start_component("agent_controller_v36")
    agent_state = _AgentState(
        payload=payload,
        template=template,
        ranked_chunks=ranked_chunks,
        selected_chunks=list(selected_chunks),
        chunk_evidence=dict(chunk_evidence),
        query_variants=list(query_variants),
        baseline_value=baseline_value,
        baseline_text=baseline_response.text,
        preserve_text_output=preserve_text,
        step_budget=step_budget,
        token_budget=token_budget,
    )

    agent_clock_start = time.perf_counter()
    final_value, final_reason, agent_total_tokens_in, agent_total_tokens_out = _run_agent_loop(agent_state)
    agent_runtime_ms = round((time.perf_counter() - agent_clock_start) * 1000, 3)

    components.append(
        _finish_component(
            agent_component,
            status="success",
            details={
                "step_budget": step_budget,
                "requested_step_budget": requested_step_budget,
                "step_budget_hard_limit": _MAX_STEP_BUDGET,
                "token_budget": token_budget,
                "requested_token_budget": requested_token_budget,
                "token_budget_hard_limit": _MAX_TOKEN_BUDGET,
                "steps_taken": len(agent_state.trace),
                "tool_call_counts": agent_state.tool_call_counts,
                "agent_trace": agent_state.trace,
                "finalize_called": agent_state.finalize_called,
                "fallback_used": not agent_state.finalize_called,
                "termination_reason": agent_state.termination_reason,
                "baseline_value": baseline_value,
                "final_value": final_value,
                "final_reason": final_reason,
                "baseline_supporting_evidence": (
                    baseline_supporting_evidence[:500]
                    if isinstance(baseline_supporting_evidence, str)
                    else None
                ),
                "baseline_exception_evidence": (
                    baseline_exception_evidence[:500]
                    if isinstance(baseline_exception_evidence, str)
                    else None
                ),
                "agent_runtime_ms": agent_runtime_ms,
                "failed_tool_calls": sum(
                    entry.get("tool") not in (None, "finalize_answer")
                    and entry.get("status") != "ok"
                    for entry in agent_state.trace
                ),
                "agent_llm_errors": sum(
                    entry.get("status") == "llm_error" and entry.get("tool") is None
                    for entry in agent_state.trace
                ),
                "malformed_tool_calls": agent_state.tool_call_counts["malformed"],
                "refine_extraction_calls": agent_state.refine_extraction_calls,
                "blocked_refine_extraction_calls": max(
                    0,
                    agent_state.tool_call_counts["refine_extraction"]
                    - agent_state.refine_extraction_calls,
                ),
                "refine_extraction_call_hard_limit": _MAX_REFINE_EXTRACTION_CALLS,
                "output_token_budget_overshoot": max(
                    0,
                    agent_state.cumulative_output_tokens - token_budget,
                ),
            },
            input_tokens=agent_total_tokens_in,
            output_tokens=agent_total_tokens_out,
        )
    )

    # 8) Parse + soft numeric normalization on whatever the agent returned.
    parser_component = _start_component("output_parser")
    if preserve_text:
        extracted_value = final_value
    else:
        extracted_value = _normalize_numeric_answer(
            final_value,
            payload,
            source_text=final_reason or baseline_response.text,
        )
    components.append(
        _finish_component(
            parser_component,
            status="success",
            details={
                "raw_candidate": final_value,
                "normalized_value": extracted_value,
                "normalization": (
                    "verbatim_text" if preserve_text else "v24_unit_and_synonym_normalization"
                ),
                "source": "agent_finalize" if agent_state.finalize_called else "v35_baseline_fallback",
            },
        )
    )

    # 9) Match.
    normalized_expected = payload.expected_value
    if not preserve_text and isinstance(payload.expected_value, (int, float)):
        normalized_expected = _normalize_numeric_answer(payload.expected_value, payload)
    is_match = evaluate_match(extracted_value, normalized_expected)
    normalized_baseline = (
        baseline_value
        if preserve_text
        else _normalize_numeric_answer(baseline_value, payload)
    )
    baseline_is_match = evaluate_match(normalized_baseline, normalized_expected)
    values_equal = (
        extracted_value is None and normalized_baseline is None
    ) or (
        isinstance(extracted_value, (int, float))
        and isinstance(normalized_baseline, (int, float))
        and math.isclose(float(extracted_value), float(normalized_baseline), rel_tol=0.0, abs_tol=1e-9)
    ) or (
        isinstance(extracted_value, str)
        and isinstance(normalized_baseline, str)
        and extracted_value.strip().casefold() == normalized_baseline.strip().casefold()
    )
    if not agent_state.finalize_called:
        outcome_category = "unchanged_fallback"
    elif is_match and not baseline_is_match:
        outcome_category = "finalized_improvement"
    elif baseline_is_match and not is_match:
        outcome_category = "harmful_finalized_revision"
    elif values_equal:
        outcome_category = "finalized_unchanged"
    else:
        outcome_category = "finalized_changed_same_match_status"

    if agent_component.details is not None:
        agent_component.details.update(
            {
                "baseline_is_match": baseline_is_match,
                "final_is_match": is_match,
                "outcome_category": outcome_category,
                "pipeline_runtime_ms": round(
                    (time.perf_counter() - pipeline_clock_start) * 1000,
                    3,
                ),
            }
        )

    total_input_tokens = baseline_response.input_tokens + agent_total_tokens_in
    total_output_tokens = baseline_response.output_tokens + agent_total_tokens_out

    result = ExperimentResult(
        expected_value=payload.expected_value,
        extracted_value=extracted_value,
        is_match=is_match,
        full_prompt=baseline_prompt,
        full_output=final_reason or baseline_response.text,
        input_tokens=total_input_tokens,
        output_tokens=total_output_tokens,
        temperature=payload.temperature,
        experiment_id=payload.experiment_id,
        pipeline_started_at=pipeline_started_at,
        pipeline_finished_at=_now_iso(),
        experiment_description=payload.experiment_description,
        used_documents=used_documents,
        system=payload.system,
        extracted_value_type=payload.value,
        min_or_max=payload.min_or_max,
        used_llm=payload.llm.value,
        components=components,
    )
    return ExperimentResponse(
        status="success",
        experiment_id=payload.experiment_id,
        pipeline=payload.pipeline,
        result=result,
    )


# ---------------------------------------------------------------------------
# Agent state and loop
# ---------------------------------------------------------------------------


class _AgentState:
    """Mutable per-run state for the agent controller."""

    def __init__(
        self,
        *,
        payload: ExperimentRequest,
        template: str,
        ranked_chunks: list[RankedChunk],
        selected_chunks: list[RankedChunk],
        chunk_evidence: dict[str, float],
        query_variants: list[str],
        baseline_value: float | str | None,
        baseline_text: str,
        preserve_text_output: bool,
        step_budget: int,
        token_budget: int,
    ) -> None:
        self.payload = payload
        self.template = template
        self.ranked_chunks = ranked_chunks
        self.selected_chunks = selected_chunks
        self.chunk_evidence = chunk_evidence
        self.query_variants = list(query_variants)
        self.baseline_value = baseline_value
        self.baseline_text = baseline_text
        self.preserve_text_output = preserve_text_output
        self.step_budget = step_budget
        self.token_budget = token_budget

        self.trace: list[dict[str, Any]] = []
        self.tool_call_counts: dict[str, int] = {name: 0 for name in _TOOL_NAMES}
        self.tool_call_counts["malformed"] = 0
        self.finalize_called = False
        self.termination_reason: str = ""
        self.cumulative_output_tokens = 0
        self.cumulative_input_tokens = 0
        self.refine_extraction_calls = 0


def _run_agent_loop(
    state: _AgentState,
) -> tuple[float | str | None, str, int, int]:
    """Execute the ReAct loop. Returns (value, reason, total_in_tokens, total_out_tokens)."""
    final_value: float | str | None = state.baseline_value
    final_reason: str = "baseline_v35_fallback"
    consecutive_malformed = 0

    for step_index in range(1, state.step_budget + 1):
        if state.cumulative_output_tokens >= state.token_budget:
            state.termination_reason = "token_budget_exhausted"
            break

        remaining_output_tokens = state.token_budget - state.cumulative_output_tokens
        agent_prompt = _build_agent_prompt(state, step_index)
        try:
            response = generate_text_component(
                prompt=agent_prompt,
                llm=state.payload.llm,
                temperature=state.payload.temperature,
                max_tokens=remaining_output_tokens,
            )
        except Exception as exc:
            state.trace.append(
                {
                    "step": step_index,
                    "status": "llm_error",
                    "error": str(exc),
                }
            )
            state.termination_reason = "llm_error"
            break

        state.cumulative_input_tokens += response.input_tokens
        state.cumulative_output_tokens += response.output_tokens

        decision = _parse_agent_decision(response.text)
        if decision is None:
            state.tool_call_counts["malformed"] += 1
            consecutive_malformed += 1
            state.trace.append(
                {
                    "step": step_index,
                    "status": "malformed",
                    "raw": response.text[:300],
                }
            )
            if consecutive_malformed >= _MAX_CONSECUTIVE_MALFORMED:
                state.termination_reason = "consecutive_malformed_limit"
                break
            continue

        consecutive_malformed = 0
        tool_name = decision["tool"]
        tool_args = decision.get("args", {}) or {}
        state.tool_call_counts[tool_name] = state.tool_call_counts.get(tool_name, 0) + 1

        if tool_name == "finalize_answer":
            value = tool_args.get("value")
            if state.preserve_text_output:
                final_value = _parse_finalized_verbatim_answer(value)
            else:
                if isinstance(value, str):
                    try:
                        value = float(value.replace(",", "."))
                    except ValueError:
                        value = None
                if isinstance(value, (int, float)):
                    final_value = float(value)
                elif value is None:
                    final_value = None
            reason = str(tool_args.get("reason", "")).strip() or "agent_finalize"
            evidence = str(tool_args.get("evidence", "")).strip()
            final_reason = reason
            state.finalize_called = True
            state.termination_reason = "finalize"
            state.trace.append(
                {
                    "step": step_index,
                    "status": "finalize",
                    "tool": tool_name,
                    "value": final_value,
                    "reason": reason[:200],
                    "evidence": evidence[:400],
                    "thought": str(decision.get("thought", ""))[:200],
                }
            )
            break

        observation = _execute_tool(state, tool_name, tool_args)
        state.trace.append(
            {
                "step": step_index,
                "status": observation.get("status", "ok"),
                "tool": tool_name,
                "args": _safe_args_summary(tool_args),
                "observation": observation.get("summary", ""),
                "thought": str(decision.get("thought", ""))[:200],
            }
        )
    else:
        # Loop completed without finalize.
        state.termination_reason = state.termination_reason or "step_budget_exhausted"

    return (
        final_value,
        final_reason,
        state.cumulative_input_tokens,
        state.cumulative_output_tokens,
    )


# ---------------------------------------------------------------------------
# Prompt assembly + decision parsing
# ---------------------------------------------------------------------------


def _build_agent_prompt(state: _AgentState, step_index: int) -> str:
    payload = state.payload
    selected_summary_lines: list[str] = []
    for item in state.selected_chunks[:8]:
        heading = item.chunk.heading or "(kein Heading)"
        evidence = state.chunk_evidence.get(item.chunk.chunk_id, 0.0)
        preview = item.chunk.text.replace("\n", " ")[:160]
        selected_summary_lines.append(
            f"- {item.chunk.chunk_id} | heading='{heading[:60]}' | score={item.score:.2f} "
            f"| evidence={evidence:.2f} | preview='{preview}'"
        )

    trace_lines: list[str] = []
    for entry in state.trace[-6:]:
        trace_lines.append(
            f"step {entry['step']}: tool={entry.get('tool', '-')} status={entry['status']} "
            f"obs={(entry.get('observation') or entry.get('raw') or '')[:160]}"
        )
    trace_block = "\n".join(trace_lines) if trace_lines else "(noch keine Schritte)"

    conditions_de, _ = build_conditions_block_de(payload.conditions)

    return "\n".join(
        [
            (
                _AGENT_VERBATIM_SYSTEM_PROMPT
                if state.preserve_text_output
                else _AGENT_SYSTEM_PROMPT
            ),
            "",
            f"Suchwert: {payload.value}",
            (
                "Frage aus dem Datensatz (Quelldokument kann deutsch oder englisch sein):\n"
                f"{payload.question}"
            ) if payload.question else "",
            f"Bedingungen:\n{conditions_de}",
            "",
            f"Baseline-Antwort (v35 single-pass): value={state.baseline_value!r}",
            f"Baseline-Rohtext (erste 400 Zeichen): {state.baseline_text[:400]}",
            "",
            f"Aktueller Schritt: {step_index} von {state.step_budget}",
            f"Verbrauchte Output-Tokens: {state.cumulative_output_tokens}/{state.token_budget}",
            "",
            "Aktuell ausgewaehlte Chunks (chunk_id | heading | score | evidence | preview):",
            "\n".join(selected_summary_lines) if selected_summary_lines else "(keine)",
            "",
            "Vorherige Agent-Schritte:",
            trace_block,
            "",
            "Antworte jetzt mit einem einzelnen JSON-Objekt {\"thought\":\"...\",\"tool\":\"...\",\"args\":{...}}.",
        ]
    )


def _parse_agent_decision(raw: str) -> dict[str, Any] | None:
    """Parse the agent JSON. Returns None if malformed or tool unknown."""
    data, _ = parse_extracted_payload(raw)
    if not data:
        return None
    tool = data.get("tool")
    if not isinstance(tool, str) or tool not in _TOOL_NAMES:
        return None
    args = data.get("args")
    if args is not None and not isinstance(args, dict):
        return None
    return {"tool": tool, "args": args or {}, "thought": data.get("thought", "")}


def _safe_args_summary(args: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for key, value in args.items():
        if isinstance(value, str):
            summary[key] = value[:120]
        elif isinstance(value, list):
            summary[key] = [str(v)[:60] for v in value[:8]]
        else:
            summary[key] = value
    return summary


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


def _execute_tool(state: _AgentState, tool: str, args: dict[str, Any]) -> dict[str, Any]:
    try:
        if tool == "inspect_chunk":
            return _tool_inspect_chunk(state, args)
        if tool == "expand_query":
            return _tool_expand_query(state, args)
        if tool == "retrieve_more_context":
            return _tool_retrieve_more_context(state, args)
        if tool == "refine_extraction":
            return _tool_refine_extraction(state, args)
    except Exception as exc:  # never crash the loop
        return {"status": "tool_error", "summary": f"tool '{tool}' raised: {exc}"}
    return {"status": "unknown_tool", "summary": f"unknown tool '{tool}'"}


def _tool_inspect_chunk(state: _AgentState, args: dict[str, Any]) -> dict[str, Any]:
    chunk_id = str(args.get("chunk_id", "")).strip()
    if not chunk_id:
        return {"status": "bad_args", "summary": "chunk_id missing"}
    for item in state.ranked_chunks:
        if item.chunk.chunk_id == chunk_id:
            text_preview = item.chunk.text.replace("\n", " ")[:600]
            heading = item.chunk.heading or "(kein Heading)"
            return {
                "status": "ok",
                "summary": (
                    f"heading='{heading[:80]}' lines={item.chunk.start_line}-{item.chunk.end_line} "
                    f"score={item.score:.2f} text='{text_preview}'"
                ),
            }
    return {"status": "not_found", "summary": f"chunk_id '{chunk_id}' not in ranked set"}


def _tool_expand_query(state: _AgentState, args: dict[str, Any]) -> dict[str, Any]:
    raw_terms = args.get("extra_terms") or []
    if not isinstance(raw_terms, list):
        return {"status": "bad_args", "summary": "extra_terms must be a list"}
    extra = [str(t).strip() for t in raw_terms if str(t).strip()][:8]
    if not extra:
        return {"status": "bad_args", "summary": "no usable extra_terms provided"}

    # Merge and re-run selection with broader query anchors.
    merged_queries = list(dict.fromkeys(state.query_variants + extra))
    new_selection = select_consistent_diverse_chunks_v25(
        ranked_chunks=state.ranked_chunks,
        top_k=max(5, len(state.selected_chunks)),
        max_per_document=2,
        max_per_heading=1,
        payload=state.payload,
        query_variants=merged_queries,
        minimum_query_length=3,
        rerank_strategy="balanced",
    )
    state.query_variants = merged_queries
    state.selected_chunks = list(new_selection["selected_chunks"])
    state.chunk_evidence.update(new_selection["chunk_evidence"])

    ids = [item.chunk.chunk_id for item in state.selected_chunks[:6]]
    return {
        "status": "ok",
        "summary": f"queries+={extra}; new_top_ids={ids}",
    }


def _tool_retrieve_more_context(state: _AgentState, args: dict[str, Any]) -> dict[str, Any]:
    try:
        k = int(args.get("k", 3))
    except (TypeError, ValueError):
        return {"status": "bad_args", "summary": "k must be an integer"}
    k = max(1, min(10, k))

    new_selection = select_consistent_diverse_chunks_v25(
        ranked_chunks=state.ranked_chunks,
        top_k=len(state.selected_chunks) + k,
        max_per_document=3,
        max_per_heading=2,
        payload=state.payload,
        query_variants=state.query_variants,
        minimum_query_length=3,
        rerank_strategy="balanced",
    )
    state.selected_chunks = list(new_selection["selected_chunks"])
    state.chunk_evidence.update(new_selection["chunk_evidence"])
    ids = [item.chunk.chunk_id for item in state.selected_chunks]
    return {"status": "ok", "summary": f"top_k bumped by {k}; selected_ids={ids[:8]}"}


def _tool_refine_extraction(state: _AgentState, args: dict[str, Any]) -> dict[str, Any]:
    if state.refine_extraction_calls >= _MAX_REFINE_EXTRACTION_CALLS:
        return {
            "status": "recheck_limit",
            "summary": "refine_extraction call limit reached for this run",
        }

    raw_ids = args.get("focus_chunk_ids") or []
    if not isinstance(raw_ids, list):
        return {"status": "bad_args", "summary": "focus_chunk_ids must be a list"}
    focus_ids = {str(c).strip() for c in raw_ids if str(c).strip()}
    hint = str(args.get("hint", "")).strip()

    focus_chunks = [item for item in state.ranked_chunks if item.chunk.chunk_id in focus_ids]
    if not focus_chunks:
        # fall back to current selection
        focus_chunks = state.selected_chunks
    focus_chunks = focus_chunks[:6]

    focus_context = _render_selected_context(focus_chunks, state.chunk_evidence)
    focus_context_with_hint = (
        f"Agent-Hinweis: {hint}\n\n{focus_context}" if hint else focus_context
    )
    refine_prompt = append_question_to_prompt(
        build_prompt_v5(
            template=state.template,
            system=state.payload.system,
            system_name=state.payload.system_name,
            value=state.payload.value,
            conditions=state.payload.conditions,
            docs_text=focus_context_with_hint,
        ),
        state.payload,
    )
    remaining_output_tokens = state.token_budget - state.cumulative_output_tokens
    if remaining_output_tokens <= 0:
        return {"status": "token_budget_exhausted", "summary": "agent output-token budget exhausted"}
    state.refine_extraction_calls += 1
    try:
        refined: LLMTextResponse = generate_text_component(
            prompt=refine_prompt,
            llm=state.payload.llm,
            temperature=state.payload.temperature,
            max_tokens=remaining_output_tokens,
        )
    except Exception as exc:
        return {"status": "llm_error", "summary": f"refine LLM error: {exc}"}

    state.cumulative_input_tokens += refined.input_tokens
    state.cumulative_output_tokens += refined.output_tokens

    refined_value = parse_extracted_answer(
        refined.text,
        preserve_text=state.preserve_text_output,
    )
    return {
        "status": "ok",
        "summary": (
            f"refined_value={refined_value} focus_ids={[c.chunk.chunk_id for c in focus_chunks]} "
            f"hint='{hint[:120]}' raw='{refined.text[:200]}'"
        ),
    }


__all__ = ["run_text_only_simple_conversion_v36"]
