# kg_comprehensive_schema_minimal_turtle_v2 Findings

Date: 2026-05-11

## What Changed

- Added a new hierarchical pipeline: `kg_comprehensive_schema_minimal_turtle_v2`.
- Added helper component `app/services/components/kg_hierarchical_extraction_component.py` for:
  - schema top-level branch candidate extraction,
  - tolerant JSON parsing for staged LLM outputs,
  - normalization of branch presence and subtype outputs.
- Registered the new pipeline in `app/services/experiment_runner.py`.
- Added API contract tests for v2 success path and syntax-failure-safe behavior.

## Why Hierarchical Extraction Helps This Dataset

The `comprehensiveKgSchemaExtraction` and `comprehensiveKgSchemaMinimalExtraction` datasets can involve a large schema and many potential entity branches. One-shot prompting tends to:

- overload context with too many classes/relations,
- miss low-frequency subtypes,
- increase hallucination or partial graph output.

Hierarchical decomposition reduces complexity per call and improves focus:

1. Detect relevant top-level branches first.
2. Detect only subtypes within those branches.
3. Extract values/details subtype-by-subtype.
4. Assemble and normalize one final Turtle output for scoring.

This keeps each extraction step narrower and improves controllability of large-schema reconstruction.

## Stage-by-Stage Behavior

1. Presence/Scope detection
- Build branch candidates from the minimal input schema.
- Ask the LLM to return JSON with detected top-level branches.
- If stage JSON is missing/invalid, use deterministic fallback to first candidates.

2. Subtype identification
- For each detected branch, run a branch-focused subtype JSON extraction.
- Normalize and cap detected subtype lists (bounded loops).

3. Value/detail extraction
- For each detected branch/subtype pair, request Turtle-only extraction.
- If no subtype is found, run a branch-level fallback extraction.

4. Final assembly and scoring
- Merge extracted Turtle chunks with a dedicated assembly step.
- Parse predicted and expected Turtle and score with existing triple scorer.
- Preserve syntax-failure-safe behavior: invalid predicted Turtle yields zero metrics and `syntax_failure: true` instead of hard pipeline failure.

---

## ❌ Experiment Results (from Dashboard Snapshot: May 18, 2026)

### FAILURE: Zero Success on Comprehensive Schema Tasks

#### Performance on comprehensiveKgSchemaExtraction Dataset
| Metric | Value |
|--------|-------|
| **Total Runs** | 13 |
| **Successful Matches** | 0 |
| **Success Rate** | **0.00%** ❌ |
| **Total Tokens Consumed** | 3,799,484 |
| **Avg Tokens per Run** | 292,268 |
| **LLM Used** | localai:gemma-3-27b-it |
| **Status** | IN PROGRESS |

#### Performance on comprehensiveKgSchemaMinimalExtraction Dataset
| Metric | Value |
|--------|-------|
| **Total Runs** | 73 |
| **Successful Matches** | 0 |
| **Success Rate** | **0.00%** ❌ |
| **Total Tokens Consumed** | 27,374,821 |
| **Avg Tokens per Run** | 374,998 |
| **LLM Used** | localai:gemma-3-27b-it |
| **Status** | IN PROGRESS |

#### Sample Failed Run (Typical Pattern)
- **System**: D2.1 - Brandschutzkitt intumeszierend
- **Expected**: 584 triples with 22 locations, 2 cables, etc.
- **Extracted**: 17 triples with minimal structure
- **F1 Score**: 0.0 (precision: 0%, recall: 0%)
- **Duration**: 63.70 seconds
- **Tokens**: 93,040 (1.4MB of context!)
- **Syntax Failure**: No, but prediction is meaningless

### Critical Issues

**v2 is completely non-functional for comprehensive KG extraction:**

1. **Massively Over-Tokenized**
   - v2: 292K-375K tokens per run (enormous!)
   - Expected budget: ~10-50K tokens
   - **Root cause**: Hierarchical decomposition is spawning too many LLM calls

2. **Zero Extraction Success**
   - Not a single correct triple across 86 runs
   - Hierarchical branching is collapsing all attempts
   - LLM cannot handle the decomposed hierarchy instructions

3. **Schema Too Complex**
   - Comprehensive schema has 30K+ triples in some cases
   - Hierarchical decomposition still cannot cope
   - Design premise is flawed for this problem scale

4. **Token Inflation Without Benefit**
   - v1 also failed (0%) but at least used reasonable tokens
   - v2 makes the problem worse by 100x token consumption
   - Suggests nested LLM loops without proper error handling

### Comparison to v1 (Previous Failure)

| Metric | v1 | v2 | Delta |
|--------|-----|-----|-------|
| Success Rate | 0% | 0% | No improvement |
| Avg Tokens/Run | ~24K | ~292K | **+1133%** 🔴 |
| Dataset | Same | Same | - |
| Status | DONE | IN PROGRESS | - |

**Conclusion**: v2 is strictly worse than v1 while maintaining 0% success rate.

### Root Cause Analysis

**Hierarchical decomposition fundamentally breaks down at scale:**

1. **Stage 1 Failure**: Branch detection doesn't align with actual schema structure
2. **Stage 2 Failure**: Subtype identification gets confused by the nested instructions
3. **Stage 3 Failure**: Each subtype extraction is independent, missing relationships
4. **Stage 4 Failure**: Assembly can't reconstruct meaningful RDF from fragments

**The design assumes LLM can reliably execute complex hierarchical reasoning.** It cannot.

### Why This Approach Failed

- **Multi-stage prompting is unreliable**: Errors compound across stages
- **LLMs struggle with schema reasoning**: Too abstract for token-based completion
- **Comprehensiveness contradicts zero-shot**: Can't learn schema from documents alone
- **RDF/Turtle is not LLM-native**: Trying to force symbolic output from statistical model

### Recommendations - ABANDON COMPREHENSIVE KG APPROACH

1. **STOP v2/v3/v4 development immediately**
   - All comprehensive schema approaches are failing
   - Investment has negative ROI

2. **Revisit the Problem**
   - Is fully-automatic comprehensive KG extraction realistic?
   - Could hybrid human-in-the-loop be better?
   - Should we target subset schemas instead?

3. **Alternative Approaches**
   - Focus on specific entity extraction (cables, pipes, rules) rather than complete schema
   - Use v12-v14 keyword-guided approach for targeted extraction
   - Consider knowledge graph completion/link prediction instead of generation

4. **Deprioritize in Roadmap**
   - Move KG extraction work to backlog
   - Allocate resources to improving text/multimodal extraction (v9, v22 etc.)
   - Shelve "comprehensive schema" until better algorithms are available

## Compatibility Notes

- API contract shape is unchanged (`ExperimentRequest`/`ExperimentResponse` compatible).
- New pipeline name/version: `kg_comprehensive_schema_minimal_turtle_v2`.
- Intended primary fit:
  - `comprehensiveKgSchemaMinimalExtraction`
  - `comprehensiveKgSchemaExtraction`
- Also usable as secondary fit for `comprehensiveKgExtraction` when schema-guided reconstruction is desired.
