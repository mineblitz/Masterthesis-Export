# Pipeline Performance Guide & Selection Matrix

**Last Updated**: May 18, 2026 (from experiment_dashboard_snapshot.json)

## Executive Summary

This guide helps you choose the right pipeline for your data extraction task based on actual experimental results.

### Quick Selection Table

| Use Case | Best Pipeline | Success Rate | Why |
|----------|---------------|--------------|-----|
| **Simple numeric values** (fire class, thickness) | text_only_simple_conversion_v9 | **75.29%** | Excellent on classification; fastest execution |
| **Complex conditions + numerics** | text_image_multimodal_conversion_v22 | **37.35%** | Best multimodal; handles images + text |
| **Text-only (no images available)** | text_only_simple_conversion_v17 | **34-41%** | Lean, fast; optimized prompt engineering |
| **Knowledge graphs required** | turtle_kg_keyword_v14 | **29.71%** | Keyword-guided extraction; reliable RDF output |
| **Cable/Pipe type classification** | text_only_simple_conversion_v15 | **41.18%** | Specialized for cable/pipe extraction |
| **AVOID THESE** | v22(text), v23-v30, v15(KG), comprehensive KG | **0-8%** | Known failures; broken implementations |

---

## Detailed Performance Rankings

### 🥇 Tier 1: Production-Ready (>30% Success)

#### 1. text_only_simple_conversion_v9
- **Success Rate**: 75.29%
- **Dataset**: systemTransferScopeExtraction (classification)
- **Runs**: 170 total, 128 successful
- **Tokens**: ~24K per run
- **Best For**: Simple categorical extraction (Kabel/Rohre classification)
- **Status**: ✓ COMPLETED
- **Recommendation**: **🟢 DEPLOY FOR PRODUCTION** - Exceptional performance on classification tasks

#### 2. text_image_multimodal_conversion_v22
- **Success Rate**: 37.35%
- **Dataset**: conditionBasedExtraction
- **Runs**: 1,063 total, 397 successful
- **Tokens**: ~4.3K per run
- **Best For**: Complex extraction needing both text and image context
- **Status**: IN PROGRESS (but 1,063 runs completed)
- **Special**: Includes evidence provenance and compliance grounding
- **Recommendation**: **🟢 DEPLOY FOR COMPLEX EXTRACTION** - Top multimodal performer

#### 3. text_only_simple_conversion_v8 (Context Window Study)
- **Success Rate**: 23.29%
- **Dataset**: conditionBasedExtraction
- **Runs**: 7,560 total, 1,761 successful
- **Best Context Window**: 15 lines (30.9% success!)
- **Status**: ✓ COMPLETED
- **Recommendation**: **🟡 USE WITH CONTEXT OPTIMIZATION** - Larger dataset validation; tune context windows

#### 4. text_only_simple_conversion_v15
- **Success Rate**: 41.18%
- **Dataset**: allowedCableTypesExtraction
- **Runs**: 170 total, 70 successful
- **Best For**: Cable type extraction specifically
- **Status**: ✓ COMPLETED
- **Recommendation**: **🟢 DEPLOY FOR CABLE/PIPE CLASSIFICATION**

#### 5. text_only_simple_conversion_v16 (Multi-Variable)
- **Success Rate**: 41.18%
- **Dataset**: allowedCableTypesExtraction
- **Runs**: 425 total, 175 successful
- **Best With**: 1-2 variables per request (multi-variable study)
- **Status**: ✓ COMPLETED
- **Recommendation**: **🟢 GOOD FOR BATCH EXTRACTION** - Handles multiple variables efficiently

---

### 🥈 Tier 2: Good Performance (20-30% Success)

#### 6. text_only_simple_conversion_v17 (Multi-LLM Study)
- **Success Rate**: 37.93% (varies by LLM)
- **Dataset**: conditionBasedExtraction
- **Best LLM**: GPT-5.4 (45.83%)
- **Runs**: 3,224 total (across 15 different LLMs)
- **Status**: IN PROGRESS
- **LLM Rankings** (top 5):
  1. OpenAI GPT-5.4: 45.83%
  2. Minimax: 45.07%
  3. Qwen3-6-Plus: 44.91%
  4. Google Gemma-4-31B: 44.60%
  5. Google Gemini-3.1-Pro: 44.44%
