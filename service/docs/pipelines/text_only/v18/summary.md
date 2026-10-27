# text_only_simple_conversion_v18 Summary

## What changed
- Added new pipeline: text_only_simple_conversion_v18
- Registered v18 in experiment runner dispatch
- Added retrieval enhancer component for v18 with:
  - multi-query retrieval expansion
  - diversity-aware selection
  - evidence-aware scoring
- Added bounded corrective retry strategy with explicit retry reason logging
- Added focused API and component tests for v18 behavior

## Backward compatibility
- Existing request schema unchanged
- Existing pipelines unchanged
- New controls are optional and read via payload.model_extra

## Optional model_extra keys in v18
- top_k_chunks (int, default 3)
- retrieval_confidence_threshold (float, default 0.58)
- enable_corrective_retry (bool, default true)
- max_corrective_retries (int, default 1)
- query_expansion_limit (int, default 6)
- diversity_max_per_document (int, default 2)
- diversity_max_per_heading (int, default 1)
- evidence_score_threshold (float, default 0.42)

## Validation
- Static diagnostics: no errors in changed files
- Focused test execution command could not be run from available toolset in this session

## Deferred improvements
- Learned/dense retriever integration inspired by Longtriever
- External reranking model for evidence calibration
- Section-level semantic deduplication beyond lexical signatures
