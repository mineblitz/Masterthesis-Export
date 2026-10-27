# text_only_simple_conversion_v18 Plan

## Goal
Upgrade v17 text-only retrieval pipeline with higher-quality context selection and bounded corrective behavior while preserving existing request/response schema and numeric extraction semantics.

## Why v17 -> v18
- v17 already has structured chunking, ranking, and a retry loop.
- Required upgrades map naturally onto v17 extension points (query formulation, selection, scoring, retry policy).
- Lowest integration risk with highest retrieval upside compared with introducing new model families.

## Required upgrades and technical mapping
1. Multi-query retrieval expansion
- Build query variants from: value key, translated conditions, system/system_name, and search terms.
- Use variants in ranking-time evidence and coverage calculation.

2. Retrieval diversity selection
- Select ranked chunks with constraints to reduce near-duplicates and improve spread across headings/documents.
- Keep fallback behavior if candidate pool is small.

3. Evidence-aware scoring signal
- Add lightweight evidence score per chunk using:
  - numeric cues (digits, units, comparators)
  - condition coverage cues
  - heading relevance cues
- Combine with base hybrid rank score.

4. Bounded corrective retry with reason logging
- Retry only up to configured max attempts (default 2 total attempts).
- Trigger reasons are explicit (retrieval quality, null extraction, low evidence, or combined).
- Log reason and attempt metadata in component details.

5. Backward compatibility
- No schema changes; all knobs optional and read from payload.model_extra.
- Existing v17 and others untouched.

## New optional model_extra keys (v18)
- top_k_chunks: int (default 3)
- retrieval_confidence_threshold: float (default 0.58)
- enable_corrective_retry: bool (default true)
- max_corrective_retries: int (default 1)
- query_expansion_limit: int (default 6)
- diversity_max_per_document: int (default 2)
- diversity_max_per_heading: int (default 1)
- evidence_score_threshold: float (default 0.42)

## Validation plan
- API contract tests for v18 success path and retry behavior.
- Targeted component tests for v18 retrieval helper behavior (query expansion, diversity, evidence score).
- Focused pytest runs only for touched tests.
