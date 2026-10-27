# text_only_simple_conversion_v22 - Technical Research and Findings

## Problem statement
The first unfinished detailed finding in experiment_analysis_and_improvement_plan.md identifies a retrieval and matching gap for text-only scalar extraction on simpleMinMaxExtraction: fire-class values and units appear in many paraphrased forms (for example EI 90, REI 90, F90, 90 min, 1.5 h), while existing retrieval and comparison behavior was mostly surface-form based.

## Why this first unfinished finding was selected
Section 1 is the first unfinished detailed finding and explicitly recommends v22 with two concrete changes:
1. Domain-specific query expansion for fire-class and unit synonyms.
2. Numeric normalization before final comparison and evidence handling.

This implementation directly targets those two items using the strongest available lineage (v21 text-only retrieval pipeline).

## What was changed
- Added new retrieval component: app/services/components/retrieval_enhancer_v22_text.py
  - Extends v21 query variant generation with fire-domain expansions (EI/REI/F class forms, minute and hour forms).
  - Adds normalization helper for fire-resistance numeric values (hour-to-minute conversion where appropriate).
  - Recomputes consistency/conflict signals on normalized numeric candidates.
- Added new pipeline: app/services/pipelines/text_only_simple_conversion_v22.py
  - v21-derived flow with v22 retrieval enhancer.
  - Applies numeric normalization to parsed LLM candidates before consistency gating.
  - Applies numeric normalization to numeric expected value before final match evaluation.
- Registered v22 dispatch in app/services/experiment_runner.py.
- Added tests in tests/test_retrieval_enhancer_v22.py for:
  - Fire-domain query expansion terms.
  - Numeric normalization conversion (1.5 h -> 90 min equivalent scalar).

## Expected benefits
- Better retrieval recall for fire-resistance class variables when documents use alternative standard notations.
- Fewer false negatives caused by unit representation mismatches (hours vs minutes).
- More stable evidence consistency checks because numeric candidate conflicts are evaluated in canonical form.

## Known risks
- Hour-to-minute normalization heuristic for low numeric values may be over-aggressive for non-fire variables if incorrectly classified.
- Additional query variants can increase retrieval breadth and potentially add noise if query_limit is too high.
- Existing thresholds were not retuned in this change; normalization may shift observed consistency and retry behavior.

## Recommended next experiments
1. Run text_only_simple_conversion_v22 on simpleMinMaxExtraction with gemma-4 and compare against v21 on success and correctness.
2. Break out analysis by variable family (fire class vs thickness/width) to validate normalization impact.
3. Tune query_expansion_limit and evidence_consistency_threshold on a small validation split.
4. Run v22 on conditionBasedExtraction as a transfer check for side effects on conditional retrieval behavior.

---

## ⚠️ Experiment Results (from Dashboard Snapshot: May 18, 2026)

### CRITICAL FINDING: v22 Shows 0% Success Rate

#### Performance on simpleMinMaxExtraction Dataset
| Metric | Value |
|--------|-------|
| **Total Runs** | 786 |
| **Successful Matches** | 0 |
| **Success Rate** | **0.00%** ❌ |
| **Total Tokens Consumed** | 7,920,666 |
| **Avg Tokens per Run** | 10,077 |
| **LLM Used** | localai:gemma-3-27b-it |
| **Status** | IN PROGRESS |

#### Performance on conditionBasedExtraction Dataset
| Metric | Value |
|--------|-------|
| **Total Runs** | 1,074 |
| **Successful Matches** | 0 |
| **Success Rate** | **0.00%** ❌ |
| **Total Tokens Consumed** | 10,360,710 |
| **Avg Tokens per Run** | 9,647 |
| **LLM Used** | localai:gemma-3-27b-it |
| **Status** | IN PROGRESS |

### Sample Failed Run
- **System**: Brandschutzkitt intumeszierend (D2.1)
- **Dataset**: simpleMinMaxExtraction
- **Value**: fire_resistance_class
- **Expected**: 90.0 → **Extracted**: null ❌
- **Duration**: 11.66 seconds
- **Tokens**: 10,143
- **Tokens per Run**: Increased ~2.2x vs v21 (was 4.5K, now 10K)

### Root Cause Analysis

**The pipeline is completely non-functional.** Possible causes:
1. **Normalization logic error**: The numeric normalization heuristic may be incorrectly rejecting all comparisons (too-strict consistency gate)
2. **Query expansion interference**: Fire-domain expansions may be over-polluting the query space
3. **Integration bug**: Retrieval enhancer v22 may not be properly integrated in the pipeline
4. **LLM instruction failure**: Changes to the prompt or parsing may be causing extraction to always return null

### Tokens Tell the Story
- **v21 (working)**: ~4.5K tokens/run
- **v22 (broken)**: ~10K tokens/run (2.2x increase)
- **Interpretation**: v22 is doing MORE work (likely more LLM calls due to retries or larger contexts) but NEVER extracting successfully

### Recommendations
1. **REVERT v22 immediately** - it is completely broken
2. **Investigate in order**:
   - Check if pipeline registration is correct in experiment_runner.py
   - Check if retrieval_enhancer_v22 methods are being called
   - Validate the numeric normalization heuristic with unit tests
   - Check if the consistency gate is too aggressive (test with threshold=0.0)
3. **Next attempt (v23)**: 
   - Start fresh with simpler changes (e.g., just query expansion WITHOUT normalization)
   - Add extensive logging to understand where extraction fails
   - Validate on small sample set before full experiment run

### Lessons Learned
- **Automated numeric normalization is dangerous**: Domain-specific heuristics can silently break if not thoroughly tested
- **Token count inflation is a red flag**: 2.2x increase with 0% success indicates algorithmic breakdown, not just inefficiency
- **Integration testing critical**: A new retrieval component must be validated in isolation before pipeline integration
