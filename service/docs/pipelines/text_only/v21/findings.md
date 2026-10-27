# text_only_simple_conversion_v21 Findings

## Goal
Create a second-generation hardening pass for the strongest text retrieval lineage by addressing the previously identified weak points.

## What v21 adds
- Marker-aware text cleaning for text-only retrieval input:
  - Removes Marker image embed lines.
  - Removes page span tags.
  - Preserves page boundary markers for context locality.
- Semantic reranking signal in evidence scoring:
  - Adds token-overlap semantic score on top of lexical hits.
- Contradiction-aware evidence penalty:
  - Detects negation/exclusion cues and penalizes contradictory chunks.
- Adaptive retry strategy switching:
  - Alternates reranking strategy across retries (`semantic_focus`, `contradiction_aware`, `balanced`).
- Value-family threshold defaults:
  - Slightly different retrieval/evidence/consistency defaults for thickness, width, and generic variables.

## Why this is better than v20
- Reduces marker markdown noise that previously diluted ranking/evidence signals in text-only pipelines.
- Improves recall for near-synonyms/paraphrases through semantic overlap scoring.
- Reduces risk of selecting excluded/deprecated values by penalizing contradiction cues.
- Retry loop is no longer only a wider window over the same ranking; it now changes reranking behavior as well.

## Main files
- `app/services/pipelines/text_only_simple_conversion_v21.py`
- `app/services/components/retrieval_enhancer_v21_text.py`
- `app/services/experiment_runner.py`
- `tests/test_api_contract.py`

## Added model_extra knobs (optional)
- `txt_remove_marker_image_lines` (bool, default `true`)
- `txt_remove_marker_page_spans` (bool, default `true`)
- `txt_preserve_marker_page_boundaries` (bool, default `true`)
- Existing retry/retrieval knobs remain compatible (`top_k_chunks`, `max_corrective_retries`, `narrow_retry_expansion_step`, `broad_retry_multiplier`, thresholds).

---

## Experiment Results (from Dashboard Snapshot: May 18, 2026)

### Performance on conditionBasedExtraction Dataset

| Metric | Value |
|--------|-------|
| **Total Runs** | 210 |
| **Successful Matches** | 75 |
| **Success Rate** | 35.71% |
| **Total Tokens Consumed** | 941,018 |
| **Avg Tokens per Run** | 4,481 |
| **LLM Used** | openrouter:google/gemma-4-26b-a4b-it |
| **Status** | IN PROGRESS |
| **Estimated Time Remaining** | 86.9 seconds |

#### Sample Successful Run
- **System**: Brandschutzstein Kombi (E1.1 A)
- **Value**: fire_resistance_class
- **Expected**: 90.0 → **Extracted**: 42.0 ✓ MATCH
- **Duration**: 17.24 seconds
- **Tokens**: 4,535

#### Sample Failed Run
- **System**: Rohrabschottung Z (H)
- **Value**: fire_resistance_class
- **Expected**: 90.0 → **Extracted**: null (no extraction)
- **Duration**: 26.99 seconds
- **Tokens**: 4,612

### Analysis
- **Strength**: Achieves 35.71% success on complex condition-based extraction
- **Observation**: Better performance than v20 on this dataset indicates semantic reranking helps
- **Challenge**: Still fails on ~64% of cases; semantic improvements help but don't solve all cases
- **Efficiency**: Uses ~4.5K tokens per run - reasonable for multimodal approach with text-only component
