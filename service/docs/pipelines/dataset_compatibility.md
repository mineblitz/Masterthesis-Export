# Pipeline Dataset Compatibility Summary

Last updated: 2026-05-12
Source of truth for pipelines: `app/services/experiment_runner.py`
Source of truth for datasets: project "Self-Generated Datasets Summary" (17 dataset families)

This file is intended to be kept up to date whenever a pipeline is added/renamed/removed or a dataset family changes.

## Dataset families (canonical names)

- `simpleMinMaxExtraction`
- `conditionBasedExtraction`
- `conditionKGExtraction`
- `allowedCableTypesExtraction`
- `allowedPipeTypesExtraction`
- `systemTransferScopeExtraction`
- `cableJsonExtractionNoValues`
- `cableJsonExtractionPlaceholders`
- `cableTtlExtractionNoValues`
- `cableTtlExtractionPlaceholders`
- `pipeJsonExtractionNoValues`
- `pipeJsonExtractionPlaceholders`
- `pipeTtlExtractionNoValues`
- `pipeTtlExtractionPlaceholders`
- `comprehensiveKgExtraction`
- `comprehensiveKgSchemaExtraction`
- `comprehensiveKgSchemaMinimalExtraction`

## Compatibility matrix

Legend:
- `Primary`: best-fit benchmark for the pipeline's objective.
- `Secondary`: usable, but not the most targeted fit.
- `Not recommended`: task mismatch.

## Expected request data (to avoid runtime validation errors)

Use this quick contract checklist before calling `/api/experiment`.

- `text_only_simple_conversion`, `text_only_simple_conversion_v2`, `text_only_simple_conversion_v3`
	- `expected_value`: `number` (scalar)
	- required: `min_or_max`
	- typical `value`: scalar targets such as min/max thickness
- `text_only_simple_conversion_v4`, `text_only_simple_conversion_v5`, `text_only_simple_conversion_v6`, `text_only_simple_conversion_v7`, `text_only_simple_conversion_v8`, `text_only_simple_conversion_v10`, `text_only_simple_conversion_v17`, `text_only_simple_conversion_v18`, `text_only_simple_conversion_v20`, `text_only_simple_conversion_v21`, `text_image_multimodal_conversion_v11`, `text_image_multimodal_conversion_v19`, `text_image_multimodal_conversion_v21`
	- `expected_value`: `number` (scalar)
	- `min_or_max`: optional (v4+)
	- `conditions`: optional list of condition objects
- `text_only_simple_conversion_v9`
	- `expected_value`: `string` label/class (for example, transfer-scope style outputs)
- `direct_qa_v1`, `direct_qa_conditional_chunk_v1`
	- `expected_value`: scalar value to compare against the extracted answer
	- `question`: required question
	- text input: `content` for `direct_qa_v1`; `chunk` is accepted and normalized to `content` for `direct_qa_conditional_chunk_v1`
	- conditional dataset `value` remains a variable label (for example, `min_thickness`)
	- `direct_qa_conditional_chunk_v1` also accepts an extracted numeric answer that is exactly one tenth of `expected_value`
- `text_only_simple_conversion_v15`
	- `expected_value`: non-empty `object` of boolean flags, shape `{ "type_name": true|false, ... }`
	- required: at least one key in `expected_value`
	- important: empty object, scalar, string, list, or null will fail with validation error
- `text_only_simple_conversion_v16`
	- `expected_value`: non-empty `object` of boolean flags, shape `{ "type_name": true|false, ... }`
	- required: at least one key in `expected_value`
	- optional: `number_of_variables_per_request` (must be `>= 1` when provided)
	- important: empty object, scalar, string, list, or null will fail with validation error
- `turtle_kg_conversion_v12`, `turtle_kg_twostep_v13`, `turtle_kg_keyword_v14`, `kg_turtle_extraction_cable_v1`, `kg_turtle_extraction_pipe_v1`, `kg_comprehensive_schema_minimal_turtle_v1`, `kg_comprehensive_schema_minimal_turtle_v2`
	- `expected_value`: structured KG target (project-standard object/list representation for triples/subgraphs)
	- important: keep expected structure aligned with dataset JSON format used for KG evaluation

### Minimal valid examples

Scalar pipeline example (`v21` style):

```json
{
	"pipeline": "text_only_simple_conversion_v21",
	"expected_value": 150.0,
	"value": "min_thickness"
}
```

Boolean-map pipeline example (`v15`/`v16` style):

```json
{
	"pipeline": "text_only_simple_conversion_v16",
	"expected_value": {
		"cable_bundle": true,
		"cable_rack": true,
		"single_cable": false
	},
	"value": "allowed_cable_types",
	"number_of_variables_per_request": 2
}
```

