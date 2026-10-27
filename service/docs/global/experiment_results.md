# Experiment Results Summary (as of May 18, 2026)

## Overview
- **Total Experiments**: 64
- **Snapshot Generated**: 2026-05-18T10:39:43.695451+00:00
- **Completed Runs**: 36 fully completed experiments
- **In Progress**: 28 experiments still running or pending

---

## Pipeline Performance Comparison

### Text-Only Simple Conversion Pipelines

| Pipeline | Dataset | LLM | Success Rate | Runs | Successful | Total Tokens | Status |
|----------|---------|-----|--------------|------|-----------|--------------|--------|
| text_only_simple_conversion | simpleMinMaxExtraction | localai:gemma-3-27b-it | 16.46% | 158 | 26 | 3,879,501 | ✓ DONE |
| text_only_simple_conversion_v2 | simpleMinMaxExtraction | localai:gemma-3-27b-it | 18.48% | 790 | 146 | 19,986,364 | ✓ DONE |
| text_only_simple_conversion_v3 | simpleMinMaxExtraction | localai:gemma-3-27b-it | 19.13% | 790 | 151 | 18,124,553 | ✓ DONE |
| text_only_simple_conversion_v3 (Temperature Study) | simpleMinMaxExtraction | localai:gemma-3-27b-it | 19.26% | 4,740 | 913 | 108,735,948 | ✓ DONE |
| run_text_only_simple_conversion_v4 | conditionBasedExtraction | localai:gemma-3-27b-it | 11.11% | 216 | 24 | 3,533,031 | ✓ DONE |
| text_only_simple_conversion_v5 | conditionBasedExtraction | localai:gemma-3-27b-it | 12.96% | 216 | 28 | 3,551,312 | ✓ DONE |
| text_only_simple_conversion_v5 (1080 runs) | conditionBasedExtraction | localai:gemma-3-27b-it | 12.50% | 1,080 | 135 | 17,752,219 | ✓ DONE |
| text_only_simple_conversion_v6 | conditionBasedExtraction | localai:gemma-3-27b-it | 12.31% | 1,080 | 133 | 27,192,657 | ✓ DONE |
| text_only_simple_conversion_v8 (Context Window Study) | conditionBasedExtraction | localai:gemma-3-27b-it | 23.29% | 7,560 | 1,761 | 41,112,159 | ✓ DONE |
| text_only_simple_conversion_v8 | conditionBasedExtraction | openrouter:google/gemma-4-26b-a4b-it | 28.43% | 3,226 | 917 | 19,753,864 | IN PROGRESS |
| text_only_simple_conversion_v8 | simpleMinMaxExtraction | openrouter:google/gemma-4-26b-a4b-it | 24.39% | 2,362 | 576 | 15,562,130 | IN PROGRESS |
| text_only_simple_conversion_v10 (Context Window Study) | conditionBasedExtraction | localai:gemma-3-27b-it | 15.87% | 7,560 | 1,200 | 84,524,686 | ✓ DONE |
| text_only_simple_conversion_v9 | systemTransferScopeExtraction | localai:gemma-3-27b-it | 75.29% | 170 | 128 | 3,970,899 | ✓ DONE |
| text_only_simple_conversion_v7 | conditionBasedExtraction | localai:gemma-3-27b-it | 11.96% | 920 | 110 | 15,876,218 | IN PROGRESS |
| text_only_simple_conversion_v15 | allowedCableTypesExtraction | localai:gemma-3-27b-it | 41.18% | 170 | 70 | 3,968,476 | ✓ DONE |
| text_only_simple_conversion_v15 | allowedPipeTypesExtraction | localai:gemma-3-27b-it | 11.18% | 170 | 19 | 3,987,777 | ✓ DONE |
| text_only_simple_conversion_v16 (Multi-var) | allowedCableTypesExtraction | localai:gemma-3-27b-it | 41.18% | 425 | 175 | 39,573,338 | ✓ DONE |
| text_only_simple_conversion_v16 (Multi-var) | allowedPipeTypesExtraction | localai:gemma-3-27b-it | 10.35% | 425 | 44 | 75,192,590 | ✓ DONE |
| text_only_simple_conversion_v17 | simpleMinMaxExtraction | localai:gemma-3-27b-it | 21.52% | 158 | 34 | 417,037 | ✓ DONE |
| text_only_simple_conversion_v17 | conditionBasedExtraction | localai:gemma-3-27b-it | 34.26% | 216 | 74 | 533,449 | ✓ DONE |
| text_only_simple_conversion_v17 (LLM Study) | conditionBasedExtraction | Multiple LLMs | 37.93% | 3,224 | 1,223 | 14,296,345 | IN PROGRESS |
| text_only_simple_conversion_v18 | conditionBasedExtraction | localai:gemma-3-27b-it | 32.87% | 216 | 71 | 724,261 | ✓ DONE |
| text_only_simple_conversion_v18 | simpleMinMaxExtraction | localai:gemma-3-27b-it | 23.73% | 177 | 42 | 609,676 | IN PROGRESS |
| text_only_simple_conversion_v22 | simpleMinMaxExtraction | localai:gemma-3-27b-it | 0.00% | 786 | 0 | 7,920,666 | IN PROGRESS |
| text_only_simple_conversion_v22 | conditionBasedExtraction | localai:gemma-3-27b-it | 0.00% | 1,074 | 0 | 10,360,710 | IN PROGRESS |
| text_only_simple_conversion_v23 | conditionBasedExtraction | localai:gemma-3-27b-it | 0.00% | 1,075 | 0 | 10,301,668 | IN PROGRESS |
| text_only_simple_conversion_v24 | conditionBasedExtraction | localai:gemma-3-27b-it | 5.86% | 1,075 | 63 | 10,306,344 | IN PROGRESS |
| text_only_simple_conversion_v25 | conditionBasedExtraction | localai:gemma-3-27b-it | 7.37% | 1,072 | 79 | 10,363,808 | IN PROGRESS |
| text_only_simple_conversion_v26 | conditionBasedExtraction | localai:gemma-3-27b-it | 7.91% | 1,074 | 85 | 10,388,241 | IN PROGRESS |
| text_only_simple_conversion_v27 | conditionBasedExtraction | localai:gemma-3-27b-it | 8.02% | 1,072 | 86 | 11,070,009 | IN PROGRESS |
| text_only_simple_conversion_v28 | conditionBasedExtraction | localai:gemma-3-27b-it | 16.57% | 1,080 | 179 | 0 | ✓ DONE |
| text_only_simple_conversion_v29 | conditionBasedExtraction | localai:gemma-3-27b-it | 0.00% | 1,076 | 0 | 11,592,972 | IN PROGRESS |
| text_only_simple_conversion_v30 | conditionBasedExtraction | localai:gemma-3-27b-it | 0.00% | 1,074 | 0 | 11,741,856 | IN PROGRESS |

