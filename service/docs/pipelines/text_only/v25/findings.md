# Text-only Simple Conversion v25 Findings

Date: 2026-05-12
Pipeline: text_only_simple_conversion_v25

## Selected literature-driven finding
Section 7 in `pipeline_inventory_and_paper_mapping.md`, first finding:

- Retrieval pipelines should add an explicit routing/prefilter stage before extraction.
- Relevant literature anchors: `Semantic Text Classification for Supporting Automated Compliance Checking in Construction` (2013) and `A platform-based Natural Language processing-driven strategy for digitalising regulatory compliance processes for the built environment` (2024).

The concrete repo interpretation is: requirement-like sections should be preferred over administrative or meta sections before the normal extraction prompt runs.

## Design choices
- Started from v24 because it is the strongest current text-only retrieval baseline in the repo.
- Kept the change additive: v25 only reranks retrieval candidates before the existing v24 selection logic.
- Used lightweight clause/section routing heuristics instead of adding a second LLM call.
- Focused on requirement-first behavior for Brandschutz-style approvals: requirement headings and requirement language are boosted; administrative sections are deprioritized.

## Implementation details

### New Component: [app/services/components/retrieval_enhancer_v25_text.py](app/services/components/retrieval_enhancer_v25_text.py)
- Adds `_route_prefilter_candidates_v25(...)` as a routing layer ahead of v24 selection.
- Builds routing anchors from query variants, payload value tokens, and condition metadata.
- Boosts chunks with requirement-style headings and clause language, such as `Anforderungen`, `Feuerwiderstand`, `Mindestdicke`, `Abschottung`, `Wand`, and `Decke`.
- Penalizes chunks with administrative/meta headings, such as `Allgemeines`, `Hinweise`, `Verweise`, `Antragsteller`, `Hersteller`, and fee/process language.
- Delegates query expansion, numeric normalization, adaptive consistency, and retry planning to v24 for compatibility.

### New Pipeline: [app/services/pipelines/text_only_simple_conversion_v25.py](app/services/pipelines/text_only_simple_conversion_v25.py)
- Mirrors the v24 execution flow.
- Switches chunk selection from `select_consistent_diverse_chunks_v24(...)` to `select_consistent_diverse_chunks_v25(...)`.
- Adds routing diagnostics to component logs:
  - `compliance_routing_prefilter`
  - `route_focus`
  - `route_anchor_count`
  - `route_boosted_chunk_ids`
  - `route_penalized_chunk_ids`

### Registration: [app/services/experiment_runner.py](app/services/experiment_runner.py)
- Added import and dispatch for `text_only_simple_conversion_v25`.
- Updated supported pipeline list.

### Tests: [tests/test_retrieval_enhancer_v25.py](tests/test_retrieval_enhancer_v25.py)
- Verifies that requirement sections outrank administrative sections even if the base score is slightly lower.
- Verifies that requirement headings matching query anchors receive a positive routing boost.

## Expected impact
- Better first-pass retrieval precision on compliance-style approvals where true evidence is concentrated in requirement sections rather than front matter or approval metadata.
- Lower risk that administrative chunks consume top-k slots before extraction.
- Strongest expected benefit on conditional scalar extraction tasks where a relevant section heading often disambiguates the correct clause family.

## Risks
- Heuristic routing can over-penalize valid chunks if a document uses unusual heading names.
- Administrative sections can still contain true constraints in edge cases; v25 therefore deprioritizes rather than hard-removes them.
- The heuristic vocabulary is German-heavy and Brandschutz-oriented; other domains may need additional routing terms.

## Validation
- Focused test run: `python -m pytest tests/test_retrieval_enhancer_v25.py`
- Result: 2 tests passed.

## Next experiments
1. Run v25 against `conditionBasedExtraction` with gemma-3 and gemma-4 and compare against v24.
2. Inspect failure cases where the winning chunk is still administrative and extend routing vocabulary only if the errors are systematic.
3. If v25 helps, consider reusing the routing layer for Turtle/KG retrieval stages where clause family matters before formalization.