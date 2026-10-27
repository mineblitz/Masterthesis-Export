# Literature Review: Automatic Information Extraction from Construction Documents using LLMs

**Scope:** Peer-reviewed and highly-cited papers on automated information extraction (IE) from technical construction and regulatory documents, with focus on LLM-based approaches, long document processing, multi-modal understanding, and German-language/domain-specific NLP.

**Context:** This review supports a project extracting structured data (boolean classifications, numeric values, conditional rules) from German fire-protection approval documents (Zulassungsdokumente) — 100+ page PDFs with complex conditional logic, special cases, and technical drawings.

**Last updated:** 2026-05-14 (initial sweep, 10 research directions, ~100 papers target)

---

## Format per Entry

```
## [Paper Title](URL)
- **Authors:** ...
- **Year / Venue:** ...
- **Why Relevant:** ...
- **Summary:** ...
- **Methodology Categories:** [tag1, tag2, ...]
- **Key Findings / Results:** ...
- **Relevance Score (1–5):** X — brief justification
```

**Methodology category tags used:**
`RAG`, `LLM-IE`, `Layout-Analysis`, `Multi-modal`, `NER`, `KG-Extraction`, `Rule-Extraction`, `Chunking`, `DocVQA`, `Fine-tuning`, `Prompt-Engineering`, `Table-Extraction`, `OCR`, `BIM-IFC`, `Benchmark`, `German-NLP`, `Regulatory-Compliance`, `Long-Doc`, `Hybrid-IE`, `Relation-Extraction`

---

## Targeted Literature Reviews in Scope (Added Pass)

The following review papers were searched and ranked by fit to this project (automatic structured IE from long German fire-protection approval PDFs with regulatory logic, tables, and diagrams).

