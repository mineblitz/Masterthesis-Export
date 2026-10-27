# Text-only Simple Conversion v30 Findings

Date: 2026-05-15
Pipeline: text_only_simple_conversion_v30

## Selected literature-driven finding
From item 16 in `experiment_analysis_and_improvement_plan.md`:

- Add object-model bridge between extracted fields and KG/BIM validation targets.
- Main paper anchor: Development of an object model for automated compliance checking.

## Design choices
- Built directly on v29 to preserve retrieval/ranking/retry/IR behavior.
- Added deterministic object-model bridge stage as an additive extension.
- Kept `ExperimentResult` schema and extraction semantics unchanged.

## Implementation details

### New component: app/services/components/object_model_bridge_v30.py
- Deterministic mapper with canonical bridge fields:
  - `entity_type`
  - `entity_id`
  - `property_key`
  - `property_value`
  - `property_unit`
  - `condition_bindings`
  - `provenance`
- Deterministic ID generation from system, system name, value key, and canonicalized conditions.
- Specialized mappings:
  - `min_thickness` -> `minimum_thickness`
  - `fire_resistance_class` -> `fire_resistance_class`
  - `allowed*` -> `allowed_types`
- Fallback mapping:
  - `generic_requirement_property` with explicit fallback reason in `mapping_decisions`.

### New component alias module: app/services/components/retrieval_enhancer_v30_text.py
- Re-exports v29 retrieval helpers under v30 names.
- Preserves v29 retrieval semantics for lineage consistency.

### New pipeline: app/services/pipelines/text_only_simple_conversion_v30.py
- Runs v29 flow and then performs deterministic bridge mapping before returning.
- Adds `object_model_bridge_v30` component log with canonical field list, mapping decisions, and fallback reason.
- Appends serialized bridge output to `full_output` under `[Object Model Bridge v30]` section.
- Keeps `extracted_value` and `is_match` behavior unchanged.

### Prompt template: prompts/text_only_v11.txt
- Based on v10 with explicit note that output may be mapped into canonical object-model entities.

### Registration
- Added import and dispatch entry for `text_only_simple_conversion_v30` in `app/services/experiment_runner.py`.

## Expected impact
- More stable downstream compliance checks by transforming scalar outputs into canonical object-model records.
- Improved traceability through deterministic entity IDs, canonical condition bindings, and source-chunk provenance.
- No regression risk in core extraction semantics because v29 flow remains intact.

## Risks and caveats
- Current specialized mapping list is intentionally minimal and should be extended for additional variable families.
- `allowed*` values are mapped at family level (`allowed_types`) and may require subtype canonicalization in future iterations.

## Validation (focused)
Planned commands:
- `pytest tests/test_object_model_bridge_v30.py -v`
- `pytest tests/test_text_only_simple_conversion_v30_flow.py -v`
- `python -c "from app.services.experiment_runner import run_experiment; from app.services.pipelines.text_only_simple_conversion_v30 import run_text_only_simple_conversion_v30; print('ok')"`