### Multimodal Conversion Pipelines (Text + Image)

| Pipeline | Dataset | LLM | Success Rate | Runs | Successful | Status |
|----------|---------|-----|--------------|------|-----------|--------|
| text_image_multimodal_conversion_v11 | conditionBasedExtraction | openrouter:google/gemma-4-26b-a4b-it | 37.96% | 216 | 82 | ✓ DONE |
| text_image_multimodal_conversion_v19 | conditionBasedExtraction | openrouter:google/gemma-4-26b-a4b-it | 36.19% | 210 | 76 | IN PROGRESS |
| text_image_multimodal_conversion_v21 | conditionBasedExtraction | openrouter:google/gemma-4-26b-a4b-it | 35.71% | 210 | 75 | IN PROGRESS |
| text_image_multimodal_conversion_v11 | simpleMinMaxExtraction | openrouter:google/gemma-4-26b-a4b-it | 26.36% | 774 | 204 | IN PROGRESS |
| text_image_multimodal_conversion_v19 | simpleMinMaxExtraction | openrouter:google/gemma-4-26b-a4b-it | 26.14% | 788 | 206 | IN PROGRESS |
| text_image_multimodal_conversion_v21 | simpleMinMaxExtraction | openrouter:google/gemma-4-26b-a4b-it | 26.21% | 782 | 205 | IN PROGRESS |
| text_image_multimodal_conversion_v22 | conditionBasedExtraction | openrouter:google/gemma-4-26b-a4b-it | 37.35% | 1,063 | 397 | IN PROGRESS |
| text_image_multimodal_conversion_v23 | conditionBasedExtraction | openrouter:google/gemma-4-26b-a4b-it | 8.99% | 1,079 | 97 | IN PROGRESS |