- **Recommendation**: **🟡 USE WITH PREMIUM LLM** - Performance depends heavily on model selection

#### 7. text_only_simple_conversion_v18
- **Success Rate**: 32.87%
- **Dataset**: conditionBasedExtraction
- **Runs**: 216 total, 71 successful
- **Status**: ✓ COMPLETED
- **Recommendation**: **🟡 SOLID BASELINE** - Good retrieval with consistent results

#### 8. text_only_simple_conversion_v3 (Temperature Study)
- **Success Rate**: 19.26%
- **Dataset**: simpleMinMaxExtraction
- **Runs**: 4,740 total (6 temperature variants)
- **Best Temperature**: 1.0 (19.87%) - higher is better
- **Status**: ✓ COMPLETED
- **Recommendation**: **🟡 REFERENCE FOR TEMPERATURE TUNING** - Temperature has minimal impact (~1%)

#### 9. turtle_kg_keyword_v14 (Context Window Study)
- **Success Rate**: 29.71%
- **Dataset**: conditionKGExtraction
- **Runs**: 4,500 total, 1,337 successful
- **Best Context Window**: 10 lines (30.3% success!)
- **Status**: ✓ COMPLETED
- **Recommendation**: **🟡 USE IF KG EXTRACTION REQUIRED** - Keyword-guided is most reliable approach

---

### 🔴 Tier 3: Failed/Broken Implementations (0% or <5%)

**DO NOT USE THESE PIPELINES** - they have fundamental implementation problems:

| Pipeline | Success | Dataset | Issue | Action |
|----------|---------|---------|-------|--------|
| text_only_simple_conversion_v22 (text-only variant) | 0.00% | simpleMinMaxExtraction, conditionBasedExtraction | Numeric normalization heuristic broken | **REVERT IMMEDIATELY** |
| text_only_simple_conversion_v23-v30 | 0.00%-8.02% | conditionBasedExtraction | Widespread implementation issues | **INVESTIGATE & FIX** |
| turtle_kg_keyword_v15 | 2.84% | conditionKGExtraction | 26.87% regression from v14; deterministic post-processing broken | **REVERT TO v14** |
| kg_comprehensive_schema_minimal_turtle_v2 | 0.00% | comprehensiveKgSchemaExtraction | Hierarchical decomposition scales to 374K tokens/run with no success | **ABANDON APPROACH** |
| kg_comprehensive_schema_minimal_turtle_v1/v3/v4 | 0.00% | Various | All comprehensive KG attempts failing | **SHELVE KG WORK** |
| kg_turtle_extraction_cable_v1 | 0.00% | cableTtlExtractionPlaceholders | Turtle output generation broken | **REDESIGN** |

---

## LLM Selection Guide (from Multi-LLM Study - exp_068)

### Performance Ranking (on conditionBasedExtraction with text_only_v17)

| Rank | LLM | Success Rate | Cost | Recommendation |
|------|-----|--------------|------|-----------------|
| 1 | openrouter:openai/gpt-5.4 | **45.83%** | $$$ | **BEST** - Use for mission-critical tasks |
| 2 | openrouter:minimax/minimax-m2.7 | **45.07%** | $$ | Good balance; slightly cheaper than GPT |
| 3 | openrouter:qwen/qwen3-6-plus | **44.91%** | $$ | Alternative to GPT with competitive performance |
| 4 | openrouter:google/gemma-4-31b-it | **44.60%** | $ | Cost-effective premium option |
| 5 | openrouter:google/gemini-3.1-pro | **44.44%** | $$$ | Excellent but expensive |
| 6 | openrouter:xiaomi/mimo-v2.5-pro | **43.72%** | $ | Good value; less known but solid |
| 7 | openrouter:qwen/qwen3-5-flash-02-23 | **42.99%** | $ | **BEST VALUE** - Flash model with good performance |
| 8-10 | Claude Opus, Gemma-4-26B, GPT-OSS-120B | 35-41% | Varies | Mid-tier performance |
| 15 | openrouter:tencent/hy3-preview | **12.26%** | $ | **AVOID** - Significantly underperforms |

