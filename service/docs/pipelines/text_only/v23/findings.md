# Text-only Simple Conversion v23 Findings

Date: 2026-05-12
Pipeline: text_only_simple_conversion_v23

## Selected unfinished finding
Section 2 (Text-only conditional scalar extraction), Finding A:
Marker input noise in v6/v7/v10 (image embeds, span tags, repeated boilerplate) degrades retrieval quality by creating false-positive numeric signals.

## Design choices
- Started from the strongest text-only lineage (v22) to keep proven architecture and numeric normalization behavior.
- Added explicit marker-noise mitigation in retrieval selection instead of broad architecture changes.
- Kept additive behavior: v23 reuses v22 query expansion and retry strategy, and only hardens chunk selection.

## Implementation details
- Added component [app/services/components/retrieval_enhancer_v23_text.py](app/services/components/retrieval_enhancer_v23_text.py):
  - Line-level noise filtering for marker artifacts (`![img](...)`, `<span ...>`, `class=...`, `data-page`, page counters).
  - Noise-aware score penalty based on noisy-line ratio and artifact-token density.
  - Hard suppression of highly noisy chunks with no query/condition anchors.
  - Delegates query expansion, retry planning, and numeric normalization to v22 logic for compatibility.
- Added pipeline [app/services/pipelines/text_only_simple_conversion_v23.py](app/services/pipelines/text_only_simple_conversion_v23.py):
  - Mirrors v22 flow.
  - Switches retrieval enhancer calls to v23 functions.
  - Adds component log markers (`marker_noise_mitigation`) for traceability.
- Registered v23 in [app/services/experiment_runner.py](app/services/experiment_runner.py).
- Added focused test [tests/test_retrieval_enhancer_v23.py](tests/test_retrieval_enhancer_v23.py) to verify noisy marker chunks are suppressed in favor of clean evidence.

## Expected impact
- Higher precision for condition-based retrieval on marker-derived text.
- Reduced false positives caused by numeric tokens inside image paths and HTML span boilerplate.
- Better stability when marker markdown still contains residual artifacts after base cleaning.

## Risks
- Over-penalization could suppress genuinely relevant chunks that contain mixed clean/noisy lines.
- Noise patterns are heuristic; unseen marker artifacts may still slip through.
- Dataset-specific marker formatting differences may require tuning suppression thresholds.

## Next experiments
1. Run v23 on conditionBasedExtraction with gemma-3 and gemma-4 against v22 and v21 baselines.
2. Compare retrieval diagnostics (selected chunks, evidence score, contradiction hits) for v22 vs v23 on failure cases from v10/v17.
3. If over-suppression appears, tune noise suppression threshold and anchor-preservation logic.
4. Evaluate whether the same noise-aware selector should be backported as an optional mode for v22.