### Knowledge Graph (Turtle/RDF) Pipelines

| Pipeline | Dataset | LLM | Success Rate | Runs | Successful | Status |
|----------|---------|-----|--------------|------|-----------|--------|
| turtle_kg_conversion_v12 | conditionKGExtraction | localai:gemma-3-27b-it | 23.78% | 900 | 214 | ✓ DONE |
| turtle_kg_twostep_v13 | conditionKGExtraction | localai:gemma-3-27b-it | 22.56% | 900 | 203 | ✓ DONE |
| turtle_kg_keyword_v14 (Context Window Study) | conditionKGExtraction | localai:gemma-3-27b-it | 29.71% | 4,500 | 1,337 | ✓ DONE |
| turtle_kg_keyword_v15 | conditionKGExtraction | localai:gemma-3-27b-it | 2.84% | 4,500 | 128 | ✓ DONE |
| kg_turtle_extraction_cable_v1 | cableTtlExtractionPlaceholders | localai:gemma-3-27b-it | 0.00% | 45 | 0 | ✓ DONE |
| kg_turtle_extraction_cable_v1 | cableTtlExtractionNoValues | localai:gemma-3-27b-it | 0.00% | 45 | 0 | ✓ DONE |
| kg_turtle_extraction_cable_v1 | cableTtlExtractionNoValues | openrouter:google/gemma-4-26b-a4b-it | 0.00% | 34 | 0 | IN PROGRESS |
| kg_turtle_extraction_pipe_v1 | pipeTtlExtractionPlaceholders | localai:gemma-3-27b-it | 0.00% | 8 | 0 | IN PROGRESS |
| kg_turtle_extraction_pipe_v1 | pipeTtlExtractionNoValues | localai:gemma-3-27b-it | 0.00% | 5 | 0 | IN PROGRESS |
| kg_turtle_extraction_pipe_v1 | pipeTtlExtractionNoValues | openrouter:google/gemma-4-26b-a4b-it | 0.00% | 10 | 0 | IN PROGRESS |

### Comprehensive Schema Extraction (KG)

| Pipeline | Dataset | LLM | Success Rate | Runs | Successful | Status |
|----------|---------|-----|--------------|------|-----------|--------|
| kg_comprehensive_schema_minimal_turtle_v1 | comprehensiveKgSchemaExtraction | localai:gemma-3-27b-it | 0.00% | 17 | 0 | ✓ DONE |
| kg_comprehensive_schema_minimal_turtle_v1 | comprehensiveKgSchemaMinimalExtraction | localai:gemma-3-27b-it | 0.00% | 17 | 0 | ✓ DONE |
| kg_comprehensive_schema_minimal_turtle_v2 | comprehensiveKgSchemaExtraction | localai:gemma-3-27b-it | 0.00% | 13 | 0 | IN PROGRESS |
| kg_comprehensive_schema_minimal_turtle_v2 | comprehensiveKgSchemaMinimalExtraction | localai:gemma-3-27b-it | 0.00% | 73 | 0 | IN PROGRESS |
| kg_comprehensive_schema_minimal_turtle_v3 | comprehensiveKgSchemaMinimalExtraction | localai:gemma-3-27b-it | 0.00% | 77 | 0 | IN PROGRESS |
| kg_comprehensive_schema_minimal_turtle_v4 | comprehensiveKgSchemaMinimalExtraction | localai:gemma-3-27b-it | 0.00% | 72 | 0 | IN PROGRESS |

---

## Key Findings by Pipeline Category

### ✅ Best Performing Pipelines (>30% Success)
1. **text_only_simple_conversion_v9** - 75.29% on systemTransferScopeExtraction (simple classification task)
2. **text_only_simple_conversion_v15** - 41.18% on allowedCableTypesExtraction
3. **text_only_simple_conversion_v8 (Context Window Study)** - 23.29% on conditionBasedExtraction (7,560 runs!)
4. **text_only_simple_conversion_v16** - 41.18% on allowedCableTypesExtraction (multi-variable variant)
5. **turtle_kg_keyword_v14** - 29.71% on conditionKGExtraction (with context window study)

### ⚠️ Moderate Performing (15-25% Success)
- text_only_simple_conversion_v3 variants: 18-19%
- text_only_simple_conversion_v28: 16.57% (completed run with 1,080 samples)
- text_only_simple_conversion_v17: 21.52-34.26% depending on dataset/LLM