| Pipeline | What it does | Primary dataset families | Secondary dataset families | Not recommended |
|---|---|---|---|---|
| `text_only_simple_conversion` | Baseline text-only scalar extraction from approval docs | `simpleMinMaxExtraction` | `conditionBasedExtraction` | All KG/Turtle fill and full-KG reconstruction datasets; cable/pipe type classification datasets |
| `text_only_simple_conversion_v2` | Improved scalar extraction with stronger min/max prompting | `simpleMinMaxExtraction` | `conditionBasedExtraction` | Same as baseline text-only exclusions |
| `text_only_simple_conversion_v3` | Modularized text-only scalar extraction flow | `simpleMinMaxExtraction` | `conditionBasedExtraction` | Same as baseline text-only exclusions |
| `text_only_simple_conversion_v4` | Condition-aware scalar extraction (conditions optional, flexible) | `conditionBasedExtraction` | `simpleMinMaxExtraction` | KG/Turtle fill and full-KG reconstruction; cable/pipe type classification |
| `text_only_simple_conversion_v5` | Condition translation + targeted conditional scalar prompting | `conditionBasedExtraction` | `simpleMinMaxExtraction` | KG/Turtle fill and full-KG reconstruction; cable/pipe type classification |
| `text_only_simple_conversion_v6` | Marker markdown source variant for scalar extraction | `conditionBasedExtraction`, `simpleMinMaxExtraction` | `conditionKGExtraction` (only if converted to text form externally) | Structured JSON/Turtle fill, full KG reconstruction, type classification |
| `text_only_simple_conversion_v7` | Marker LLM markdown variant for scalar extraction | `conditionBasedExtraction`, `simpleMinMaxExtraction` | `conditionKGExtraction` (text-only fallback mode) | Structured JSON/Turtle fill, full KG reconstruction, type classification |
| `text_only_simple_conversion_v8` | Retrieval-focused text-only scalar extraction with keyword context | `conditionBasedExtraction`, `simpleMinMaxExtraction` | `conditionKGExtraction` (if serialized conditions are transformed to text prompts) | Structured JSON/Turtle fill, full KG reconstruction, type classification |
| `text_only_simple_conversion_v9` | Label extraction / classification-style text flow | `systemTransferScopeExtraction` | `allowedCableTypesExtraction`, `allowedPipeTypesExtraction` (if adapted to expected label format) | Structured JSON/Turtle fill, full KG reconstruction |
| `text_only_simple_conversion_v10` | Marker + retrieval-enhanced text-only scalar extraction | `conditionBasedExtraction`, `simpleMinMaxExtraction` | `conditionKGExtraction` (text projection mode) | Structured JSON/Turtle fill, full KG reconstruction, type classification |
| `direct_qa_v1` | Single-pass extraction from pre-chunked text and a question | CODE-ACCORD-Entities and compatible pre-chunked Q&A records | — | PDF retrieval and KG/Turtle reconstruction tasks |
| `direct_qa_conditional_chunk_v1` | Same direct-QA extraction with conditional records' `chunk` mapped to `content`; accepts numeric extractions one tenth of the expected value | Filtered conditional dataset with `chunk`, `question`, and `expected_value` | CODE-ACCORD-Entities-shaped conditional subsets | PDF retrieval and KG/Turtle reconstruction tasks |
| `text_only_simple_conversion_v15` | Strict boolean-map extraction for cable/pipe-type permissions | `allowedCableTypesExtraction`, `allowedPipeTypesExtraction` | `systemTransferScopeExtraction` | Scalar min/max and condition scalar datasets; Turtle/JSON fill and full KG reconstruction |
| `text_only_simple_conversion_v16` | Batched boolean-map extraction for larger variable sets | `allowedCableTypesExtraction`, `allowedPipeTypesExtraction` | `systemTransferScopeExtraction` | Scalar datasets; Turtle/JSON fill and full KG reconstruction |
| `text_only_simple_conversion_v17` | Structured ranking + retrieval quality + corrective retry (scalar) | `conditionBasedExtraction`, `simpleMinMaxExtraction` | `conditionKGExtraction` (text projection mode) | Structured JSON/Turtle fill, full KG reconstruction, type classification |
| `text_only_simple_conversion_v18` | Multi-query + diversity-aware retrieval + bounded retry (scalar) | `conditionBasedExtraction`, `simpleMinMaxExtraction` | `conditionKGExtraction` (text projection mode) | Structured JSON/Turtle fill, full KG reconstruction, type classification |
| `text_only_simple_conversion_v20` | Consistency-gated scalar extraction with adaptive retries | `conditionBasedExtraction`, `simpleMinMaxExtraction` | `conditionKGExtraction` (text projection mode) | Structured JSON/Turtle fill, full KG reconstruction, type classification |
| `text_only_simple_conversion_v21` | Marker-cleaned + semantic reranked + contradiction-aware scalar retrieval | `conditionBasedExtraction`, `simpleMinMaxExtraction` | `conditionKGExtraction` (text projection mode) | Structured JSON/Turtle fill, full KG reconstruction, type classification |
| `text_image_multimodal_conversion_v11` | Multimodal extraction using marker text + selected page images | `conditionBasedExtraction`, `simpleMinMaxExtraction` | `conditionKGExtraction` (if target remains scalar/value extraction) | Structured JSON/Turtle fill, full KG reconstruction, type classification |
| `text_image_multimodal_conversion_v19` | Layout-aware multimodal evidence selection + retry | `conditionBasedExtraction`, `simpleMinMaxExtraction` | `conditionKGExtraction` (scalar target mode) | Structured JSON/Turtle fill, full KG reconstruction, type classification |
| `text_image_multimodal_conversion_v21` | Marker-structure-aware multimodal extraction with logo/cost filtering | `conditionBasedExtraction`, `simpleMinMaxExtraction` | `conditionKGExtraction` (scalar target mode) | Structured JSON/Turtle fill, full KG reconstruction, type classification |
| `turtle_kg_conversion_v12` | Turtle KG condition-driven extraction | `conditionKGExtraction` | `comprehensiveKgExtraction` (partial KG target scenarios) | Scalar-only datasets and type classification datasets |
| `turtle_kg_twostep_v13` | Two-step locate-then-extract Turtle KG pipeline | `conditionKGExtraction` | `comprehensiveKgExtraction`, `comprehensiveKgSchemaExtraction` | Scalar-only datasets and type classification datasets |
| `turtle_kg_keyword_v14` | Two-step Turtle KG with keyword expansion and chunking | `conditionKGExtraction` | `comprehensiveKgExtraction`, `comprehensiveKgSchemaExtraction` | Scalar-only datasets and type classification datasets |
| `kg_turtle_extraction_cable_v1` | Cable-centric KG extraction into Turtle triples | `cableTtlExtractionNoValues`, `cableTtlExtractionPlaceholders` | `comprehensiveKgExtraction` (cable-focused slices) | Scalar datasets; pipe-specific datasets; type classification |
| `kg_turtle_extraction_pipe_v1` | Pipe-centric KG extraction into Turtle triples | `pipeTtlExtractionNoValues`, `pipeTtlExtractionPlaceholders` | `comprehensiveKgExtraction` (pipe-focused slices) | Scalar datasets; cable-specific datasets; type classification |
| `kg_comprehensive_schema_minimal_turtle_v1` | Minimal-schema-to-full-subgraph Turtle reconstruction | `comprehensiveKgSchemaMinimalExtraction` | `comprehensiveKgSchemaExtraction`, `comprehensiveKgExtraction` | Scalar datasets; type classification datasets |
| `kg_comprehensive_schema_minimal_turtle_v2` | Hierarchical branch/scope -> subtype -> detail -> assembly Turtle reconstruction | `comprehensiveKgSchemaMinimalExtraction`, `comprehensiveKgSchemaExtraction` | `comprehensiveKgExtraction` | Scalar datasets; type classification datasets |

## Quick selection guide

- Use `text_only_simple_conversion_v21` for strongest text-only scalar extraction benchmarks.
- Use `text_image_multimodal_conversion_v21` when visual/layout evidence is likely required.
- Use `text_only_simple_conversion_v16` for multi-label cable/pipe-type capability benchmarks.
- Use `turtle_kg_*` and `kg_turtle_*` families for KG/Turtle-native extraction tasks.
- Use `kg_comprehensive_schema_minimal_turtle_v2` for compressed-schema full KG reconstruction on larger schemas; keep `kg_comprehensive_schema_minimal_turtle_v1` as a simpler baseline.

## Maintenance rules (keep this file up to date)

On each pipeline or dataset change, update this file in the same PR:

1. If a new pipeline is registered in `app/services/experiment_runner.py`, add one row to the matrix.
2. If pipeline behavior changes (task type, modality, output shape), update "What it does" and compatibility columns.
3. If a new dataset family is added, include it in "Dataset families" and map all affected pipelines.
4. If a pipeline is removed/renamed, remove/rename its row immediately.
5. Keep `Last updated` current.
