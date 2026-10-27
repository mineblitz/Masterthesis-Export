# Pipeline Inventory and Paper Mapping

This file summarizes all currently registered pipelines and their specialization.
Paper links are mapped from emd.md. If a pipeline has no direct explicit mapping in emd.md, it is marked as indirect or none.

## Direct Q&A pipelines

| Pipeline | Specialty | Closest baseline / lineage | Dataset fit |
|---|---|---|---|
| direct_qa_v1 | Single-pass value extraction from pre-chunked content and a question | CODE-ACCORD direct-QA baseline | CODE-ACCORD-Entities and similar pre-chunked Q&A datasets |
| direct_qa_conditional_chunk_v1 | Same direct-QA extraction using conditional dataset `chunk` records, with one-place decimal-shift tolerance | direct_qa_v1 input-format variant | Conditional dataset records with `chunk`, `question`, and numeric `expected_value` |

`direct_qa_conditional_chunk_v1` normalizes `chunk` to `content`; `expected_value`
remains the answer used for evaluation. The dataset's `value` field is a variable label,
not the expected answer.

## 1) Text-only pipelines

| Pipeline | Specialty | Closest baseline / lineage | Paper mapping from emd.md |
|---|---|---|---|
| text_only_simple_conversion | Basic PDF text extraction + single-pass numeric extraction | Initial baseline | No direct explicit mapping |
| text_only_simple_conversion_v2 | Value glossary + stronger prompt guidance for min/max selection | v1 upgrade | No direct explicit mapping |
| text_only_simple_conversion_v3 | Modular components + filtered PDF extraction | v2 upgrade | No direct explicit mapping |
| text_only_simple_conversion_v4 | Flexible condition-based extraction (conditions without mandatory min_or_max) | v3 upgrade | Indirect via structured IE papers |
| text_only_simple_conversion_v5 | Condition translation and targeted conditional prompting | v4 upgrade | Direct: Structured information extraction from scientific text with large language models (2024); Understanding Tradeoffs in Clinical Text Extraction (2026) |
| text_only_simple_conversion_v6 | Marker markdown input instead of raw PDF text | v5 input-source upgrade | No direct explicit mapping |
| text_only_simple_conversion_v7 | Marker LLM markdown input variant | v6 input-source upgrade | No direct explicit mapping |
| text_only_simple_conversion_v8 | Keyword-context chunking over full PDF text | Retrieval-focused branch | Direct: Longtriever (2023); Enhancing Retrieval-Augmented Generation (2025); Corrective Retrieval Augmented Generation (2024); Retrieval augmented generation-driven information retrieval and question answering in construction management (2025) |
| text_only_simple_conversion_v9 | Label extraction (classification-style output) with PDF cleaner v2 | v8 sibling branch | No direct explicit mapping |
| text_only_simple_conversion_v10 | Marker markdown + keyword-context chunking | v8 marker-based branch | Direct: Longtriever (2023); Enhancing Retrieval-Augmented Generation (2025); Corrective Retrieval Augmented Generation (2024); Retrieval augmented generation-driven information retrieval and question answering in construction management (2025) |
| text_only_simple_conversion_v15 | Strict boolean-map extraction for cable/pipe type sets | Structured IE branch | Direct: Structured information extraction from scientific text with large language models (2024) |
| text_only_simple_conversion_v16 | Batched boolean-map extraction for larger variable sets | v15 scalability upgrade | Direct: Structured information extraction from scientific text with large language models (2024) |
| text_only_simple_conversion_v17 | Structured chunk ranking + retrieval quality + corrective retry | v10 retrieval-quality upgrade | Direct: Corrective Retrieval Augmented Generation (2024), plus retrieval best-practice papers |
| text_only_simple_conversion_v18 | Expanded multi-query retrieval, diversity-aware selection, evidence-aware scoring, bounded corrective retries | v17 advanced retrieval upgrade | Direct: Corrective Retrieval Augmented Generation (2024); Enhancing Retrieval-Augmented Generation (2025); Longtriever-inspired retrieval expansion |
| text_only_simple_conversion_v20 | Consistency-gated extraction with adaptive narrow/broad retries | v18 refinement | Direct: Corrective Retrieval Augmented Generation (2024); Enhancing Retrieval-Augmented Generation (2025); Longtriever-inspired retrieval expansion |
| text_only_simple_conversion_v21 | Marker-cleaned input + semantic reranking + contradiction-aware adaptive retries | v20 hardening upgrade | Direct: Corrective Retrieval Augmented Generation (2024); Enhancing Retrieval-Augmented Generation (2025); Longtriever-inspired retrieval expansion; informed by multimodal marker-cleaning learnings |
| text_only_simple_conversion_v22 | Domain query expansion + numeric normalization for fire-regulation terminology | v21 domain-query upgrade | Direct: Corrective Retrieval Augmented Generation (2024); Enhancing Retrieval-Augmented Generation (2025); Longtriever-inspired retrieval expansion |
| text_only_simple_conversion_v23 | Marker-noise-aware retrieval with stronger evidence filtering | v22 marker-noise hardening | Direct: Corrective Retrieval Augmented Generation (2024); Enhancing Retrieval-Augmented Generation (2025); Longtriever-inspired retrieval expansion |
| text_only_simple_conversion_v24 | Adaptive consistency gating with modal-value acceptance for multi-valued variables | v23 consistency refinement | Direct: Corrective Retrieval Augmented Generation (2024); Enhancing Retrieval-Augmented Generation (2025); Longtriever-inspired retrieval expansion |
| text_only_simple_conversion_v25 | Compliance-routing prefilter before extraction | v24 compliance retrieval upgrade | Direct: Semantic Text Classification for Supporting Automated Compliance Checking in Construction (2013); A platform-based Natural Language processing-driven strategy for digitalising regulatory compliance processes for the built environment (2024) |
| text_only_simple_conversion_v26 | Clause typing + semantic verifier gate for compliance-style scalar extraction | v25 structured extraction verification upgrade | Direct: Extraction of Construction Regulatory Requirements from Textual Documents Using NLP Techniques (2012); Semantic NLP-Based Information Extraction from Construction Regulatory Documents for Automated Compliance Checking (2016); A deep neural network-based method for deep information extraction using transfer learning strategies to support automated compliance checking (2021) |
| text_only_simple_conversion_v27 | Rule-class-aware extraction profiles and scoring deltas by variable family | v26 routing refinement | Direct: Semantic Text Classification for Supporting Automated Compliance Checking in Construction (2013); A platform-based Natural Language processing-driven strategy for digitalising regulatory compliance processes for the built environment (2024) |
| text_only_simple_conversion_v28 | Library-backed retrieval stack (BM25 + cross-encoder reranker + instructor schema parser) | v27 library-backed implementation branch | Indirect via retrieval/structured-output papers already mapped in v17-v27 lineage |
| text_only_simple_conversion_v29 | Deterministic regulation-to-executable clause IR compiler before scalar extraction; IR-driven scalar decision layer | v27 retrieval/verifier lineage + executable IR stage | Direct: Translating building legislation into a computer-executable format for evaluating compliance of design models (2014); supported by compliance formalization literature in Section 7 |
| text_only_simple_conversion_v30 | Deterministic object-model bridge mapping resolved fields to canonical KG/BIM validation entities/properties with provenance | v29 IR lineage + canonical object-model bridge stage | Direct: Development of an object model for automated compliance checking; supported by compliance formalization and schema-canonicalization lineage in Section 7 |
| text_only_simple_conversion_v35 | Lean compliance-routed single-pass extraction (v9 simplicity + v25 routing; all v26-v34 gates removed) | Consolidation of v25 + v9 best practices | Indirect via Group A (compliance routing) + Group B (single-pass LLM IE) anchors documented in `docs/pipelines/text_only/v35/research.md` |
| text_only_simple_conversion_v36 | Agentic ReAct controller over v35 prep with 5 tools (inspect_chunk, expand_query, retrieve_more_context, refine_extraction, finalize_answer); bounded step + token budget; v35 single-pass result is the deterministic fallback | v35 + agentic LLM controller | Direct: ReAct (Yao et al., ICLR 2023); Toolformer (Schick et al., NeurIPS 2023); CRAG (Yan et al., 2024) used as negative scoping anchor; Enhancing RAG best-practices (COLING 2025) |

