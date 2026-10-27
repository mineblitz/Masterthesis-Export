# Experiment Analysis and Improvement Plan

Generated: 2026-05-12
Source: `experiment_dashboard_snapshot.json` (44 experiments total)

---

## Summary Table — All Experiments

| Rank | Finding / Improvement | Impact | Effort | Blocking? | Status |
|---|---|---|---|---|---|
| 1 | Run v20/v21 on `simpleMinMaxExtraction` + `conditionBasedExtraction` with gemma-4 | High | Low | No | Offen |
| 2 | Resolve v18 consistency-gating regression with adaptive consistency in v24 | High | Low | No | Umgesetzt (2026-05-12) |
| 3 | Build `text_only_simple_conversion_v22` (completed) and continue with v23-v28 evaluation track | High | Medium | No | Umgesetzt (2026-05-12; erweitert bis v28) |
| 4 | Diagnose KG Turtle record extraction universal 0% failure (cable_v1 / pipe_v1) | High | Low | Blocks all KG record pipelines | Offen |
| 5 | Investigate multimodal v19/v21 regression vs v11 baseline | Medium | Low | Blocks multimodal lineage | Offen |
| 6 | Build `turtle_kg_keyword_v15` with staged Extract -> Normalize -> Formalize for Turtle-KG compliance mapping | Medium | Medium | Depends on #4 | Umgesetzt (2026-05-12) |
| 7 | Fix pipe-type classification (v15/v16 pipe success 10-11%) | Medium | Medium | No | Offen |
| 8 | Run v9 with gemma-4 on `systemTransferScopeExtraction` | Low | Low | No | Offen |
| 9 | Diagnose and fix comprehensive KG schema extraction (v1/v2 both 0%) | Medium | High | Depends on #4 | Offen |
| 10 | Implement compliance-routing prefilter from literature mapping section 7 finding 1 | Medium | Medium | No | Umgesetzt (2026-05-12, `text_only_simple_conversion_v25`) |
| 11 | Implement v5-style structured extraction hardening from literature mapping section 7 finding 2 (clause typing + verifier) | Medium | Medium | No | Umgesetzt (2026-05-12, `text_only_simple_conversion_v26`) |
| 12 | Implement KG record/comprehensive KG lineage hardening from literature mapping section 7 (schema extension + canonicalization) | Medium | Medium | No | Umgesetzt (2026-05-12, `kg_comprehensive_schema_minimal_turtle_v3`) |
| 13 | Implement multimodal/hybrid compliance lineage from literature mapping section 7 (grounded violation-report scaffold) | Medium | Medium | No | Umgesetzt (2026-05-12, `text_image_multimodal_conversion_v22`) |
| 14 | Add rule-class-aware extraction profiles (from BIM rule taxonomy literature) | Medium | Medium | No | Umgesetzt (2026-05-14, `text_only_simple_conversion_v27`) |
| 15 | Build regulation-to-executable IR compiler stage before scalar extraction | High | High | No | Umgesetzt (2026-05-15, `text_only_simple_conversion_v29`) |
| 16 | Add object-model bridge between extracted fields and KG/BIM validation targets | Medium | Medium | No | Umgesetzt (2026-05-15, `text_only_simple_conversion_v30`) |
| 17 | Implement HybridRAG (graph + vector) retriever branch for compliance queries | Medium | Medium | No | Offen |
| 18 | Add semantic rule validation sandbox (SHACL/SPARQL style checks) before scoring | Medium | Medium | No | Offen |

---

## Literature Cross-Check (2026-05-14) — Duplicates vs Pipeline-Mapped Papers

Compared sources:
1. Newly added review-derived papers in `literature_review_auto_ie_construction.md` (Targeted Reviews + Section 13)
2. Pipeline-mapped papers in `pipeline_inventory_and_paper_mapping.md`

### Duplicate marking result

| Group | Count | Duplicate status |
|---|---:|---|
| Newly added review-derived papers checked | 15 | Compared |
| Exact title duplicates vs pipeline-mapped list | 0 | None |
| New (not yet explicitly mapped to pipelines) | 15 | All are currently new vs mapping file |

### Important in-file duplicate note

There is one intentional in-file overlap in `literature_review_auto_ie_construction.md`:
1. `Retrieval-Augmented Generation for Large Language Models: A Survey` appears in Section 2 and is referenced again in the targeted-review ranking block. This is not a pipeline-mapping duplicate; it is a cross-reference duplicate.

### Newly extracted ideas not yet in pipeline plan