### ❌ Low/Failing Pipelines (<15% or 0%)
- text_only_simple_conversion_v22 through v30: Most are 0-8% with gemma-3-27b-it
- All comprehensive KG schema extraction variants: 0% success
- All cable/pipe TTL extraction variants: 0% success
- Knowledge graph pipelines (v12-v15): 2.84-29.71%

---

## LLM Performance Comparison (from exp_068 - Multi-LLM study)

| LLM | Success Rate | Runs | Successful |
|-----|--------------|------|-----------|
| openrouter:openai/gpt-5.4 | 45.83% | 216 | 99 |
| openrouter:minimax/minimax-m2.7 | 45.07% | 213 | 96 |
| openrouter:qwen/qwen3-6-plus | 44.91% | 216 | 97 |
| openrouter:google/gemma-4-31b-it | 44.60% | 213 | 95 |
| openrouter:google/gemini-3.1-pro-preview | 44.44% | 216 | 96 |
| openrouter:xiaomi/mimo-v2.5-pro | 43.72% | 215 | 94 |
| openrouter:qwen/qwen3-5-flash-02-23 | 42.99% | 214 | 92 |
| openrouter:anthropic/claude-opus-4.7 | 41.67% | 216 | 90 |
| openrouter:gemma-4-26b-a4b-it | 40.93% | 215 | 88 |
| openrouter:openai/gpt-oss-120b | 37.21% | 215 | 80 |
| localai:gemma-3-27b-it | 35.19% | 216 | 76 |
| openrouter:x-ai/grok-4.3 | 34.72% | 216 | 75 |
| openrouter:moonshotai/kimi-k2.6 | 30.70% | 215 | 66 |
| openrouter:deepseek/deepseek-v3.2 | 24.54% | 216 | 53 |
| openrouter:tencent/hy3-preview | 12.26% | 212 | 26 |

### Insights:
- **Proprietary models (GPT, Gemini, Claude)** consistently outperform open models
- **Multi-language models (Minimax, Qwen)** show competitive performance (44-45%)
- **Local Gemma-3 27B** achieves 35% - decent but lags proprietary options by 10-15%
- **Qwen3 Flash versions** offer better efficiency while maintaining 43% success rate
- **Deepseek V3** shows weakness (24.54%) on this text extraction task
- **Tencent HY3** significantly underperforms at 12.26%

---

## Completed Experiments (36 Total)

### Completed Datasets
- simpleMinMaxExtraction (6 experiments)
- conditionBasedExtraction (8 experiments)
- conditionKGExtraction (2 experiments)
- systemTransferScopeExtraction (1 experiment)
- allowedCableTypesExtraction (2 experiments)
- allowedPipeTypesExtraction (2 experiments)
- cableTtlExtractionPlaceholders (1 experiment)
- cableTtlExtractionNoValues (1 experiment)
- comprehensiveKgSchemaExtraction (1 experiment)
- comprehensiveKgSchemaMinimalExtraction (1 experiment)
- Other comprehensive schema variants (various)

---

## In Progress Experiments (28 Total)

These experiments are still running and have not yet completed:
- Various v8, v19, v21 multimodal variants
- v22-v30 text-only variants (most showing 0% success, likely failures)
- Comprehensive KG schema v3, v4
- Pipe TTL extraction variants

---

## Recommendations for Next Steps

1. **Prioritize high-performers**: Focus on v9, v15, v16 for production deployment
2. **Investigate v22-v30 failures**: These pipelines show 0% success - check for implementation issues
3. **Optimize LLM selection**: GPT-5.4 and Minimax show 45% success - consider for critical tasks
4. **Shelve comprehensive KG work**: All KG extraction variants failing - reconsider approach
5. **Context window optimization**: v8 and v11 show benefit from context window tuning - apply to other pipelines
6. **Resume multimodal variants**: v22 shows promise at 37.35% - continue refinement

---

## Metrics Definitions

- **Success Rate**: Percentage of runs where `is_match=true` (extracted value matches expected value)
- **Correctness %**: For complex outputs (e.g., JSON/boolean arrays), percentage of correct fields within matches
- **Total Tokens**: Cumulative LLM tokens consumed across all runs
- **Avg Tokens/Run**: Average tokens per individual extraction attempt
- **Status**: DONE = completed; IN PROGRESS = still running