## 2) Multimodal pipelines

| Pipeline | Specialty | Closest baseline / lineage | Paper mapping from emd.md |
|---|---|---|---|
| text_image_multimodal_conversion_v11 | Marker text + related images, multimodal extraction with OpenRouter | Initial multimodal baseline | Direct: DocLLM (2024), mPlug-DocOwl 1.5 (2024), Visdom (2025), SmolDocling (2025), TextMonkey (2024) |
| text_image_multimodal_conversion_v19 | Layout-aware evidence selection, multimodal evidence diversity, evidence scoring + bounded corrective retry | v11 upgrade | Direct: DocLLM (2024), mPlug-DocOwl 1.5 (2024), Visdom (2025); also aligned with OCR-free document understanding trend |
| text_image_multimodal_conversion_v21 | Marker-cleaned multimodal retrieval with hybrid text+image evidence balancing | v19 robustness upgrade | Direct: DocLLM (2024), mPlug-DocOwl 1.5 (2024), Visdom (2025); retrieval-grounding best practices |
| text_image_multimodal_conversion_v22 | Marker-aware multimodal extraction with deterministic compliance grounding and violation-report scaffold | v21 hybrid compliance grounding upgrade | Direct: Automated BIM Compliance Check through LLM+DL+Ontology (2024); LLM-Driven Code Compliance Checking in BIM (2025); builds on v19/v21 multimodal evidence lineage |
| text_image_multimodal_conversion_v23 | Layout-block-aware multimodal evidence selection using docling + rapidfuzz with BM25 text support | v22 library-backed evidence upgrade | Direct: DocLLM (2024), mPlug-DocOwl 1.5 (2024), Visdom (2025); plus layout-aware evidence selection trend |

