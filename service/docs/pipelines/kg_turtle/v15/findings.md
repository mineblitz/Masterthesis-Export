# Turtle KG Keyword v15 Findings

Date: 2026-05-12
Pipeline: turtle_kg_keyword_v15

## Selected literature-driven finding
Section 7 in pipeline_inventory_and_paper_mapping.md, third finding:

- v12/v13/v14 Turtle-KG lineage should follow a staged flow from raw text toward formal machine-readable structure.
- Relevant anchors: Information Transformation and Automated Reasoning (2013), Automated Information Transformation (2015), and Using LLMs for Interpretation of Building Regulations (2024).

## Design choices
- Started from v14 as the nearest implementation anchor.
- Kept v14 keyword-guided retrieval and extraction behavior for compatibility.
- Added deterministic post-processing stages to realize Extract -> Normalize -> Formalize without introducing new network dependencies.

## Implementation details

### New pipeline: app/services/pipelines/turtle_kg_keyword_v15.py
- Stage 1 Extract:
  - Reuses v14 flow: marker LLM markdown input, keyword expansion prompt, keyword-context chunk extraction, extraction prompt.
  - Keeps existing component logging style and API contract fields.
- Stage 2 Normalize:
  - Adds deterministic numeric canonicalization before final output.
  - Extracts numeric candidates with units from retrieved context lines.
  - Converts dimensional values to canonical mm where needed (mm/cm/m handling).
  - Selects best candidate relative to extracted value and records normalization diagnostics.
- Stage 3 Formalize:
  - Renders a deterministic Turtle snippet from normalized value.
  - Emits decimal-typed literal and provenance triple in component details and final output.

### Registration
- Added import and dispatch for turtle_kg_keyword_v15 in app/services/experiment_runner.py.
- Updated supported pipeline list accordingly.

## Tests
- Added tests/test_turtle_kg_keyword_v15.py:
  - Validates deterministic cm -> mm normalization behavior.
  - Validates numeric candidate extraction with unit normalization.
  - Validates Turtle formalization output and provenance emission.
- Extended tests/test_api_contract.py with an API-level test for turtle_kg_keyword_v15:
  - Mocks marker extraction and both LLM calls.
  - Asserts normalized extracted value and presence of normalization/formalization component logs.

## Expected impact
- Bridges KG extraction toward formalized output with a concrete intermediate normalization stage.
- Improves consistency of dimensional outputs across mixed unit mentions.
- Keeps behavior robust and testable by placing deterministic logic after LLM extraction.

## Risks and caveats
- Normalization currently targets dimensional numeric fields and common units (mm/cm/m).
- Formalization is pragmatic Turtle rendering, not full legal-rule reasoning or ontology reasoning.
- Candidate extraction is line-based and may miss values split across heavily fragmented layouts.

## Validation
- Focused unit tests:
  - python -m pytest tests/test_turtle_kg_keyword_v15.py -v
- API-level focused test:
  - python -m pytest tests/test_api_contract.py -k "turtle_kg_keyword_v15" -v

---

## ❌ Experiment Results (from Dashboard Snapshot: May 18, 2026)

### Critical Performance Drop on conditionKGExtraction Dataset

| Metric | Value |
|--------|-------|
| **Total Runs** | 4,500 |
| **Successful Matches** | 128 |
| **Success Rate** | **2.84%** ❌ |
| **Total Tokens Consumed** | 18,371,758 |
| **Avg Tokens per Run** | 4,083 |
| **LLM Used** | localai:gemma-3-27b-it |
| **Status** | ✓ COMPLETED |

#### Sample Successful Run (Rare)
- **System**: Brandschutzschaum Kombi (D4)
- **Value**: max_opening_height
- **Expected**: 320.0 → **Extracted**: 320.0 ✓ MATCH
- **Duration**: 13.80 seconds
- **Tokens**: 7,926

#### Typical Failed Run
- **System**: Rohrabschottung E (G)
- **Value**: fire_resistance_class
- **Expected**: 90.0 → **Extracted**: null ❌
- **Duration**: 174.06 seconds (extremely slow!)
- **Tokens**: 3,033
- **Observation**: Null extractions dominate failures

### Severe Regression from v14

| Pipeline | Success Rate | Total Runs | Status |
|----------|--------------|-----------|--------|
| v14 (Context Window Study) | 29.71% | 4,500 | DONE |
| v15 (This version) | 2.84% | 4,500 | DONE |
| **Change** | **-26.87%** ❌ | Same | Comparable |

### Root Cause Analysis

**v15 represents a catastrophic failure** with multiple issues:

1. **Normalization Logic Too Aggressive**
   - Dimensional unit conversion heuristics likely rejecting valid values
   - The normalization stage (Stage 2) may be filtering out all output before Turtle formalization

2. **Turtle Formalization Breaking Extraction**
   - The new Stage 3 (formalization) may be causing parsing errors
   - LLM output expected to be numeric, but formalization expects RDF triples

3. **Implementation Bug in Keyword Extraction**
   - Keyword-context chunk selection may be broken
   - Candidate extraction logic may have off-by-one or parsing errors

4. **Performance Catastrophe**
   - One failed run took 174 seconds (normal is ~15-20 seconds)
   - Suggests infinite loops or exponential retries in failure cases

### Comparison to v14

**v14 (baseline with keyword study - 29.71% success):**
- Simple keyword + extraction flow
- Fast execution (~15 seconds typical)
- Reasonable token budget

**v15 (new deterministic processing - 2.84% success):**
- Adds normalization + formalization stages
- Extremely variable timing (13-174 seconds)
- Token consumption similar but output quality terrible

### Recommendations - URGENT

1. **IMMEDIATELY REVERT v15**
   - Do not deploy; do not use for any further experiments
   - It is a complete regression and non-functional

2. **Root Cause Investigation Priority Order**
   - Unit test the normalization stage in isolation
   - Unit test the Turtle formalization stage in isolation  
   - Verify keyword extraction still works (test v14 extraction -> v15 normalization pipeline)
   - Check for infinite loops in retry logic

3. **v16 Strategy**
   - Go back to v14 as baseline
   - Add ONE change at a time: first normalization, validate, then formalization
   - Never add multiple stages together

4. **Lessons Learned**
   - Adding new post-processing stages requires extensive validation before pipeline integration
   - Deterministic logic is safer than LLM reasoning but needs careful unit testing
   - 26% performance drop suggests broken core logic, not just tuning issue

### Alternative Paths Forward

If KG extraction is required:
- **Stick with v14**: It achieves 29.71% with keyword-guided extraction
- **Or try v12**: Original implementation achieved 23.78%, but may be simpler to debug
- **Skip v15/v16 efforts**: Re-examine whether deterministic post-processing is the right approach