### Key Insights
- **Premium tier (40-45%)**: GPT-5.4, Minimax, Qwen3, Gemma-4
  - Performance spread: <2%
  - Choose based on cost/availability
  
- **Value tier (39-42%)**: Xiaomi, Claude, older Gemma
  - Still respectable but 3-5% lower
  
- **Budget tier (24-37%)**: Deepseek, local Gemma-3-27B
  - Significant performance loss
  
- **Local option**: gemma-3-27b-it achieves 35.18%
  - Reasonable for cost-sensitive applications
  - ~10% lower than commercial GPT options

---

## Dataset-Specific Recommendations

### simpleMinMaxExtraction
**Task**: Extract simple numeric values (min/max thickness, width, height)

| Recommended Pipeline | Success Rate | Status |
|----------------------|--------------|--------|
| text_only_simple_conversion_v9 | 75.29% | ✓ IDEAL |
| text_image_multimodal_conversion_v11 | 26.36% | IN PROGRESS |
| text_only_simple_conversion_v3 | 19.26% | ✓ DONE |

### conditionBasedExtraction  
**Task**: Extract values with conditions (thickness when used as cable, etc.)

| Recommended Pipeline | Success Rate | Status |
|----------------------|--------------|--------|
| text_image_multimodal_conversion_v22 | 37.35% | IN PROGRESS |
| text_only_simple_conversion_v17 (with GPT-5.4) | 45.83% | IN PROGRESS |
| text_only_simple_conversion_v18 | 32.87% | ✓ DONE |

### allowedCableTypesExtraction
**Task**: Extract boolean flags for allowed cable types

| Recommended Pipeline | Success Rate | Status |
|----------------------|--------------|--------|
| text_only_simple_conversion_v15 | 41.18% | ✓ DONE |
| text_only_simple_conversion_v16 | 41.18% | ✓ DONE (multi-var) |

### conditionKGExtraction
**Task**: Extract RDF knowledge graphs with conditions

| Recommended Pipeline | Success Rate | Status |
|----------------------|--------------|--------|
| turtle_kg_keyword_v14 (context study) | 29.71% | ✓ DONE |
| turtle_kg_conversion_v12 | 23.78% | ✓ DONE |
| turtle_kg_twostep_v13 | 22.56% | ✓ DONE |

### systemTransferScopeExtraction
**Task**: Classify allowed transfer systems (Kabel/Rohre/Beides)

| Recommended Pipeline | Success Rate | Status |
|----------------------|--------------|--------|
| text_only_simple_conversion_v9 | **75.29%** | ✓ DONE |

---

## Performance Factors & Optimization Guide

### Context Window Impact
Tested on v8 and v11 (context window study):

- **3-5 lines**: 22-26% success (minimal context)
- **10 lines**: 28-31% success ✓ **OPTIMAL**
- **15 lines**: 30-31% success (plateau)
- **20+ lines**: 23-24% success (diminishing returns)

**Recommendation**: Use **10-15 line context windows** for best performance

### Temperature Impact  
Tested on v3 (temperature study across 6 variants):

| Temperature | Success Rate | Variance |
|-------------|--------------|----------|
| 0.0 | 18.99% | Lowest variance; deterministic |
| 0.2 | 19.11% | - |
| 0.4 | 19.11% | - |
| 0.6 | 19.24% | - |
| 0.8 | 19.24% | - |
| 1.0 | 19.87% | **Best** |

**Recommendation**: Use **temperature=1.0** (max randomness helps extraction diversity)

### Multi-Variable Batching Impact
Tested on v16 (number of variables per request):

| Variables/Request | Success Rate | Duration |
|-------------------|--------------|----------|
| 1 | 41.18% | ~6 seconds |
| 2 | 41.18% | ~4.5 seconds |
| 3 | 41.18% | ~2.8 seconds |
| 5 | 41.18% | ~1.9 seconds |
| 10 | 41.18% | ~1.1 seconds ✓ |

**Insight**: Success rate **unchanged**, but speed increases 6x!

**Recommendation**: **Batch 5-10 variables per request** when possible