## 3) Turtle / KG pipelines

| Pipeline | Specialty | Closest baseline / lineage | Paper mapping from emd.md |
|---|---|---|---|
| turtle_kg_conversion_v12 | Turtle/RDF condition-driven extraction | Initial Turtle/KG condition branch | Direct: Schema-aware reference as prompt improves data-efficient knowledge graph construction (2023); Knowledge graph prompting for multi-document question answering (2024) |
| turtle_kg_twostep_v13 | Two-step locate-then-extract for Turtle/KG contexts | v12 two-step reasoning upgrade | Direct: Knowledge graph prompting for multi-document question answering (2024); Enhancing Retrieval-Augmented Generation (2025); Document-Level Relation Extraction with Relation Correlations (2024) |
| turtle_kg_keyword_v14 | Two-step Turtle KG with LLM keyword expansion + chunking | v13 retrieval/keyword enhancement | Direct: Knowledge graph prompting for multi-document question answering (2024) |
| turtle_kg_keyword_v15 | Staged Turtle KG flow with deterministic Normalize -> Formalize after keyword extraction | v14 staged formalization upgrade | Direct: Information Transformation and Automated Reasoning for Automated Compliance Checking in Construction (2013); Automated Information Transformation for Automated Regulatory Compliance Checking in Construction (2015); Using Large Language Models for the Interpretation of Building Regulations (2024) |
| kg_turtle_extraction_cable_v1 | Cable-specific KG record extraction to Turtle | Shared KG extraction core | Direct: Extract, define, canonicalize (2024); Schema-aware reference as prompt (2023); How to unleash LLMs for few-shot relation extraction? (2023) |
| kg_turtle_extraction_pipe_v1 | Pipe-specific KG record extraction to Turtle | Shared KG extraction core | Direct: Extract, define, canonicalize (2024); Schema-aware reference as prompt (2023); How to unleash LLMs for few-shot relation extraction? (2023) |
| kg_comprehensive_schema_minimal_turtle_v1 | Minimal-schema to full Turtle subgraph extraction and scoring | KG comprehensive branch | Direct: Extract, define, canonicalize (2024); Schema-aware reference as prompt (2023); Document-Level Relation Extraction with Relation Correlations (2024) |
| kg_comprehensive_schema_minimal_turtle_v2 | Hierarchical branch/subtype/detail KG extraction with staged Turtle assembly and scoring | v1 hierarchical upgrade for large schemas | Direct: Extract, define, canonicalize (2024); Schema-aware reference as prompt (2023); Document-Level Relation Extraction with Relation Correlations (2024); aligned with staged extraction best practices |
| kg_comprehensive_schema_minimal_turtle_v3 | Hierarchical comprehensive KG with schema extension merge plus deterministic Turtle canonicalization before scoring | v2 additive schema-extension/canonicalization upgrade | Direct: Extending Building Information Models Semiautomatically Using Semantic NLP Techniques (2016); Extract, define, canonicalize (2024); Using Large Language Models for the Interpretation of Building Regulations (2024) |
| kg_comprehensive_schema_minimal_turtle_v4 | Hierarchical comprehensive KG with rdflib canonicalization and rdflib-based graph scoring (+ optional SHACL gate) | v3 library-backed RDF upgrade | Direct: Extending Building Information Models Semiautomatically Using Semantic NLP Techniques (2016); Extract, define, canonicalize (2024); Using Large Language Models for the Interpretation of Building Regulations (2024) |

