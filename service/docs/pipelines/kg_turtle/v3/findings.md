# Findings: kg_comprehensive_schema_minimal_turtle_v3

Date: 2026-05-12

## Motivation

This pipeline implements the first still-open section 7 finding in `pipeline_inventory_and_paper_mapping.md` for the KG record/comprehensive KG lineage: schema extension plus canonicalization to improve mapping from free text into a constrained target schema.

## What was implemented

1. New pipeline: `kg_comprehensive_schema_minimal_turtle_v3`
- Additive evolution of `kg_comprehensive_schema_minimal_turtle_v2`.
- Keeps the hierarchical stages (presence -> subtype -> value extraction -> assembly).

2. Practical schema extension stage (`schema_extension_v3`)
- Reads optional `schema_extension_ttl` from request extras.
- Merges base minimal schema (`input_kg_schema_ttl`) with extension Turtle deterministically.
- Uses merged schema for prompt context and branch extraction.

3. Deterministic canonicalization stage (`canonicalization_v3`)
- Ensures missing `@prefix` declarations from merged schema are injected into assembled Turtle.
- Canonicalizes QName locals by deterministic lookup against schema-local identifiers.
- Canonicalizes numeric literals from `xsd:integer/int/double/float` to `xsd:decimal` form when possible.
- Removes duplicate Turtle lines deterministically.

4. Scoring and outputs
- Triple scoring remains based on `turtle_triple_scorer_component` for continuity.
- Scoring now runs on canonicalized Turtle output.
- Component logs include canonicalization and schema-extension statistics.

## Validation surface

- Focused behavior tests added in `tests/test_kg_comprehensive_schema_minimal_turtle_v3.py`.
- API-contract test added in `tests/test_api_contract.py`.
- Runner registration added in `app/services/experiment_runner.py`.

## Known limits

- Canonicalization is deterministic but heuristic (string-form QName mapping), not ontology-reasoning.
- No learned fine-tuning stage is included; this remains a practical non-fine-tuned step aligned to repo scope.