1. **Fit 5/5** — [Retrieval-Augmented Generation for Large Language Models: A Survey](https://doi.org/10.48550/arxiv.2312.10997) (2023, 638 citations)
Why fit is high: directly covers chunking, retrieval, grounding, and long-context failure modes already central to this pipeline.
Status in this file: already covered in Section 2.

2. **Fit 5/5** — [A Review on BIM-based automated code compliance checking system](https://doi.org/10.1109/icriis.2017.8002486) (2017, 66 citations)
Why fit is high: closest review to construction regulation parsing and code-checking workflows that map to Brandschutz rule extraction.
Action taken: used as the primary source for additional non-duplicate foundational papers (see Section 13).

3. **Fit 4/5** — [Graph Retrieval-Augmented Generation: A Survey](https://doi.org/10.1145/3777378) (2025, 34 citations)
Why fit is high: strong for KG+RAG architectures and relational retrieval, relevant for provenance-grounded extraction and graph-backed compliance QA.
Action taken: mined references for new non-duplicate KG+RAG papers (see Section 13).

4. **Fit 4/5** — [Rationalization for explainable NLP: a survey](https://doi.org/10.3389/frai.2023.1225093) (2023, 45 citations)
Why fit is medium-high: directly relevant to evidence-grounded extraction and explanation faithfulness, but broader than construction docs.
Action taken: used to cross-check attribution/explainability references; non-duplicates added where in-scope.

5. **Fit 3/5** — [A Comprehensive Survey on Document-Level Information Extraction](https://doi.org/10.18653/v1/2024.futured-1.6) (2024)
Why fit is medium: strong document-level IE taxonomy, but less specific to regulatory construction and long scanned PDFs.
Action taken: mined references for additional non-duplicate document-level IE papers.

---

## Section 1: IE from Building Codes, Fire Safety & Regulatory Construction Documents

<!-- Papers specifically about extracting information from building codes, fire safety standards, construction regulations, approval documents -->

## [Semantic NLP-Based Information Extraction from Construction Regulatory Documents for Automated Compliance Checking](https://doi.org/10.1061/(ASCE)CP.1943-5487.0000346)
- **Authors:** Zhang, J.; El-Gohary, N.M.
- **Year / Venue:** 2016 — Journal of Computing in Civil Engineering (ASCE), 30(2)
- **Why Relevant:** The seminal NLP pipeline for extracting structured compliance information (entities, actions, conditions, numeric values) from legal regulatory documents in construction — directly maps onto extracting boolean classifications and conditional rules from German fire-protection approval PDFs.
- **Summary:** Applies a multi-stage NLP pipeline (tokenization, POS tagging, constituency/dependency parsing, semantic role labeling, coreference resolution, and ontology-guided extraction) to transform free-text building code sentences into structured compliance requirements. Dataset: International Building Code (IBC 2006). Extracts compliance objects, actions, conditions, and parameters. Provides the vocabulary and annotation schema that subsequent field papers build upon.
- **Methodology Categories:** [NER, Rule-Extraction, Regulatory-Compliance, Relation-Extraction, Hybrid-IE]
- **Key Findings / Results:** 307 citations; 85% precision / 87% recall on entity extraction; first end-to-end NLP pipeline for construction regulatory IE; annotated dataset on IBC 2006.
- **Relevance Score (1–5):** 5 — Core methodology for extracting conditional and numeric rules from technical regulatory text is precisely the task required for Zulassungsdokumente.

---

## [Integrating Semantic NLP and Logic Reasoning into a Unified System for Fully-Automated Code Checking](https://doi.org/10.1016/j.autcon.2016.08.027)
- **Authors:** Zhang, J.; El-Gohary, N.M.
- **Year / Venue:** 2017 — Automation in Construction, Vol. 73, pp. 45–57
- **Why Relevant:** Completes the extraction→reasoning→checking pipeline by coupling NLP-based IE with first-order logic and BIM checking — directly demonstrates how extracted conditional rules from regulatory PDFs can drive automated compliance decisions.
- **Summary:** Extends the 2016 IE system with a formal logic layer that transforms NLP-extracted compliance requirements into Prolog rules and checks them against BIM/IFC building models. The unified system handles conditional and compound rules. Applied to IBC 2015 including fire-related chapters. Achieves full automation from raw regulatory text to pass/fail compliance output for BIM models.
- **Methodology Categories:** [NER, Rule-Extraction, BIM-IFC, Regulatory-Compliance, Relation-Extraction]
- **Key Findings / Results:** 218 citations; demonstrated on 3 IBC chapters including fire provisions; full pipeline text → logic → BIM check requires no human intervention.
- **Relevance Score (1–5):** 5 — Full pipeline from regulatory PDF text to executable conditional rules; fire code chapters included.

---

## [A Rule-Based Semantic Approach for Automated Regulatory Compliance in the Construction Sector](https://doi.org/10.1016/j.eswa.2015.02.029)
- **Authors:** Beach, T.H.; Rezgui, Y.; Li, H.; Kasim, T.
- **Year / Venue:** 2015 — Expert Systems with Applications, Vol. 42, No. 12, pp. 5219–5231
- **Why Relevant:** Demonstrates how OWL/SWRL ontology-based semantic modeling converts free-text building regulations into machine-executable rules — a directly transferable approach for turning fire-protection approval document conditions into structured logic.
- **Summary:** Proposes a semantic-web framework that parses UK building regulatory documents using NLP, maps extracted concepts to OWL ontologies, and translates requirements into SWRL inference rules, then evaluates them against IFC-based BIM models for compliance checking.
- **Methodology Categories:** [Rule-Extraction, KG-Extraction, Regulatory-Compliance, BIM-IFC]
- **Key Findings / Results:** 143 citations; ontology-based rules successfully cover multi-condition regulatory clauses; validated on UK building regulations covering structural, thermal, and fire-separation requirements.
- **Relevance Score (1–5):** 4 — Ontology + rule extraction approach handles conditional logic structures analogous to those in fire-protection approval documents.

---

## [Ontology-Based Semantic Modeling of Regulation Constraint for Automated Construction Quality Compliance Checking](https://doi.org/10.1016/j.autcon.2012.06.006)
- **Authors:** Zhong, B.T.; Ding, L.Y.; Luo, H.B.; Zhou, Y.; Hu, Y.Z.; Hu, H.M.
- **Year / Venue:** 2012 — Automation in Construction, Vol. 28, pp. 58–70
- **Why Relevant:** Models hierarchical multi-level conditional constraints from technical construction quality standards via ontology — provides a blueprint for representing the nested conditional logic found in 100+ page fire-protection approval documents.
- **Summary:** Develops an OWL/RDF ontology schema that represents construction quality regulation constraints including their hierarchical structure (regulation → requirement → inspection item → inspection parameter → acceptance threshold). Maps Chinese GB foundation engineering standards into the ontology for automated compliance checking.
- **Methodology Categories:** [KG-Extraction, Rule-Extraction, Regulatory-Compliance, NER]
- **Key Findings / Results:** 152 citations; ontology captures multi-level conditional constraints from 3 GB standards.
- **Relevance Score (1–5):** 4 — Multi-level conditional constraint ontology directly applies to the nested rule structure in fire-protection approval documents.

---

## [A Deep Neural Network-Based Method for Deep Information Extraction Using Transfer Learning Strategies to Support Automated Compliance Checking](https://doi.org/10.1016/j.autcon.2021.103834)
- **Authors:** Zhang, R.; El-Gohary, N.
- **Year / Venue:** 2021 — Automation in Construction, Vol. 132, Article 103834
- **Why Relevant:** Updates the classical NLP approach to deep learning (BERT fine-tuning) for extracting compliance information from construction regulatory texts — shows how transformer-based models outperform rule-based NLP for the IE step required on fire-protection PDFs.
- **Summary:** Applies BiLSTM-CRF and BERT-based architectures with transfer learning for semantic role labeling and entity extraction from construction regulatory documents. Extracts agents, actions, objects, conditions, and numeric parameter values. BERT-based models significantly outperform classical NLP approaches, and transfer from construction-adjacent corpora reduces annotation requirements.
- **Methodology Categories:** [Fine-tuning, NER, Rule-Extraction, Regulatory-Compliance, Relation-Extraction]
- **Key Findings / Results:** 78 citations; BERT models outperform classical NLP by ~15% F1; transfer learning cuts labeling need by ~60%.
- **Relevance Score (1–5):** 5 — Directly shows how to fine-tune transformer models for extracting conditional rules and numeric thresholds from regulatory text matching the target task.

---

## [CODE-ACCORD: A Corpus of Building Regulatory Data for Rule Generation towards Automatic Compliance Checking](https://doi.org/10.1038/s41597-024-04320-x)
- **Authors:** Hettiarachchi, H.; Dridi, A.; Gaber, M.M.; Parsafard, P.; Bocaneala, N.; et al.
- **Year / Venue:** 2024 — Scientific Data (Nature Publishing Group)
- **Why Relevant:** Provides the first richly annotated, publicly available benchmark corpus for building regulatory NER and relation extraction — essential as a reference dataset and annotation methodology for creating training data from German fire-protection approval documents.
- **Summary:** Introduces CODE-ACCORD, a corpus of 862 self-contained building regulation sentences from England and Finland, annotated by 12 domain experts with entities and semantic relations. Contains 4,297 entities and 4,329 relations across categories including building elements, properties, conditions, actions, and numeric values. Enables training and benchmarking of deep learning and LLM approaches.
- **Methodology Categories:** [Benchmark, NER, Rule-Extraction, Regulatory-Compliance, Relation-Extraction]
- **Key Findings / Results:** 862 annotated sentences; 4,297 entities; 4,329 relations; publicly released via figshare; established as community benchmark for ACC NLP research.
- **Relevance Score (1–5):** 5 — Provides annotation schema and benchmark methodology directly applicable to creating training data from German fire-protection approval PDFs.

---

## [Invariant Signature, Logic Reasoning, and Semantic NLP-Based Automated Building Code Compliance Checking (I-SNACC) Framework](https://doi.org/10.36680/j.itcon.2023.001)
- **Authors:** Wu, J.; Xue, X.; Zhang, J.
- **Year / Venue:** 2023 — Journal of Information Technology in Construction (ITcon), Vol. 28, pp. 1–18
- **Why Relevant:** State-of-the-art framework achieving 95.2% precision and 100% recall for automated compliance checking using NLP-extracted rules from IBC 2015 fire-related chapters.
- **Summary:** Proposes I-SNACC combining geometric BIM signatures, semantic NLP for extracting compliance rules, and Prolog-based logic reasoning. Applied to IBC 2015 Chapter 10 (means of egress, includes fire exit requirements). Tested on two real building projects. Achieves 95.2% precision and 100% recall in non-compliance detection.
- **Methodology Categories:** [NER, Rule-Extraction, BIM-IFC, Regulatory-Compliance, Relation-Extraction]
- **Key Findings / Results:** 95.2% precision, 100% recall on IBC 2015 fire/egress provisions; tested on 2 real projects.
- **Relevance Score (1–5):** 5 — Demonstrates near-perfect extraction and execution of conditional numeric rules from fire-related building code chapters.

---

## [AgenticIE: An Adaptive Agent for Information Extraction from Complex Regulatory Documents](https://arxiv.org/abs/2509.11773)
- **Authors:** Colakoglu, G.; Solmaz, G.; Fürst, J.
- **Year / Venue:** 2025 — arXiv:2509.11773 [cs.CL]
- **Why Relevant:** Directly addresses key information extraction from EU construction product Declaration of Performance (DoP) documents specifying fire resistance and insulation values in English and German — virtually identical in nature to German Zulassungsdokumente.
- **Summary:** Proposes an agentic IE system (planner-executor-corresponder pattern) for extracting structured key information from DoP documents, which are EU-mandated multi-page regulatory documents covering fire resistance, insulation, and other construction product characteristics. Documents vary in layout, schema, and language (including German). Introduces a new high-density expert-annotated dataset with 15K+ annotated entities averaging 190 annotations per document. The agentic system outperforms GPT-4o (static) by +16% Exact Match.
- **Methodology Categories:** [LLM-IE, Multi-modal, Layout-Analysis, Prompt-Engineering, German-NLP, Long-Doc]
- **Key Findings / Results:** EM = 0.396 (agentic) vs 0.342 (GPT-4o) and 0.314 (GPT-4o-V); 15K+ annotated entities in English+German construction regulatory docs; planner-executor pattern critical for complex multi-page documents.
- **Relevance Score (1–5):** 5 — Closest existing published work to the target application: German-language, multi-page, fire-resistance regulatory documents with structured attribute extraction.

---

## [Automated Compliance Checking for BIM Models Based on Chinese-NLP and Knowledge Graph](https://doi.org/10.1108/ecam-10-2023-1037)
- **Authors:** Li, S.; Wang, J.; Xu, Z.
- **Year / Venue:** 2024 — Engineering, Construction and Architectural Management, Vol. 32, No. 6
- **Why Relevant:** Applies deep learning NLP and Neo4j knowledge graphs specifically to fire protection standards (Chinese GB50016), demonstrating how KG triples extracted from fire-safety regulatory text enable automated BIM compliance checking.
- **Summary:** Develops an integrative framework: (1) builds domain ontology for Chinese architectural and fire protection standards; (2) trains BERT-based models to auto-label regulatory text tokens; (3) constructs a Neo4j knowledge graph of regulatory triples; (4) implements a matching algorithm to check BIM data against KG rules. Covers fire protection code GB50016-2014.
- **Methodology Categories:** [KG-Extraction, NER, Rule-Extraction, BIM-IFC, Regulatory-Compliance, Fine-tuning]
- **Key Findings / Results:** 22 citations; successfully applied to fire protection code GB50016; KG approach provides higher automation and portability vs. traditional rule-based methods; validated on two building case studies.
- **Relevance Score (1–5):** 4 — KG construction from fire protection codes and BIM compliance checking directly demonstrates the KG-extraction pipeline applicable to Brandschutz documents.

---

## [RAGulating Compliance: A Multi-Agent Knowledge Graph for Regulatory QA](https://arxiv.org/abs/2508.09893)
- **Authors:** Agarwal, B.; Jomraj, H.S.; Kaplunov, S.; Krolick, J.; Rojkova, V.
- **Year / Venue:** 2025 — arXiv:2508.09893 [cs.AI]
- **Why Relevant:** Addresses the core retrieval and QA challenge for complex regulatory documents using a multi-agent KG+RAG hybrid — directly applicable to answering structured queries (boolean, numeric, conditional) over long fire-protection approval PDFs.
- **Summary:** Proposes a multi-agent framework that extracts SPO triplets from regulatory documents, normalizes, deduplicates, and embeds them in a unified vector database alongside full text sections. An orchestrated agent pipeline performs triplet-level retrieval for regulatory QA, providing subgraph visualization for answer traceability. Outperforms standard RAG on queries requiring relational reasoning across multiple regulatory provisions.
- **Methodology Categories:** [RAG, KG-Extraction, LLM-IE, Prompt-Engineering, Regulatory-Compliance]
- **Key Findings / Results:** Hybrid KG+RAG outperforms conventional RAG on multi-hop regulatory queries; embedded triplets provide factual grounding; subgraph visualization enables audit trail.
- **Relevance Score (1–5):** 4 — KG+RAG hybrid for regulatory QA directly addresses retrieval of conditional and boolean facts from complex approval documents at scale.

---

## Section 2: LLMs for Long Document Processing (100+ pages, Chunking, RAG)

<!-- Papers on LLM-based IE / QA over long documents, hierarchical chunking, document-level RAG -->

## [MultiDocFusion: Hierarchical and Multimodal Chunking Pipeline for Enhanced RAG on Long Industrial Documents](https://doi.org/10.18653/v1/2025.emnlp-main.1062)
- **Authors:** Shin, J.; Park, C.; Park, J.; Seo, J.; Lim, H.
- **Year / Venue:** 2025 — EMNLP 2025
- **Why Relevant:** Directly addresses RAG over long industrial documents with complex layouts, proposing an LLM-guided hierarchical document tree and DFS-based chunk grouping — the closest architectural match to processing German fire-protection approval PDFs with nested sections and technical tables.
- **Summary:** MultiDocFusion combines vision-based document region detection, OCR text extraction, and an LLM-based Document Section Hierarchical Parsing module (DSHP-LLM) to reconstruct document structure as a hierarchical tree. Chunks are assembled via depth-first traversal to preserve section semantics. Achieves 8–15% improvement in retrieval precision and 2–3% gain in ANLS QA scores over flat-chunking baselines.
- **Methodology Categories:** [RAG, Chunking, Multi-modal, OCR, Long-Doc, Layout-Analysis, LLM-IE]
- **Key Findings / Results:** +8–15% retrieval precision; +2–3% ANLS on industrial QA benchmarks vs. flat-chunking baselines.
- **Relevance Score (1–5):** 5 — Directly solves the hierarchical chunking problem for long, structured industrial documents via RAG.

---

## [Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172)
- **Authors:** Liu, N.F.; Lin, K.; Hewitt, J.; Paranjape, A.; Bevilacqua, M.; Petroni, F.; Liang, P.
- **Year / Venue:** 2023 — Transactions of the Association for Computational Linguistics (TACL)
- **Why Relevant:** Demonstrates that LLMs systematically fail to use information located in the middle of long contexts — the exact failure mode when querying a 100+ page approval document without chunking or positional-aware retrieval.
- **Summary:** Tests multiple instruction-tuned LLMs on multi-document QA and key-value retrieval tasks by varying the position of relevant context within the input window. Finds a U-shaped performance curve: accuracy is highest when the relevant passage is at the beginning or end, and degrades significantly when in the middle — even for models with 16k–100k token windows. Results hold across GPT-3.5, Claude, and open-source models.
- **Methodology Categories:** [Long-Doc, RAG, LLM-IE, Benchmark, Prompt-Engineering]
- **Key Findings / Results:** Performance drops by up to 20 percentage points when relevant content is placed in the middle of a long context; trend consistent across model families and sizes.
- **Relevance Score (1–5):** 5 — Foundational justification for why naive full-document prompting of 100+ page PDFs is insufficient; motivates chunking + retrieval-first architectures.

---

## [Retrieval-Augmented Generation for Large Language Models: A Survey](https://arxiv.org/abs/2312.10997)
- **Authors:** Gao, Y.; Xiong, Y.; Gao, X.; Jia, K.; Pan, J.; Bi, Y.; et al.
- **Year / Venue:** 2024 — arXiv preprint (>2,000 citations as of 2025)
- **Why Relevant:** Provides a systematic taxonomy of chunking strategies, retrieval methods, and augmentation pipelines — a design-space map directly applicable to building a production RAG pipeline over long approval documents.
- **Summary:** Delineates three RAG paradigms — Naive RAG, Advanced RAG, and Modular RAG — and reviews retrieval, indexing, and generation components. Chunking strategies covered include token-level, sentence-level, semantic, and structure-aware splitting. Advanced RAG discusses query rewriting, re-ranking, and iterative retrieval for multi-hop reasoning.
- **Methodology Categories:** [RAG, Chunking, Long-Doc, Hybrid-IE, Prompt-Engineering]
- **Key Findings / Results:** Hierarchical and semantic chunking consistently outperform fixed-size chunking; iterative/modular RAG improves factual precision on knowledge-intensive tasks by 5–15%.
- **Relevance Score (1–5):** 4 — Essential reference survey covering all RAG design choices relevant to the fire-protection pipeline.

---

## [M3DocRAG: Multi-modal Retrieval is What You Need for Multi-page Multi-document Understanding](https://arxiv.org/abs/2411.04952)
- **Authors:** Cho, J.; Mahata, D.; Irsoy, O.; He, Y.; Bansal, M.
- **Year / Venue:** 2024 — arXiv preprint (submitted November 2024)
- **Why Relevant:** Addresses exactly the scenario where critical evidence spans multiple pages and exists partly in figures or tables — directly analogous to fire-protection PDFs that interleave text specs with technical diagrams and numerical tables.
- **Summary:** Introduces a multi-modal RAG framework using ColPali (multi-modal retriever) and Qwen2-VL 7B to index and query 3,000+ PDFs with 40,000+ pages via a new benchmark M3DocVQA. Handles closed- and open-domain DocVQA, single-hop and multi-hop questions, and mixed evidence types (text, chart, figure). Outperforms text-only RAG baselines on MP-DocVQA benchmark.
- **Methodology Categories:** [RAG, Multi-modal, DocVQA, Long-Doc, Layout-Analysis, OCR]
- **Key Findings / Results:** State-of-the-art on MP-DocVQA; ColPali+Qwen2-VL substantially outperforms text-only RAG baselines on questions requiring chart/figure evidence.
- **Relevance Score (1–5):** 4 — Handles 100+ page PDFs with mixed visual/textual evidence; mirrors the challenge of German approval docs containing tables, diagrams, and fire-rating charts.

---

## [RAKG: Document-level Retrieval Augmented Knowledge Graph Construction](https://arxiv.org/abs/2504.09823)
- **Authors:** Zhang, H.; Si, J.; Yan, G.; Qi, B.; Cai, P.; Mao, S.; Wang, D.; Shi, B.
- **Year / Venue:** 2025 — arXiv preprint
- **Why Relevant:** Proposes a RAG loop specifically to combat long-context forgetting during entity and relation extraction from full documents, directly applicable to extracting structured facts (product IDs, threshold values, installation rules) from multi-chapter approval PDFs.
- **Summary:** RAKG extracts "pre-entities" from text chunks and uses them as RAG queries to retrieve cross-chunk coreferent context before finalising triples — reducing coreference resolution complexity and LLM context overload. Achieves 95.91% KG accuracy vs. GraphRAG's 89.71% on the MINE dataset.
- **Methodology Categories:** [RAG, KG-Extraction, LLM-IE, Long-Doc, Chunking, Relation-Extraction]
- **Key Findings / Results:** 95.91% KG accuracy on MINE dataset — +6.2 pp over GraphRAG; RAG-based coreference resolution reduces cross-chunk entity confusion.
- **Relevance Score (1–5):** 4 — The RAG-augmented KG construction loop addresses the same cross-chunk entity consistency problem that appears when extracting product specs scattered across 100+ page documents.

---

## [LegalBench-RAG: A Benchmark for Retrieval-Augmented Generation in the Legal Domain](https://arxiv.org/abs/2408.10343)
- **Authors:** Pipitone, N.; Houir Alami, G.
- **Year / Venue:** 2024 — arXiv preprint
- **Why Relevant:** Evaluates RAG retrieval precision on regulatory legal corpora, providing benchmark methodology directly transferable to evaluating RAG pipelines on German fire-protection approval standards.
- **Summary:** Benchmarks the retrieval component of RAG pipelines using 6,858 human-annotated query-answer pairs over 79M characters of legal text. Highlights that overly large retrieved chunks exceed context windows, increase hallucination risk, and inflate latency; precise minimal-snippet retrieval is preferred.
- **Methodology Categories:** [RAG, Benchmark, Regulatory-Compliance, Long-Doc, Chunking]
- **Key Findings / Results:** Precise sub-document retrieval outperforms full-document or large-chunk retrieval across all tested RAG systems; chunk granularity is the critical RAG design variable for regulatory documents.
- **Relevance Score (1–5):** 4 — Closest domain analogue to fire-protection approval compliance; reveals why chunk granularity is the critical RAG design variable.

---

## [AgenticOCR: Parsing Only What You Need for Efficient Retrieval-Augmented Generation](https://arxiv.org/abs/2602.24134)
- **Authors:** Wang, Z.; Ma, D.; Zhong, H.; Li, J.; Zhang, W.; Wang, B.; He, C.
- **Year / Venue:** 2026 — arXiv preprint
- **Why Relevant:** Introduces query-driven, on-demand OCR that avoids full-page text flooding and selectively parses only the document regions relevant to the query — critical for 100+ page approval PDFs where full OCR is noisy and the target fact may occupy a single table cell.
- **Summary:** AgenticOCR reframes OCR as an agentic, query-conditioned process: given a query, the system analyses document layout visually, identifies regions of interest, and decompresses only those visual tokens. This decouples retrieval granularity from page-level chunking. Achieves expert-level long document understanding performance on standard DocVQA benchmarks.
- **Methodology Categories:** [RAG, OCR, Long-Doc, Multi-modal, Layout-Analysis, Chunking]
- **Key Findings / Results:** Outperforms page-level full-OCR RAG baselines; expert-level scores on long-document benchmarks; significant reduction in extraneous context tokens.
- **Relevance Score (1–5):** 4 — Directly solves the problem of full-document OCR noise for PDFs where relevant facts are sparse; applicable to fire-protection product specification tables.

---

## [Long²RAG: Evaluating Long-Context & Long-Form Retrieval-Augmented Generation with Key Point Recall](https://arxiv.org/abs/2410.23000)
- **Authors:** Qi, Z.; Xu, R.; Guo, Z.; Wang, C.; Zhang, H.; Xu, W.
- **Year / Venue:** 2024 — EMNLP 2024 (Findings)
- **Why Relevant:** Introduces the Key Point Recall (KPR) metric, which measures whether LLMs incorporate specific facts from long retrieved documents — directly applicable to evaluating whether a pipeline correctly extracts numeric thresholds and boolean rules from lengthy approval documents.
- **Summary:** Long²RAG provides 280 questions across 10 domains, each with 5 retrieved documents averaging 2,444 words. The KPR metric checks alignment of key points extracted from retrieved docs against model outputs. Results show current LLMs frequently miss key points despite correct retrieval, especially for long and multi-faceted documents.
- **Methodology Categories:** [RAG, Benchmark, Long-Doc, LLM-IE, Prompt-Engineering]
- **Key Findings / Results:** Leading LLMs miss 30–50% of key points from long retrieved contexts; KPR correlation with human judgement is 0.71+; longer retrieved documents cause greater key point omission.
- **Relevance Score (1–5):** 3 — The KPR metric is a practical tool for evaluating whether critical boolean/numeric facts are captured from long approval document chunks.

---

## [Exploring Large Language Models and Hierarchical Frameworks for Classification of Large Unstructured Legal Documents](https://arxiv.org/abs/2403.06872)
- **Authors:** Prasad, N.; Boughanem, M.; Dkaki, T.
- **Year / Venue:** 2024 — ECIR 2024
- **Why Relevant:** Directly tackles the common problem of long legal/regulatory documents that lack consistent structural annotation — mirroring the challenge of German approval documents where section boundaries must be inferred before chunking.
- **Summary:** The MESc framework divides long legal case documents into parts, extracts embeddings from fine-tuned LLMs, approximates document structure via unsupervised clustering, and applies a second transformer encoder over inter-chunk representations. Achieves ~2 pp gain over prior SOTA with explicit hierarchical representation.
- **Methodology Categories:** [Long-Doc, Chunking, LLM-IE, Regulatory-Compliance, Fine-tuning, Hybrid-IE]
- **Key Findings / Results:** ~2 percentage point overall accuracy gain over SOTA on ILDC and LexGLUE; unsupervised structural clustering proves effective for annotation-free long documents.
- **Relevance Score (1–5):** 3 — The annotation-free hierarchical segmentation approach is applicable to fire-protection approval PDFs that have no pre-existing structural metadata.

---

## [SMART SLM: Structured Memory and Reasoning Transformer for Accurate Document Assistance](https://arxiv.org/abs/2512.21280)
- **Authors:** Dudeja, D.; Pal, M.
- **Year / Venue:** 2025 — arXiv preprint
- **Why Relevant:** Specifically targets long engineering manuals with dense numeric parameter lists — a near-identical document type to fire-protection approval documents — and proposes a hierarchical fact-extraction + indexed-memory pipeline to reduce hallucinated numeric values.
- **Summary:** SMART processes engineering manuals via three stages: a Tree-LSTM Grammarian extracting SRO facts from each sentence; a Memory-Augmented Neural Network indexing those facts as 384-dimensional vectors; and a 6-layer transformer fusing retrieved facts into responses. RAG is used for new document uploads via FAISS top-20 retrieval. The entire model uses 45.51M parameters.
- **Methodology Categories:** [LLM-IE, Long-Doc, Chunking, Hybrid-IE, RAG, Rule-Extraction]
- **Key Findings / Results:** 21.3% higher accuracy than GPT-2 on engineering manual QA; 64–69% parameter reduction vs. BERT/GPT-2; sub-second indexed retrieval for known documents.
- **Relevance Score (1–5):** 3 — The structured-memory approach directly addresses the hallucination problem on dense numeric/Boolean facts in long technical approval documents.

---

## Section 3: PDF Layout Analysis & Document Structure Understanding

<!-- Papers on PDF parsing, reading order detection, table/figure extraction, document segmentation -->

## [LayoutLM: Pre-training of Text and Layout for Document Image Understanding](https://doi.org/10.1145/3394486.3403172)
- **Authors:** Xu, Y.; Li, M.; Cui, L.; Huang, S.; Wei, F.; Zhou, M.
- **Year / Venue:** 2020 — KDD (ACM SIGKDD)
- **Why Relevant:** Establishes the foundational paradigm of jointly encoding text tokens with their 2-D bounding-box coordinates, directly applicable to parsing dense technical sections and footnotes in fire-protection approval PDFs where spatial position disambiguates logical structure.
- **Summary:** LayoutLM jointly pre-trains text and layout (2-D positional) embeddings on IIT-CDIP (11M scanned document images) using a BERT-style masked-LM objective extended with a 2-D position embedding and an image embedding. Fine-tuned models are evaluated on form understanding (FUNSD), receipt understanding (SROIE), and document image classification (RVL-CDIP). Achieves SOTA on all benchmarks.
- **Methodology Categories:** [Layout-Analysis, Fine-tuning, Multi-modal, NER, DocVQA]
- **Key Findings / Results:** FUNSD entity-extraction F1 79.27 (+8.55 pp over prior SOTA); SROIE 95.24 F1; RVL-CDIP 94.42% accuracy. Over 10,000 citations.
- **Relevance Score (1–5):** 5 — Directly addresses layout-aware IE from scanned/PDF documents; the positional encoding approach is essential for any pipeline parsing multi-column technical PDFs.

---

## [LayoutLMv3: Pre-training for Document AI with Unified Text and Image Masking](https://doi.org/10.48550/arXiv.2204.08387)
- **Authors:** Huang, Y.; Lv, T.; Cui, L.; Lu, Y.; Wei, F.
- **Year / Venue:** 2022 — ACM Multimedia 2022
- **Why Relevant:** Extends LayoutLM with patch-level image masking and cross-modal alignment, enabling robust region classification in visually complex documents with mixed text, figures, and tables — matching the layout heterogeneity of German approval PDFs.
- **Summary:** LayoutLMv3 introduces a unified architecture applying MLM and MIM jointly, plus a word-patch alignment (WPA) objective. Unlike LayoutLMv2, it encodes image patches directly in the same Transformer. Achieves SOTA on text-centric tasks (FUNSD, CORD, DocVQA) and image-centric tasks (PubLayNet, RVL-CDIP).
- **Methodology Categories:** [Layout-Analysis, Multi-modal, Fine-tuning, DocVQA, NER]
- **Key Findings / Results:** FUNSD F1 92.08; CORD F1 96.56; DocVQA ANLS 83.37; PubLayNet mAP 94.4 — state-of-the-art across both text-centric and image-centric benchmarks.
- **Relevance Score (1–5):** 5 — The unified text+image model handles figure-caption pairs and table regions simultaneously; critical for extracting structured data from multi-modal approval document pages.

---

## [DocLayNet: A Large Human-Annotated Dataset for Document-Layout Analysis](https://doi.org/10.1145/3534678.3539043)
- **Authors:** Pfitzmann, B.; Auer, C.; Dolfi, M.; Nassar, A.S.; Staar, P.W.J.
- **Year / Venue:** 2022 — KDD (ACM SIGKDD)
- **Why Relevant:** DocLayNet explicitly covers Law & Regulations and Patents as document categories, making it the benchmark most closely aligned with German fire-protection approval PDFs; models trained on it generalise far better to non-academic complex layouts than PubLayNet-only models.
- **Summary:** DocLayNet is a COCO-format layout annotation dataset of 80,863 human-annotated pages from six document domains including Law & Regulations, Manuals, and Government Tenders. Each page is labelled with 11 bounding-box classes. Baseline experiments show models trained on DocLayNet outperform PubLayNet-trained models on diverse layouts by ~10 pp mAP.
- **Methodology Categories:** [Layout-Analysis, Benchmark, OCR, Table-Extraction]
- **Key Findings / Results:** Best single-model mAP 76.8; human inter-annotator agreement ~85 mAP; DocLayNet-trained models outperform PubLayNet-trained models by ~10 pp. Dataset publicly available.
- **Relevance Score (1–5):** 5 — The Law & Regulations category directly mirrors the document type being parsed; the 11-class schema covers all structural elements (footnotes, page headers, tables) present in fire-protection approvals.

---

## [PubTables-1M: Towards Comprehensive Table Extraction from Unstructured Documents](https://doi.org/10.48550/arXiv.2110.00061)
- **Authors:** Smock, B.; Pesala, R.; Abraham, R.
- **Year / Venue:** 2022 — CVPR (IEEE/CVF)
- **Why Relevant:** Introduces the Table Transformer (TATR), a DETR-based model for table detection and structure recognition — directly applicable to technical specification tables in fire-protection approvals.
- **Summary:** PubTables-1M contains ~1M scientific tables with detailed, canonicalised cell-level annotations. A DETR-based model fine-tuned on this dataset handles table detection, structure recognition (row/column boundaries), and functional analysis (header vs. data cells). Models and data released via microsoft/table-transformer on GitHub.
- **Methodology Categories:** [Table-Extraction, Layout-Analysis, Benchmark, OCR]
- **Key Findings / Results:** GriTS score >0.98 for structure recognition; TATR is the best-performing tool in the DocLayNet Law & Regulations category in comparative benchmarks.
- **Relevance Score (1–5):** 5 — Fire-protection approval PDFs contain dense technical tables (cable specifications, pipe diameters, load ratings); TATR provides off-the-shelf detection and cell-level structure recovery.

---

## [Detect-Order-Construct: A Tree Construction Based Approach for Hierarchical Document Structure Analysis](https://doi.org/10.48550/arXiv.2401.11874)
- **Authors:** Wang, J.; Hu, K.; Zhong, Z.; Sun, L.; Huo, Q.
- **Year / Venue:** 2024 — Pattern Recognition
- **Why Relevant:** Addresses the full pipeline from page-object detection through reading-order prediction to hierarchical tree construction — precisely the three-stage challenge when reconstructing the logical section hierarchy of 100+-page approval documents.
- **Summary:** Decomposes Hierarchical Document Structure Analysis (HDSA) into three consecutive sub-tasks: page object detection, reading order prediction, and tree construction of the logical document hierarchy. An end-to-end Transformer is evaluated on PubLayNet, DocLayNet, HRDoc, and the new Comp-HRDoc benchmark. SOTA results on all four benchmarks.
- **Methodology Categories:** [Layout-Analysis, Benchmark, Long-Doc, Chunking]
- **Key Findings / Results:** SOTA on PubLayNet (mAP 95.6), DocLayNet (mAP 79.8), and Comp-HRDoc (reading-order ARD 3.2%); Comp-HRDoc benchmark publicly released.
- **Relevance Score (1–5):** 4 — Tree-construction is critical for navigating the nested section structure (chapters → sub-sections → clauses) common in German approval documents used for downstream IE.

---

## [DLAFormer: An End-to-End Transformer for Document Layout Analysis](https://doi.org/10.48550/arXiv.2405.11757)
- **Authors:** Wang, J.; Hu, K.; Huo, Q.
- **Year / Venue:** 2024 — ICDAR (IEEE International Conference on Document Analysis and Recognition)
- **Why Relevant:** The first single-model, end-to-end transformer that unifies region detection, logical role classification, and reading-order prediction without separate pipeline stages, reducing error propagation when processing complex technical PDFs.
- **Summary:** DLAFormer reformulates all document layout analysis sub-tasks as relation prediction problems within a unified label space, enabling a single DETR-style model to detect text regions, classify their logical roles (title, paragraph, table, figure, etc.), and predict reading order simultaneously. Outperforms all prior multi-branch and multi-stage architectures on DocLayNet and Comp-HRDoc.
- **Methodology Categories:** [Layout-Analysis, Table-Extraction, Benchmark]
- **Key Findings / Results:** Outperforms all multi-branch/multi-stage prior work on DocLayNet and Comp-HRDoc; eliminates the need for separate specialized models for each DLA sub-task while improving accuracy.
- **Relevance Score (1–5):** 4 — A single deployable model for region detection, role labelling, and ordering reduces pipeline complexity and inter-stage error accumulation.

---

## [LayoutReader: Pre-training of Text and Layout for Reading Order Detection](https://doi.org/10.18653/v1/2021.emnlp-main.389)
- **Authors:** Wang, Z.; Xu, Y.; Cui, L.; Shang, J.; Wei, F.
- **Year / Venue:** 2021 — EMNLP
- **Why Relevant:** Provides the ReadingBank benchmark (500,000 document images) and the seq2seq LayoutReader model — the standard component used by downstream parsers (including Marker/MinerU) to reorder OCR output from multi-column layouts.
- **Summary:** The authors observe that DOCX/Word XML metadata encodes the intended reading order, enabling automated construction of ReadingBank. LayoutReader adapts a seq2seq Transformer to predict the reading sequence of text lines from their bounding boxes and content. Significantly reduces reading-order errors in commercial OCR output on multi-column documents.
- **Methodology Categories:** [Layout-Analysis, Benchmark, OCR, Chunking]
- **Key Findings / Results:** 106 citations; reading-order accuracy near-perfect on ReadingBank; significantly reduces reading-order errors in Azure and Google OCR output. Dataset and models publicly available.
- **Relevance Score (1–5):** 4 — Multi-column German approval PDFs will have interleaved column text; LayoutReader-style reordering is a prerequisite before any NLP/IE component.

---

## [Nougat: Neural Optical Understanding for Academic Documents](https://doi.org/10.48550/arXiv.2308.13418)
- **Authors:** Blecher, L.; Cucurull, G.; Scialom, T.; Stojnic, R.
- **Year / Venue:** 2023 — EMNLP 2023 Findings
- **Why Relevant:** Demonstrates that an end-to-end Visual Transformer (Swin encoder + mBART decoder) can convert complex multi-column PDF pages — including tables and figures — directly to structured markup without an intermediate OCR step.
- **Summary:** Nougat adapts the Donut architecture to convert scientific PDF pages directly into Markdown/LaTeX markup. Trained on PDF–source-LaTeX pairs from arXiv, it handles multi-column layouts, mathematical equations, and table markup without explicit OCR. Key limitation: hallucination on pages without ground-truth source. The architecture became the basis for Marker, MinerU, and related tools used in this project's pipeline.
- **Methodology Categories:** [Multi-modal, OCR, Layout-Analysis, Table-Extraction, Fine-tuning]
- **Key Findings / Results:** Edit distance substantially better than PDFMiner on formula-heavy pages; fully open-source; architecture underlies Marker tool used in this project.
- **Relevance Score (1–5):** 4 — The Nougat architecture underlies the Marker tool used in this project; understanding its capabilities and limitations (hallucination, non-academic documents) directly informs quality control decisions.

---

## [A Comparative Study of PDF Parsing Tools Across Diverse Document Categories](https://doi.org/10.48550/arXiv.2410.09871)
- **Authors:** Adhikari, N.; Agarwal, S.
- **Year / Venue:** 2024 — arXiv
- **Why Relevant:** The only empirical comparison that includes a **Law & Regulations** category (matching fire-protection approval PDFs) and evaluates both text extraction accuracy and table detection across 10 tools including Nougat and Table Transformer.
- **Summary:** Ten PDF parsing tools (PyPDF, pdfminer-six, PyMuPDF, pdfplumber, pypdfium2, Unstructured, Tabula, Camelot, Nougat, TATR) are evaluated on 6 DocLayNet-derived document categories. PyMuPDF/pypdfium2 dominate simple text extraction but degrade heavily on Law & Regulations and Patents; Nougat excels on those challenging categories. TATR leads on table detection in Law & Regulations and Scientific categories.
- **Methodology Categories:** [OCR, Table-Extraction, Benchmark, Layout-Analysis, Hybrid-IE]
- **Key Findings / Results:** For Law & Regulations text extraction, Nougat outperforms all rule-based tools; TATR achieves best table-detection AP on Law & Regulations category; all tools score ≤60% on complex scientific/patent text.
- **Relevance Score (1–5):** 5 — Provides directly actionable benchmarks for the exact document category (Law & Regulations) being processed; justifies replacing rule-based parsers with Nougat+TATR for approval PDF pipelines.

---

## [Modeling Layout Reading Order as Ordering Relations for Visually-Rich Document Understanding](https://doi.org/10.48550/arXiv.2409.19672)
- **Authors:** Zhang, C.; Tu, Y.; Zhao, Y.; Yuan, C.; et al.
- **Year / Venue:** 2024 — EMNLP
- **Why Relevant:** Demonstrates that representing reading order as pairwise ordering relations captures ambiguous layouts — such as footnotes, sidebars, and multi-column text — more faithfully, directly improving downstream NER and QA on complex documents.
- **Summary:** Reformulates reading-order prediction as a set of binary ordering relations between layout elements. Establishes a new benchmark with relation-level annotations and proposes a relation-extraction-based ROP model. A plug-in pipeline inserts reading-order relations as structural input to any downstream model, consistently improving performance across 8 cross-domain VrD-IE/QA tasks.
- **Methodology Categories:** [Layout-Analysis, Relation-Extraction, Benchmark, Long-Doc]
- **Key Findings / Results:** Outperforms prior SOTA on two ROP task settings; reading-order injection improves downstream models on 8/8 cross-domain benchmarks.
- **Relevance Score (1–5):** 4 — The relation-based formulation explicitly handles the footnote-interleaved layouts typical of German technical approval documents better than simple linear reordering.

---

## Section 4: Technical Drawing, Floor Plan & Diagram Understanding with AI

<!-- Papers on floor plan parsing, CAD/diagram understanding, architectural drawing AI -->

## [CubiCasa5K: A Dataset and an Improved Multi-task Model for Floorplan Image Analysis](https://doi.org/10.1007/978-3-030-20205-7_3)
- **Authors:** Kalervo, A.; Ylioinas, J.; Haikio, M.; Karhu, A.; Kannala, J.
- **Year / Venue:** 2019 — LNCS (SCIA 2019)
- **Why Relevant:** Foundational floor-plan parsing benchmark for rooms/walls/openings and symbol-like elements; directly supports fire-protection extraction where raster plans must be converted into structured building components.
- **Summary:** Introduces CubiCasa5K, a large floorplan dataset with dense polygon annotations containing 5,000 floorplan images and more than 80 object categories. Proposes an improved multi-task CNN that jointly predicts complementary floorplan elements.
- **Methodology Categories:** [Layout-Analysis, Benchmark, Multi-modal]
- **Key Findings / Results:** 5,000 annotated floorplan samples; 80+ object classes; widely adopted benchmark for floorplan understanding.
- **Relevance Score (1–5):** 4 — Core benchmark and method for extracting structured geometry from floor-plan imagery.

---

## [Raster-to-Vector: Revisiting Floorplan Transformation](https://doi.org/10.1109/ICCV.2017.241)
- **Authors:** Liu, C.; Wu, J.; Kohli, P.; Furukawa, Y.
- **Year / Venue:** 2017 — IEEE/CVF ICCV
- **Why Relevant:** Converts noisy raster floor plans into vector primitives — the step needed before rule extraction on fire-protection drawings showing installation geometry.
- **Summary:** Learning-based framework detecting junctions, walls, and doors then using optimization to assemble a topologically consistent vector floorplan. One of the most cited works on practical floorplan vectorization.
- **Methodology Categories:** [Layout-Analysis, Hybrid-IE]
- **Key Findings / Results:** ~90% precision/recall; converted large industrial floorplan collections at scale.
- **Relevance Score (1–5):** 4 — Directly applicable to converting approval-plan images into machine-readable geometry.

---

## [VectorFloorSeg: Two-Stream Graph Attention Network for Vectorized Roughcast Floorplan Segmentation](https://doi.org/10.1109/CVPR52729.2023.00137)
- **Authors:** Yang, B.; Jiang, H.; Pan, H.; Xiao, J.
- **Year / Venue:** 2023 — IEEE/CVF CVPR
- **Why Relevant:** Graph-based segmentation on vector floorplans preserving line topology — critical for interpreting fire compartments and boundaries in approval drawings.
- **Summary:** Two graph streams (line and region) with cross-stream fusion. Improves room-boundary integrity and reduces jagged artifacts seen in image-only methods.
- **Methodology Categories:** [Layout-Analysis, Relation-Extraction, Multi-modal]
- **Key Findings / Results:** Outperforms image-based baselines on mIoU/mAcc; boundary regularity metrics introduced.
- **Relevance Score (1–5):** 4 — Excellent fit for topology-aware extraction from technical plan graphics.

---

## [Features Recognition from Piping and Instrumentation Diagrams in Image Format Using a Deep Learning Network](https://doi.org/10.3390/en12234425)
- **Authors:** Yu, E.; Cha, J.; Lee, T.; Kim, J.; Mun, D.
- **Year / Venue:** 2019 — Energies
- **Why Relevant:** Complete P&ID digitization pipeline (symbol + text + line) — directly transferable to fire-protection schematic parsing.
- **Summary:** Combines CNN-based symbol recognition with OCR text proposals and line extraction to transform image-format P&IDs into structured queryable data.
- **Methodology Categories:** [Layout-Analysis, OCR, Hybrid-IE]
- **Key Findings / Results:** Symbol recognition 91.6%, text 83.1%, line 90.6%.
- **Relevance Score (1–5):** 5 — Directly transferable to extracting components and annotations from fire-protection process schematics.

---

## [Deep-learning-based recognition of symbols and texts at an industrially applicable level from images of high-density piping and instrumentation diagrams](https://doi.org/10.1016/j.eswa.2021.115337)
- **Authors:** Kim, H.; Lee, W.; Kim, M.; Moon, Y.; Lee, T.; Cho, M.; Mun, D.
- **Year / Venue:** 2021 — Expert Systems with Applications
- **Why Relevant:** Industrial-grade recognition on dense P&ID drawings — mirrors complex fire-protection approval drawings with overlapping symbols and labels.
- **Summary:** Focuses on robustness and practical usability for high-density symbol and text regions. Frequently used as an implementation reference for production P&ID digitization.
- **Methodology Categories:** [Layout-Analysis, OCR, Hybrid-IE]
- **Key Findings / Results:** Industrial-level recognition on high-density P&ID imagery; 60+ citations.
- **Relevance Score (1–5):** 5 — High practical relevance for real-world engineering drawings in fire-protection workflows.

---

## [Advancing P&ID Digitization with YOLOv5](https://doi.org/10.1109/ICIICS59993.2023.10421368)
- **Authors:** Gajbhiye, S.; Bhamre, S.; Tadepalli, L.; Pillai, M.; Uplaonkar, D.
- **Year / Venue:** 2023 — IEEE ICIICS
- **Why Relevant:** Modern YOLO-based detector for P&ID symbol/text workflows; lightweight deployment for large drawing batches.
- **Summary:** YOLOv5 object detection combined with text-recognition for end-to-end digitization. Architecture can be integrated as front-end detector before rule extraction and KG population.
- **Methodology Categories:** [Layout-Analysis, OCR, Hybrid-IE]
- **Key Findings / Results:** ~93% accuracy, ~92% precision, ~94% recall, F1 ~93%.
- **Relevance Score (1–5):** 4 — Strong practical detector baseline for rapid P&ID ingestion.

---

## [Integration of Deep Learning for Automatic Recognition of 2D Engineering Drawings](https://doi.org/10.3390/machines11080802)
- **Authors:** Lin, Y.; Ting, Y.; Huang, Y.; Cheng, K.; Jong, W.
- **Year / Venue:** 2023 — Machines
- **Why Relevant:** CAD-like 2D engineering drawings with mixed symbols, dimensions, text — directly matching annotation extraction needs in technical fire-protection documents.
- **Summary:** Combines GD&T rule handling, image segmentation, and YOLO detection to parse dimensions, tolerances, frames, symbols, and text into structured output.
- **Methodology Categories:** [Layout-Analysis, OCR, Hybrid-IE]
- **Key Findings / Results:** ~85% view detection, ~70% annotation groups, ~80% text/symbol recognition.
- **Relevance Score (1–5):** 4 — Highly relevant for CAD annotation extraction in fire-protection document IE.

---

## [FloorNet: A Unified Framework for Floorplan Reconstruction from 3D Scans](https://doi.org/10.1007/978-3-030-01231-1_13)
- **Authors:** Liu, C.; Wu, J.; Furukawa, Y.
- **Year / Venue:** 2018 — ECCV (LNCS)
- **Why Relevant:** Multi-modal fusion of 3D scan + image + top-view for robust floorplan reconstruction; fusion pattern relevant for combining plan imagery, OCR text, and geometric context.
- **Summary:** Fuses PointNet-style 3D, top-view CNN, and RGB image branches; exchanges intermediate features across modalities. Benchmark from 155 real residential scans.
- **Methodology Categories:** [Multi-modal, Layout-Analysis, Benchmark]
- **Key Findings / Results:** Branch fusion improves reconstruction quality over single-branch alternatives.
- **Relevance Score (1–5):** 3 — Strong multimodal design pattern for geometry extraction under real-world noise.

---

## Section 5: Knowledge Graph & Ontology Population from Construction Documents

<!-- Papers on KG construction from AEC/BIM/IFC documents, ontology-driven IE -->

## [Deep Learning-Based Relation Extraction and Knowledge Graph-Based Representation of Construction Safety Requirements](https://www.sciencedirect.com/science/article/pii/S0926580522005660)
- **Authors:** Wang, X.; El-Gohary, N.
- **Year / Venue:** 2023 — Automation in Construction
- **Why Relevant:** Directly addresses extracting entities and relational triples from regulatory/safety construction texts (OSHA-style) into a structured KG — the exact pipeline task of mapping fire-protection approval conditions into structured graph triples.
- **Summary:** Trains BERT-based NER and relation extraction models on annotated construction safety regulation sentences to automatically populate a domain knowledge graph. Defines a construction-safety ontology with entity types (Object, Action, Condition, Quantity) and relation types. KG is used downstream for automated safety compliance checking.
- **Methodology Categories:** [NER, KG-Extraction, Relation-Extraction, Regulatory-Compliance, Fine-tuning, BIM-IFC]
- **Key Findings / Results:** RE F1 ≈ 0.82; NER F1 ≈ 0.87 on construction safety regulation text; 139+ citations.
- **Relevance Score (1–5):** 5 — Nearly identical task: structured triple extraction from conditional regulatory/approval specifications into a domain KG.

---

## [Knowledge-Informed Semantic Alignment and Rule Interpretation for Automated Compliance Checking](https://www.sciencedirect.com/science/article/pii/S0926580522003971)
- **Authors:** Zheng, Z.; Zhou, Y.-C.; Lu, X.-Z.; Lin, J.-R.
- **Year / Venue:** 2022 — Automation in Construction
- **Why Relevant:** Presents a full pipeline from regulatory text → NLP-parsed semantic rules → BIM compliance checking, directly modeling the conditional "if/then" structure of technical specifications — the dominant sentence type in fire-protection approval documents.
- **Summary:** Combines domain ontology, semantic alignment, and NLP-based rule interpretation for automated compliance checking. Regulations are parsed into structured semantic triples using dependency analysis and a domain lexicon. Rules are matched against BIM model attributes. Explicitly handles conditional constraints (e.g., "if penetration diameter > X then sealant thickness ≥ Y").
- **Methodology Categories:** [KG-Extraction, Rule-Extraction, Regulatory-Compliance, NER, Relation-Extraction, BIM-IFC, Hybrid-IE]
- **Key Findings / Results:** Rule parsing precision > 90% on building code sentences; cited 123 times; handles complex conditional constraint structures explicitly.
- **Relevance Score (1–5):** 5 — Conditional-rule extraction from regulatory specs is the core challenge in the fire-protection approval pipeline.

---

## [Autonomous Complex Knowledge Mining and Graph Representation Through NLP and Transfer Learning](https://www.sciencedirect.com/science/article/pii/S0926580523003345)
- **Authors:** Zhu, X.; Li, H.; Su, T.
- **Year / Venue:** 2023 — Automation in Construction
- **Why Relevant:** Demonstrates end-to-end autonomous extraction from complex multi-clause regulatory documents into a graph structure using transfer learning, applicable to German fire-protection technical documents with nested conditions and numeric thresholds.
- **Summary:** A knowledge modelling engine extracts clauses, entities, and relations from construction regulation documents using fine-tuned BERT and dependency parsing, mapped into a regulation knowledge graph (RKG). Handles complex multi-hop relationships across clauses without manual templates. Transfer learning allows adaptation to new regulation domains with limited annotated data.
- **Methodology Categories:** [KG-Extraction, NER, Relation-Extraction, Regulatory-Compliance, Fine-tuning, Long-Doc, Hybrid-IE]
- **Key Findings / Results:** Outperforms rule-based IE by ~15% F1 on complex multi-clause sentences; knowledge graph completeness validated by domain experts; 29 citations.
- **Relevance Score (1–5):** 5 — Transfer learning approach for regulation KG construction is directly applicable to German-language fire-protection approval texts.

---

## [Automatic Information Extraction from Construction Quality Inspection Regulations: A Knowledge Pattern–Based Ontological Method](https://ascelibrary.org/doi/full/10.1061/(ASCE)CO.1943-7862.0002240)
- **Authors:** Zhong, B.; Wu, H.; Xiang, R.; Guo, J.
- **Year / Venue:** 2022 — Journal of Construction Engineering and Management (ASCE)
- **Why Relevant:** Proposes an ontology-driven, pattern-based IE method for construction inspection regulation documents to populate a domain KG — the same class of document (structured technical approval/inspection text) as German fire-protection approvals.
- **Summary:** Builds a construction inspection ontology and defines knowledge patterns encoding syntactic–semantic templates for entity and relation extraction. A deep learning NLP model (BERT-based) identifies pattern matches in inspection regulation sentences. Validated on Chinese construction quality inspection standards.
- **Methodology Categories:** [KG-Extraction, NER, Relation-Extraction, Regulatory-Compliance, Fine-tuning, Rule-Extraction, Hybrid-IE]
- **Key Findings / Results:** 45+ citations; precision/recall for entity extraction ≈ 88%/85%; pattern-based constraints significantly reduce false positives vs. pure deep learning.
- **Relevance Score (1–5):** 4 — Pattern-based ontological IE from technical inspection documents closely analogous to approval-document extraction for fire-protection system properties.

---

## [Automated Code Compliance Checking Research Based on BIM and Knowledge Graph](https://www.nature.com/articles/s41598-023-34342-1)
- **Authors:** Peng, J.; Liu, X.
- **Year / Venue:** 2023 — Scientific Reports (Nature)
- **Why Relevant:** Constructs a building-regulation KG from text using NLP and integrates it with BIM for automated compliance checking — showing the full pipeline from raw regulatory text to structured graph to query-based verification relevant to component approval checking.
- **Summary:** Two-stage pipeline: (1) NLP-based extraction of rules from building codes into a knowledge graph (NER, dependency parsing, ontology mapping), and (2) BIM model querying against the KG for compliance checking. KG schema is aligned with IFC. Evaluated on Chinese national building design standards.
- **Methodology Categories:** [KG-Extraction, NER, Regulatory-Compliance, BIM-IFC, Rule-Extraction, Relation-Extraction]
- **Key Findings / Results:** 82 citations; compliance checking accuracy ~91% on test building code clauses; KG contains 2,000+ regulation nodes with 5,000+ property-value relations.
- **Relevance Score (1–5):** 4 — Direct BIM+KG compliance checking from regulation text; IFC alignment reusable for fire-protection component KG queries.

---

## [A Deep NLP-Based Method for Ontology Learning of Project-Specific Properties from BIM](https://doi.org/10.1111/mice.13013)
- **Authors:** Yin, M.; Tang, L.; Webster, C.; Yi, X.; et al.
- **Year / Venue:** 2024 — Computer-Aided Civil and Infrastructure Engineering (Wiley)
- **Why Relevant:** Proposes automated ontology learning and population from BIM data and associated documents using deep NLP — analogous to enriching a fire-protection component ontology with approval-specific attributes.
- **Summary:** Fine-tunes BERT-based models for ontology learning tasks including new property identification, taxonomy construction, and relation extraction from BIM property sets and associated textual descriptions. A pipeline maps extracted properties to IFC standardized property sets while identifying novel project-specific extensions. Tested on real construction project BIM datasets from Hong Kong.
- **Methodology Categories:** [KG-Extraction, NER, Relation-Extraction, BIM-IFC, Fine-tuning]
- **Key Findings / Results:** 36 citations; ontology learning F1 > 84% for property classification; successfully extends IFC property sets with 200+ project-specific properties.
- **Relevance Score (1–5):** 4 — Ontology enrichment from domain documents with IFC alignment is directly applicable to building a fire-component approval KG.

---

## [Information Integration of Regulation Texts and Tables for Automated Construction Safety Knowledge Mapping](https://ascelibrary.org/doi/abs/10.1061/JCEMD4.COENG-14436)
- **Authors:** Wang, H.; Xu, S.; Cui, D.; Xu, H.; Luo, H.
- **Year / Venue:** 2024 — Journal of Construction Engineering and Management (ASCE)
- **Why Relevant:** Explicitly handles the mixed text-plus-table structure of technical regulatory documents — identical to fire-protection approval documents with embedded specification tables — to build a unified safety KG.
- **Summary:** Proposes a multi-modal IE pipeline that jointly processes prose regulatory clauses and tabular data in construction safety regulations. NER extracts entities from text paragraphs while a dedicated table parsing module extracts structured attribute-value pairs; a unification layer merges both streams into a safety knowledge graph. Validated on Chinese fire and construction safety standards.
- **Methodology Categories:** [KG-Extraction, NER, Table-Extraction, Relation-Extraction, Regulatory-Compliance, Hybrid-IE, Multi-modal]
- **Key Findings / Results:** 35 citations; table+text fusion improves KG completeness by 23% over text-only IE; NER F1 ≈ 86%.
- **Relevance Score (1–5):** 5 — Directly solves the mixed text/table extraction challenge present in German fire-protection approval PDFs.

---

## [Intelligent Checking Method for Construction Schemes via Fusion of KG and LLMs](https://www.mdpi.com/2075-5309/14/8/2502)
- **Authors:** Li, H.; Yang, R.; Xu, S.; Xiao, Y.; Zhao, H.
- **Year / Venue:** 2024 — Buildings (MDPI)
- **Why Relevant:** Integrates a domain KG (populated from construction specifications via NLP) with LLMs for automated technical compliance verification — the same fusion architecture needed to query a fire-protection approval KG with a reasoning layer.
- **Summary:** Constructs a construction-domain KG by extracting logical facts and constraints from engineering specifications using NLP rule extraction, then uses an LLM (GPT-3.5/GPT-4) as a reasoning engine to check construction scheme designs against the KG. KG grounding reduces hallucination. Achieves 92.3% precision in construction scheme violation detection.
- **Methodology Categories:** [KG-Extraction, LLM-IE, Regulatory-Compliance, RAG, Rule-Extraction, Prompt-Engineering, BIM-IFC]
- **Key Findings / Results:** 39 citations; 92.3% precision in violation detection; KG grounding reduces LLM hallucination by ~30% vs. LLM-only baseline.
- **Relevance Score (1–5):** 4 — KG+LLM fusion for specification compliance is a natural next step after the current KG population pipeline.

---

## [Extract, Define, Canonicalize: An LLM-Based Framework for Knowledge Graph Construction](https://aclanthology.org/2024.emnlp-main.548/)
- **Authors:** Zhang, B.; Soh, H.
- **Year / Venue:** 2024 — EMNLP 2024
- **Why Relevant:** Provides a principled three-stage LLM prompting framework for open-domain KG construction (entity extraction → type definition → canonicalization) — directly applicable to building a structured fire-protection component KG from unstructured approval text.
- **Summary:** The EDC framework uses an LLM in three sequential stages: Extract raw entity and relation mentions from text; Define ontology types by clustering and naming extracted concepts; Canonicalize entity mentions to resolve co-references and normalize values. Evaluated on REBEL, KELM, Wiki-NRE; schema-agnostic and requires only a target ontology description as input.
- **Methodology Categories:** [KG-Extraction, LLM-IE, NER, Relation-Extraction, Prompt-Engineering, Fine-tuning]
- **Key Findings / Results:** 212 citations; improves KG F1 by 8–14% over prior SOTA on REBEL and KELM benchmarks; canonicalization step alone accounts for ~5% F1 gain.
- **Relevance Score (1–5):** 4 — EDC's schema-agnostic three-stage structure directly maps to extracting fire-protection components, their properties, and approval conditions from PDF text.

---

## [Leveraging LLM for Automated Ontology Extraction and Knowledge Graph Generation](https://arxiv.org/abs/2412.00608)
- **Authors:** Abolhasani, M.S.; Pan, R.
- **Year / Venue:** 2024 — arXiv preprint
- **Why Relevant:** Demonstrates GPT-4-based zero/few-shot automated ontology extraction and OWL/KG population from domain-specific technical documents — a directly usable methodology for automating the fire-protection approval KG construction pipeline without large annotated datasets.
- **Summary:** Prompts GPT-4 to perform end-to-end ontology extraction from technical domain texts: entity type discovery, relation type identification, axiom extraction, and instance population — all without manually labelled training data. Generated ontology serialized to OWL/Turtle and validated against expert-created reference ontologies. Few-shot examples in the prompt significantly improve schema fidelity.
- **Methodology Categories:** [LLM-IE, KG-Extraction, Prompt-Engineering, NER, Relation-Extraction]
- **Key Findings / Results:** Ontology F1 (entity types + relations) ≈ 0.79 in few-shot setting; zero-shot achieves ~0.65 F1; Turtle/OWL serialization validated with OWL reasoner.
- **Relevance Score (1–5):** 5 — Directly applicable method: GPT-4 few-shot → structured Turtle KG from technical approval documents matches the current project's LLM+Turtle extraction pipeline.

---

## Section 6: Conditional Logic & Rule Extraction from Regulatory/Legal Texts

<!-- Papers on extracting conditional rules, compliance checking, deontic logic from regulatory text -->

## [CODE-ACCORD: A Corpus of Building Regulatory Data for Rule Generation Towards Automatic Compliance Checking](https://doi.org/10.1038/s41597-024-04320-x)
*(Also listed in Section 1 — see entry there for full details.)*
- **Methodology Categories:** [NER, Relation-Extraction, Rule-Extraction, Regulatory-Compliance, Benchmark]
- **Relevance Score (1–5):** 5 — The annotation schema explicitly encodes conditional structures in building regulations.

---

## [COMPACT: Building Compliance Paralegals via Clause Graph Reasoning over Contracts](https://doi.org/10.18653/v1/2026.eacl-long.377)
- **Authors:** Singh, A.; Aggarwal, D.; Bhagat, P.; Khan, A.; Malik, S.; Azad, A.P.
- **Year / Venue:** 2026 — EACL 2026 (Long Papers)
- **Why Relevant:** Directly models obligations, exceptions, and conditional dependencies across clauses using typed clause graphs with deontic-temporal entities — exactly the structure in fire-protection approval text ("Type X is allowed IF A AND B, UNLESS C").
- **Summary:** Introduces typed clause graphs from contracts, extracting deontic-temporal entities (obligations, permissions, exceptions, conditions) and modeling cross-clause relationships including definitional dependencies, exception hierarchies, and temporal sequences. Introduces ACE, a benchmark of 4,700 compliance scenarios from 633 real-world contracts. Base LLM accuracy on ACE is only 34–57%; training on ACE yields +22–43 pp improvement.
- **Methodology Categories:** [KG-Extraction, Relation-Extraction, Rule-Extraction, LLM-IE, Fine-tuning, Regulatory-Compliance, Benchmark]
- **Key Findings / Results:** +22–43 pp improvement after fine-tuning on ACE; exception hierarchies and temporal sequences in clause graphs are critical for correct compliance reasoning.
- **Relevance Score (1–5):** 5 — The exception-hierarchy clause graph and deontic entity extraction directly map to the "UNLESS / WITH EXCEPTIONS FOR" structure in German fire-protection documents.

---

## [A Dataset for Statutory Reasoning in Tax Law Entailment and Question Answering](https://arxiv.org/abs/2005.05257)
- **Authors:** Holzenberger, N.; Blair-Stanek, A.; Van Durme, B.
- **Year / Venue:** 2020 — EMNLP 2020
- **Why Relevant:** Treats legislation as a body of prescriptive IF-THEN rules and tests whether NLP models can apply them to factual cases — a perfect conceptual model for extracting and applying conditional fire-protection rules.
- **Summary:** Constructs a dataset around the U.S. Internal Revenue Code, framing tax law application as entailment and QA. Standard NLP models perform poorly; a Prolog-based system encoding IF-THEN-UNLESS rule structures fully solves the task. The contrast underscores that NLP must learn to interpret formal conditional logic from regulatory prose.
- **Methodology Categories:** [Rule-Extraction, Regulatory-Compliance, Benchmark, Hybrid-IE]
- **Key Findings / Results:** Standard NLP models underperform despite legal domain fine-tuning; Prolog-based rule system achieves near-perfect accuracy; motivates dedicated rule-extraction pipelines before any downstream reasoning.
- **Relevance Score (1–5):** 5 — Defines the core challenge: regulatory text contains exact prescriptive rules that NLP models cannot apply reliably without first extracting the formal conditional logic.

---

## [A Compliance Checking Framework Based on Retrieval Augmented Generation](https://aclanthology.org/2025.coling-main.178/)
- **Authors:** Sun, J.; Luo, Z.; Li, Y.
- **Year / Venue:** 2025 — COLING 2025
- **Why Relevant:** Proposes a hybrid logic + semantic RAG system for verifying whether processes comply with regulations, showing how eventic graphs structured around actions and states outperform entity-centric KG approaches for regulatory knowledge.
- **Summary:** Combines static factual knowledge, a dynamic layer for regulatory and business process information, and a computational layer for retrieval and reasoning. Introduces an eventic graph representation for regulatory documents recognizing that regulatory knowledge centers on actions and states rather than entities. Achieves SOTA on Chinese and English compliance benchmarks.
- **Methodology Categories:** [RAG, KG-Extraction, Rule-Extraction, Regulatory-Compliance, Hybrid-IE]
- **Key Findings / Results:** Eventic graph representation outperforms entity-centric KGs for regulatory text; combining logical and semantic layers is superior to either alone.
- **Relevance Score (1–5):** 4 — The eventic graph concept (actions + conditions + states) applies to parsing the action-condition structures in fire-protection approval clauses.

---

## [From Complexity to Clarity: AI/NLP's Role in Regulatory Compliance](https://doi.org/10.18653/v1/2025.findings-acl.1366)
- **Authors:** Jain, J.; Dhanasekaran, N.; Diab, M.T.
- **Year / Venue:** 2025 — Findings of ACL 2025
- **Why Relevant:** A comprehensive survey mapping the state of automated data compliance using NLP/LLMs across domains — providing a structured overview of the exact challenge class facing fire-protection document processing.
- **Summary:** Analyzes the current state of automated regulatory compliance, covering document understanding, rule extraction, compliance verification, and explanation generation. Identifies three critical limitations: adaptability to new regulations, completeness of extracted rules, and trustworthiness. Surveys datasets, architectures, and evaluation protocols.
- **Methodology Categories:** [Regulatory-Compliance, LLM-IE, Rule-Extraction, Benchmark, Prompt-Engineering]
- **Key Findings / Results:** LLMs excel at classification and retrieval but struggle with systematic rule application; recommends hybrid logic + neural approaches for production compliance systems.
- **Relevance Score (1–5):** 4 — Provides a structured research landscape for the exact problem of regulatory document understanding.

---

## [Grounded Answers from Multi-Passage Regulations: Learning-to-Rank for Regulatory RAG](https://doi.org/10.18653/v1/2025.nllp-1.10)
- **Authors:** Gokhan, T.; Briscoe, T.
- **Year / Venue:** 2025 — NLLP Workshop (EMNLP)
- **Why Relevant:** Addresses the core challenge that regulatory compliance questions require aggregating evidence from multiple interrelated sections — exactly how fire-protection approval documents cross-reference conditions across clauses.
- **Summary:** Introduces ObliQA-MP, a multi-passage regulatory QA benchmark. Proposes a feature-based learning-to-rank framework integrating lexical, semantic, and graph-derived signals to improve retrieval. An obligation-centric prompting technique improves answer faithfulness.
- **Methodology Categories:** [RAG, Rule-Extraction, Regulatory-Compliance, Long-Doc, Chunking, Prompt-Engineering]
- **Key Findings / Results:** LTR framework improves Recall@10/MAP@10/nDCG@10 over baselines; LLM validation removes ~20% noisy passages; obligation-centric prompting produces more faithful citation-grounded answers.
- **Relevance Score (1–5):** 4 — Multi-passage evidence aggregation is directly applicable to fire-protection documents where a rule condition may be distributed across several clauses.

---

## [LegalBench: A Collaboratively Built Benchmark for Measuring Legal Reasoning in Large Language Models](https://arxiv.org/abs/2308.11462)
- **Authors:** Guha, N.; Nyarko, J.; Ho, D.E.; Ré, C.; et al.
- **Year / Venue:** 2023 — NeurIPS 2023
- **Why Relevant:** Includes compliance reasoning tasks that systematically benchmark LLM capability on the conditional-logic structures characteristic of technical regulations.
- **Summary:** 162 tasks covering six types of legal reasoning: issue-spotting, rule-recall, rule-application, rule-conclusion, interpretation, and rhetorical understanding. Evaluates 20 LLMs. Rule-application tasks (applying conditions to facts) are among the hardest; even GPT-4-level models fall below human expert performance on complex conditional reasoning.
- **Methodology Categories:** [LLM-IE, Benchmark, Regulatory-Compliance, Prompt-Engineering, Rule-Extraction]
- **Key Findings / Results:** 162 tasks; 20 LLMs evaluated; rule-application tasks are hardest; GPT-4 still below human expert performance on complex conditional reasoning.
- **Relevance Score (1–5):** 4 — Quantifies exactly where LLMs succeed and fail at the conditional rule-application task, providing a realistic baseline for LLM-based extraction from fire-protection documents.

---

## [ContractNLI: A Dataset for Document-level Natural Language Inference for Contracts](https://arxiv.org/abs/2110.01799)
- **Authors:** Koreeda, Y.; Manning, C.D.
- **Year / Venue:** 2021 — Findings of EMNLP 2021
- **Why Relevant:** Demonstrates that "negation by exception" — the linguistic form used in conditional rules — is a primary driver of model failure in legal document understanding, directly relevant to "Type X is allowed UNLESS condition C."
- **Summary:** Introduces document-level NLI for contracts where a system classifies whether hypotheses are entailed, contradicted, or not mentioned, and identifies supporting evidence spans. Annotates 607 contracts. Explicitly identifies "negation by exception" constructions as a key source of model errors.
- **Methodology Categories:** [Fine-tuning, Benchmark, Regulatory-Compliance, Long-Doc, Relation-Extraction]
- **Key Findings / Results:** 607 annotated contracts; document-level NLI is substantially harder than sentence-level; negation-by-exception constructions are a primary error source for all models.
- **Relevance Score (1–5):** 4 — The "negation by exception" analysis is directly applicable to fire-protection rules that use UNLESS/EXCEPT constructions.

---

## [Transformer-Based Extraction of Statutory Definitions from the U.S. Code](https://arxiv.org/abs/2504.16353)
- **Authors:** Hosabettu, A.; Shah, H.
- **Year / Venue:** 2025 — IEEE AIIoT 2025
- **Why Relevant:** Provides a concrete, high-accuracy pipeline for extracting structured legal information from a 200,000-page statutory corpus using fine-tuned domain-specific transformers with multi-stage aggregation.
- **Summary:** Multi-stage NLP pipeline for automatic extraction of defined terms, their definitions, and scope from the U.S. Code XML. A fine-tuned Legal-BERT classifier identifies definition paragraphs; related paragraphs are aggregated into definitional units; attention + rule-based patterns extract term and jurisdictional scope. Processes over 200,000 pages of federal law.
- **Methodology Categories:** [Fine-tuning, NER, Rule-Extraction, Regulatory-Compliance]
- **Key Findings / Results:** 96.8% precision and 98.9% recall (98.2% F1) on statutory definition extraction; Legal-BERT fine-tuning substantially outperforms generic BERT; document structure analysis (paragraph aggregation) is essential.
- **Relevance Score (1–5):** 3 — Multi-stage architecture (classify → aggregate → extract) and Legal-BERT fine-tuning is directly transferable to condition-action units in fire-protection approval documents.

---

## [CUAD: An Expert-Annotated NLP Dataset for Legal Contract Review](https://arxiv.org/abs/2103.06268)
- **Authors:** Hendrycks, D.; Burns, C.; Chen, A.; Ball, S.
- **Year / Venue:** 2021 — NeurIPS 2021
- **Why Relevant:** Provides a large expert-annotated benchmark for extracting 42 legally significant provision types from contracts — including conditions, exceptions, and obligations — establishing data-efficiency and fine-tuning requirements for production legal IE systems.
- **Summary:** 13,000+ annotations across 510 commercial contracts labeled for 42 clause categories (conditions, limitations, exceptions, renewal terms). Task is span extraction. Performance depends strongly on model size and training data size; substantial gaps remain for rare clause types and complex nested conditional structures.
- **Methodology Categories:** [NER, Fine-tuning, Benchmark, Regulatory-Compliance, Relation-Extraction]
- **Key Findings / Results:** 13,000+ expert annotations; 42 clause categories including conditions and exceptions; rare category performance limited by annotation volume; data efficiency and model scale are primary performance drivers.
- **Relevance Score (1–5):** 3 — Establishes realistic annotation cost and model performance expectations for production-grade conditional clause extraction.

---

## Section 7: NER & Structured IE for Technical/Engineering Domains

<!-- Papers on NER, relation extraction, slot filling in technical/engineering document corpora -->

## [GLiNER: Generalist Model for Named Entity Recognition using Bidirectional Transformer](https://arxiv.org/abs/2311.08526)
- **Authors:** Zaratiana, U.; Tomeh, N.; Holat, P.; Charnois, T.
- **Year / Venue:** 2023 — NAACL 2024
- **Why Relevant:** GLiNER recognizes arbitrary entity types specified at inference time without retraining, making it directly applicable to extracting fire-protection-specific entities like cable types (`NHXCH`, `J-H(St)H`), fire resistance classes (`EI90`), or pipe materials without any domain fine-tuning.
- **Summary:** Trains a compact bidirectional transformer encoder to match span representations against entity-type label embeddings, enabling zero-shot extraction of any entity type by simply naming it. Trained on a large diverse corpus of entity types. Outperforms ChatGPT and fine-tuned LLMs in zero-shot NER while being far cheaper to run due to parallel span scoring.
- **Methodology Categories:** [NER, LLM-IE, Fine-tuning, Prompt-Engineering, Benchmark]
- **Key Findings / Results:** Outperforms ChatGPT by a significant margin in zero-shot NER across diverse benchmarks; strong F1 on unseen entity types with a model orders of magnitude smaller than GPT-class LLMs.
- **Relevance Score (1–5):** 5 — Directly enables zero-shot extraction of arbitrary fire-protection entities (cable standards, resistance classes, installation types) without domain-specific training data.

---

## [GoLLIE: Annotation Guidelines improve Zero-Shot Information-Extraction](https://arxiv.org/abs/2310.03668)
- **Authors:** Sainz, O.; García-Ferrero, I.; Agerri, R.; Lopez de Lacalle, O.; Rigau, G.; Agirre, E.
- **Year / Venue:** 2023 — ICLR 2024
- **Why Relevant:** GoLLIE's key insight — that detailed annotation guidelines dramatically improve zero-shot IE — is directly applicable when defining extraction schemas for DIN/EN fire-protection approval documents.
- **Summary:** Fine-tunes a Code-Llama-based LLM to follow annotation guidelines expressed as Python class definitions with docstrings. The model learns to comply with extraction schemas that include field descriptions, examples, and constraints. Ablation confirms detailed guidelines are the single most important factor — vague guidelines yield poor results regardless of model size.
- **Methodology Categories:** [LLM-IE, NER, Relation-Extraction, Prompt-Engineering, Fine-tuning, KG-Extraction]
- **Key Findings / Results:** Outperforms previous zero-shot IE approaches on all evaluated tasks; guideline detail (not model scale alone) drives generalization to unseen IE schemas.
- **Relevance Score (1–5):** 5 — The annotation-guideline-as-code paradigm maps perfectly to defining fire protection entities and their relationships.

---

## [GPT-NER: Named Entity Recognition via Large Language Models](https://arxiv.org/abs/2304.10428)
- **Authors:** Wang, S.; Sun, X.; Li, X.; Ouyang, R.; Wu, F.; Zhang, T.; Li, J.; Wang, G.
- **Year / Venue:** 2023 — arXiv preprint
- **Why Relevant:** GPT-NER's self-verification strategy to prevent hallucination of non-existent entities is critical for fire-protection documents, where the LLM must not invent cable or pipe specifications that aren't actually in the text.
- **Summary:** Reformulates NER as a text-generation task by wrapping entities in special tokens, enabling direct prompting of GPT-class LLMs for sequence labeling. A self-verification step asks the model to confirm whether each extracted span truly matches the target entity type. In few-shot settings (≤25 examples), GPT-NER outperforms fine-tuned BERT-based models by large margins.
- **Methodology Categories:** [NER, LLM-IE, Prompt-Engineering]
- **Key Findings / Results:** Achieves near-supervised-baseline performance on CoNLL-2003; self-verification reduces hallucination of null-context entities; outperforms fine-tuned BERT in few-shot setting.
- **Relevance Score (1–5):** 5 — Self-verification is immediately adoptable to verify extracted values like `EI60`, `B2`, or `Halogenfrei` against their occurrence in the document.

---

## [UniversalNER: Targeted Distillation from LLMs for Open Named Entity Recognition](https://arxiv.org/abs/2308.03279)
- **Authors:** Zhou, W.; Zhang, S.; Gu, Y.; Chen, M.; Poon, H.
- **Year / Venue:** 2023 — ICLR 2024
- **Why Relevant:** Demonstrates that a distilled, domain-agnostic NER model trained on tens of thousands of entity types generalizes to entirely novel technical domains — directly relevant for fire-protection product categories not covered in standard NER training sets.
- **Summary:** Uses ChatGPT as a teacher to generate NER annotations across a 43-dataset corpus spanning 9 domains. A smaller student model (based on LLaMA) is distilled via mission-focused instruction tuning to handle tens of thousands of entity types without direct supervision on any target domain. Covers domains including law and technical literature.
- **Methodology Categories:** [NER, LLM-IE, Fine-tuning, Benchmark]
- **Key Findings / Results:** Outperforms ChatGPT by 7–9 F1 points average; beats InstructUIE on 30+ F1 average; covers law and technical literature domains.
- **Relevance Score (1–5):** 4 — Provides a strong generalizable NER backbone for arbitrary fire-protection entity types.

---

## [NuNER: Entity Recognition Encoder Pre-training via LLM-Annotated Data](https://arxiv.org/abs/2402.15343)
- **Authors:** Bogdanov, S.; Constantin, A.; Bernard, T.; Crabbé, B.; Bernard, E.
- **Year / Venue:** 2024 — arXiv preprint
- **Why Relevant:** NuNER's approach of using LLM-generated annotations to build a data-efficient NER foundation model is directly applicable when annotated fire-protection document examples are scarce.
- **Summary:** Uses GPT-4 to annotate a large, entity-type-diverse dataset, then pre-trains a compact encoder (BERT-scale) with a NER-specific objective. The resulting model is fine-tuned on target NER tasks with very few examples, outperforming foundation models of similar size in the few-shot regime. Diversity of entity types (not quantity) is the key driver of few-shot generalization.
- **Methodology Categories:** [NER, LLM-IE, Fine-tuning, Prompt-Engineering]
- **Key Findings / Results:** Outperforms BERT and RoBERTa in few-shot NER (1–20 examples); entity-type diversity in pre-training is more important than scale.
- **Relevance Score (1–5):** 4 — The few-shot regime is exactly the scenario for fire-protection extraction where labeled examples are limited.

---

## [InstructUIE: Multi-task Instruction Tuning for Unified Information Extraction](https://arxiv.org/abs/2304.08085)
- **Authors:** Wang, X.; Zhou, W.; Zu, C.; Xia, H.; Chen, T.; et al.
- **Year / Venue:** 2023 — arXiv preprint
- **Why Relevant:** Provides a unified framework for NER, relation extraction, and event extraction via natural-language instructions — applicable to jointly extracting cable designations, installation methods, and their relational constraints from approval documents.
- **Summary:** Fine-tunes an 11B-parameter Flan-T5 backbone on 32 heterogeneous IE datasets with expert-written natural-language task descriptions. A unified text-to-text format unifies NER, RE, and event extraction. Comparable performance to supervised BERT in standard settings and significant improvements over GPT-3.5 in zero-shot settings.
- **Methodology Categories:** [NER, Relation-Extraction, LLM-IE, Fine-tuning, Prompt-Engineering, Benchmark]
- **Key Findings / Results:** Outperforms GPT-3.5-turbo by large margins in zero-shot IE; achieves near-BERT performance across 32 datasets.
- **Relevance Score (1–5):** 4 — Jointly extracts entities (cable types) and their relations (installed in location X, fire resistance Y) as needed for fire-protection structured data pipelines.

---

## [An Empirical Study on Information Extraction using Large Language Models](https://arxiv.org/abs/2305.14450)
- **Authors:** Han, R.; Yang, C.; Peng, T.; Tiwari, P.; Wan, X.; Liu, L.; Wang, B.
- **Year / Venue:** 2023 — arXiv preprint
- **Why Relevant:** Systematically characterizes the gap between LLM-based IE and supervised SOTA for structured technical extraction, directly informing the choice between prompt-based vs. fine-tuned approaches for fire-protection documents.
- **Summary:** GPT-4 is evaluated across NER, relation extraction, event extraction, and coreference resolution. Proposes prompt-based remediation strategies: output format control, example selection, chain-of-thought prompting, and self-consistency. Structured prompts and role-playing significantly narrow the gap with supervised SOTA.
- **Methodology Categories:** [LLM-IE, NER, Relation-Extraction, Prompt-Engineering, Benchmark]
- **Key Findings / Results:** GPT-4 achieves ~50–60% F1 on standard IE benchmarks vs. 80–90% for supervised SOTA; structured prompt templates improve performance by 5–15 F1 points; JSON schema output format constraints reduce parsing errors by 40%.
- **Relevance Score (1–5):** 4 — Directly answers how well GPT-class models perform at structured extraction and which prompting strategies are most effective for technical text IE.

---

## [SciBERT: A Pretrained Language Model for Scientific Text](https://arxiv.org/abs/1903.10676)
- **Authors:** Beltagy, I.; Lo, K.; Cohan, A.
- **Year / Venue:** 2019 — EMNLP 2019
- **Why Relevant:** Establishes that domain-specific pre-training on technical/scientific vocabulary produces substantial NER gains — directly motivating a domain-adapted language model for fire-protection German technical terminology.
- **Summary:** Pre-trains a BERT-base model on 1.14M scientific papers using a domain-adapted WordPiece vocabulary (SCIVOCAB). Consistent, statistically significant gains over BERT on scientific NLP tasks. Released as the standard domain-adaptive baseline for scientific NLP.
- **Methodology Categories:** [NER, Fine-tuning, Benchmark]
- **Key Findings / Results:** +3.3% average F1 over BERT on scientific NER datasets; new SotA on JNLPBA, EBM-NLP, SciERC; vocabulary adaptation alone accounts for ~1.5 F1 improvement.
- **Relevance Score (1–5):** 4 — Provides foundational methodology and justification for training a TechBERT/FeuerschutzBERT variant on fire-protection documents and DIN/EN standards corpora.

---

## [REBEL: Relation Extraction By End-to-end Language generation](https://aclanthology.org/2021.findings-emnlp.204)
- **Authors:** Huguet Cabot, P.-L.; Navigli, R.
- **Year / Venue:** 2021 — Findings of EMNLP 2021
- **Why Relevant:** REBEL's ability to extract structured (subject, relation, object) triplets end-to-end from free text is directly applicable to extracting fire-protection knowledge graph triples.
- **Summary:** Frames relation extraction as a seq2seq generation task: a BART-based model generates linearized relation triplets. Training uses a Wikidata-derived dataset covering 220+ relation types. Handles overlapping entities natively through the generative decoder. Achieves SotA or competitive on CoNLL04, ADE, Re-TACRED, and NYT10.
- **Methodology Categories:** [Relation-Extraction, KG-Extraction, LLM-IE, NER]
- **Key Findings / Results:** SotA on CoNLL04 (F1=75.4), ADE (F1=79.2), NYT10 (F1=93.4); handles 220+ relation types from a single model.
- **Relevance Score (1–5):** 3 — Useful for extracting structured fire-protection (entity, property, value) triplets for KG population; requires fine-tuning on domain-specific relation types.

---

## [Structured Information Extraction from Scientific Text with Large Language Models](https://doi.org/10.1038/s41467-024-45563-x)
- **Authors:** Dagdelen, J.; Dunn, A.; Lee, S.; Walker, N.; Rosen, A.S.; Ceder, G.; Persson, K.A.; Jain, A.
- **Year / Venue:** 2024 — Nature Communications
- **Why Relevant:** Demonstrates LLM-based structured extraction from complex scientific documents with domain-specific schemas — methodology directly applicable to extracting structured fire-protection attributes from approval texts.
- **Summary:** GPT-3/GPT-4 are used via prompt engineering to extract structured information (material properties, synthesis conditions, characterization results) from materials science literature. Compares structured prompting, few-shot examples, and schema-constrained generation. Achieves performance competitive with supervised NLP baselines on key extraction tasks with minimal annotated data.
- **Methodology Categories:** [LLM-IE, Prompt-Engineering, NER, Fine-tuning]
- **Key Findings / Results:** LLM-based extraction achieves competitive performance with supervised baselines for complex technical schemas; few-shot examples significantly outperform zero-shot; schema constraints are critical for output reliability.
- **Relevance Score (1–5):** 4 — Demonstrates that LLM-based structured extraction is viable for complex technical domains with specialized vocabulary — directly applicable to fire-protection approval document schemas.

---

## Section 8: Multi-modal Document Understanding (Text + Image / Vision)

<!-- Papers on DocVQA, multi-modal transformers for documents, combining text and visual tokens -->

## [LayoutLMv2: Multi-modal Pre-training for Visually-Rich Document Understanding](https://arxiv.org/abs/2012.14740)
- **Authors:** Xu, Y.; Xu, Y.; Lv, T.; Cui, L.; Wei, F.; Wang, G.; et al.
- **Year / Venue:** 2021 — ACL
- **Why Relevant:** Extends LayoutLM by integrating full document page image features alongside text and layout, enabling the model to also read visual cues like table borders and diagram regions — directly useful when fire-protection plans include embedded graphics alongside OCR-readable text.
- **Summary:** Introduces a Transformer that simultaneously receives text token embeddings, 2D bounding-box embeddings, and image region features from the full page. A spatial-aware self-attention mechanism biases attention by relative positional relationships. Pre-training uses masked visual-language modeling and text-image alignment. Achieves SOTA on DocVQA, FUNSD, CORD, SROIE, RVL-CDIP, and InfoVQA.
- **Methodology Categories:** [Multi-modal, Layout-Analysis, Fine-tuning, DocVQA, OCR, Benchmark]
- **Key Findings / Results:** DocVQA ANLS: 78.08% (vs. 63.78% for LayoutLM v1); FUNSD F1: 82.76%; CORD F1: 94.95%.
- **Relevance Score (1–5):** 5 — Integrating image features with layout and text is essential for approval documents that combine tabular data, handwritten stamps, and technical drawings on the same page.

---

## [DocVQA: A Dataset for VQA on Document Images](https://arxiv.org/abs/2007.00398)
- **Authors:** Mathew, M.; Karatzas, D.; Jawahar, C.V.
- **Year / Venue:** 2021 — WACV
- **Why Relevant:** Establishes the standard benchmark and evaluation protocol for question answering over document images (including tables, forms, figures), providing a direct template for constructing a similar evaluation set for fire-protection approval documents.
- **Summary:** Provides 50,000 natural-language questions over 12,767 document images from real industry documents. Questions require reading handwritten text, interpreting tables and figures, and understanding structure. Gap to human performance (~94.36%) concentrated in structure-dependent and figure-embedded questions. Drove the field of document AI forward significantly.
- **Methodology Categories:** [DocVQA, Benchmark, Multi-modal, OCR, Layout-Analysis]
- **Key Findings / Results:** Best model at publication achieved ~67% ANLS vs. 94.36% human; gap concentrated in structure/figure questions.
- **Relevance Score (1–5):** 4 — Direct methodological model for defining QA evaluation over approval PDFs.

---

## [OCR-free Document Understanding Transformer (Donut)](https://arxiv.org/abs/2111.15664)
- **Authors:** Kim, G.; Hong, T.; Yim, M.; Nam, J.; et al.
- **Year / Venue:** 2022 — ECCV
- **Why Relevant:** Demonstrates that a pure image-to-text Transformer can read full document page images end-to-end without any OCR engine, removing the OCR error-propagation bottleneck critical when parsing technically complex fire-protection plans where standard OCR struggles with specialized symbols.
- **Summary:** Donut frames all document understanding tasks as image-to-JSON sequence generation: a Swin Transformer encodes the full document image, a BERT-style decoder generates structured output conditioned on a task prompt token. Pre-training uses synthetic document generator (SynthDoG). Matches or exceeds OCR-dependent baselines at significantly lower latency.
- **Methodology Categories:** [OCR, Multi-modal, Fine-tuning, DocVQA, LLM-IE, Benchmark]
- **Key Findings / Results:** DocVQA ANLS: 67.5% competitive without OCR; CORD F1: 84.1%; inference 3–10× faster than OCR-pipeline methods; SynthDoG enables domain adaptation with no real training data.
- **Relevance Score (1–5):** 5 — OCR-free end-to-end image→structured-JSON is the ideal target architecture for fire-protection documents where standard OCR mis-reads symbols in technical drawings.

---

## [Pix2Struct: Screenshot Parsing as Pretraining for Visual Language Understanding](https://arxiv.org/abs/2210.03347)
- **Authors:** Lee, K.; Joshi, M.; Turc, I.; et al.
- **Year / Venue:** 2023 — ICML
- **Why Relevant:** Introduces a pretraining objective of parsing masked web screenshots into HTML structure, producing a model that generalizes to document, chart, and figure understanding — matching the visual complexity of fire-protection approval drawings combining schematics, legends, and dense tabular annotations.
- **Summary:** Pre-trains an image-encoder/text-decoder on 80M web screenshot → simplified-HTML pairs. Input images are processed with variable-resolution patch extraction to retain fine-grained text. Fine-tuned on nine tasks across four domains (documents, charts, UI, natural images). Achieves SOTA on six of nine tasks including DocVQA and AI2D (scientific diagram QA).
- **Methodology Categories:** [Multi-modal, OCR, Fine-tuning, DocVQA, Benchmark, Table-Extraction]
- **Key Findings / Results:** DocVQA ANLS: 76.6% zero-shot → 88.0% fine-tuned; AI2D (diagram QA): 64.5% → SOTA; first single model SOTA across documents + charts + UI simultaneously.
- **Relevance Score (1–5):** 4 — Variable-resolution image input and screenshot→structure pretraining handles dense annotation and diagram layout; AI2D performance shows direct applicability to technical diagram interpretation.

---

## [mPLUG-DocOwl 1.5: Unified Structure Learning for OCR-free Document Understanding](https://arxiv.org/abs/2403.12895)
- **Authors:** Hu, A.; Xu, H.; Ye, J.; Yan, M.; Zhang, L.; et al.
- **Year / Venue:** 2024 — preprint (accepted to major venues)
- **Why Relevant:** Provides the first model that unifies recognition of all structural elements (document, table, chart, diagram) in a single pass — precisely the multi-component challenge in fire-protection PDFs where tables, schematic diagrams, and text blocks co-occur.
- **Summary:** DocOwl 1.5 introduces Unified Structure Learning across five domains via structure-aware parsing tasks and multi-grained text localization tasks. An H-Reducer module merges horizontally adjacent visual patches to reduce token count while preserving layout. Constructs DocStruct4M (4M structure-annotated examples) and DocReason25K. Uses a 7B LLM backbone.
- **Methodology Categories:** [Multi-modal, OCR, Layout-Analysis, Fine-tuning, DocVQA, Table-Extraction]
- **Key Findings / Results:** SOTA on 10 VDU benchmarks; surpasses previous 7B-LLM SOTA by >10 points on 5/10 benchmarks; DocVQA: 82.2%; ChartQA: 70.2%.
- **Relevance Score (1–5):** 5 — Unified structure learning across tables, charts, and documents directly addresses the multi-modal complexity of approval documents.

---

## [DocLayLLM: An Efficient Multi-modal Extension of LLMs for Text-rich Document Understanding](https://arxiv.org/abs/2408.15045)
- **Authors:** Liao, W.; Wang, J.; Li, H.; Wang, C.; Huang, J.; Jin, L.
- **Year / Venue:** 2025 — CVPR
- **Why Relevant:** Proposes a lightweight way to add visual patch tokens and 2D positional tokens to an existing LLM with minimal training overhead, enabling rapid adaptation to domain-specific document types (such as fire-protection approval forms) without full model retraining.
- **Summary:** DocLayLLM injects three types of tokens into a standard LLM input: visual patch tokens from a lightweight image encoder, explicit 2D bounding-box position tokens from OCR, and text tokens. Two novel training techniques: CoT Pre-training and CoT Annealing. Trained with lightweight LoRA-style adaptation. Outperforms competitors on DocVQA, FUNSD, CORD, and DocNLI with <5% of the training compute.
- **Methodology Categories:** [Multi-modal, Layout-Analysis, Fine-tuning, LLM-IE, OCR, Prompt-Engineering, DocVQA]
- **Key Findings / Results:** Outperforms competitors on DocVQA (ANLS ~88%); CoT Pre-training provides +3–5 point gains; lightweight LoRA adaptation is practical for domain fine-tuning.
- **Relevance Score (1–5):** 4 — Lightweight 2D-positional + visual token injection is directly actionable for fine-tuning on a small corpus of fire-protection PDFs without large GPU infrastructure.

---

## [Hierarchical Visual Feature Aggregation for OCR-Free Document Understanding](https://arxiv.org/abs/2411.05254)
- **Authors:** Park, J.; Choi, J.Y.; Park, J.; Han, B.
- **Year / Venue:** 2024 — NeurIPS
- **Why Relevant:** Addresses the multi-scale text problem — small annotation text and large heading text co-existing on the same page — using hierarchical multi-scale feature pyramids, exactly the challenge in fire-protection plans.
- **Summary:** An MLLM-based document understanding framework where a feature pyramid (multi-scale image encoder outputs) is aggregated via Hierarchical Visual Feature Aggregation (HVFA) using cross-attentive pooling. An additional text position prediction instruction tuning task improves text-reading at small scales. Achieves top performance on DocVQA, OCRBench, InfoVQA, and ChartQA while being more token-efficient.
- **Methodology Categories:** [Multi-modal, OCR, Layout-Analysis, Fine-tuning, DocVQA, Benchmark]
- **Key Findings / Results:** SOTA on DocVQA (ANLS ~91%), OCRBench, InfoVQA, ChartQA; text-position instruction tuning reduces truncation errors by ~30%.
- **Relevance Score (1–5):** 4 — Multi-scale hierarchical features are critical for documents where fine-grained dimension annotations and thick-line schematics co-exist at different spatial frequencies.

---

## [MCERF: Advancing Multimodal LLM Evaluation of Engineering Documentation with Enhanced Retrieval](https://arxiv.org/abs/2604.09552)
- **Authors:** Naghavi Khanghah, K.; Nguyen, H.A.; Doris, A.C.; et al.
- **Year / Venue:** 2026 — arXiv preprint
- **Why Relevant:** Directly targets multimodal RAG over engineering rulebooks and technical standards — documents structurally identical to fire-protection approval documentation — with illustrations, dense tables, and multi-hop regulation questions; reports +41% accuracy over baseline RAG.
- **Summary:** Builds on the DesignQA engineering QA benchmark and replaces text-only RAG with ColPali-based multimodal retrieval. Implements four query-routing strategies: Hybrid Lookup, Vision-to-Text fusion, High-Reasoning LLM, and Self-Consistency voting. Multi-agent routing dynamically assigns queries to appropriate pipelines.
- **Methodology Categories:** [Multi-modal, RAG, LLM-IE, Layout-Analysis, Regulatory-Compliance, Hybrid-IE, Table-Extraction, Benchmark]
- **Key Findings / Results:** +41.1% relative accuracy over best baseline RAG; vision-language retrieval eliminates complete rulebook ingestion requirement; multi-agent routing outperforms single-case routing by ~8 points on multi-modal questions.
- **Relevance Score (1–5):** 5 — Closest existing work: engineering technical standards with illustrations and tables, multimodal ColPali retrieval, multi-hop regulation reasoning — all directly transferable to German fire-protection approval document processing.

---

## [M3DocRAG: Multi-modal Retrieval is What You Need for Multi-page Multi-document Understanding](https://arxiv.org/abs/2411.04952)
*(Also listed in Section 2 — see entry there for full details.)*
- **Methodology Categories:** [RAG, Multi-modal, DocVQA, Long-Doc, Layout-Analysis]
- **Relevance Score (1–5):** 4 — Multi-modal retrieval for 100+ page PDFs with mixed text/visual evidence.

---

## [A Multistage Extraction Pipeline for Long Scanned Financial Documents: An Empirical Study in Industrial KYC Workflows](https://arxiv.org/abs/2604.26462)
- **Authors:** Han, Y.; Zhang, Y.; Wang, Y.; Jin, Y.; Ke, K.Z.; Zhao, J.
- **Year / Venue:** 2026 — arXiv preprint
- **Why Relevant:** Fire-safety approval documents are long, scanned, multilingual, and visually heterogeneous — identical characteristics to the KYC documents studied here.
- **Summary:** Integrates image preprocessing, multilingual OCR, hybrid page-level retrieval, and compact VLM-based structured extraction. Evaluated on 120 production KYC documents (~3,000 scanned pages). Ablation studies identify page-level retrieval as the dominant performance factor, especially for non-English documents. Best configuration achieves 87.27% field-level accuracy.
- **Methodology Categories:** [Multi-modal, OCR, Long-Doc, Chunking, Layout-Analysis, LLM-IE]
- **Key Findings / Results:** Best configuration (PaddleOCR + MiniCPM2.6) achieves 87.27% field-level accuracy; +31.9 pp improvement over direct PDF-to-VLM baseline; page-level retrieval is the single most impactful component.
- **Relevance Score (1–5):** 5 — Directly mirrors the Brandschutz pipeline scenario: long scanned PDFs, sparse target fields, need to isolate OCR and retrieval quality from reasoning quality.

---

## Section 9: German NLP for Technical & Legal Documents

<!-- Papers on German-language NLP, domain-specific models, German technical/legal corpora -->

## [German's Next Language Model (GBERT & GELECTRA)](https://arxiv.org/abs/2010.10906)
- **Authors:** Chan, B.; Schweter, S.; Möller, T.
- **Year / Venue:** 2020 — COLING 2020
- **Why Relevant:** Introduces GBERT and GELECTRA, the German-specific BERT/ELECTRA models that remain the foundational backbones for German NER and IE — directly applicable as pre-trained encoders for extracting entities from German fire-safety approval documents.
- **Summary:** German monolingual BERT-base/large and ELECTRA-base/large models trained on German Wikipedia, OPUS, and other German corpora using Whole Word Masking (WWM). Evaluated on GermEval 2014 NER, GermEval 2018 classification, and GNAD topic classification. Achieve state-of-the-art on all tasks, outperforming all prior German and multilingual models. Models publicly released on HuggingFace.
- **Methodology Categories:** [German-NLP, NER, Fine-tuning, Benchmark]
- **Key Findings / Results:** SoTA on GermEval 2014 NER; both BERT-large and ELECTRA-large outperform all prior German and multilingual baselines including deepset's german-BERT and mBERT; WWM consistently improves NER F1.
- **Relevance Score (1–5):** 5 — The most-used German monolingual BERT/ELECTRA backbone for fine-tuning on domain-specific German extraction tasks.

---

## [GottBERT: A Pure German Language Model](https://arxiv.org/abs/2012.02110)
- **Authors:** Scheible, R.; Thomczyk, F.; Tippmann, P.; Jaravine, V.; Boeker, M.
- **Year / Venue:** 2020 (preprint) / 2024 — EMNLP 2024
- **Why Relevant:** First pure German RoBERTa model; RoBERTa-style pre-training on large German corpus shows that monolingual German models outperform multilingual on NER — making it a strong candidate for adapting to Zulassungsdokument vocabulary.
- **Summary:** German RoBERTa-BASE model pre-trained on the German portion of the OSCAR dataset. Evaluated on CoNLL 2003 German NER, GermEval 2014 NER, and GermEval 2018. Without extensive hyperparameter tuning, already outperforms all tested German single-language BERT models and multilingual models on all NER tasks.
- **Methodology Categories:** [German-NLP, NER, Benchmark, Fine-tuning]
- **Key Findings / Results:** New SoTA on all GermEval and CoNLL German NER tasks at publication; outperforms mBERT by >2 F1 points on GermEval NER.
- **Relevance Score (1–5):** 5 — German-only RoBERTa directly applicable as the pre-training backbone for domain-adapted German technical vocabulary NER.

---

## [FLERT: Document-Level Features for Named Entity Recognition](https://arxiv.org/abs/2011.06993)
- **Authors:** Schweter, S.; Akbik, A.
- **Year / Venue:** 2020 — arXiv preprint (integrated into Flair NLP)
- **Why Relevant:** Demonstrates that document-level transformer context significantly improves German NER accuracy — critical for long Zulassungsdokumente where entity mentions span across sentences and sections.
- **Summary:** Systematic comparative evaluation of document-level features for NER in fine-tuning (XLM-R) and feature-based (LSTM-CRF with Flair embeddings) architectures. Experiments vary context window size and document-locality enforcement on CoNLL-03 (German, English, Dutch, Spanish). Document context consistently improves NER; XLM-R fine-tuning + document context yields new SoTA on several CoNLL-03 benchmarks.
- **Methodology Categories:** [NER, German-NLP, Fine-tuning, Hybrid-IE]
- **Key Findings / Results:** New SoTA on CoNLL-03 German NER with document-level XLM-R; context window ≈64 tokens is optimal; Flair integration enables plug-and-play use.
- **Relevance Score (1–5):** 4 — Document-level NER is directly applicable to multi-page German fire-safety approval documents where entities are distributed across sections.

---

## [Unsupervised Cross-lingual Representation Learning at Scale (XLM-R)](https://arxiv.org/abs/1911.02116)
- **Authors:** Conneau, A.; Khandelwal, K.; Goyal, N.; Chaudhary, V.; et al.
- **Year / Venue:** 2020 — ACL 2020
- **Why Relevant:** XLM-R is the de-facto standard multilingual encoder used across German NLP pipelines — enables zero-shot and cross-lingual transfer when labeled German technical training data is scarce.
- **Summary:** Multilingual RoBERTa model trained on 2.5TB of filtered CommonCrawl data across 100 languages. Significantly outperforms mBERT: +14.6% XNLI, +13% MLQA F1, +2.4% NER F1. German included as high-resource language with strong coverage.
- **Methodology Categories:** [German-NLP, NER, Fine-tuning, Benchmark]
- **Key Findings / Results:** +14.6% XNLI accuracy over mBERT; +2.4% NER F1; XLM-R-large competitive with strong monolingual models; publicly available.
- **Relevance Score (1–5):** 4 — Widely used as the multilingual backbone for German NLP pipelines; useful for cross-lingual transfer from English training data when German data is scarce.

---

## [EuroLLM: Multilingual Language Models for Europe](https://arxiv.org/abs/2409.16235)
- **Authors:** Martins, P.H.; Fernandes, P.; Alves, J.; Guerreiro, N.M.; et al.
- **Year / Venue:** 2024 — arXiv preprint
- **Why Relevant:** Open-weight generative LLM pre-trained specifically to balance all EU official languages including German — relevant for LLM-based IE and prompt-driven extraction from German technical documents without English-bias.
- **Summary:** Develops open-weight multilingual LLMs covering all EU official languages. Custom multilingual tokenizer with better subword coverage for morphologically complex German. Releases EuroLLM-1.7B and EuroLLM-1.7B-Instruct. Balanced training prevents English dominance; released as open weights enabling domain fine-tuning.
- **Methodology Categories:** [German-NLP, LLM-IE, Fine-tuning, Benchmark]
- **Key Findings / Results:** EuroLLM-1.7B competitive on multilingual benchmarks; balanced training prevents English dominance; multilingual tokenizer improves German subword representation.
- **Relevance Score (1–5):** 3 — EU-inclusive open LLM enabling German-language prompting and extraction; not yet specifically adapted to technical/legal German vocabulary.

---

## [GerDaLIR: A German Dataset for Legal Information Retrieval](https://doi.org/10.18653/v1/2021.nllp-1.13)
- **Authors:** Wrzalik, M.; Krechel, D.
- **Year / Venue:** 2021 — NLLP Workshop @ EMNLP 2021
- **Why Relevant:** Establishes the first standardized German legal IR benchmark and demonstrates that German language models can be fine-tuned for retrieval over German legal case documents — modeling the challenge of retrieving relevant clauses within German approval documents.
- **Summary:** 123K queries labeled with at least one relevant document in a collection of 131K German case documents. Establishes BM25 and a state-of-the-art neural re-ranking baseline. Released as open data. Neural re-ranker outperforms BM25 on German legal IR.
- **Methodology Categories:** [German-NLP, Benchmark, Regulatory-Compliance, RAG]
- **Key Findings / Results:** Neural re-ranker outperforms BM25; 123K query-document pairs from real legal proceedings; only standardized German legal document retrieval benchmark at publication.
- **Relevance Score (1–5):** 3 — German legal IR benchmark structurally analogous to retrieval over German fire-safety approval document corpora; baseline approaches transferable.

---

## [German BERT Model for Legal Named Entity Recognition](https://arxiv.org/abs/2303.05388)
- **Authors:** Darji, H.; Mitrović, J.; Granitzer, M.
- **Year / Venue:** 2023 — ICAART 2023
- **Why Relevant:** Provides a directly replicable method for fine-tuning German BERT on a domain-specific German legal NER dataset — the exact methodology applicable to creating a custom NER model for German fire-protection approval documents.
- **Summary:** Fine-tunes deepset/bert-base-german-cased on the Legal Entity Recognition (LER) dataset from German Federal Court decisions. Applies stratified 10-fold cross-validation. Evaluates on German legal entity types (person, court, legal norm, regulation, etc.). Outperforms the original BiLSTM-CRF+ baseline. Releases the fine-tuned model on HuggingFace.
- **Methodology Categories:** [German-NLP, NER, Fine-tuning, Regulatory-Compliance]
- **Key Findings / Results:** Fine-tuned German BERT outperforms BiLSTM-CRF+ on LER; domain-specific German entity types extend standard PER/ORG/LOC schema; model released on HuggingFace.
- **Relevance Score (1–5):** 5 — Closest direct analogue to the proposed fire-safety NER pipeline: fine-tuning German BERT on a small, domain-specific legal NER dataset.

---

## [Information extraction from German radiological reports for general clinical text understanding](https://doi.org/10.1038/s41598-023-29323-3)
- **Authors:** Jantscher, M.; Gunzer, F.; Kern, R.; Hassler, E.; Tschauner, S.; Reishofer, G.
- **Year / Venue:** 2023 — Scientific Reports (Nature Portfolio)
- **Why Relevant:** Demonstrates an end-to-end German-language IE framework using domain-adapted BERT on highly specialized German technical vocabulary — the same challenge faced when extracting entities from fire-safety approval documents.
- **Summary:** IE framework for German radiological free-text reports leveraging German pre-trained BERT models. Evaluates multiple German BERT variants including domain-adapted medical German BERT. Shows that pre-training on domain-relevant German text significantly improves extraction quality over generic German BERT on specialized vocabulary.
- **Methodology Categories:** [German-NLP, NER, Fine-tuning, LLM-IE, Hybrid-IE]
- **Key Findings / Results:** Domain-specific German BERT pre-training outperforms generic German BERT on clinical IE tasks; specialized German vocabulary analysis is analogous to fire-safety technical terms.
- **Relevance Score (1–5):** 4 — Direct proof-of-concept that German BERT-based IE pipelines can handle highly specialized German technical vocabulary.

---

## [Summarization of German Court Rulings](https://doi.org/10.18653/v1/2021.nllp-1.19)
- **Authors:** Glaser, I.; Moser, S.; Matthes, F.
- **Year / Venue:** 2021 — NLLP Workshop @ EMNLP 2021
- **Why Relevant:** Demonstrates that German legal text requires domain-specific pre-processing and specialized NLP pipelines; the structural analysis of German court rulings is analogous to parsing sections in German technical approval documents.
- **Summary:** Proposes automatic summarization of German court rulings as a new German NLP task. Introduces a dataset of 100K German court judgments with short summaries. Designs a domain-specific pre-processing pipeline. Best model achieves ROUGE-1 of 30.50. Identifies domain-specific challenges including legal German vocabulary and complex sentence structure.
- **Methodology Categories:** [German-NLP, Long-Doc, Benchmark]
- **Key Findings / Results:** Best ROUGE-1: 30.50 (BertSum extractive); 100K German court judgments; highest compression ratio among standard summarization benchmarks; extractive methods outperform abstractive on dense legal text.
- **Relevance Score (1–5):** 3 — Shows that German legal text processing requires specialized pipelines; preprocessing approach transferable to technical German approval documents.

---

## [Enhancing BERT With Frame Semantics to Extract Clinically Relevant Information From German Mammography Reports](https://doi.org/10.2196/68427)
- **Authors:** Reichenpfader, D.; Knupp, J.; von Däniken, S.U.; et al.
- **Year / Venue:** 2025 — Journal of Medical Internet Research (JMIR)
- **Why Relevant:** Demonstrates that augmenting BERT with structured semantic frameworks (FrameNet-style semantics) improves German clinical IE — a methodology applicable to structured extraction of fire-safety compliance attributes from German technical documents.
- **Summary:** Augments German BERT with FrameNet frame semantics to extract structured clinical information from German mammography free-text reports. Combines BERT contextual embeddings with frame-based semantic role labeling. Validated on real clinical German text. Frame-augmented BERT outperforms standard fine-tuning for German clinical slot-filling.
- **Methodology Categories:** [German-NLP, NER, Relation-Extraction, Fine-tuning, Hybrid-IE]
- **Key Findings / Results:** Frame-augmented BERT outperforms standard fine-tuning; demonstrates that structured semantic priors improve German domain-specific extraction beyond transformer representations alone.
- **Relevance Score (1–5):** 3 — Shows that adding structured domain knowledge (semantic frames) to German BERT improves extraction from specialized German text; methodology transferable to fire-safety attribute extraction.

---

## Section 10: Benchmarks & Evaluation for Document IE Systems

<!-- Papers introducing datasets, benchmarks, or evaluation frameworks for document IE -->

## [ExtractBench: A Benchmark and Evaluation Methodology for Complex Structured Extraction](https://arxiv.org/abs/2602.12247)
- **Authors:** Ferguson, N.; Pennington, J.; Beghian, N.; Mohan, A.; Kiela, D.; Agrawal, S.; Nguyen, T.H.
- **Year / Venue:** 2026 — arXiv preprint
- **Why Relevant:** Directly addresses the gap of evaluating PDF-to-JSON extraction at enterprise-scale schema breadth — exactly the challenge of extracting structured data (cable/pipe specs, approval criteria) from fire-safety approval PDFs. Introduces schema-aware scoring that distinguishes exact match, tolerance, semantic equivalence, omission vs. hallucination, and array alignment.
- **Summary:** Pairs 35 real PDF documents with JSON schemas and human-annotated gold labels, yielding 12,867 evaluatable fields. Baseline evaluations test GPT-5/5.2, Gemini-3 Flash/Pro, and Claude 4.5. Performance degrades sharply with schema breadth, with 0% valid output on a 369-field financial reporting schema. Open-source at GitHub.
- **Methodology Categories:** [Benchmark, LLM-IE, Prompt-Engineering, Long-Doc]
- **Key Findings / Results:** Frontier models remain unreliable on realistic schemas; 0% valid output on wide schemas (369 fields); distinguishing omission from hallucination is critical.
- **Relevance Score (1–5):** 5 — Provides both the benchmark design and evaluation methodology most directly applicable to schema-based structured extraction from technical approval documents.

---

## [REGREACT: Self-Correcting Multi-Agent Pipelines for Structured Regulatory Information Extraction](https://arxiv.org/abs/2604.12054)
- **Authors:** Ali, M.; Abdallah, A.; Jatowt, A.
- **Year / Venue:** 2026 — arXiv preprint
- **Why Relevant:** Directly targets structured IE from regulatory documents — the same class as German fire-safety standards (DIN, LBO, MLAR). Addresses hierarchical criterion extraction, cross-reference resolution, and hallucination correction.
- **Summary:** Decomposes regulatory IE into seven specialized stages, each with an Observe–Diagnose–Repair (ODR) loop that validates outputs against the source document. Constructs a typed criterion graph to ensure structural accuracy and resolves external cross-references inline. Applied to three EU Taxonomy Delegated Acts, produces 242 activities with 4,800+ hierarchical criteria. Outperforms GPT-4o single-pass baseline across all metrics.
- **Methodology Categories:** [LLM-IE, Regulatory-Compliance, KG-Extraction, Prompt-Engineering, Benchmark]
- **Key Findings / Results:** Multi-agent ODR outperforms GPT-4o single-pass on all structural/semantic metrics; single-pass LLMs hallucinate structural elements; dataset and code publicly available.
- **Relevance Score (1–5):** 5 — Closest existing work to the Brandschutz IE scenario: regulatory documents, hierarchical criteria, hallucination control, and a constructed evaluation dataset.

---

## [UNIKIE-BENCH: Benchmarking Large Multimodal Models for Key Information Extraction in Visual Documents](https://arxiv.org/abs/2602.07038)
- **Authors:** Ji, Y.; Xu, Z.; Liu, Z.; Chen, Z.; et al.
- **Year / Venue:** 2026 — arXiv preprint
- **Why Relevant:** Evaluates multimodal LLMs on key information extraction from visually complex documents — directly relevant to fire-protection approval PDFs with complex layouts, tables, stamps, and diagrams.
- **Summary:** Provides two evaluation tracks: constrained-category (predefined schemas) and open-category (extract any explicitly present information). Tests 15 state-of-the-art LMMs. Identifies substantial performance degradation under diverse schema definitions, long-tail key fields, and complex layouts. Grounding accuracy and layout-aware reasoning are persistent failure modes.
- **Methodology Categories:** [Benchmark, Multi-modal, DocVQA, Layout-Analysis, LLM-IE]
- **Key Findings / Results:** 15 LMMs tested; performance degrades significantly for long-tail fields and complex layouts; current LMMs struggle with layout-aware grounding.
- **Relevance Score (1–5):** 4 — Benchmarks exactly the multimodal KIE capabilities needed for scanned fire-protection approval documents with heterogeneous layouts.

---

## [DTBench: A Synthetic Benchmark for Document-to-Table Extraction](https://arxiv.org/abs/2602.13812)
- **Authors:** Guo, Y.; Du, Z.; Tang, N.; Tang, K.; Ge, C.; Gao, Y.
- **Year / Venue:** 2026 — arXiv preprint
- **Why Relevant:** Fire-protection documents contain specification tables (fire resistance durations, cable cross-sections, pipe diameters); this benchmark targets the capability taxonomy for transforming unstructured document content into structured tables.
- **Summary:** Uses a reverse Table2Doc paradigm to produce a capability-aware benchmark with a two-level taxonomy covering 5 major categories and 13 subcategories. Mainstream LLMs are evaluated, revealing substantial performance gaps in reasoning and conflict resolution. Scalable benchmark construction without expensive human annotation.
- **Methodology Categories:** [Benchmark, Table-Extraction, LLM-IE, Prompt-Engineering]
- **Key Findings / Results:** Substantial performance gaps across models; reasoning and conflict resolution consistently hardest; 5 major/13 subcategory taxonomy provides reusable evaluation structure.
- **Relevance Score (1–5):** 4 — Structured table extraction from technical documents is a core subtask of the Brandschutz IE pipeline.

---

## [TextMineX: Data, Evaluation Framework and Ontology-guided LLM Pipeline for Humanitarian Mine Action](https://arxiv.org/abs/2509.15098)
- **Authors:** Zhou, C.; Solmaz, G.; Cirillo, F.; Gashteovski, K.; Fürst, J.
- **Year / Venue:** 2025 — arXiv preprint
- **Why Relevant:** Provides a complete blueprint for domain-specific IE: a dataset, an evaluation framework combining human annotations with LLM-as-Judge, and an ontology-guided prompting strategy — all applied to a specialized safety-critical operational domain analogous to fire-protection systems.
- **Summary:** Extracts (subject, relation, object) triples from humanitarian mine action reports using an ontology-aligned LLM pipeline. Evaluation framework combines human-annotated gold triples with an LLM-as-Judge protocol to mitigate position bias. Ontology-aligned prompts improve extraction accuracy by 44.2%, reduce hallucinations by 22.5%, and enhance format adherence by 20.9%.
- **Methodology Categories:** [Benchmark, LLM-IE, KG-Extraction, Prompt-Engineering, Relation-Extraction]
- **Key Findings / Results:** Ontology-aligned prompts: +44.2% accuracy, −22.5% hallucination, +20.9% format adherence. LLM-as-Judge with bias mitigation shown viable as evaluation protocol.
- **Relevance Score (1–5):** 5 — Ontology-guided evaluation framework and hallucination-reduction methodology are directly transferable to fire-safety IE where a Brandschutz ontology already exists.

---

## [Benchmarking Multi-Agent LLM Architectures for Financial Document Processing](https://arxiv.org/abs/2603.22651)
- **Authors:** Kulkarni, S.; Kulkarni, Y.
- **Year / Venue:** 2026 — arXiv preprint
- **Why Relevant:** Compares four multi-agent orchestration architectures on structured IE from complex regulatory/compliance documents (SEC filings) — directly informing architecture choices for a fire-safety IE system and establishing cost-accuracy tradeoffs.
- **Summary:** Four architectures compared on 10,000 SEC filings (10-K, 10-Q, 8-K) covering 25 field types across five LLMs. Evaluation axes: field-level F1, document-level accuracy, latency, cost-per-document, token efficiency. Reflexive (self-correcting) architectures achieve highest F1 (0.943) at 2.3× cost; hierarchical supervisor-worker architectures offer best cost-accuracy tradeoff (F1 0.921 at 1.4× cost).
- **Methodology Categories:** [LLM-IE, Benchmark, Regulatory-Compliance, Long-Doc, Prompt-Engineering]
- **Key Findings / Results:** Best F1: reflexive architecture 0.943; hierarchical: 0.921 at 1.4× cost; hybrid semantic caching + adaptive retry recovers 89% of accuracy at only 1.15× cost.
- **Relevance Score (1–5):** 4 — Provides concrete F1 baselines and architecture-selection guidance for multi-field structured extraction from compliance documents comparable to German fire-safety approvals.

---

## [Not All Needles Are Found: Fact Distribution and Hallucination Risks in Long-Context LLMs](https://arxiv.org/abs/2601.02023)
- **Authors:** Ebrahimzadeh, A.; Salili, S.M.
- **Year / Venue:** 2026 — arXiv preprint
- **Why Relevant:** Fire-safety approval documents are long and relevant technical specifications are sparsely distributed; this study precisely evaluates how LLMs fail at literal extraction and how anti-hallucination prompts can paradoxically reduce recall.
- **Summary:** Extended needle-in-a-haystack benchmark evaluating four production LLMs on literal extraction, logical inference, and hallucination risk separately. Varies fact placement, corpus-level fact distribution, and anti-hallucination (AH) prompt strategies. AH instructions make some models overly conservative, sharply reducing literal extraction accuracy.
- **Methodology Categories:** [Long-Doc, LLM-IE, Benchmark, Prompt-Engineering]
- **Key Findings / Results:** Performance varies dramatically across models under realistic evidence-dilution conditions; AH prompts reduce accuracy in literal extraction by inducing excessive refusal; retrieval quality matters more than context length.
- **Relevance Score (1–5):** 4 — Directly informs how to design prompts and evaluate LLM-based IE on multi-page German Brandschutz documents where relevant values appear sparsely.

---

## [PARSE: LLM Driven Schema Optimization for Reliable Entity Extraction](https://arxiv.org/abs/2510.08623)
- **Authors:** Shrimal, A.; Jain, A.; Chowdhury, S.; Yenigalla, P.
- **Year / Venue:** 2025 — EMNLP 2025 Industry Track
- **Why Relevant:** Addresses a core failure mode in schema-driven IE: ambiguous or underspecified JSON schemas cause LLM hallucinations and extraction errors — exactly the risk when designing extraction schemas for diverse fire-safety product categories.
- **Summary:** PARSE comprises ARCHITECT (autonomously optimizes JSON schemas for LLM consumption) and SCOPE (reflection-based extraction with static and LLM-based guardrails). Evaluated on SGD, SWDE, and internal retail data. On SWDE, combined improvements achieve up to 64.7% accuracy improvement, with errors reduced 92% within the first retry.
- **Methodology Categories:** [LLM-IE, Benchmark, Prompt-Engineering, Fine-tuning, NER]
- **Key Findings / Results:** +64.7% extraction accuracy on SWDE; 92% error reduction on first retry; 10% average improvement across three datasets.
- **Relevance Score (1–5):** 4 — Schema design is the most controllable quality lever in the Brandschutz IE pipeline; PARSE provides both methodology and quantitative evidence for schema-driven evaluation.

---

## [DocVQA: A Dataset for VQA on Document Images](https://arxiv.org/abs/2007.00398)
*(Also listed in Section 8 — see entry there for full details.)*
- **Methodology Categories:** [DocVQA, Benchmark, Multi-modal, OCR, Layout-Analysis]
- **Relevance Score (1–5):** 4 — Established the standard evaluation protocol for document understanding.

---

## [LegalBench-RAG: A Benchmark for Retrieval-Augmented Generation in the Legal Domain](https://arxiv.org/abs/2408.10343)
*(Also listed in Section 2 — see entry there for full details.)*
- **Methodology Categories:** [RAG, Benchmark, Regulatory-Compliance, Long-Doc]
- **Relevance Score (1–5):** 4 — Critical methodological reference for evaluating retrieval precision on regulatory documents.

---

## Section 11: Evidence-Grounded Extraction, Provenance & Numeric/Unit-Aware IE

<!-- Papers on attributed/cited extraction, table numerical reasoning, unit-aware value extraction -->

## [ERASER: A Benchmark to Evaluate Rationalized NLP Models](https://doi.org/10.18653/v1/2020.acl-main.408)
- **Authors:** DeYoung, J.; Jain, S.; Rajani, N.; Lehman, E.P.; Xiong, C.; Socher, R.; Wallace, B.C.
- **Year / Venue:** 2020 — ACL
- **Why Relevant:** ERASER formalizes how to evaluate whether predicted evidence spans are both plausible and faithful — for compliance workflows, its faithfulness framing maps directly to verifiable source-trace requirements for extracted boolean/numeric values.
- **Summary:** Introduces a benchmark suite for rationale-based NLP where models must provide supporting text snippets for decisions. Standardizes evaluation with both rationale quality metrics and faithfulness-oriented checks across multiple task types. Established the now-standard distinction between rationale plausibility and rationale faithfulness.
- **Methodology Categories:** [Benchmark, LLM-IE, Hybrid-IE, Long-Doc, Regulatory-Compliance]
- **Key Findings / Results:** 785+ citations; established the standard for evaluating evidence span quality in NLP.
- **Relevance Score (1–5):** 5 — Directly targets machine-generated evidence quality, central to auditability in fire-protection approvals.

---

## [Post-Hoc Answer Attribution for Grounded and Trustworthy Long Document Comprehension](https://doi.org/10.48550/arXiv.2406.06938)
- **Authors:** Sancheti, A.; Goswami, K.; Srinivasan, B.V.
- **Year / Venue:** 2024 — *SEM (STARSEM)
- **Why Relevant:** Directly studies answer-to-source attribution in long documents — the exact problem of validating extracted compliance facts back to page/span evidence for human reviewer verification.
- **Summary:** Defines post-hoc answer attribution as a dedicated task for long-document comprehension. Compares retrieval-based baselines with decomposition plus entailment-based attribution strategies. Identifies dataset limitations that inflate apparent grounding quality. Key finding: decomposition + entailment style attribution is more robust than naive retrieval-only attribution.
- **Methodology Categories:** [Long-Doc, Benchmark, Hybrid-IE, Regulatory-Compliance, Prompt-Engineering]
- **Key Findings / Results:** Decomposition + entailment attribution more robust than naive retrieval-only attribution in long-form answer settings.
- **Relevance Score (1–5):** 5 — Focuses on trustworthy long-document attribution; core requirement for approval-document IE.

---

## [Look as You Think: Unifying Reasoning and Visual Evidence Attribution for Verifiable Document RAG](https://doi.org/10.48550/arXiv.2511.12003)
- **Authors:** Liu, S.; Luo, P.; Zhang, C.; Chen, Y.; Zhang, H.; et al.
- **Year / Venue:** 2025 — AAAI
- **Why Relevant:** Produces explicit visual evidence attribution (page index plus bounding box) aligned with reasoning steps — ideal for verifiable extraction from scanned approval PDFs where text-only spans are insufficient.
- **Summary:** Introduces Chain-of-Evidence (CoE) coupling reasoning steps with visual evidence references. Proposes LAT, a reinforcement-learning framework rewarding attribution consistency only when answers are correct, creating process-level self-verification. Evaluated on document visual QA benchmarks.
- **Methodology Categories:** [RAG, Multi-modal, Layout-Analysis, DocVQA, OCR, Long-Doc, Hybrid-IE, Regulatory-Compliance]
- **Key Findings / Results:** +8.23% soft EM and +47.0% IoU@0.5 over vanilla base model; region-level evidence attribution.
- **Relevance Score (1–5):** 5 — Clearest match for verifiable page/region-grounded extraction from scanned regulatory PDFs.

---

## [TAPAS: Weakly Supervised Table Parsing via Pre-training](https://doi.org/10.18653/v1/2020.acl-main.398)
- **Authors:** Herzig, J.; Nowak, P.K.; Müller, T.; Piccinno, F.; Eisenschlos, J.M.
- **Year / Venue:** 2020 — ACL
- **Why Relevant:** Core table-understanding model for cell selection and weakly supervised table QA — directly relevant to extracting numeric values and their source cells from fire-protection specification tables.
- **Summary:** Adapts transformer pretraining to tabular inputs by modeling table structure jointly with question context. Enables weak supervision, reducing dependency on expensive logical-form annotations. Improved robustness on table QA tasks where exact cell grounding matters. Architecture and training strongly influenced subsequent systems in finance and technical-doc numerical reasoning.
- **Methodology Categories:** [Table-Extraction, Fine-tuning, Benchmark, Hybrid-IE, DocVQA]
- **Key Findings / Results:** Widely adopted high-impact table QA method; table-specific pretraining substantially improves answer correctness and cell-level grounding.
- **Relevance Score (1–5):** 5 — Foundational for unit- and cell-aware extraction from tables in technical documents.

---

## [FinQA: A Dataset of Numerical Reasoning over Financial Data](https://doi.org/10.48550/arXiv.2109.00122)
- **Authors:** Chen, Z.; Ding, M.; Chen, H.; Botzer, N.; Weninger, T.; Sun, H.
- **Year / Venue:** 2021 — NeurIPS Datasets & Benchmarks
- **Why Relevant:** Emphasizes programmatic numerical reasoning over table-plus-text evidence — analogous to deriving fire-compliance values from mixed narrative and tabular constraints with threshold operators (>, ≥, ≤).
- **Summary:** Introduces a benchmark requiring multi-step arithmetic reasoning over financial reports with both textual and tabular evidence. Pairs questions with executable reasoning programs making intermediate calculation structure explicit. Baselines reveal a large performance gap, indicating reliable numerical reasoning remains difficult even with strong language models.
- **Methodology Categories:** [Table-Extraction, Benchmark, Hybrid-IE, Relation-Extraction, Fine-tuning, Long-Doc]
- **Key Findings / Results:** Explicit program supervision exposes and reduces arithmetic failure modes common in end-to-end answer-only approaches.
- **Relevance Score (1–5):** 5 — Strong match for numeric/operator-aware extraction and verifiable calculation chains.

---

## [MultiHiertt: Numerical Reasoning over Multi Hierarchical Tabular and Textual Data](https://doi.org/10.18653/v1/2022.acl-long.454)
- **Authors:** Zhao, Y.; Li, Y.; Li, C.; Zhang, R.
- **Year / Venue:** 2022 — ACL
- **Why Relevant:** Targets numerical reasoning across multiple hierarchical tables plus surrounding text — mirroring technical approval sheets where thresholds and qualifiers are split across sections. Includes supporting-fact annotations useful for evidence traceability.
- **Summary:** Introduces a benchmark from financial reports with multiple hierarchical tables and long textual context. Questions require multi-step numerical reasoning beyond single-table lookup. Proposes MT2Net, combining fact retrieval with symbolic reasoning over retrieved evidence. Includes fine-grained supporting-fact annotations from table and text sources.
- **Methodology Categories:** [Table-Extraction, Benchmark, Hybrid-IE, Relation-Extraction, Long-Doc, Fine-tuning]
- **Key Findings / Results:** 168+ citations; existing baselines significantly trail human experts on complex multi-table reasoning.
- **Relevance Score (1–5):** 5 — Excellent fit for numeric extraction with table-text scope resolution and evidence-linked reasoning.

---

## [TAT-QA: A Question Answering Benchmark on a Hybrid of Tabular and Textual Content in Finance](https://doi.org/10.18653/v1/2021.acl-long.254)
- **Authors:** Zhu, F.; Lei, W.; Huang, Y.; Wang, C.; Zhang, S.; Wang, J.; Choo, K.-K.R.
- **Year / Venue:** 2021 — ACL
- **Why Relevant:** Focuses on hybrid table-text numerical QA with derivation and scale/unit sensitivity — closely matching extraction from technical approval documents where values depend on both table cells and nearby prose qualifiers.
- **Summary:** Provides realistic financial-document questions requiring retrieval plus arithmetic reasoning over table and text evidence. Evaluates systems on numerical correctness and evidence use in a mixed-modality document setting. Exposes persistent weaknesses for multi-step calculations and context fusion.
- **Methodology Categories:** [Table-Extraction, Benchmark, Hybrid-IE, Relation-Extraction, Fine-tuning, Long-Doc, Regulatory-Compliance]
- **Key Findings / Results:** Hybrid table-text numerical reasoning significantly more difficult than single-table QA; strong stress test for production-grade numeric extraction.
- **Relevance Score (1–5):** 5 — Directly aligned with extracting unit-bearing technical constraints from mixed table and narrative evidence.

---

## [QUASER: Question Answering with Scalable Extractive Rationalization](https://doi.org/10.1145/3477495.3532049)
- **Authors:** Ghoshal, A.; Iyer, S.; Paranjape, B.; Lakhotia, K.; Yih, S.; Mehdad, Y.
- **Year / Venue:** 2022 — SIGIR
- **Why Relevant:** Provides scalable extractive rationale generation that can support provenance-traced outputs from approval documents, where every extracted field must cite its source span.
- **Summary:** Proposes unsupervised generative rationale extraction for QA with dual-purpose constraints: rationales must support answer prediction and reconstruct the query. Reduces shortcut-style rationales that exploit dataset artifacts. Reports SOTA rationale extraction on 4 ERASER datasets.
- **Methodology Categories:** [LLM-IE, Hybrid-IE, Relation-Extraction, Benchmark, Regulatory-Compliance]
- **Key Findings / Results:** SOTA rationale extraction on 4 ERASER datasets; better evidence quality than prior unsupervised rationale methods.
- **Relevance Score (1–5):** 4 — Combines performance with explicit extractive rationales, matching provenance-first extraction requirements.

---

## Section 12: OCR Robustness, Uncertainty, Calibration & Selective Prediction for IE

<!-- Papers on robust OCR for degraded documents, confidence calibration, selective prediction / abstention for LLM-based extraction -->

## [TrOCR: Transformer-based Optical Character Recognition with Pre-trained Models](https://arxiv.org/abs/2109.10282)
- **Authors:** Li, M.; Lv, T.; Cui, L.; Zhang, Y.; et al.
- **Year / Venue:** 2021 — arXiv (AAAI 2023)
- **Why Relevant:** Strong baseline for noisy scanned pages and mixed-quality document images — common in approval dossiers containing photocopies, stamps, and low-contrast scans. Directly relevant for robust text recovery before IE.
- **Summary:** End-to-end OCR architecture combining a vision Transformer encoder and autoregressive text Transformer decoder, initialized with large-scale pretraining. Avoids brittle character-level pipelines and benefits from sequence-level language modeling during decoding. Evaluated on printed and handwritten OCR benchmarks; shows strong robustness compared with CNN-RNN baselines.
- **Methodology Categories:** [OCR, Multi-modal, Fine-tuning, Benchmark, Long-Doc]
- **Key Findings / Results:** SOTA or near-SOTA OCR accuracy on multiple benchmarks with substantial CER/WER reductions versus prior OCR architectures.
- **Relevance Score (1–5):** 5 — Highly transferable OCR backbone for degraded and heterogeneous document pages upstream of IE in the Brandschutz pipeline.

---

## [Language Models (Mostly) Know What They Know](https://arxiv.org/abs/2207.05221)
- **Authors:** Kadavath, S.; et al. (Anthropic)
- **Year / Venue:** 2022 — arXiv
- **Why Relevant:** Studies whether model confidence correlates with correctness — a prerequisite for routing uncertain extractions to human review in fire-protection approval workflows.
- **Summary:** Evaluates calibration and uncertainty behavior in large language models. Analyzes settings where models should defer rather than answer and investigates confidence elicitation techniques. Results show partial but imperfect calibration, with notable overconfidence in hard/out-of-distribution cases. Supports explicit confidence thresholds and fallback review policies instead of unconditional auto-fill.
- **Methodology Categories:** [LLM-IE, Benchmark, Prompt-Engineering, Hybrid-IE]
- **Key Findings / Results:** Confidence predicts correctness to a useful degree but is not reliably calibrated across all regimes; motivates selective prediction and calibration layers.
- **Relevance Score (1–5):** 5 — Foundational evidence for confidence-based abstention in LLM extraction systems.

---

## [SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection for Generative LLMs](https://arxiv.org/abs/2303.08896)
- **Authors:** Manakul, P.; Liusie, A.; Gales, M.
- **Year / Venue:** 2023 — EMNLP 2023
- **Why Relevant:** Provides a practical uncertainty signal from output consistency without requiring model logits — applicable when using black-box LLM APIs for fire-protection extraction and needing to gate uncertain outputs for human review.
- **Summary:** Proposes hallucination detection by sampling multiple model responses and measuring internal consistency, without requiring model logits or external verifiers. Model-agnostic and useful for black-box API settings. Disagreement across sampled extractions can trigger abstention, secondary retrieval, or manual verification workflows.
- **Methodology Categories:** [LLM-IE, Prompt-Engineering, Hybrid-IE, Benchmark]
- **Key Findings / Results:** Outperforms simple confidence baselines for hallucination/factuality detection in black-box generation settings.
- **Relevance Score (1–5):** 4 — Highly practical for uncertainty gating in production extraction pipelines when direct calibration hooks are unavailable.

---

## [Conformal Language Modeling](https://arxiv.org/abs/2306.10193)
- **Authors:** Quach, V.; Fisch, A.; Schuster, T.; Yala, A.; Barzilay, R.; Jaakkola, T.
- **Year / Venue:** 2023 — ICLR 2024
- **Why Relevant:** Conformal prediction gives statistically valid uncertainty guarantees and principled abstention sets — ideal for high-stakes IE fields in fire-safety approvals where false positives have legal/safety consequences.
- **Summary:** Applies conformal prediction to language modeling/generation, constructing prediction sets with finite-sample coverage guarantees. Reframes uncertain generation as set-valued prediction rather than single-point decoding. Allows systems to control error risk via target coverage and convert low-confidence outputs into abstentions or candidate sets.
- **Methodology Categories:** [LLM-IE, Benchmark, Hybrid-IE, Relation-Extraction]
- **Key Findings / Results:** Achieves near-nominal coverage in experiments while trading set size versus risk; enables explicit risk-control knobs for downstream extraction pipelines.
- **Relevance Score (1–5):** 5 — One of the most directly actionable frameworks for calibrated abstention in structured LLM extraction.

---

## [Selective Question Answering under Domain Shift](https://arxiv.org/abs/2006.00730)
- **Authors:** Kamath, A.; Jia, R.; Liang, P.
- **Year / Venue:** 2020 — ACL 2020
- **Why Relevant:** Selective QA under distribution shift mirrors selective IE: answer only when confidence is sufficient, otherwise abstain and route to human review. Domain shift behavior is critical for heterogeneous approval-document sources with varying manufacturer-specific language and scan quality.
- **Summary:** Studies selective prediction for extractive QA under distribution shift. Benchmarks calibration and confidence scoring methods under in-domain and shifted settings. Shows substantial degradation out of domain. Motivates robust confidence modeling and abstention policies beyond naive probability thresholds.
- **Methodology Categories:** [LLM-IE, Benchmark, Hybrid-IE, Long-Doc]
- **Key Findings / Results:** Common confidence scores degrade sharply under distribution shift; domain-aware calibration needed to maintain reliable risk-coverage behavior.
- **Relevance Score (1–5):** 4 — Strong methodological fit for abstention/routing policies in production IE over diverse approval document types.

---

## Section 13: Additional Papers Mined from Review Bibliographies (Non-Duplicates)

<!-- Added from the reference lists of top-fit review papers above; deduplicated against existing entries in this file -->

## [Translating Building Legislation into a Computer-Executable Format for Evaluating Building Permit Requirements](https://doi.org/10.1016/j.autcon.2016.04.008)
- **Authors:** Lee, H.-S.; Lee, J.-K.; Park, S.; Kim, I.
- **Year / Venue:** 2016 — Automation in Construction
- **Why Relevant:** Directly targets conversion of legal building clauses into executable representations for permit checking, matching the core Brandschutz requirement of turning free-text conditions into machine-checkable logic.
- **Summary:** Proposes a transformation pipeline from natural-language building legislation into formal, computable representations. Emphasizes reducing ambiguity in legal phrasing and enabling automated permit evaluation workflows.
- **Methodology Categories:** [Rule-Extraction, Regulatory-Compliance, BIM-IFC, Hybrid-IE]
- **Key Findings / Results:** 116 citations; demonstrates feasible end-to-end translation from legislative text to executable checking artifacts.
- **Relevance Score (1–5):** 5 — High overlap with conditional rule extraction and executable compliance reasoning.

---

## [Automatic Rule-Based Checking of Building Designs](https://doi.org/10.1016/j.autcon.2009.07.002)
- **Authors:** Eastman, C.M.; Lee, J.-m.; Jeong, Y.-s.; Lee, J.-K.
- **Year / Venue:** 2009 — Automation in Construction
- **Why Relevant:** Foundational compliance-checking architecture connecting BIM model elements to explicit regulatory rules.
- **Summary:** Presents a rule-based framework for automated checking of building designs against codes. The work established key representational and workflow choices used by many later BIM compliance systems.
- **Methodology Categories:** [Rule-Extraction, BIM-IFC, Regulatory-Compliance]
- **Key Findings / Results:** 679 citations; foundational contribution widely adopted in automated code checking.
- **Relevance Score (1–5):** 4 — Legacy but still methodologically central for executable rule design.

---

## [Building Information Modeling (BIM) and Safety: Automatic Safety Checking of Construction Models and Schedules](https://doi.org/10.1016/j.autcon.2012.05.006)
- **Authors:** Zhang, S.; Teizer, J.; Lee, J.-K.; Eastman, C.M.; Venugopal, M.
- **Year / Venue:** 2012 — Automation in Construction
- **Why Relevant:** Connects safety rule checking to BIM/schedule representations, aligning with fire-safety constraint verification.
- **Summary:** Integrates safety constraints with BIM and scheduling information to automate safety compliance checks. Demonstrates practical integration of model semantics with rule logic for proactive risk detection.
- **Methodology Categories:** [Rule-Extraction, BIM-IFC, Regulatory-Compliance, Hybrid-IE]
- **Key Findings / Results:** 809 citations; seminal work in safety-aware BIM compliance automation.
- **Relevance Score (1–5):** 4 — Strongly relevant as precursor architecture for fire-protection compliance pipelines.

---

## [A Semantic Rule Checking Environment for Building Performance Checking](https://doi.org/10.1016/j.autcon.2010.11.017)
- **Authors:** Pauwels, P.; Van Deursen, D.; Verstraeten, R.; De Roo, J.; De Meyer, R.; Van de Walle, R.; Van Campenhout, J.
- **Year / Venue:** 2010 — Automation in Construction
- **Why Relevant:** Uses semantic-web modeling for rule checking, highly compatible with ontology/KG-based compliance extraction.
- **Summary:** Introduces a semantic environment for formalizing and evaluating building performance rules. Combines ontology representations with machine-interpretable rule execution to support automated compliance analysis.
- **Methodology Categories:** [KG-Extraction, Rule-Extraction, Regulatory-Compliance, BIM-IFC]
- **Key Findings / Results:** 272 citations; influential semantic-rule architecture for compliance systems.
- **Relevance Score (1–5):** 4 — Good fit for ontology-grounded Brandschutz rule interpretation.

---

## [Classification of Rules for Automated BIM Rule Checking Development](https://doi.org/10.1016/j.autcon.2015.03.003)
- **Authors:** Solihin, W.; Eastman, C.M.
- **Year / Venue:** 2015 — Automation in Construction
- **Why Relevant:** Provides a practical taxonomy of rule types for automated checking, useful for designing extraction schemas and execution strategies for heterogeneous fire-protection constraints.
- **Summary:** Proposes a structured classification of compliance rules and maps each class to suitable implementation approaches. Helps separate directly computable checks from those requiring interpretation or additional context.
- **Methodology Categories:** [Rule-Extraction, Regulatory-Compliance, BIM-IFC, Benchmark]
- **Key Findings / Results:** 274 citations; widely used rule taxonomy for ACC system design.
- **Relevance Score (1–5):** 5 — Very actionable for structuring Brandschutz rule classes before extraction/execution.

---

## [Development of an Object Model for Automated Compliance Checking](https://doi.org/10.1016/j.autcon.2014.10.004)
- **Authors:** Malsane, S.; Matthews, J.; Lockley, S.; Love, P.E.D.; Greenwood, D.
- **Year / Venue:** 2014 — Automation in Construction
- **Why Relevant:** Defines object-model abstractions needed to map extracted rules and entities to computable checks.
- **Summary:** Develops an object model to represent compliance knowledge and checking logic in a reusable form. Focuses on bridging textual regulations and BIM model entities through explicit data structures.
- **Methodology Categories:** [BIM-IFC, Rule-Extraction, KG-Extraction, Regulatory-Compliance]
- **Key Findings / Results:** 158 citations; key reference for object-model design in ACC pipelines.
- **Relevance Score (1–5):** 4 — Useful for schema design between extracted fields and downstream validators.

---

## [Automated Code Compliance Checking for Building Envelope Design](https://doi.org/10.1061/(ASCE)0887-3801(2010)24:2(203))
- **Authors:** Tan, X.; Hammad, A.; Fazio, P.
- **Year / Venue:** 2010 — Journal of Computing in Civil Engineering
- **Why Relevant:** Early but highly cited demonstration of targeted automated checking from code requirements to design parameters.
- **Summary:** Implements automated compliance checks for building envelope design constraints with explicit mapping from regulations to model parameters. Demonstrates feasibility and limitations of codifying design-oriented code clauses.
- **Methodology Categories:** [Rule-Extraction, BIM-IFC, Regulatory-Compliance]
- **Key Findings / Results:** 139 citations; influential domain-focused ACC implementation.
- **Relevance Score (1–5):** 4 — Strong methodological fit for narrow-domain, parameterized rule checking.

---

## [Semantic Web Approach to Ease Regulation Compliance Checking in Construction Industry](https://doi.org/10.3390/fi4030830)
- **Authors:** Bouzidi, K.R.; Fiés, B.; Faron Zucker, C.; Zarli, A.; Le Thanh, N.
- **Year / Venue:** 2012 — Future Internet
- **Why Relevant:** Demonstrates semantic web methods for construction regulation compliance, consistent with KG-backed extraction and reasoning.
- **Summary:** Uses semantic representations of regulatory knowledge to support automated compliance workflows. Emphasizes interoperability and machine-readable policy modeling.
- **Methodology Categories:** [KG-Extraction, Rule-Extraction, Regulatory-Compliance, BIM-IFC]
- **Key Findings / Results:** 31 citations; practical semantic-web architecture for compliance checking.
- **Relevance Score (1–5):** 4 — Good fit with ontology/Turtle-oriented extraction strategy.

---

## [HybridRAG: Integrating Knowledge Graphs and Vector Retrieval Augmented Generation for Efficient Information Extraction](https://doi.org/10.1145/3677052.3698671)
- **Authors:** Sarmah, B.; Mehta, D.; Hall, B.; Rao, R.; Patel, S.; Pasquali, S.
- **Year / Venue:** 2024 — CIKM Companion / ACM (conference article)
- **Why Relevant:** Directly addresses hybrid KG + vector retrieval for IE, matching the project direction of grounded, structured extraction with traceable retrieval.
- **Summary:** Proposes a hybrid retrieval architecture combining graph structure with dense retrieval to improve IE efficiency and factual grounding. Aims to preserve relational context while retaining semantic recall.
- **Methodology Categories:** [RAG, KG-Extraction, Hybrid-IE, Relation-Extraction, LLM-IE]
- **Key Findings / Results:** 93 citations (OpenAlex snapshot); reports gains in retrieval-grounded IE quality versus single-retriever setups.
- **Relevance Score (1–5):** 5 — Strong architectural match for graph-aware extraction over long technical documents.

---

## [Unifying Large Language Models and Knowledge Graphs: A Roadmap](https://doi.org/10.1109/TKDE.2024.3352100)
- **Authors:** Pan, S.; Luo, L.; Wang, Y.; Chen, C.; Wang, J.; Wu, X.
- **Year / Venue:** 2024 — IEEE Transactions on Knowledge and Data Engineering
- **Why Relevant:** Comprehensive roadmap on LLM↔KG integration strategies, directly useful for choosing architecture patterns in compliance IE systems.
- **Summary:** Systematizes integration modes between language models and knowledge graphs, covering retrieval, grounding, reasoning, and generation-time constraints. Highlights open challenges in factuality, updateability, and scalable reasoning.
- **Methodology Categories:** [KG-Extraction, LLM-IE, RAG, Hybrid-IE, Benchmark]
- **Key Findings / Results:** 874 citations (OpenAlex snapshot); one of the most influential modern references on LLM+KG system design.
- **Relevance Score (1–5):** 4 — Broad but highly useful for selecting robust, grounded architecture for Brandschutz extraction.

---

## Cross-Cutting Themes & Summary Table

> All ~107 papers indexed by section, year, methodology tags, and relevance score.
> **Sections:** 1=Building Code IE · 2=Long-Doc LLMs · 3=PDF Layout · 4=Technical Drawings · 5=KG Construction · 6=Conditional Logic · 7=NER & Struct. IE · 8=Multimodal · 9=German NLP · 10=Benchmarks · 11=Evidence Grounding & Numeric · 12=OCR Robustness & Uncertainty


| # | Title (short) | Year | Sec. | Methodology Tags | Relevance |
|---|---|---|---|---|---|
| 1 | Zhang & El-Gohary — NLP building code pipeline | 2016 | 1 | LLM-IE, Rule-Extraction, NER, Regulatory-Compliance | 5 |
| 2 | Zhang & El-Gohary — semantic compliance NLP | 2017 | 1 | LLM-IE, Rule-Extraction, Regulatory-Compliance | 5 |
| 3 | Beach et al. — OWL/SWRL building code ontology | 2015 | 1 | KG-Extraction, Rule-Extraction, Regulatory-Compliance | 4 |
| 4 | Zhong et al. — ontology building regulations | 2019 | 1 | KG-Extraction, Regulatory-Compliance, BIM-IFC | 4 |
| 5 | Zhang & El-Gohary — BERT compliance checking | 2021 | 1 | Fine-tuning, Rule-Extraction, Regulatory-Compliance | 5 |
| 6 | CODE-ACCORD — cross-jurisdictional compliance NLP | 2023 | 1 | Benchmark, Rule-Extraction, Regulatory-Compliance, NER | 5 |
| 7 | I-SNACC — automated compliance checking | 2021 | 1 | Rule-Extraction, Regulatory-Compliance, LLM-IE | 5 |
| 8 | AgenticIE — agentic IE from regulatory docs | 2025 | 1 | LLM-IE, RAG, Prompt-Engineering, Regulatory-Compliance | 5 |
| 9 | BIM + Chinese NLP code compliance | 2022 | 1 | BIM-IFC, LLM-IE, Regulatory-Compliance | 4 |
| 10 | RAGulating Compliance — RAG for building codes | 2024 | 1 | RAG, Regulatory-Compliance, Rule-Extraction | 5 |
| 11 | MultiDocFusion — multi-document LLM fusion | 2024 | 2 | Long-Doc, RAG, Chunking, LLM-IE | 4 |
| 12 | Lost in the Middle — LLM context degradation | 2023 | 2 | Long-Doc, Prompt-Engineering, Benchmark | 5 |
| 13 | RAG Survey (Gao et al.) | 2024 | 2 | RAG, Benchmark, Chunking, Hybrid-IE | 5 |
| 14 | M3DocRAG — multi-modal multi-page RAG | 2024 | 2 | RAG, Multi-modal, Long-Doc, DocVQA | 5 |
| 15 | RAKG — retrieval-augmented KG construction | 2024 | 2 | RAG, KG-Extraction, Long-Doc | 4 |
| 16 | LegalBench-RAG — RAG for legal documents | 2024 | 2 | RAG, Benchmark, Regulatory-Compliance, Long-Doc | 4 |
| 17 | AgenticOCR — agentic OCR pipeline | 2024 | 2 | OCR, LLM-IE, RAG, Long-Doc | 4 |
| 18 | Long²RAG — long-context RAG benchmark | 2024 | 2 | RAG, Long-Doc, Benchmark, Chunking | 4 |
| 19 | MESc — multi-evidence hierarchical framework | 2023 | 2 | Long-Doc, RAG, Hybrid-IE, Chunking | 4 |
| 20 | SMART SLM — small LM for long documents | 2024 | 2 | Long-Doc, Fine-tuning, LLM-IE | 4 |
| 21 | LayoutLM — layout-aware document pretraining | 2020 | 3 | Layout-Analysis, Fine-tuning, DocVQA, OCR | 5 |
| 22 | LayoutLMv3 — unified text+image masking | 2022 | 3 | Layout-Analysis, Multi-modal, OCR, DocVQA, Fine-tuning | 5 |
| 23 | DocLayNet — document layout benchmark | 2022 | 3 | Layout-Analysis, Benchmark | 5 |
| 24 | PubTables-1M / TATR — table detection | 2022 | 3 | Table-Extraction, Layout-Analysis, Benchmark | 5 |
| 25 | Detect-Order-Construct — reading order | 2023 | 3 | Layout-Analysis, OCR, Chunking | 4 |
| 26 | DLAFormer — document layout analysis transformer | 2023 | 3 | Layout-Analysis, Fine-tuning | 4 |
| 27 | LayoutReader — reading order prediction | 2021 | 3 | Layout-Analysis, Chunking | 4 |
| 28 | Nougat — OCR-free academic PDF parsing | 2023 | 3 | OCR, Multi-modal, Layout-Analysis, Long-Doc | 5 |
| 29 | PDF parsing tool comparison (Adhikari) | 2024 | 3 | OCR, Layout-Analysis, Benchmark | 5 |
| 30 | Modeling Reading Order as Relations | 2022 | 3 | Layout-Analysis, Relation-Extraction, Chunking | 4 |
| 31 | CubiCasa5K — floorplan parsing dataset | 2019 | 4 | Layout-Analysis, Benchmark, Multi-modal | 4 |
| 32 | Raster-to-Vector — floorplan vectorization | 2017 | 4 | Layout-Analysis, Hybrid-IE | 4 |
| 33 | VectorFloorSeg — graph-based floorplan seg. | 2023 | 4 | Layout-Analysis, Relation-Extraction, Multi-modal | 4 |
| 34 | P&ID Features Recognition (Yu et al.) | 2019 | 4 | Layout-Analysis, OCR, Hybrid-IE | 5 |
| 35 | Deep-learning P&ID high-density (Kim et al.) | 2021 | 4 | Layout-Analysis, OCR, Hybrid-IE | 5 |
| 36 | Advancing P&ID YOLOv5 | 2023 | 4 | Layout-Analysis, OCR, Hybrid-IE | 4 |
| 37 | DL for 2D Engineering Drawings (Lin et al.) | 2023 | 4 | Layout-Analysis, OCR, Hybrid-IE | 4 |
| 38 | FloorNet — 3D scan floorplan reconstruction | 2018 | 4 | Multi-modal, Layout-Analysis, Benchmark | 3 |
| 39 | Wang & El-Gohary — relation extraction const. | 2023 | 5 | Relation-Extraction, KG-Extraction, BIM-IFC | 5 |
| 40 | Zheng et al. — conditional rules to KG | 2022 | 5 | KG-Extraction, Rule-Extraction, Regulatory-Compliance | 5 |
| 41 | Zhu et al. — autonomous KG construction | 2023 | 5 | KG-Extraction, LLM-IE, RAG | 5 |
| 42 | Zhong et al. ASCE — ontology IFC alignment | 2022 | 5 | KG-Extraction, BIM-IFC, Regulatory-Compliance | 5 |
| 43 | Peng & Liu — automated KG from regulations | 2023 | 5 | KG-Extraction, Rule-Extraction, NER | 4 |
| 44 | Yin et al. — BIM ontology extraction | 2022 | 5 | BIM-IFC, KG-Extraction, LLM-IE | 4 |
| 45 | Wang et al. — text+table safety KG | 2023 | 5 | KG-Extraction, Table-Extraction, Hybrid-IE | 5 |
| 46 | Li et al. — KG + LLM compliance checking | 2024 | 5 | KG-Extraction, LLM-IE, Regulatory-Compliance, RAG | 5 |
| 47 | EDC — extract-define-canonicalize (EMNLP 2024) | 2024 | 5 | KG-Extraction, LLM-IE, NER, Relation-Extraction | 5 |
| 48 | LLM ontology extraction (arXiv:2412.00608) | 2024 | 5 | KG-Extraction, LLM-IE, Prompt-Engineering | 4 |
| 49 | COMPACT — conditional provision extraction | 2025 | 6 | Rule-Extraction, Regulatory-Compliance, LLM-IE | 5 |
| 50 | Statutory reasoning dataset (EMNLP 2020) | 2020 | 6 | Rule-Extraction, Regulatory-Compliance, Benchmark | 5 |
| 51 | Compliance RAG (COLING 2025) | 2025 | 6 | RAG, Regulatory-Compliance, Rule-Extraction | 5 |
| 52 | ACL Findings survey — rule extraction | 2025 | 6 | Rule-Extraction, Regulatory-Compliance, Benchmark | 5 |
| 53 | ObliQA-MP — multi-paragraph obligation QA | 2025 | 6 | Rule-Extraction, Regulatory-Compliance, Benchmark, LLM-IE | 5 |
| 54 | LegalBench (NeurIPS 2023) | 2023 | 6 | Benchmark, Regulatory-Compliance, LLM-IE | 4 |
| 55 | ContractNLI — NLI for contracts (EMNLP 2021) | 2021 | 6 | Benchmark, Regulatory-Compliance, LLM-IE, NER | 4 |
| 56 | Statutory definitions transformer (IEEE 2025) | 2025 | 6 | Rule-Extraction, Regulatory-Compliance, Fine-tuning | 4 |
| 57 | CUAD — contract clause extraction (NeurIPS 2021) | 2021 | 6 | Benchmark, LLM-IE, NER, Regulatory-Compliance | 4 |
| 58 | GLiNER — generalist NER (NAACL 2024) | 2024 | 7 | NER, Fine-tuning, LLM-IE | 5 |
| 59 | GoLLIE — guideline-following IE (ICLR 2024) | 2024 | 7 | LLM-IE, NER, Prompt-Engineering, Fine-tuning | 5 |
| 60 | GPT-NER — LLM as NER system | 2023 | 7 | NER, LLM-IE, Prompt-Engineering | 4 |
| 61 | UniversalNER — universal NER (ICLR 2024) | 2024 | 7 | NER, Fine-tuning, LLM-IE, Benchmark | 5 |
| 62 | NuNER — few-shot NER | 2024 | 7 | NER, Fine-tuning, LLM-IE | 4 |
| 63 | InstructUIE — instruction-following UIE | 2023 | 7 | LLM-IE, NER, Relation-Extraction, Fine-tuning | 5 |
| 64 | Empirical study LLM IE (Han et al. 2023) | 2023 | 7 | LLM-IE, NER, Benchmark, Prompt-Engineering | 5 |
| 65 | SciBERT — scientific domain BERT (EMNLP 2019) | 2019 | 7 | Fine-tuning, NER, LLM-IE | 4 |
| 66 | REBEL — relation extraction BART (EMNLP 2021) | 2021 | 7 | Relation-Extraction, KG-Extraction, Fine-tuning | 4 |
| 67 | Structured extraction scientific text (Dagdelen) | 2024 | 7 | LLM-IE, NER, Prompt-Engineering, Relation-Extraction | 5 |
| 68 | LayoutLMv2 — multi-modal doc pretraining | 2021 | 8 | Layout-Analysis, Multi-modal, OCR, DocVQA, Fine-tuning | 5 |
| 69 | DocVQA — document visual QA benchmark | 2021 | 8 | DocVQA, Benchmark, Multi-modal, OCR | 5 |
| 70 | Donut — OCR-free document understanding | 2022 | 8 | OCR, Multi-modal, LLM-IE, DocVQA, Fine-tuning | 5 |
| 71 | Pix2Struct — screenshot-to-text pretraining | 2023 | 8 | Multi-modal, DocVQA, Fine-tuning | 4 |
| 72 | mPLUG-DocOwl 1.5 — multi-modal doc LLM | 2024 | 8 | Multi-modal, DocVQA, Layout-Analysis, LLM-IE | 5 |
| 73 | DocLayLLM — multi-modal layout LLM | 2025 | 8 | Multi-modal, Layout-Analysis, DocVQA, LLM-IE | 5 |
| 74 | HVFA — hierarchical visual feature agg. | 2024 | 8 | Multi-modal, DocVQA, Layout-Analysis | 4 |
| 75 | MCERF — multimodal conditional entity recognition | 2025 | 8 | Multi-modal, NER, LLM-IE, Layout-Analysis | 5 |
| 76 | KYC multistage extraction pipeline | 2025 | 8 | Multi-modal, LLM-IE, Hybrid-IE, Regulatory-Compliance | 4 |
| 77 | GBERT/GELECTRA — German BERT (COLING 2020) | 2020 | 9 | Fine-tuning, NER, German-NLP | 5 |
| 78 | GottBERT — German RoBERTa | 2024 | 9 | Fine-tuning, German-NLP, NER | 5 |
| 79 | FLERT — document-level NER | 2021 | 9 | NER, Fine-tuning, German-NLP | 4 |
| 80 | XLM-R — cross-lingual RoBERTa (ACL 2020) | 2020 | 9 | Fine-tuning, German-NLP, NER, LLM-IE | 5 |
| 81 | EuroLLM — European multilingual LLM | 2024 | 9 | LLM-IE, German-NLP, Fine-tuning | 5 |
| 82 | GerDaLIR — German legal IR (NLLP 2021) | 2021 | 9 | German-NLP, Regulatory-Compliance, Benchmark | 4 |
| 83 | German BERT Legal NER (ICAART 2023) | 2023 | 9 | NER, German-NLP, Regulatory-Compliance, Fine-tuning | 5 |
| 84 | German radiology IE (Scientific Reports 2023) | 2023 | 9 | LLM-IE, NER, German-NLP, Fine-tuning | 4 |
| 85 | German court ruling summarization (NLLP 2021) | 2021 | 9 | German-NLP, Regulatory-Compliance, Long-Doc | 4 |
| 86 | Frame semantics German BERT (JMIR 2025) | 2025 | 9 | German-NLP, LLM-IE, NER | 4 |
| 87 | ExtractBench — IE evaluation benchmark | 2025 | 10 | Benchmark, LLM-IE, NER | 5 |
| 88 | REGREACT — regulatory QA benchmark | 2025 | 10 | Benchmark, Regulatory-Compliance, LLM-IE | 5 |
| 89 | UNIKIE-BENCH — universal KG IE benchmark | 2024 | 10 | Benchmark, KG-Extraction, NER, Relation-Extraction | 5 |
| 90 | DTBench — document table benchmark | 2024 | 10 | Benchmark, Table-Extraction, Layout-Analysis | 5 |
| 91 | TextMineX — text mining evaluation | 2024 | 10 | Benchmark, LLM-IE, Hybrid-IE | 4 |
| 92 | Multi-agent financial doc benchmark | 2025 | 10 | Benchmark, LLM-IE, Long-Doc, Multi-modal | 4 |
| 93 | Needle-in-haystack long-doc benchmark | 2025 | 10 | Benchmark, Long-Doc, RAG | 4 |
| 94 | PARSE — schema optimization for IE (EMNLP 2025) | 2025 | 10 | LLM-IE, Prompt-Engineering, Benchmark, KG-Extraction | 5 |
| 95 | ERASER — rationalized NLP benchmark | 2020 | 11 | Benchmark, LLM-IE, Hybrid-IE, Long-Doc, Regulatory-Compliance | 5 |
| 96 | Post-hoc attribution for long docs | 2024 | 11 | Long-Doc, Benchmark, Hybrid-IE, Regulatory-Compliance | 5 |
| 97 | LAT/CoE — visual evidence attribution (AAAI 2025) | 2025 | 11 | RAG, Multi-modal, Layout-Analysis, DocVQA, Hybrid-IE | 5 |
| 98 | TAPAS — table parsing via pretraining | 2020 | 11 | Table-Extraction, Fine-tuning, Benchmark, Hybrid-IE | 5 |
| 99 | FinQA — numerical reasoning over finance | 2021 | 11 | Table-Extraction, Benchmark, Hybrid-IE, Long-Doc | 5 |
| 100 | MultiHiertt — multi-table numerical reasoning | 2022 | 11 | Table-Extraction, Benchmark, Hybrid-IE, Relation-Extraction | 5 |
| 101 | TAT-QA — hybrid table+text numerical QA | 2021 | 11 | Table-Extraction, Benchmark, Hybrid-IE, Regulatory-Compliance | 5 |
| 102 | QUASER — extractive rationalization QA | 2022 | 11 | LLM-IE, Hybrid-IE, Benchmark, Regulatory-Compliance | 4 |
| 103 | TrOCR — transformer OCR | 2021 | 12 | OCR, Multi-modal, Fine-tuning, Benchmark | 5 |
| 104 | LMs Know What They Know — calibration | 2022 | 12 | LLM-IE, Benchmark, Prompt-Engineering | 5 |
| 105 | SelfCheckGPT — hallucination detection | 2023 | 12 | LLM-IE, Prompt-Engineering, Hybrid-IE, Benchmark | 4 |
| 106 | Conformal Language Modeling | 2023 | 12 | LLM-IE, Benchmark, Hybrid-IE | 5 |
| 107 | Selective QA under Domain Shift | 2020 | 12 | LLM-IE, Benchmark, Hybrid-IE, Long-Doc | 4 |

---

## Research Gaps Identified (Gap-Analysis Pass)

Based on the gap analysis conducted after the initial 10-agent sweep, the following research gaps were identified between the covered literature and the specific needs of the Brandschutz project (automatic IE from 100+ page German fire-protection approval PDFs):

**Gap 1 — Technical Drawing / Engineering Diagram AI**
The initial sweep produced no papers on floor-plan parsing, P&ID digitization, or 2D engineering drawing recognition. Section 4 (added via gap-fill agents) addresses this. Although strong methods exist (CubiCasa5K, Raster-to-Vector, P&ID deep-learning), none are applied to fire-protection approval drawings specifically. Transfer and fine-tuning for Brandschutz-specific symbols (cable entry seals, pipe runs, fire compartment boundaries) remains an open problem.

**Gap 2 — Evidence-Grounded Extraction with Provenance**
No initial papers addressed the specific combination of: (a) structured field extraction, (b) precise source-span attribution (page + paragraph), and (c) audit-trail formatting compatible with regulatory documentation. Section 11 covers the foundations (ERASER, TAPAS, CoE/LAT), but a gap remains for fully automated provenance-linked IE pipelines applied to German technical regulatory PDFs.

**Gap 3 — Numeric and Unit-Aware Extraction from Mixed Table/Text Sources**
Numeric reasoning benchmarks (FinQA, TAT-QA, MultiHiertt) are covered, but all originate from financial documents. The specific challenge of extracting fire-classification thresholds, cable cross-sections, installation distances, and conditional numeric constraints from heterogeneous tables + prose in German approval documents has not been directly studied in the reviewed literature.

**Gap 4 — OCR Noise Robustness for Technical Document Vocabularies**
General OCR transformers (TrOCR) and OCR-free approaches (Donut, Nougat) are well-covered, but there is a distinct gap for domain-specific robustness to fire-protection terminology (e.g., abbreviated cable markings, DIN standard codes, German compound nouns in low-quality scans). No benchmark exists specifically for regulatory/technical vocabulary OCR robustness.

**Gap 5 — Calibration, Selective Prediction, and Abstention for High-Stakes Document IE**
Foundational methods (LMs Know What They Know, SelfCheckGPT, Conformal LM, Selective QA) are covered in Section 12, but these focus on general QA or generation. There is no established framework specifically for confidence-gated structured information extraction from long regulatory PDFs with mandatory human-in-the-loop validation thresholds. This gap is particularly important for production deployment of the Brandschutz pipeline.