## 4) Shared KG core

| Module | Specialty | Used by | Paper mapping from emd.md |
|---|---|---|---|
| _kg_turtle_extraction_common | Shared implementation for KG Turtle record extraction pipelines | kg_turtle_extraction_cable_v1, kg_turtle_extraction_pipe_v1 | Same as KG family mapping above |

## 5) Quick comparison recommendations

For quality benchmarking, compare within each lineage:

1. Text retrieval lineage: v8 -> v10 -> v17 -> v18 -> v20 -> v21 -> v22 -> v23 -> v24 -> v25 -> v26 -> v27 -> v28 -> v29 -> v30
2. Boolean structured extraction lineage: v15 -> v16
3. Multimodal lineage: v11 -> v19 -> v21 -> v22 -> v23
4. Turtle/KG reasoning lineage: v12 -> v13 -> v14
5. KG record extraction lineage: cable_v1 / pipe_v1 / comprehensive KG (task-dependent)
6. Comprehensive schema KG lineage: kg_comprehensive_schema_minimal_turtle_v1 -> kg_comprehensive_schema_minimal_turtle_v2 -> kg_comprehensive_schema_minimal_turtle_v3 -> kg_comprehensive_schema_minimal_turtle_v4

## 6) Weak points in pre-library retrieval pipelines (v17-v26)

Scope: This analysis targets the custom-heuristic text-retrieval lineage before the library-backed v28 branch.

1. Over-reliance on lexical substring matching
Both ranking and retrieval-quality checks are based on normalized substring containment. This can miss semantically relevant chunks with paraphrases, synonyms, or morphology variants that do not share exact token substrings.

2. Numeric bias can overweight irrelevant chunks
Rank scoring and evidence scoring reward presence of digits and common units. In technical documents this can elevate unrelated numeric tables/specs over semantically correct but less numeric passages.

3. No calibrated confidence model
Quality/evidence/consistency thresholds are static heuristics (for example 0.58, 0.45, 0.62 defaults). There is no calibration loop against ground truth per variable type, so thresholds can be brittle across domains and document styles.

4. Selection consistency can suppress valid alternatives
v20 consistency gating treats multiple numeric candidates as conflict and can block extraction when evidence is naturally multi-valued (ranges, table variants, revision notes), causing false negatives.