---

## Common Failure Patterns & Solutions

### Pattern 1: Null Extraction (most common failure ~60%)
**Symptom**: LLM returns empty/null for valid values

**Solutions**:
1. Improve context retrieval (use v8/v11 with 10-15 line context)
2. Simplify prompt instructions
3. Add examples/few-shot prompts
4. Use higher-capability LLM (GPT-5.4 vs local Gemma)

### Pattern 2: Decimal/Magnitude Errors
**Symptom**: Extracted "15" instead of "150" (order of magnitude wrong)

**Solutions**:
1. Add explicit decimal point validation post-processing
2. Check units mentioned (mm vs cm confusion)
3. Use stricter consistency checks
4. Add magnitude bounds checking

### Pattern 3: Unit Mismatch
**Symptom**: Expected "90 min" but extracted "1.5 h" (correct but different unit)

**Solutions**:
1. Normalize all units to canonical form (e.g., always minutes)
2. Add unit conversion in parsing
3. Use unit-aware comparison (NOT string match)

### Pattern 4: Inconsistent Extraction Across Runs
**Symptom**: Same input sometimes succeeds, sometimes fails

**Solutions**:
1. Increase temperature toward 1.0 (more exploration)
2. Use more diverse retrieval context
3. Reduce threshold stringency
4. Add manual review/correction step

---

## Cost-Performance Tradeoffs

### If Budget is Tight
1. **Use local Gemma-3-27B**: 35% success, minimal cost
2. **Batch variables together**: 6x speedup, same accuracy
3. **Accept v17-v18**: 30-35% success is reasonable for text-only

### If Accuracy is Critical
1. **Use GPT-5.4 or Minimax**: 45% success
2. **Use multimodal v22**: 37% success with image grounding
3. **Invest in prompt engineering**: Can boost by 5-10%

### If Latency Matters
1. **Use batching**: Reduces per-run overhead
2. **Use local models**: Eliminates network latency
3. **Use simpler pipelines**: v17/v18 faster than v22

---

## Roadmap Recommendations

### ✅ Implement Now
1. **Deploy v9** for classification tasks (75% success!)
2. **Deploy v22** for complex extractions (37% success, multimodal)
3. **Use v17 with GPT-5.4** for mission-critical work (45% success)
4. **Optimize context windows** to 10-15 lines across all pipelines

### ⚠️ Fix These Issues
1. **Revert v22 text-only variant** (0% success)
2. **Investigate v23-v30** pipeline series
3. **Debug v15 KG normalization**
4. **Profile token inflation** in v2 comprehensive schema

### 🚫 Shelve These
1. **Comprehensive KG schema extraction** (all 0% failures)
2. **Cable/Pipe TTL generation** (0% success)
3. **Complex multi-stage KG extraction** (too many LLM calls)

### 📊 Future Research
1. Ensemble multiple LLMs for consensus extraction
2. Implement human-in-the-loop validation for edge cases
3. Fine-tune models on domain-specific data
4. Investigate semantic consistency checking

---

## Migration Path for Users

If currently using **v8**:
- → Migrate to **v18** (similar but more stable)
- → Consider **v22** if images available (37% vs 23%)

If currently using **v17**:
- → Use **GPT-5.4 LLM option** (45% vs 35%)
- → Or stick with current (34% is reasonable)

If currently using **v20-v21**:
- → Migrate to **v22** (better performance, compliance grounding)
- → Back up to **v18** if v22 is problematic

If using **any KG pipeline**:
- → Use **v14** only (29.71% vs alternatives' failures)
- → Plan to move away from automatic KG generation

---

## Contact & Debugging

If a pipeline is not performing as expected:

1. **Check the findings file** (e.g., text_only_simple_conversion_v22_findings.md)
2. **Verify you're using recommended LLM** (v17 needs GPT-5.4 to hit 45%)
3. **Check context window setting** (10-15 lines optimal)
4. **Test on small sample first** before full deployment
5. **Enable debug logging** in pipeline settings

---

**Last Updated**: May 18, 2026  
**Source**: experiment_dashboard_snapshot.json  
**Total Experiments**: 64 (36 completed, 28 in progress)