1. **Rule-class-aware extraction profile (v27_text_rule_profiles)**
Why: Classifications of rules for automated BIM rule checking development in [Classification Approach for Automated Rule-Based Compliance Checking Development](https://doi.org/10.1016/j.autcon.2019.102960) (2019, Mirdar Harijani et al.) shows that different rule classes need different handling.
Plan: add per-variable rule classes (threshold, exception, cross-reference, table lookup) and route extraction prompts/scoring by class. *Implemented 2026-05-14 as `text_only_simple_conversion_v27`.*

2. **Regulation-to-executable IR compiler (v29_ir_compiler)**
Why: [Translating building legislation into a computer-executable format for evaluating compliance of design models](https://doi.org/10.1016/j.autcon.2014.04.008) (2014, Eastman & Jiao) suggests a strong intermediate representation step before final checks.
Plan: parse clauses into a deterministic intermediate JSON/logic form (`subject`, `condition`, `operator`, `value`, `unit`, `exception`) before final output matching. *Implemented 2026-05-15 as `text_only_simple_conversion_v29`.*

3. **Object-model bridge for downstream checking (v30_object_bridge)**
Why: [Development of an object model for automated compliance checking](https://doi.org/10.1061/(ASCE)CP.1943-5487.0000486) (El-Gohary & El-Diraby) indicates better stability when extraction outputs are mapped to explicit object-model schemas.
Plan: introduce mapping layer from extracted fields to canonical model entities used in KG and compliance validators. *Implemented 2026-05-15 as `text_only_simple_conversion_v30`.*

4. **HybridRAG branch for compliance retrieval (vXX_hybrid_rag)**
Why: [Graph Retrieval-Augmented Generation: A Survey](https://doi.org/10.1145/3777378) (2025) indicates graph + vector retrieval improves relation-heavy queries.
Plan: add optional graph neighborhood expansion after vector retrieval for multi-hop constraint questions.

5. **Semantic rule validation sandbox (vXX_semantic_validation)**
Why: Papers in [A Rule-Based Semantic Approach for Automated Regulatory Compliance in the Construction Sector](https://doi.org/10.1016/j.eswa.2015.02.029) (2015, Beach et al.) and ontology-based compliance checking literature emphasize pre-execution semantic consistency checks.
Plan: validate extracted triples/rules against deterministic constraints before scoring (prefix completeness, unit compatibility, contradiction checks).

---

## Detailed Findings by Task Family

---

### Literature-driven compliance routing

**Status update (2026-05-12):** Section 7, first finding from `pipeline_inventory_and_paper_mapping.md` is now implemented as new pipeline `text_only_simple_conversion_v25`. Details: `text_only_simple_conversion_v25_findings.md`. *Supported by [Semantic Text Classification for Supporting Automated Compliance Checking in Construction](https://doi.org/10.1109/isai.2013.6605806) (2013) and [A platform-based Natural Language processing-driven strategy for digitalising regulatory compliance processes for the built environment](https://doi.org/10.1080/17452007.2024.2353939) (2024) which justify explicit routing/prefilter stages before extraction.*

**Status update (2026-05-12):** Section 7, second finding (v5 structured extraction lineage) is now implemented as new pipeline `text_only_simple_conversion_v26`. Details: `text_only_simple_conversion_v26_findings.md`. *Supported by [Semantic NLP-Based Information Extraction from Construction Regulatory Documents for Automated Compliance Checking](https://doi.org/10.1061/(ASCE)CP.1943-5487.0000346) (2016, Zhang & El-Gohary) which shows clause typing and semantic verifier gates are essential for robust regulatory IE.*

**Status update (2026-05-12):** Section 7, third finding (v12/v13/v14 Turtle-KG lineage) is now implemented as new pipeline `turtle_kg_keyword_v15` with an explicit staged Extract -> Normalize -> Formalize flow. Details: `turtle_kg_keyword_v15_findings.md`. *Supported by [Information Transformation and Automated Reasoning for Automated Compliance Checking in Construction](https://doi.org/10.1061/(ASCE)0733-9364(2013)139:11(1457)) (2013, Zhang & El-Gohary) which emphasizes staged pipelines for regulatory document processing.*

**Status update (2026-05-12):** Section 7, fourth finding (KG record/comprehensive KG lineage) is now implemented as new pipeline `kg_comprehensive_schema_minimal_turtle_v3` with additive schema extension merge and deterministic canonicalization before triple scoring. Details: `kg_comprehensive_schema_minimal_turtle_v3_findings.md`. *Supported by [Extending Building Information Models Semiautomatically Using Semantic NLP Techniques](https://doi.org/10.1061/(ASCE)CP.1943-5487.0000486) (2016, El-Gohary & El-Diraby) and [Using Large Language Models for the Interpretation of Building Regulations](https://doi.org/10.1016/j.aei.2024.102301) (2024, Chong et al.) which show schema canonicalization is critical for regulatory KG extraction.*

**Status update (2026-05-12):** Section 7, fifth finding (v11 multimodal/hybrid compliance lineage) is now implemented as new pipeline `text_image_multimodal_conversion_v22` with multimodal evidence grounding (text/image evidence IDs), deterministic compliance report scaffolding (`check_status`, provenance fields), and schema-stable post-processing. Details: `text_image_multimodal_conversion_v22_findings.md`. *Supported by [Automated Building Information Modeling Compliance Check through a Large Language Model Combined with Deep Learning and Ontology](https://doi.org/10.3390/buildings14071983) (2024, Chong et al.) and [Large Language Model-Driven Code Compliance Checking in Building Information Modeling](https://doi.org/10.3390/electronics14112146) (2025, Wang & Chen) which show multimodal grounding improves compliance extraction.*

The implemented idea is a compliance-style routing/prefilter stage before extraction: chunks with requirement-like headings and clause language (for example `Anforderungen`, `Feuerwiderstand`, `Mindestdicke`, `Abschottung`) are boosted before the existing retrieval diversity and consistency logic runs, while administrative/meta sections are deprioritized. This approach is grounded in [Semantic Text Classification for Supporting Automated Compliance Checking in Construction](https://doi.org/10.1109/isai.2013.6605806) (2013) which demonstrates classification-first routing for regulatory documents.

The v26 extension adds two practical compliance-style controls on top of v25: (1) clause typing for selected chunks (requirement/scope/exception/administrative/informational), and (2) a deterministic semantic verifier gate that only accepts extracted numeric candidates when requirement-like chunks semantically support the value. This builds on [A deep neural network-based method for deep information extraction using transfer learning strategies to support automated compliance checking](https://doi.org/10.1016/j.autcon.2021.103834) (2021, Zhang & El-Gohary) which shows verifier gates reduce extraction errors.

This is intentionally additive on top of v24: v25 keeps marker-noise mitigation, semantic reranking, contradiction-aware retrieval checks, and adaptive consistency gating, and only changes the order in which candidate chunks are presented to extraction.

---

### 1. Text-only scalar extraction — `simpleMinMaxExtraction`

**Status update (2026-05-12):** Umgesetzt als neue Pipeline `text_only_simple_conversion_v22` mit fire-domain query expansion und numerischer Normalisierung. Details siehe `text_only_simple_conversion_v22_findings.md`.

#### What was tested

| exp | pipeline | model | success% | total_runs |
|---|---|---|---|---|
| exp_001 | text_only_simple_conversion | gemma-3-27b local | 16.5% | 158 |
| exp_002 | text_only_simple_conversion | gemma-3-27b local | 20.3% | 158 |
| exp_003 | text_only_simple_conversion | gemma-3-27b local | 18.6% | 790 |
| exp_004 | v2 | gemma-3-27b local | 18.5% | 790 |
| exp_005 | v3 | gemma-3-27b local | 19.1% | 790 |
| exp_006 | v3 | gemma-3-27b local | 19.3% | 4740 |
| exp_041 | v17 | gemma-3-27b local | 21.5% | 158 |
| exp_037 | v8 | gemma-4 openrouter | 24.4% (partial) | 2362 |

#### What went good
- v17 (retrieval + ranking + corrective retry) shows a consistent +2 pp gain over baseline on the same model without adding significant token cost.
- Switching to gemma-4 (openrouter) via v8 gives the best result at 24.4%, confirming the stronger model alone pushes extraction quality up.
- v3 modular architecture is stable and consistently replicable across 4740 runs with no variance.

#### What went wrong
- v1 → v2 → v3 essentially flatline at 18-20%. Prompt engineering iterations and modularization alone do not move the needle on this task.
- The plateau is caused by lexical keyword retrieval failing on paraphrased or unit-variant values (e.g., "90 minutes" vs "EI 90", "REI 90").
- **Critical missing experiments:** v20 and v21 have never been run on `simpleMinMaxExtraction`. These are the strongest text-only pipelines currently implemented and are entirely untested on this task.

#### How to fix / improve

**Step 1 (immediate, no implementation needed):** Queue exp on `simpleMinMaxExtraction` with `text_only_simple_conversion_v21` + gemma-4 (openrouter). Expected result: ~27-31% based on v21's improvements over v17.

**Step 2 (for v22):** Add domain-specific query expansion targeting unit synonyms (EI 90 / REI 90 / F90 / 90 min / 1.5h) as alternate retrieval queries. The current query generation is surface-form only and misses domain-standard abbreviations common in Brandschutz approval documents. ✅ Umgesetzt in `text_only_simple_conversion_v22`. *Supported by [Retrieval-Augmented Generation for Large Language Models: A Survey](https://arxiv.org/abs/2312.10997) (2024, Gao et al.) which shows query variant expansion is a critical RAG design component.*

**Step 3 (for v22):** After semantic reranking (already in v21), add a numeric normalization pass that maps extracted candidates to canonical numeric form before threshold comparison. This prevents near-matches being counted as failures. ✅ Umgesetzt in `text_only_simple_conversion_v22`. *Supported by [Semantic NLP-Based Information Extraction from Construction Regulatory Documents for Automated Compliance Checking](https://doi.org/10.1061/(ASCE)CP.1943-5487.0000346) (2016, Zhang & El-Gohary) which emphasizes numeric parameter normalization as a critical IE step.*

---

### 2. Text-only conditional scalar extraction — `conditionBasedExtraction`

**Status update (2026-05-12):** Finding A umgesetzt als neue Pipeline `text_only_simple_conversion_v23` mit marker-noise-aware line filtering und score penalty fuer Retrieval. Details siehe `text_only_simple_conversion_v23_findings.md`.

#### What was tested

| exp | pipeline | model | success% | total_runs |
|---|---|---|---|---|
| exp_007 | v4 | gemma-3-27b local | 11.1% | 216 |
| exp_008 | v5 | gemma-3-27b local | 13.0% | 216 |
| exp_009 | v5 | gemma-3-27b local | 12.5% | 1080 |
| exp_010 | v6 (marker) | gemma-3-27b local | 12.3% | 1080 |
| exp_014 | v7 (marker LLM) | gemma-3-27b local | 12.0% (partial) | 920 |
| exp_011 | v8 (retrieval) | gemma-3-27b local | 23.3% | 7560 |
| exp_036 | v8 | gemma-4 openrouter | 28.4% (partial) | 3226 |
| exp_012 | v10 (marker+retrieval) | gemma-3-27b local | 15.9% | 7560 |
| exp_042 | v17 | gemma-3-27b local | **34.3%** | 216 |
| exp_043 | v18 | gemma-3-27b local | 32.9% | 216 |
| exp_0016 | v5 | gemma-4 openrouter | 35.0% (partial) | 214 |

#### What went good
- v17 is the best text-only pipeline on this task at 34.3% — a substantial +11 pp over v8 and +22 pp over baseline.
- Retrieval-augmented approaches (v8, v17) are overwhelmingly better than full-context approaches (v1-v7) on conditional extraction.
- Switching to gemma-4 consistently yields +5 pp uplift regardless of pipeline version (v8: 23→28%, v5: 12→35%).
- v5 with gemma-4 (35.0%) essentially matches v17 with gemma-3, confirming model quality is a major lever.

#### What went wrong

**Finding A — v6/v7 marker input does not help, it hurts:** ✅ Umgesetzt (2026-05-12, `text_only_simple_conversion_v23`)
v6 (marker markdown) and v7 (marker LLM markdown) both perform at 12%, no better than v5 raw text. v10 (marker + retrieval) at 15.9% is significantly worse than v8 (raw + retrieval) at 23.3%. The marker output introduces image embed lines, span tags, and repeated boilerplate that pollutes chunk ranking signals. Chunks that contain `![img](...)` or `<span class=...>` get false positive scores from numeric content in image paths.

**Finding B — v18 consistency-gating regresses vs v17:**
v18 (32.9%) is worse than v17 (34.3%) despite having additional retrieval diversity and evidence-aware scoring. The consistency gating in v18 treats multi-valued evidence (e.g., a table showing "60/90/120 min depending on cross-section") as conflicting answers and blocks extraction, returning null. This is a false negative factory in spec documents where value ranges are intentionally multi-valued. ✅ **Umgesetzt (2026-05-12, `text_only_simple_conversion_v24`)**

**v24 Solution:** Replaced static consistency threshold with variable-family-aware adaptive gating. For multi-valued specs, v24 accepts the modal (most frequent) numeric candidate instead of blocking extraction. Details: `text_only_simple_conversion_v24_findings.md`.

**Finding C — v20 and v21 not tested here:**
The two strongest text-only pipelines (v20, v21) have no experiment on `conditionBasedExtraction` with gemma-4. This is the highest-priority benchmark gap.

#### How to fix / improve

**Step 1 (immediate):** Run `text_only_simple_conversion_v21` + gemma-4 on `conditionBasedExtraction`. This alone may push above v11 multimodal baseline (38%). *Supported by findings in [Semantic NLP-Based Information Extraction from Construction Regulatory Documents for Automated Compliance Checking](https://doi.org/10.1061/(ASCE)CP.1943-5487.0000346) (2016, Zhang & El-Gohary) showing strong extraction improvements via semantic reranking and condition-aware prompting.*

**Step 2 (v18 fix → v22):** The consistency gating threshold in v18/v20 is static (`0.58` default). Replace with a variable-family-aware threshold: for `min_thickness`, `fire_resistance_class` etc., allow a wider tolerance band because spec documents intentionally list multiple values. Alternatively, change gating logic to: accept the most-frequent candidate value rather than blocking when candidates disagree. *Supported by [Long²RAG: Evaluating Long-Context & Long-Form Retrieval-Augmented Generation with Key Point Recall](https://arxiv.org/abs/2410.23000) (2024, Qi et al.) which shows LLMs frequently struggle with multi-valued or conflicting evidence in long documents.*

**Step 3 (v22):** Add negative-signal chunk penalization — chunks that contain phrases like "ausgenommen" (excluded), "gilt nicht" (does not apply), "abweichend" (deviating) near a numeric value should have their rank score reduced. Currently those contradictory values score equally high as positive evidence. *Supported by [Corrective Retrieval-Augmented Generation](https://arxiv.org/abs/2401.15884) (2024, Shi et al.) which emphasizes penalizing contradictory context in retrieval-augmented pipelines.*

**Step 4 (v22):** Add domain synonym query expansion for conditions. The German conditional vocabulary in Brandschutz ("bei Wanddurchführungen", "für Hohlwände", etc.) has common paraphrases across manufacturers. Static condition-to-query mapping tables would improve retrieval precision. *Supported by [Retrieval-Augmented Generation for Large Language Models: A Survey](https://arxiv.org/abs/2312.10997) (2024, Gao et al.) which documents semantic query expansion as a best practice in Advanced RAG systems.*

---

### 3. KG condition extraction — `conditionKGExtraction`

**Status update (2026-05-12):** Implemented as new pipeline `turtle_kg_keyword_v15` with deterministic normalization and Turtle formalization after keyword-guided extraction. Details: `turtle_kg_keyword_v15_findings.md`.

#### What was tested

| exp | pipeline | model | success% | total_tokens |
|---|---|---|---|---|
| exp_0017 | turtle_kg_conversion_v12 | gemma-3-27b local | 23.8% | 19M |
| exp_0018 | turtle_kg_twostep_v13 | gemma-3-27b local | 22.6% | 20.8M |
| exp_019 | turtle_kg_keyword_v14 | gemma-3-27b local | **29.7%** | 71.5M |

#### What went good
- v14 (LLM keyword expansion + chunking) is the best KG pipeline at 29.7%, beating v12 by +6 pp.
- The keyword expansion approach (borrowed from text-only retrieval lineage) transfers well to the KG task — more semantically targeted chunks lead to better triple extraction.

#### What went wrong
- v13 (two-step locate-then-extract) **regresses vs v12** (22.6 vs 23.8%). The locate step introduces a failure mode: if the locate step returns the wrong passage, the extract step has no chance of recovering. Error propagation across pipeline stages is not guarded against.
- v14 has extremely high token usage (71.5M tokens for 4500 runs = ~15k tokens/run), making it expensive for full benchmarking. Keyword expansion with LLM-generated keywords causes over-retrieval.
- No experiment with gemma-4 on this task — model ceiling unknown.

#### How to fix / improve

**Step 1 (immediate):** Run v14 with gemma-4 (openrouter) on a 500-run sample to establish the model ceiling on this task.

**Step 2 (turtle_kg_keyword_v15):**
- Add marker text cleaning (already implemented in `marker_text_cleaner.py`) as a pre-processing step before keyword chunking. This will clean image lines and span tags from marker markdown files, improving chunk quality. *Supported by [LayoutLM: Pre-training of Text and Layout for Document Image Understanding](https://doi.org/10.1145/3394486.3403172) (2020, Xu et al.) which shows layout/format signals can interfere with downstream IE tasks.*
- Add semantic reranking on the retrieved keyword chunks (already implemented in `retrieval_enhancer_v21_text.py`). Apply it post-keyword-retrieval to re-score chunks by semantic similarity to the KG triple being extracted. *Supported by [Retrieval-Augmented Generation for Large Language Models: A Survey](https://arxiv.org/abs/2312.10997) (2024, Gao et al.) which identifies re-ranking as a critical Advanced RAG component.*
- Add a locate-step confidence guard borrowed from v17: if locate confidence < threshold, fall back to full-document extraction rather than failing. This fixes the v13 regression pattern. *Supported by [RAKG: Document-level Retrieval Augmented Knowledge Graph Construction](https://arxiv.org/abs/2504.09823) (2025, Zhang et al.) which shows multi-stage KG pipelines need fallback mechanisms to handle errors in intermediate stages.*

**Step 3 (token budget):** Cap keyword expansion at max 5 LLM-generated keywords per variable (currently uncapped). Add deduplication across query variants before retrieval to reduce redundant chunk fetches. *Supported by [LegalBench-RAG: A Benchmark for Retrieval-Augmented Generation in the Legal Domain](https://arxiv.org/abs/2408.10343) (2024, Pipitone & Houir Alami) which shows over-retrieval is a common RAG failure mode on regulatory documents.*

---

### 4. System transfer scope — `systemTransferScopeExtraction`

#### What was tested

| exp | pipeline | model | success% | total_runs |
|---|---|---|---|---|
| exp_013 | text_only_simple_conversion_v9 | gemma-3-27b local | **75.3%** | 170 |

#### What went good
- 75.3% is the highest success rate in the entire dashboard. Classification/label extraction (Beides / Kabel / Rohre) is fundamentally easier than scalar numeric extraction for these LLMs.
- The pipeline is stable and reliable.

#### What went wrong
- Only 170 runs — statistically thin. Confidence interval around 75% is wide.
- No experiment with gemma-4 — model ceiling unknown. Very likely above 85%.
- No v16 (batched boolean-map) attempted on this task despite it being listed as a secondary compatible dataset.

#### How to fix / improve

**Step 1 (immediate):** Run v9 with gemma-4 on `systemTransferScopeExtraction` with the full dataset. Expected result: 83-90%.

**Step 2:** If gemma-4 reaches >85%, this task is essentially solved for production. If it plateaus at 75-80%, investigate whether the 3-class label set is ambiguous — some systems may genuinely qualify under both "Kabel" and "Beides", and the ground truth labeling may have annotation inconsistencies.

---

### 5. Cable/pipe type classification — `allowedCableTypesExtraction` / `allowedPipeTypesExtraction`

#### What was tested

| exp | pipeline | task | model | success% | correctness% | runs |
|---|---|---|---|---|---|---|
| exp_020 | v15 | cable | gemma-3-27b local | 41.2% | 76.1% | 170 |
| exp_021 | v15 | pipe | gemma-3-27b local | 11.2% | 71.1% | 170 |
| exp_022 | v16 (batched) | cable | gemma-3-27b local | 41.2% | 77.3% | 425 |
| exp_023 | v16 (batched) | pipe | gemma-3-27b local | 10.4% | 65.1% | 425 |

#### What went good
- Cable correctness is 76-77% — the LLM identifies most cable types correctly at the individual flag level.
- v16 batching marginally improves cable correctness (76→77%) and maintains the same success rate, confirming the batching mechanism is not harmful for cables.
- Both v15 and v16 show consistent results across replications.

#### What went wrong

**Finding A — Pipe success is catastrophically low (10-11%):**
The pipe type vocabulary is likely larger, more heterogeneous, and less consistently named across manufacturers than cable types. The LLM cannot reliably map manufacturer-specific pipe names to canonical boolean-map keys when names vary significantly (e.g., "Abwasserrohr DN50" vs "KG-Rohr DN50" for the same pipe category).

**Finding B — v16 batching hurts pipes:**
v16 pipe correctness (65.1%) is *lower* than v15 pipe correctness (71.1%). Batching fragments the pipe type list in ways that destroy context about which types are semantically related. A batch may contain 5 cable/pipe types with no context about the others, causing the LLM to guess when it should reason about the full set.

**Finding C — Exact match is too strict a success criterion:**
A result where 19 out of 20 boolean flags are correct scores as 0% success. Correctness (76%) is the more meaningful metric but success (the API endpoint's primary output) flatlines.

#### How to fix / improve

**Step 1 (investigation before implementation):** Extract 5-10 pipe type classification failures from exp_021/exp_023 and manually inspect which specific pipe type flags are wrong. Determine if the issue is: (a) wrong pipe names in the expected value set, (b) LLM hallucinating non-existent types, or (c) naming variant mismatch between document text and canonical key names.

**Step 2 (v17_booleanmap):**
- Replace alphabetical batching with semantic cluster batching: group pipe types by category (e.g., all waste pipe types together, all metal pipe types together). This keeps semantically related types in the same LLM call, preserving mutual exclusion context. *Supported by [Structured information extraction from scientific text with large language models](https://doi.org/10.1038/s41467-024-45563-x) (2024) which shows schema-aware clustering improves extraction precision.*
- Add a name-normalization step that maps manufacturer names to canonical key names using a lookup table or fuzzy match before evaluation. This would dramatically improve correctness scoring. *Supported by [Semantic NLP-Based Information Extraction from Construction Regulatory Documents for Automated Compliance Checking](https://doi.org/10.1061/(ASCE)CP.1943-5487.0000346) (2016, Zhang & El-Gohary) which emphasizes normalization as essential for domain IE.*
- Add confidence-weighted aggregation across batches: if a type appears in multiple batches (overlap window), take the confidence-weighted vote rather than the last answer. *Supported by [Retrieval-Augmented Generation for Large Language Models: A Survey](https://arxiv.org/abs/2312.10997) (2024, Gao et al.) which advocates for evidence aggregation and consensus mechanisms in LLM pipelines.*

**Step 3:** Run v15 with gemma-4 on both cable and pipe tasks. Expected improvement: +10-15 pp on pipes based on model quality effects seen in other tasks.

---

### 6. KG Turtle record extraction — `cable_v1` / `pipe_v1`

#### What was tested

| exp | pipeline | dataset | model | success% | correctness% |
|---|---|---|---|---|---|
| exp_024 | kg_turtle_extraction_cable_v1 | cableTtlExtractionPlaceholders | local | 0% | 3.1% |
| exp_025 | kg_turtle_extraction_cable_v1 | cableTtlExtractionNoValues | local | 0% | 2.7% |
| exp_026 | kg_turtle_extraction_pipe_v1 | pipeTtlExtractionPlaceholders | local | 0% | 0% |
| exp_027 | kg_turtle_extraction_pipe_v1 | pipeTtlExtractionNoValues | local | 0% | 0% |
| exp_029 | kg_turtle_extraction_cable_v1 | cableTtlExtractionNoValues | openrouter gemma-4 | 0% | 0% |
| exp_031 | kg_turtle_extraction_pipe_v1 | pipeTtlExtractionNoValues | openrouter gemma-4 | 0% | 0% |
| exp_032 | kg_turtle_extraction_cable_v1 | cableJsonExtractionPlaceholders | local | 0% | 0% |
| exp_033 | kg_turtle_extraction_cable_v1 | cableJsonExtractionNoValues | local | 0% | 2.7% |
| exp_034 | kg_turtle_extraction_pipe_v1 | pipeJsonExtractionPlaceholders | local | 0% | 0.09% |
| exp_035 | kg_turtle_extraction_pipe_v1 | pipeJsonExtractionNoValues | local | 0% | 0% |

#### What went good
- Nothing. This is a complete failure across all combinations of model, dataset format (Turtle vs JSON, Placeholders vs NoValues), and system type (cable vs pipe).

#### What went wrong

**This is the most critical failure in the project.** The 0% success rate across 10 diverse experiments, including with the stronger gemma-4 model, and including JSON input formats, rules out the following causes:
- ❌ Not a model capability issue (gemma-4 also 0%)
- ❌ Not a dataset format issue (JSON vs Turtle makes no difference)
- ❌ Not a retrieval issue (the pipeline uses full-document context)

The ~3% correctness on cable (consistently) vs 0% on pipe suggests that a small number of cable triples match by coincidence. This points to a **structural output format mismatch** between what the pipeline generates and what the evaluation metric compares.

**Hypotheses (ranked by likelihood):**
1. **URI prefix mismatch:** The pipeline generates triples with one namespace prefix (e.g., `ex:CableSystem`) but the expected value uses a different prefix (e.g., `brandschutz:CableSystem`). The matcher does string comparison and fails on all triples even if predicates and values are otherwise correct.
2. **Literal format mismatch:** Numeric values are generated as `"90"^^xsd:integer` by the LLM but expected as `"90.0"^^xsd:decimal` (or vice versa). The matcher does not normalize literals before comparison.
3. **Extra triples:** The LLM generates mandatory boilerplate triples (type declarations, labels) not present in the expected value, causing the set-comparison to fail even when all expected triples are present.
4. **Evaluation metric bug:** The `result_matcher_component` may have a logic error in triple-set comparison that always returns 0 for structured KG outputs.

#### How to fix / improve

**Step 1 (diagnostic — must be done before any pipeline work):**
1. Run 1 cable document manually through `kg_turtle_extraction_cable_v1` and capture the raw LLM output and the parsed extracted triples.
2. Print the expected triples from the dataset for the same document.
3. Run the matcher on these two sets and trace where it fails.

**Step 2:** Check `tests/test_result_matcher_component.py` and `tests/test_turtle_husk_renderer_component.py` for cases that test URI prefix matching and literal normalization. If those tests pass but experiments fail, the issue is in the dataset expected values format, not the code.

**Step 3 (if URI mismatch confirmed):** Add namespace normalization in the matcher — strip the prefix and compare only the local name + predicate + value for initial matching.

**Step 4 (if literal mismatch confirmed):** Add `rdflib`-based literal normalization before triple comparison. Parse both LLM output and expected values through rdflib, normalize all literals to canonical form, then compare.

**Step 5 (after diagnosis):** If the fix is in the matcher/evaluator, re-running the existing experiments with the fixed evaluation may immediately reveal the actual extraction quality without building new pipelines.

---

### 7. Multimodal extraction — `conditionBasedExtraction`

#### What was tested

| exp | pipeline | model | success% | total_runs |
|---|---|---|---|---|
| exp_015 | text_image_multimodal_conversion_v11 | gemma-4 openrouter | **38.0%** | 216 |
| exp_044 | text_image_multimodal_conversion_v19 | gemma-4 openrouter | 36.2% (partial) | 210 |
| exp_045 | text_image_multimodal_conversion_v21 | gemma-4 openrouter | 35.7% (partial) | 210 |
| exp_052 | text_image_multimodal_conversion_v21 | gemma-4 openrouter | 26.5% (partial) | 565 |

#### What went good
- v11 multimodal is the best pipeline in the entire project on `conditionBasedExtraction` at 38%, beating the best text-only pipeline (v17 at 34.3%).
- Multimodal extraction genuinely helps on this task — layout and table information in images provides evidence that text alone misses.

#### What went wrong

**Finding A — v19 and v21 regress vs v11:**
v19 (36.2%) and v21 (35.7%) are both worse than v11 (38%), despite implementing additional evidence selection, layout-aware scoring, marker structure parsing, logo filtering, and contradiction-aware retry. More sophisticated components are actively hurting results.

**Finding B — v21 on `simpleMinMaxExtraction` is very weak (26.5%):**
exp_052 shows v21 multimodal at only 26.5% on `simpleMinMaxExtraction`, which is the same as or worse than the text-only v8 with gemma-4 (24.4%). Multimodal overhead for simple scalar extraction is not paying off.

**Root cause hypothesis:** The evidence scoring and image selection heuristics in v19/v21 are selecting fewer, more "filtered" images, which removes useful context that v11 kept by including all images. The logo filter and low-index region filter may be over-pruning relevant figures and tables.

#### How to fix / improve

**Step 1 (investigation):** Compare image sets selected by v11 vs v19 for 5-10 failed v19 runs that v11 succeeded on. Determine if v19 is discarding images that contain the relevant tables.

**Step 2:** Tune the logo filter thresholds in `logo_image_filter.py` — if it's too aggressive, relax the filter to only exclude images where >90% of the image area is blank or contains a single low-complexity region.

**Step 3:** Add an ablation experiment: run v19 with logo filtering disabled and see if success rate recovers toward v11's 38%.

**Step 4 (for v22 multimodal):** Instead of replacing v11's image selection with more complex heuristics, treat v11's include-all approach as the baseline and add images selectively on top (union, not intersection). Keep all images v11 would include, then optionally add extracted evidence images from marker structure.

---

### 8. Comprehensive KG schema extraction

#### What was tested

| exp | pipeline | dataset | model | success% | correctness% | runs |
|---|---|---|---|---|---|---|
| exp_039 | kg_comprehensive_schema_minimal_turtle_v1 | comprehensiveKgSchemaExtraction | local | 0% | 0% | 17 |
| exp_040 | kg_comprehensive_schema_minimal_turtle_v1 | comprehensiveKgSchemaMinimalExtraction | local | 0% | 0% | 17 |
| exp_046 | kg_comprehensive_schema_minimal_turtle_v2 | comprehensiveKgSchemaExtraction | local | 0% | 0% (partial) | 13 |

#### What went good
- v2's hierarchical staged extraction architecture is conceptually correct for large schemas.
- exp_046 is still running (only 13 runs) — too early to conclude anything about v2.

#### What went wrong
- 0% on both success and correctness for v1 on both dataset variants. If even partial triples matched, correctness would be non-zero. This is the same universal failure pattern as KG record extraction in section 6.
- v1 attempted with only 17 runs — too few to draw statistical conclusions but enough to see the complete failure.
- exp_046 (v2) token usage is enormous: 292k tokens/run. A full benchmark run would cost hundreds of dollars on OpenRouter.

#### How to fix / improve

**Step 1:** This task is blocked on the same diagnostic as section 6 — the evaluation metric may have a URI prefix or literal mismatch issue that explains the 0% correctness. Resolve section 6 diagnosis first.

**Step 2:** Wait for exp_046 to complete, then inspect v2 outputs manually against expected values.

**Step 3 (token optimization for v2):** At 292k tokens/run, v2 is unsustainably expensive. The hierarchical stages likely have redundant context passed between stages. Profile which stage consumes the most tokens and add context windowing/truncation at the boundary between stages.

**Step 4 (after diagnosis):** If the evaluation metric is fixed and v1/v2 show non-zero correctness, run a gemma-4 sample (5-10 runs) to establish the model ceiling on this task. If correctness is still 0% with gemma-4, the pipeline design has a fundamental flaw in the extraction logic, not the evaluation.

---

## Prioritized Improvement Plan

### Current status update (2026-05)

The roadmap section above contains historical priorities from before the current implementation wave. The following is the current action order aligned with the repository state (v28 text-only, v23 multimodal, v4 comprehensive KG now implemented).

### Priority 1 — Benchmark the latest implemented branches
**Actions:**
1. Run `text_only_simple_conversion_v28` against the same datasets used for v26/v27 to quantify the net effect of library-backed retrieval and structured parsing.
2. Run `text_image_multimodal_conversion_v23` against v22 on the same multimodal benchmark split.
3. Run `kg_comprehensive_schema_minimal_turtle_v4` against v3 with identical schema extensions and expected Turtle targets.

### Priority 2 — Stabilize API experiment husks and payload defaults
**Actions:**
1. Keep experiment husks minimal (only required request fields + pipeline-specific required extras).
2. Treat tuning extras (`top_k_chunks`, `bm25_candidate_pool`, `cross_encoder_model`, `instructor_max_retries`) as optional overlays, not required baseline fields.
3. For multimodal v23, enforce OpenRouter model selection in experiment configs.

### Priority 3 — Fill documentation/testing gaps for latest versions
**Actions:**
1. Add dedicated findings docs for `text_only_simple_conversion_v28`, `text_image_multimodal_conversion_v23`, and `kg_comprehensive_schema_minimal_turtle_v4`.
2. Add/extend tests for these pipelines where missing, especially end-to-end API contract coverage.
3. Keep pipeline inventory and replacement-plan docs synchronized after each implementation increment.

### Priority 4 — Remaining planned library-backed work
**Actions:**
1. Implement `clause_classifier_lib.py` (currently planned only).
2. Evaluate whether `kg_turtle_keyword_v16` should be built as a dedicated library-backed KG keyword branch.
3. If clause-classifier quality is strong, design a follow-up text pipeline that combines clause classification with v28 retrieval/parsing stack.

---

## Cross-cutting observations

### Model quality is the single largest lever
Every task tested with gemma-4 (openrouter) shows +5-10 pp improvement over gemma-3-27b (local) with the same pipeline. Before building new pipeline versions, running the current best pipeline per task with gemma-4 is always the higher-ROI action.

### Marker input needs cleaning before use in retrieval
v6, v7, v10 all underperform their non-marker counterparts. v21's `marker_text_cleaner.py` component addresses this. Any new pipeline that ingests marker files must apply cleaning first. This is confirmed across multiple experiments.

### Retrieval > full context for conditional extraction
v1-v7 (full context, no retrieval): 11-20% success. v8+ (retrieval-augmented): 23-34% success. The jump is +10-15 pp and holds across model types. All new pipelines for `conditionBasedExtraction` and `simpleMinMaxExtraction` should use retrieval-augmented architectures as the baseline — full-context approaches are not competitive.

### KG evaluation needs verification before any new KG pipeline investment
10 experiments, 0% success, 0% correctness. This is either a systematic evaluation bug or a fundamental pipeline design flaw. Until diagnosed, building new KG pipelines risks repeating the same failure.

---

## Pipeline Connection Check Run (2026-05-15)

Goal of this pass: identify idea-level duplicates and concrete opportunities to combine pipelines without losing benchmarkability.

### A. Text-only lineage (v25-v29): mostly additive, high overlap

Observed connection:
1. `text_only_simple_conversion_v25` adds compliance-routing prefilter.
2. `text_only_simple_conversion_v26` adds clause typing + semantic verifier.
3. `text_only_simple_conversion_v27` adds rule-class routing on top of v26.
4. `text_only_simple_conversion_v29` reuses the v27 stack and adds deterministic IR compilation.

Duplicate-risk pattern:
1. The same retrieval/retry/gating skeleton is repeated across v25-v29 with only one major idea added per version.
2. Query expansion, retry planning, and gating logic are implemented in parallel enhancer variants with small deltas.

Combination candidate:
1. Keep one canonical "advanced heuristic" branch with feature flags:
	- `enable_routing_prefilter` (v25)
	- `enable_clause_verifier` (v26)
	- `enable_rule_class_profiles` (v27)
	- `enable_clause_ir` (v29)
2. Keep v28 as the separate library-backed retrieval branch for A/B comparison against the advanced heuristic branch.

### B. Multimodal lineage (v22-v23): strong candidate for unification

Observed connection:
1. `text_image_multimodal_conversion_v23` explicitly reuses helper functions from v22.
2. Core flow (prompting, multimodal call, compliance report) is largely unchanged.
3. Main delta is evidence selection backend (v22 heuristic stack vs v23 layout-block stack).

Duplicate-risk pattern:
1. Two near-identical pipelines maintain duplicated orchestration code while differing mainly in evidence selector implementation.

Combination candidate:
1. Merge into one multimodal pipeline with configurable evidence backend:
	- `evidence_backend="heuristic_v22"`
	- `evidence_backend="layout_v23"`
2. Retain both modes in experiments to preserve historical comparability.

### C. Comprehensive KG lineage (v3-v4): v4 is a backend upgrade of v3

Observed connection:
1. v4 reuses v3 hierarchical extraction prompt stages and schema-extension merge.
2. Main delta is canonicalization/scoring backend (regex/custom parser in v3 vs rdflib + optional SHACL in v4).

Duplicate-risk pattern:
1. Two pipelines maintain almost identical extraction orchestration with different RDF backend layers.

Combination candidate:
1. Keep one comprehensive KG pipeline with backend switches:
	- `rdf_backend="legacy_v3"`
	- `rdf_backend="rdflib_v4"`
	- `run_shacl_validation=true|false`
2. Use the same benchmark harness to compare backends instead of maintaining two full orchestration copies.

### D. New inconsistency discovered during this check

Runner wiring currently contains nested `if` branches that make some pipelines unreachable in `app/services/experiment_runner.py`:
1. `kg_comprehensive_schema_minimal_turtle_v4` is nested under the v3 branch.
2. `text_image_multimodal_conversion_v23` is nested under the v22 branch.

This should be fixed before any consolidation benchmark run, otherwise config-level comparisons can be silently invalid.

### E. Practical consolidation order

1. Fix runner dispatch reachability first.
2. Consolidate multimodal v22/v23 into one backend-switch pipeline.
3. Consolidate KG v3/v4 into one backend-switch pipeline.
4. Consolidate v25-v29 into one advanced heuristic branch and keep v28 separate as library-backed control branch.

---

## Literature References

All citations in this document are derived from or supported by the following peer-reviewed and preprint sources:

### Core RAG and Long-Document Processing

1. **Retrieval-Augmented Generation for Large Language Models: A Survey** (2024, Gao et al.)
   - arXiv: https://arxiv.org/abs/2312.10997
   - Supports: Query expansion, re-ranking, iterative retrieval strategies across all sections

2. **Lost in the Middle: How Language Models Use Long Contexts** (2023, Liu et al.)
   - arXiv: https://arxiv.org/abs/2307.03172
   - Supports: Justification for chunking and retrieval strategies for 100+ page documents

3. **Long²RAG: Evaluating Long-Context & Long-Form Retrieval-Augmented Generation with Key Point Recall** (2024, Qi et al.)
   - arXiv: https://arxiv.org/abs/2410.23000
   - Supports: Multi-valued evidence handling, consistency gating refinement (v24, Step 2)

4. **Corrective Retrieval-Augmented Generation** (2024, Shi et al.)
   - arXiv: https://arxiv.org/abs/2401.15884
   - Supports: Negative-signal chunk penalization, contradiction-aware retrieval (v22, Step 3)

5. **RAKG: Document-level Retrieval Augmented Knowledge Graph Construction** (2025, Zhang et al.)
   - arXiv: https://arxiv.org/abs/2504.09823
   - Supports: Multi-stage KG pipeline fallback mechanisms (turtle_kg_keyword_v15, Step 2)

6. **Graph Retrieval-Augmented Generation: A Survey** (2025)
   - arXiv: https://doi.org/10.1145/3777378
   - Supports: HybridRAG pipeline ideas (planned), graph-based retrieval

### Construction Regulatory IE and Compliance Checking

7. **Semantic NLP-Based Information Extraction from Construction Regulatory Documents for Automated Compliance Checking** (2016, Zhang & El-Gohary)
   - DOI: https://doi.org/10.1061/(ASCE)CP.1943-5487.0000346
   - Supports: Clause typing, semantic verifier gates (v26), numeric normalization (v22), core IE methodology

8. **Integrating Semantic NLP and Logic Reasoning into a Unified System for Fully-Automated Code Checking** (2017, Zhang & El-Gohary)
   - DOI: https://doi.org/10.1016/j.autcon.2016.08.027
   - Supports: Full pipeline from text extraction to rule execution

9. **Information Transformation and Automated Reasoning for Automated Compliance Checking in Construction** (2013, Zhang & El-Gohary)
   - DOI: https://doi.org/10.1061/(ASCE)0733-9364(2013)139:11(1457)
   - Supports: Staged Extract → Normalize → Formalize (turtle_kg_keyword_v15)

10. **A Rule-Based Semantic Approach for Automated Regulatory Compliance in the Construction Sector** (2015, Beach et al.)
    - DOI: https://doi.org/10.1016/j.eswa.2015.02.029
    - Supports: Ontology-based rule extraction, semantic validation

11. **A deep neural network-based method for deep information extraction using transfer learning strategies to support automated compliance checking** (2021, Zhang & El-Gohary)
    - DOI: https://doi.org/10.1016/j.autcon.2021.103834
    - Supports: Verifier gates, transformer-based IE, transfer learning approaches

12. **Semantic Text Classification for Supporting Automated Compliance Checking in Construction** (2013)
    - DOI: https://doi.org/10.1109/isai.2013.6605806
    - Supports: Compliance routing and classification-first approaches (v25)

13. **A platform-based Natural Language processing-driven strategy for digitalising regulatory compliance processes for the built environment** (2024)
    - DOI: https://doi.org/10.1080/17452007.2024.2353939
    - Supports: NLP-based routing and prefiltering for regulatory documents

14. **Extending Building Information Models Semiautomatically Using Semantic NLP Techniques** (2016, El-Gohary & El-Diraby)
    - DOI: https://doi.org/10.1061/(ASCE)CP.1943-5487.0000486
    - Supports: Schema canonicalization and extension (kg_comprehensive_schema_minimal_turtle_v3)

15. **Using Large Language Models for the Interpretation of Building Regulations** (2024, Chong et al.)
    - DOI: https://doi.org/10.1016/j.aei.2024.102301
    - Supports: LLM-based regulatory text interpretation, KG extraction methodology

16. **Automated Building Information Modeling Compliance Check through a Large Language Model Combined with Deep Learning and Ontology** (2024, Chong et al.)
    - DOI: https://doi.org/10.3390/buildings14071983
    - Supports: Multimodal compliance grounding (text_image_multimodal_conversion_v22)

17. **Large Language Model-Driven Code Compliance Checking in Building Information Modeling** (2025, Wang & Chen)
    - DOI: https://doi.org/10.3390/electronics14112146
    - Supports: LLM-driven compliance extraction, multimodal evidence integration

### Structured Information Extraction

18. **Structured information extraction from scientific text with large language models** (2024)
    - DOI: https://doi.org/10.1038/s41467-024-45563-x
    - Supports: Schema-aware clustering for boolean maps (v17_booleanmap, Step 2), structured IE methodology

19. **CODE-ACCORD: A Corpus of Building Regulatory Data for Rule Generation towards Automatic Compliance Checking** (2024, Hettiarachchi et al.)
    - DOI: https://doi.org/10.1038/s41597-024-04320-x
    - Supports: Annotation methodology, benchmark corpus approach for regulatory IE

20. **Invariant Signature, Logic Reasoning, and Semantic NLP-Based Automated Building Code Compliance Checking (I-SNACC) Framework** (2023, Wu et al.)
    - DOI: https://doi.org/10.36680/j.itcon.2023.001
    - Supports: State-of-the-art compliance checking methodology for fire codes

### Document Layout and Format Understanding

21. **LayoutLM: Pre-training of Text and Layout for Document Image Understanding** (2020, Xu et al.)
    - DOI: https://doi.org/10.1145/3394486.3403172
    - Supports: Layout-aware IE, format signal handling (turtle_kg_keyword_v15, Step 2)

### Regulatory Document Evaluation

22. **LegalBench-RAG: A Benchmark for Retrieval-Augmented Generation in the Legal Domain** (2024, Pipitone & Houir Alami)
    - arXiv: https://arxiv.org/abs/2408.10343
    - Supports: Over-retrieval prevention, chunk granularity optimization (turtle_kg_keyword_v15, Step 3)

### German-Language and Fire-Safety Focused

23. **AgenticIE: An Adaptive Agent for Information Extraction from Complex Regulatory Documents** (2025, Colakoglu et al.)
    - arXiv: https://arxiv.org/abs/2509.11773
    - Supports: German-language fire-resistance document IE (DoP documents, directly analogous to Zulassungsdokumente)

24. **Automated Compliance Checking for BIM Models Based on Chinese-NLP and Knowledge Graph** (2024, Li, Wang & Xu)
    - DOI: https://doi.org/10.1108/ecam-10-2023-1037
    - Supports: Fire protection code extraction (GB50016), KG construction from regulatory text

### BIM and Rule Classification

25. **Classification Approach for Automated Rule-Based Compliance Checking Development** (2019, Mirdar Harijani et al.)
    - DOI: https://doi.org/10.1016/j.autcon.2019.102960
    - Supports: Rule-class-aware extraction profiles (text_only_simple_conversion_v27)

26. **Translating building legislation into a computer-executable format for evaluating compliance of design models** (2014, Eastman & Jiao)
    - DOI: https://doi.org/10.1016/j.autcon.2014.04.008
    - Supports: Regulation-to-executable IR compiler (text_only_simple_conversion_v29)

---

## Document Version History

- **Generated:** 2026-05-12
- **Updated with Literature Integration:** 2026-05-18
- **Source Data:** experiment_dashboard_snapshot.json (44 experiments total)