5. Chunk granularity is structure-driven but coarse
Chunking splits mostly by headings and blank lines. Long dense sections can remain large, reducing retrieval precision; conversely short context links across paragraph boundaries can be broken.

6. Retry strategy only expands top-ranked window
Corrective retries use narrow/broad expansion over the same ranked list rather than alternate retrieval strategies. If the initial ranking is systematically wrong, retries can repeatedly amplify that error.

7. Diversity controls can hide best single-source evidence
Per-document and per-heading caps improve coverage but may downrank the strongest evidence when the best answers cluster in one document section (common in standards/spec PDFs).

8. Marker markdown noise still affects text-only lineage
v17-v20 marker ingestion does not apply v21-style marker cleaning (image embed removal, span-tag cleanup). This can dilute rank/evidence signals when marker files contain repetitive boilerplate/image lines.

9. Limited query expansion semantics
Query variants are generated via surface-form transformations and condition concatenation. There is no learned or ontology-based expansion for domain synonyms (for example fire classes, insulation naming variants, code abbreviations).

10. Missing negative-signal handling
The retriever rewards hits but does not explicitly penalize contradictory context near candidate values (for example exclusions, deprecated values, note sections), increasing wrong-value risk in mixed-version docs.

Recommended priority order for hardening:
1. Add marker-aware cleaning to text-only retrieval input (high impact, low risk).
2. Add semantic reranking after lexical prefilter (high impact).
3. Calibrate thresholds per variable family using eval sets (high impact).
4. Add contradiction-aware scoring and provenance checks (medium-high impact).

## 7) Compliance-checking extraction mapping

This section narrows the literature specifically to automated compliance checking over building/regulatory documents, because that subfield is closer to the repository's long-term target than generic IE alone.

| Pipeline family | Additional paper mapping | Why this matters for the repo |
|---|---|---|
| v8 / v10 retrieval lineage | [Semantic NLP-Based Information Extraction from Construction Regulatory Documents for Automated Compliance Checking](https://doi.org/10.1061/(ASCE)CP.1943-5487.0000346) (2016, Zhang & El-Gohary); [A platform-based Natural Language processing-driven strategy for digitalising regulatory compliance processes for the built environment](https://doi.org/10.1080/17452007.2024.2353939) (2024) | These papers justify an explicit routing/prefilter stage before extraction: first classify or route the clause/section type, then run targeted extraction or retrieval over a narrower slice. ✅ Umgesetzt am 2026-05-12 als `text_only_simple_conversion_v25` mit requirement-first routing/prefilter fuer retrieval chunks. |
| v5 structured text extraction | [Extraction of Construction Regulatory Requirements from Textual Documents Using NLP Techniques](https://doi.org/10.1061/(ASCE)CP.1943-5487.0000216) (2012, Hjelsén & Janssen); [Semantic NLP-Based Information Extraction from Construction Regulatory Documents for Automated Compliance Checking](https://doi.org/10.1061/(ASCE)CP.1943-5487.0000346) (2016, Zhang & El-Gohary); [A deep neural network-based method for deep information extraction using transfer learning strategies to support automated compliance checking](https://doi.org/10.1016/j.autcon.2021.103834) (2021, Zhang & El-Gohary) | v5-style field extraction is closest to the classical compliance IE problem. The main lesson is that robust extraction usually needs clause typing, semantic patterns, and sometimes a learned verifier rather than prompt-only extraction. ✅ Umgesetzt am 2026-05-12 als `text_only_simple_conversion_v26` mit clause typing auf selektierten Chunks plus deterministischem semantic verifier gate fuer extrahierte Zahlenwerte. |
| v12 / v13 / v14 Turtle-KG lineage | [Information Transformation and Automated Reasoning for Automated Compliance Checking in Construction](https://doi.org/10.1061/(ASCE)0733-9364(2013)139:11(1457)) (2013, Zhang & El-Gohary); [Automated Information Transformation for Automated Regulatory Compliance Checking in Construction](https://doi.org/10.1016/j.autcon.2015.09.024) (2015, Zhang & El-Gohary); [Using Large Language Models for the Interpretation of Building Regulations](https://doi.org/10.1016/j.aei.2024.102301) (2024, Chong et al.) | These are the strongest direct matches for a staged pipeline that moves from raw regulatory text toward formal machine-readable structure. They support the repo's Extract -> Normalize -> Formalize direction. Implemented on 2026-05-12 as `turtle_kg_keyword_v15` with deterministic normalization and Turtle formalization stages after keyword-guided extraction. |
| KG record / comprehensive KG lineage | [Extending Building Information Models Semiautomatically Using Semantic NLP Techniques](https://doi.org/10.1061/(ASCE)CP.1943-5487.0000486) (2016, El-Gohary & El-Diraby); [Using Large Language Models for the Interpretation of Building Regulations](https://doi.org/10.1016/j.aei.2024.102301) (2024, Chong et al.); [Fine-tuning a large language model for automated code compliance of building regulations](https://doi.org/10.1016/j.aei.2025.103676) (2025, Liu et al.) | The key pattern is schema extension plus canonicalization. Compliance papers repeatedly need mapping from free text to a constrained target schema, which is exactly the weak point in the repo's KG family. ✅ Umgesetzt am 2026-05-12 als `kg_comprehensive_schema_minimal_turtle_v3` mit `schema_extension_v3` und deterministischer `canonicalization_v3` vor Triple-Scoring. |
| v11 multimodal / hybrid compliance lineage | [Automated Building Information Modeling Compliance Check through a Large Language Model Combined with Deep Learning and Ontology](https://doi.org/10.3390/buildings14071983) (2024, Chong et al.); [Large Language Model-Driven Code Compliance Checking in Building Information Modeling](https://doi.org/10.3390/electronics14112146) (2025, Wang & Chen) | These papers show where multimodal or BIM-coupled extraction becomes valuable: not just reading the regulation text, but connecting it to model context, generating executable checks, and returning grounded violation reports. ✅ Umgesetzt am 2026-05-12 als `text_image_multimodal_conversion_v22` mit evidenzgebundener Grounding-Stage, deterministischem Compliance-Report-Scaffold und strukturierten Provenance-Feldern. |

### Practical reading order for implementation

1. Read the El-Gohary compliance line first: 2012, 2015, 2016. It gives the clearest decomposition into classify, extract, transform, and reason.
2. Read `Using Large Language Models for the Interpretation of Building Regulations` next. It is the cleanest LLM-native bridge from regulatory text to formal representation.
3. Read the 2024 Buildings hybrid paper after that. It shows how LLMs become stronger when combined with a prior structuring stage and ontology support.
4. Use the 2024 platform paper and the 2025 BIM papers as architecture references once the extraction core is stable.

### Implementation status

- First finding from this section is now implemented: `text_only_simple_conversion_v25` adds a compliance-style routing/prefilter layer before extraction and is the active repository example of clause/section routing for retrieval.
- Second finding from this section is now implemented: `text_only_simple_conversion_v26` adds clause typing and a semantic verifier gate after extraction to require requirement-like evidence support before accepting numeric outputs.
- Third finding from this section is now implemented: `turtle_kg_keyword_v15` extends the v12/v13/v14 Turtle/KG lineage with a practical staged Extract -> Normalize -> Formalize flow and deterministic Turtle output rendering.
- Fourth finding from this section is now implemented: `kg_comprehensive_schema_minimal_turtle_v3` extends comprehensive KG extraction with schema extension merge and deterministic canonicalization (prefix completion, QName normalization, numeric literal canonicalization) before Turtle scoring. Details: `kg_comprehensive_schema_minimal_turtle_v3_findings.md`.
- Fifth finding from this section is now implemented: `text_image_multimodal_conversion_v22` extends the multimodal lineage with deterministic compliance grounding that binds extracted values to selected text/image evidence IDs and emits a violation-report style scaffold with stable provenance fields. Details: `text_image_multimodal_conversion_v22_findings.md`.
