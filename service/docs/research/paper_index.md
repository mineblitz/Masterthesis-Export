# Uebersicht: Aktuelle Peer-Reviewed Paper (Text-Only, LLM-fokussiert)

Kriterien:
- Fokus auf Auswertung von Text (Information Extraction oder Information Retrieval)
- Bevorzugt LLM-basierte Ansaetze
- Peer-reviewed Quellen
- Sortierung nach vorgestelltm Ansatz

Hinweis zur Code-Spalte:
- Schnellpruefung ueber Titel/DOI-Websuche durchgeführt.
- "Nicht ersichtlich" bedeutet: kein direktes, eindeutig zugeordnetes Repo im Schnellcheck gefunden.

## Ansatz 1: RAG + IR/QA (Baukontext)

| Paper | Jahr | Ansatz (kurz) | Code/Repo fuer Uebernahme | Implementierung in Pipeline | Kommentare | Schon gelesen |
|---|---:|---|---|---|---|---|
| [Performance comparison of retrieval-augmented generation and fine-tuned large language models for construction safety management knowledge retrieval](https://doi.org/10.1016/j.autcon.2024.105846) | 2024 | Vergleich RAG vs. Fine-Tuning fuer Safety-Wissensretrieval aus Textdokumenten | Nicht ersichtlich (Schnellcheck) | Mittel bis hoch (4/5): RAG-Infrastruktur + Evaluationsset + Guardrails | vergleich llm, llm spezial, rag based für info retrival aus saftey managment daten, koreanische daten| gelesen |
| [Effectiveness of retrieval augmented generation-based large language models for generating construction safety information](https://doi.org/10.1016/j.autcon.2024.105926) | 2025 | RAG-basierte Generierung von Sicherheitsinformationen aus Projektdokumenten | Nicht ersichtlich (Schnellcheck) | Mittel (3/5): mit bestehender Vektor-DB relativ direkt umsetzbar | nicht relevant |  |
| [Automated safety risk management guidance enhanced by retrieval-augmented large language model](https://doi.org/10.1016/j.autcon.2025.106255) | 2025 | RAG-unterstuetzte Leitfaden-/Guidance-Generierung fuer Safety Risk Management | Nicht ersichtlich (Schnellcheck) | Mittel bis hoch (4/5): domain rules + Nachvollziehbarkeit der Antworten noetig |  |  |
| [Retrieval augmented generation-driven information retrieval and question answering in construction management](https://doi.org/10.1016/j.aei.2025.103158) | 2025 | RAG-getriebenes IR + QA im Construction Management | Nicht ersichtlich (Schnellcheck) | Mittel (3/5): gute Blaupause fuer End-to-End Retrieval-Pipeline |  |  |

## Ansatz 2: LLM-basierte strukturierte Information Extraction (Text -> Struktur)

| Paper | Jahr | Ansatz (kurz) | Code/Repo fuer Uebernahme | Implementierung in Pipeline | Kommentare | Schon gelesen |
|---|---:|---|---|---|---|---|
| [Structured information extraction from scientific text with large language models](https://doi.org/10.1038/s41467-024-45563-x) | 2024 | LLM-gestuetzte Extraktion strukturierter Fakten aus wissenschaftlichem Text | Nicht ersichtlich (Schnellcheck) | Mittel (3/5): Prompting + Schema/Validatoren + Postprocessing |  |  |
| [Automatic bridge inspection database construction through hybrid information extraction and large language models](https://doi.org/10.1016/j.dibe.2024.100549) | 2024 | Hybrid-IE (klassisch + LLM) fuer Brueckeninspektionsberichte | Nicht ersichtlich (Schnellcheck) | Mittel bis hoch (4/5): Hybrid-Orchestrierung + Datenqualitaetskontrollen |  |  |
| [Scalable information extraction from free text electronic health records using large language models](https://doi.org/10.1186/s12874-025-02470-z) | 2025 | Skalierbare LLM-IE fuer grosse Mengen Freitext | Nicht ersichtlich (Schnellcheck) | Hoch (4/5): Skalierung, Batch-Strategie, Kosten- und Fehlerkontrolle |  |  |
| [Information extraction from historical well records using a large language model](https://doi.org/10.1038/s41598-024-81846-5) | 2024 | LLM-Extraktion aus historischen technischen Texten | Nicht ersichtlich (Schnellcheck) | Mittel (3/5): domain-spezifische Normalisierung und Robustheit noetig |  |  |
| [Information extraction from employment tribunal judgments using a large language model](https://doi.org/10.1007/s10506-025-09443-z) | 2025 | Juristische IE mit LLM (long-form Dokumente) | Nicht ersichtlich (Schnellcheck) | Mittel bis hoch (4/5): lange Kontexte, Labelkonsistenz, Halluzinationsschutz |  |  |
| [Large language model enhanced hierarchical script extraction from multiple documents](https://doi.org/10.1016/j.knosys.2026.115608) | 2026 | Hierarchische, dokumentuebergreifende Extraktion | Nicht ersichtlich (Schnellcheck) | Hoch (5/5): Multi-Dokument-Fusion, konsistente Entitaetsauflösung |  |  |

## Ansatz 3: Prompting/NER-orientierte Text-Extraktion mit LLM

| Paper | Jahr | Ansatz (kurz) | Code/Repo fuer Uebernahme | Implementierung in Pipeline | Kommentare | Schon gelesen |
|---|---:|---|---|---|---|---|
| [Improving large language models for clinical named entity recognition via prompt engineering](https://doi.org/10.1093/jamia/ocad259) | 2024 | Prompt-Engineering fuer NER-Qualitaet | Nicht ersichtlich (Schnellcheck) | Niedrig bis mittel (2/5): schnell als Prompt-Template in bestehende Pipeline integrierbar |  |  |
| [Understanding Tradeoffs in Clinical Text Extraction: Prompting, Retrieval-Augmented Generation, and Supervised Learning on Electronic Health Records](https://doi.org/10.3390/a19030215) | 2026 | Vergleich Prompting vs RAG vs Supervised Learning fuer IE | Nicht ersichtlich (Schnellcheck) | Mittel (3/5): gut als Entscheidungsgrundlage fuer Architekturwahl |  |  |

## Kurzbewertung nach Ansatzklasse

- RAG + IR/QA (Ansatz 1): Beste direkte Passung fuer deine Information-Retrieval-Zielsetzung im Baukontext.
- Strukturierte IE (Ansatz 2): Stark fuer feldgenaue Extraktion; gut kombinierbar mit RAG (erst extrahieren, dann abrufen).
- Prompting/NER-Fokus (Ansatz 3): Niedrige Einstiegshuerde, eignet sich gut fuer Prototypen und schnelle Baselines.

## Praktische Priorisierung fuer Umsetzung

1. Mit Ansatz 1 starten (RAG + QA/IR) fuer schnelle End-to-End-Nutzbarkeit.
2. Danach Ansatz 2 fuer stabile strukturierte Felder (Schema + Validatoren) ergaenzen.
3. Ansatz 3 als schnelles Benchmark-Setup fuer Baseline und Fehlersuche nutzen.

---

# Multimodale Modelle: Uebersicht (Text + Bild/Layout)

Kriterien:
- Modelle oder Paper, die Text UND visuelle/Layout-Informationen kombinieren
- Fokus: Information Extraction / Key-Value Extraktion aus Dokumenten
- Bevorzugt peer-reviewed (CVPR, ACL, EMNLP, AAAI, KDD, ACM, IEEE Journals)
- Öffentlich verfuegbare Modelle priorisiert

---

## Ansatz A: Layout-Aware Vortrainings-Modelle (Text + Layout + Bild)

| Paper | Jahr | Ansatz (kurz) | Code/Modell verfuegbar | Implementierung in Pipeline | Kommentare | Schon gelesen |
|---|---:|---|---|---|---|---|
| [LayoutLM: Pre-training of Text and Layout for Document Image Understanding](https://arxiv.org/abs/1912.13318) | 2020 | 2D-Positions-Embeddings + BERT fuer Formulare und Belege | ✅ [microsoft/unilm](https://github.com/microsoft/unilm) + [HuggingFace](https://huggingface.co/microsoft/layoutlm-base-uncased) | Niedrig (2/5): fertige HF-Klassen, klar dokumentiert | Grundlagenarbeit, 1400+ Zitate; guter Einstiegspunkt |  |
| [LayoutLMv2: Multi-modal Pre-training for Visually-Rich Document Understanding](https://arxiv.org/abs/2012.14740) | 2021 | Text + Bild + Layout, spatial-aware attention | ✅ [microsoft/unilm](https://github.com/microsoft/unilm) + HuggingFace | Niedrig bis mittel (2/5): Erweiterung auf v2 schnell | FUNSD 84.20%, CORD 96.01%, DocVQA 86.72% |  |
| [LayoutLMv3: Pre-training for Document AI with Unified Text and Image Masking](https://arxiv.org/abs/2204.08387) | 2022 | Vereinheitlichtes Text+Bild-Masking; multi-task | ✅ [microsoft/unilm](https://github.com/microsoft/unilm) + HuggingFace (581k Downloads) | Niedrig bis mittel (2/5): direktes Fine-Tuning moeglich | Aktuell sterkste Layout-Modell-Familie; empfohlen als Baseline |  |

## Ansatz B: OCR-freie End-to-End Dokumentenmodelle

| Paper | Jahr | Ansatz (kurz) | Code/Modell verfuegbar | Implementierung in Pipeline | Kommentare | Schon gelesen |
|---|---:|---|---|---|---|---|
| [Donut: OCR-free Document Understanding Transformer](https://arxiv.org/abs/2111.15664) | 2022 | Swin-Encoder + BART-Decoder, kein OCR-Schritt noetig | ✅ [clovaai/donut](https://github.com/clovaai/donut) + HuggingFace | Mittel (3/5): eigenes Fine-Tuning auf Zieldokumenten erforderlich | Sehr relevant: kein OCR-Preprocessing, DocVQA ~86%; gut fuer PDFs mit komplexem Layout |  |
| [Nougat: Neural Optical Understanding for Academic Documents](https://arxiv.org/abs/2308.13418) | 2023 | Vision-Transformer -> Markdown (no OCR), spezialisiert auf wissenschaftliche PDFs | ✅ [HuggingFace facebook/nougat-base](https://huggingface.co/facebook/nougat-base) | Mittel (3/5): out-of-the-box fuer PDF->Text-Konvertierung | Gut fuer Textextraktion aus technischen/wissenschaftlichen PDFs; weniger fuer KV-Extraktion |  |
| [GOT-OCR 2.0: General OCR Theory](https://github.com/Ucas-HaoranWei/GOT-OCR2.0) | 2024 | Vereinheitlichtes End-to-End OCR ohne Vorverarbeitung | ✅ [GOT-OCR2.0 GitHub](https://github.com/Ucas-HaoranWei/GOT-OCR2.0) (8100+ Stars) | Mittel (3/5): direkter Einsatz als Preprocessing-Schritt | Stark fuer robuste Texterkennung, mehrsprachig; gute Alternative zu Tesseract |  |
| [SmolDocling: Ultra-Compact VLM for End-to-End Multi-Modal Document Conversion](https://openaccess.thecvf.com/content/ICCV2025/html/Nassar_SmolDocling_An_ultra-compact_vision-language_model_for_end-to-end_multi-modal_document_conversion_ICCV_2025_paper.html) | 2025 | Kompaktes VLM fuer Multi-Modal Dokumentenkonvertierung ohne Halluzinationen | ✅ Öffentlich verfuegbar | Mittel (3/5): sehr klein, deploybar | ICCV 2025; gut fuer ressourcenbeschraenkte Pipelines |  |

## Ansatz C: Multimodales VQA & Structured Extraction mit aktuellen LLMs

| Paper | Jahr | Ansatz (kurz) | Code/Modell verfuegbar | Implementierung in Pipeline | Kommentare | Schon gelesen |
|---|---:|---|---|---|---|---|
| [Pix2Struct: Screenshot Parsing as Pretraining for Visual Language Understanding](https://arxiv.org/abs/2210.03347) | 2022 | Bild->HTML-Parsing als Vortraining; variable Aufloesung | ✅ [HuggingFace google/pix2struct-base](https://huggingface.co/google/pix2struct-base) | Mittel (3/5): direktes Fine-Tuning; sehr layout-sensitiv | Stark fuer UI/Screenshots/Formulare; STATA auf 6/9 Benchmarks |  |
| [TextMonkey: OCR-Free Large Multimodal Model for Document Understanding](https://arxiv.org/abs/2403.04473) | 2024 | Shifted Window Attention + Token-Filterung; Textspotting | ✅ [Yuliang-Liu/Monkey GitHub](https://github.com/Yuliang-Liu/Monkey) | Mittel (3/5) | OCRBench SOTA (561); +6.9% auf DocVQA/InfoVQA vs. Baseline |  |
| [mPlug-DocOwl 1.5: Unified Structure Learning for OCR-Free Document Understanding](https://aclanthology.org/2024.findings-emnlp.175/) | 2024 | OCR-freies einheitliches Struktur-Lernen | ✅ [x-plug/mplug-docowl GitHub](https://github.com/x-plug/mplug-docowl) | Mittel (3/5): state-of-art fuer komplexe Layouts | EMNLP 2024; sehr gut fuer gemischte Dokumente |  |
| [InternVL: Scaling up Vision Foundation Models](https://arxiv.org/abs/2312.14238) | 2023 | 6B Vision-Modell + LLM-Alignment; 32 Benchmarks | ✅ [OpenGVLab/InternVL GitHub](https://github.com/OpenGVLab/InternVL) | Mittel bis hoch (4/5): gross, GPU-intensiv | Sehr stark allgemein; DocVQA und document-tasks comptetitiv |  |
| [Docopilot: Improving Multimodal Models for Document-Level Understanding](https://openaccess.thecvf.com/content/CVPR2025/html/Duan_Docopilot_Improving_Multimodal_Models_for_Document-Level_Understanding_CVPR_2025_paper.html) | 2025 | Verbesserung multi-modaler Modelle fuer Dokumenten-Level-Verstaendnis | ✅ Verfuegbar | Mittel bis hoch (4/5) | CVPR 2025 |  |

## Ansatz D: Multimodales RAG fuer lange/komplexe Dokumente

| Paper | Jahr | Ansatz (kurz) | Code/Modell verfuegbar | Implementierung in Pipeline | Kommentare | Schon gelesen |
|---|---:|---|---|---|---|---|
| [Visdom: Multi-Document QA with Visually Rich Elements using Multimodal RAG](https://aclanthology.org/2025.naacl-long.310/) | 2025 | Multimodales RAG fuer Multi-Dokument-QA mit Tabellen/Charts | ✅ Verfuegbar | Mittel bis hoch (4/5): visuelle Chunk-Strategie noetig | NAACL 2025; direkt relevant fuer Dokumente mit Tabellen und Grafiken |  |
| [URaG: Unified Retrieval and Generation in Multimodal LLMs for Long Document Understanding](https://ojs.aaai.org/index.php/AAAI/article/view/39729) | 2025 | Kombiniertes Retrieval+Generierung in einem Framework | ✅ Verfuegbar | Hoch (4/5) | AAAI 2026; gut fuer sehr lange Dokumente |  |
| [Multi-Modal Vision vs. Text-Based Parsing: Benchmarking LLM Strategies for Invoice Processing](https://arxiv.org/abs/2509.04469) | 2025 | Direkter Vergleich Vision vs. Text fuer Invoice-Extraktion | ✅ Verfuegbar | Niedrig (2/5): Designentscheidungs-Grundlage | Sehr nützlich als Entscheidungsgrundlage: wann Multimodal, wann Text-only |  |

## Ansatz E: Baukontext + Multimodal / VLM

| Paper | Jahr | Ansatz (kurz) | Code/Modell verfuegbar | Implementierung in Pipeline | Kommentare | Schon gelesen |
|---|---:|---|---|---|---|---|
| [Zero-shot Building Attribute Extraction from Large-Scale Vision and Language Models](https://openaccess.thecvf.com/content/WACV2024/html/Pan_Zero-Shot_Building_Attribute_Extraction_From_Large-Scale_Vision_and_Language_Models_WACV_2024_paper.html) | 2024 | Zero-Shot VLM fuer Gebaeudeattribut-Extraktion | ❌ nicht oeffentlich | Hoch (5/5): erfordert Domain-Adaptation | WACV 2024; erste Arbeit zu VLMs auf Gebaeudedaten |  |
| [Automated Building Information Modeling Compliance Check through LLM + Deep Learning + Ontology](https://doi.org/10.3390/buildings14071983) | 2024 | BIM + LLM + DL + Ontologie fuer Compliance-Checks | ❌ nicht oeffentlich | Hoch (5/5): komplexe Multi-Komponenten-Architektur | Buildings 2024; hybrid-Ansatz; stark fuer Bauvorschriften |  |
| [Fine-tuning a large language model for automated code compliance of building regulations](https://doi.org/10.1016/j.aei.2025.103676) | 2025 | Fine-Tuned LLM fuer automatisiertes Code-Compliance-Checking | ❌ nicht oeffentlich | Mittel bis hoch (4/5) | Advanced Engineering Informatics 2025; Bauvorschriften-Fokus |  |
| [Large Language Model-Driven Code Compliance Checking in Building Information Modeling](https://doi.org/10.3390/electronics14112146) | 2025 | LLM-gestuetztes Code-Compliance-Checking in BIM | ❌ nicht oeffentlich | Mittel bis hoch (4/5) | Electronics MDPI 2025 |  |

## Surveys & Benchmarks (Referenzwerke)

| Paper | Jahr | Typ | Link | Kommentare | Schon gelesen |
|---|---:|---|---|---|---|
| [LLMs in Document Intelligence: Comprehensive Survey](https://dl.acm.org/doi/abs/10.1145/3768156) | 2025 | Survey | ACM Transactions on Information Systems | Beste Uebersicht ueber den Stand der Technik |  |
| [Deep Learning Based Key Information Extraction from Business Documents: Systematic Literature Review](https://dl.acm.org/doi/abs/10.1145/3749369) | 2025 | Survey | ACM Computing Surveys | Systematisches Review 2017-2024; extrem nützlich |  |
| [OmniDocBench: Benchmarking Diverse PDF Document Parsing](https://openaccess.thecvf.com/content/CVPR2025/html/Ouyang_OmniDocBench_Benchmarking_Diverse_PDF_Document_Parsing_with_Comprehensive_Annotations_CVPR_2025_paper.html) | 2025 | Benchmark | CVPR 2025 | 9 Dokumenttypen; gut fuer Modellvergleich |  |
| [OCRBench: On the Hidden Mystery of OCR in Large Multimodal Models](https://arxiv.org/abs/2305.07895) | 2023 | Benchmark | arXiv (peer-reviewed Follow-up) | 29 Datensaetze; Standard fuer OCR-Modell-Vergleich |  |
| [ExStrucTiny: A Benchmark for Schema-Variable Structured IE from Document Images](https://arxiv.org/abs/2602.12203) | 2026 | Benchmark | EACL 2026 | Direkt relevant: schema-variable KV-Extraktion |  |

## Kurzfazit Multimodale Modelle

- **Schneller Einstieg** (text-only bleibt): Ansatz A (LayoutLMv3) als FT-Baseline.
- **OCR-freie Alternative**: Donut oder mPlug-DocOwl (B) wenn PDF-Qualitaet schwankt.
- **Ressourcen vorhanden**: InternVL / TextMonkey fuer state-of-art Ergebnisse.
- **Bau-Compliance-Fokus**: Paper in Ansatz E zeigen, dass Fine-Tuning + Ontologien der aktuelle Stand sind; kein oeffentliches Modell vorhanden.
- **Entscheidungsgrundlage Text vs. Multimodal**: Paper "Multi-Modal Vision vs. Text-Based Parsing" (Ansatz D) gibt direkte Orientierung.

---

# Update 2026-05: Pipeline-nahe Paper

Ziel dieses Updates:
- Fokus auf Paper, die methodisch direkt zu den existierenden Pipelines passen
- Bevorzugt peer-reviewed Journal-/Conference-Paper
- Sortierung nach Pipeline-Familie statt nur nach grober Themenklasse

## 1. Text-only: Prompting, Context Narrowing, Retrieval

| Paper | Jahr | Relevante Pipeline(s) | Warum relevant | Implementierung in Pipeline | Kommentare | Schon gelesen |
|---|---:|---|---|---|---|---|
| [Structured information extraction from scientific text with large language models](https://doi.org/10.1038/s41467-024-45563-x) | 2024 | v5, v15, v16 | Sehr gute Referenz fuer strukturierte Extraktion aus langen Texten mit LLMs | Mittel (3/5): Prompting + Validierung + Mehrfachdurchlaeufe |  |  |
| [Longtriever: A Pre-trained Long Text Encoder for Dense Document Retrieval](https://aclanthology.org/2023.emnlp-main.223/) | 2023 | v8, v10 | Direkter Upgrade-Pfad fuer keyword-basierte Kontextfenster hin zu learned retrieval | Hoch (4/5): eigener Retriever oder Reranker noetig |  |  |
| [Enhancing Retrieval-Augmented Generation: a Study of Best Practices](https://aclanthology.org/2025.coling-main.449/) | 2025 | v8, v10, v13 | Relevant fuer bessere Kontextauswahl, Satzselektion und Retrieval-Fallbacks | Mittel (3/5): gute Zwischenstufe vor vollem Dense Retrieval |  |  |
| [Corrective Retrieval Augmented Generation](https://openreview.net/forum?id=JnWJbrnaUE) | 2024 | v8, v10, v11 | Hilft fuer Retrieval-Qualitaetspruefung und adaptive Fallbacks auf groesseren Kontext | Mittel (3/5): zusaetzliche Bewertungs-/Retry-Stufe |  |  |
| [Understanding Tradeoffs in Clinical Text Extraction: Prompting, Retrieval-Augmented Generation, and Supervised Learning on Electronic Health Records](https://doi.org/10.3390/a19030215) | 2026 | v5, v8, v10 | Gute Entscheidungsgrundlage fuer Text-only Architekturwahl im Repo | Niedrig bis mittel (2/5): eher Benchmark-/Evaluationsinspiration |  |  |

## 2. Multimodal: Text + Bild/Layout

| Paper | Jahr | Relevante Pipeline(s) | Warum relevant | Implementierung in Pipeline | Kommentare | Schon gelesen |
|---|---:|---|---|---|---|---|
| [DocLLM: A layout-aware generative language model for multimodal document understanding](https://aclanthology.org/2024.acl-long.463/) | 2024 | v11 | Direktester methodischer Vergleich zu Text+Bild-Extraktion mit Layoutbezug | Hoch (4/5): braucht layout-aware Fusion statt nur Bildanhang |  |  |
| [mPlug-DocOwl 1.5: Unified Structure Learning for OCR-Free Document Understanding](https://aclanthology.org/2024.findings-emnlp.175/) | 2024 | v11 | OCR-freies, struktur-aware Dokumentverstaendnis; sehr nah an Approval-PDF-Use-Case | Mittel bis hoch (4/5): als Modellwechsel oder Baseline nutzbar |  |  |
| [Visdom: Multi-Document QA with Visually Rich Elements using Multimodal Retrieval-Augmented Generation](https://aclanthology.org/2025.naacl-long.310/) | 2025 | v11, spaeter RAG-Erweiterung | Relevant fuer multimodales RAG ueber lange Dokumente mit Tabellen/Grafiken | Hoch (4/5): Retrieval- und Indexschicht noetig |  |  |
| [SmolDocling: An ultra-compact vision-language model for end-to-end multi-modal document conversion](https://openaccess.thecvf.com/content/ICCV2025/html/Nassar_SmolDocling_An_ultra-compact_vision-language_model_for_end-to-end_multi-modal_document_conversion_ICCV_2025_paper.html) | 2025 | v11, Preprocessing | Interessant als leichtgewichtige Alternative fuer Marker + Bildverarbeitung | Mittel (3/5): gut fuer schnelle Versuche und lokale Deployments |  |  |
| [TextMonkey: An OCR-Free Large Multimodal Model for Understanding Document](https://arxiv.org/abs/2403.04473) | 2024 | v11 | Sehr starker OCR-freier Vergleichspunkt fuer Document Understanding | Mittel bis hoch (4/5): eher Baseline-/Vergleichsmodell als schneller Drop-in |  |  |

## 3. KG- und schema-konstruierte Extraktion

| Paper | Jahr | Relevante Pipeline(s) | Warum relevant | Implementierung in Pipeline | Kommentare | Schon gelesen |
|---|---:|---|---|---|---|---|
| [Extract, define, canonicalize: An LLM-based framework for knowledge graph construction](https://aclanthology.org/2024.emnlp-main.548/) | 2024 | cable_v1, pipe_v1, comprehensive KG | Sehr starker Treffer fuer mehrstufige KG-Extraktion mit Kanonisierung | Mittel bis hoch (4/5): Extract -> Canonicalize -> Validate |  |  |
| [Schema-aware reference as prompt improves data-efficient knowledge graph construction](https://dl.acm.org/doi/10.1145/3539618.3591763) | 2023 | cable_v1, pipe_v1, comprehensive KG, v12 | Direkt relevant fuer schema- und promptgeführte KG-Erstellung | Mittel (3/5): Prompt- und Few-shot-Upgrade |  |  |
| [Generative Knowledge Graph Construction: A Review](https://aclanthology.org/2022.emnlp-main.1/) | 2022 | alle KG/Turtle Pipelines | Gute methodische Uebersicht ueber linearisierte KG-Generierung und Constraints | Niedrig bis mittel (2/5): eher Designreferenz als direkte Implementierung |  |  |
| [A comprehensive survey on automatic knowledge graph construction](https://dl.acm.org/doi/10.1145/3618295) | 2023 | alle KG/Turtle Pipelines | Sehr gute Referenz fuer Evaluations- und Architekturentscheidungen | Niedrig bis mittel (2/5): Survey fuer Architekturabgleich |  |  |

## 4. Two-step / locate-then-extract / relation extraction

| Paper | Jahr | Relevante Pipeline(s) | Warum relevant | Implementierung in Pipeline | Kommentare | Schon gelesen |
|---|---:|---|---|---|---|---|
| [Knowledge graph prompting for multi-document question answering](https://ojs.aaai.org/index.php/AAAI/article/view/29889) | 2024 | v13, v14, v12 | Passt stark zu KG-gefuehrtem locate-then-extract ueber laengere Dokumente | Mittel (3/5): vor allem Prompt-/Verifikationslogik |  |  |
| [How to unleash the power of large language models for few-shot relation extraction?](https://aclanthology.org/2023.sustainlp-1.13/) | 2023 | v13, cable_v1, pipe_v1 | Relevante Few-shot- und Stufenlogik fuer relation-/record-artige Extraktion | Niedrig bis mittel (2/5): schnell mit Few-shot-Beispielen testbar |  |  |
| [Document-Level Relation Extraction with Relation Correlations](https://doi.org/10.1016/j.neunet.2023.11.062) | 2024 | v13, comprehensive KG | Relevant fuer Dokument-level Relationen statt isolierter Felder | Mittel bis hoch (4/5): komplexer als aktueller Prompt-Flow |  |  |

## 5. Construction/AEC direkt relevant, besonders Compliance-Checking

| Paper | Jahr | Relevante Pipeline(s) | Dokumente/Input | Extraktionsziel | Warum relevant | Implementierung in Pipeline | Kommentare | Schon gelesen |
|---|---:|---|---|---|---|---|---|---|
| [Extraction of Construction Regulatory Requirements from Textual Documents Using Natural Language Processing Techniques](https://doi.org/10.1061/9780784412343.0057) | 2012 | v12, v13, v14, KG-Familie | IBC 2006 / IFC 2009 Textdokumente | quantitative Anforderungen und Regelkandidaten | Sehr frueher, aber sauberer Text->Regel-Extraktionsbaseline fuer Bauvorschriften | Mittel (3/5): gute Vorlage fuer regelbasierte locate-then-extract Templates | Hybrid aus syntaktischen und semantischen NLP-Techniken; direkter Vorlaeufer der spaeteren El-Gohary-Linie. ✅ v5-nahe Umsetzung am 2026-05-12 als `text_only_simple_conversion_v26` (clause typing + semantic verifier gate). |  |
| [Semantic Text Classification for Supporting Automated Compliance Checking in Construction](https://doi.org/10.1061/(ASCE)CP.1943-5487.0000301) | 2013 | v8, v10, v12, v13 | regulatorische und vertragliche Bau-Dokumente | Klausel-/Abschnittsklassifikation vor der Extraktion | Stark fuer Vorfilterung, Routing und Hierarchie-Klassifikation vor eigentlicher Extraktion | Mittel (3/5): als Pre-classifier oder Retrieval-Prefilter gut anschlussfaehig | Paper berichtet 100% Recall und 96% Precision; methodisch relevant fuer Section-Routing und Negativfilter. ✅ Umgesetzt am 2026-05-12 als `text_only_simple_conversion_v25` (requirement-first routing/prefilter vor Extraktion). |  |
| [Information Transformation and Automated Reasoning for Automated Compliance Checking in Construction](https://doi.org/10.1061/9780784413029.088) | 2013 | v12, v13, v14, KG-Familie | regulatorische Textdokumente im Baukontext | Formalisierung in computer-processable Regeln | Gute Referenz fuer den kompletten Schritt Extract -> Formalize -> Reason | Mittel bis hoch (4/5): passt direkt zu Turtle-/KG-Pipelines mit Validierung | Kombiniert Textklassifikation, IE, Transformation und logikbasiertes Reasoning; sehr nah an spaeterem KG-Output. Umgesetzt am 2026-05-12 als `turtle_kg_keyword_v15` mit explizitem Normalize->Formalize Schritt nach der Extraktion. |  |
| [Automated Information Transformation for Automated Regulatory Compliance Checking in Construction](https://doi.org/10.1061/(ASCE)CP.1943-5487.0000427) | 2015 | v12, v13, v14, KG-Familie, v5 | verschiedene Construction-Regeldokumente, getestet auf IBC 2009 | quantitative Anforderungen in Logikklauseln | Eine der staerksten Vor-LLM-Arbeiten fuer regelnahe Texttransformation im Bau | Mittel bis hoch (4/5): Mapping-/Conflict-Resolution-Stage ist direkt uebertragbar | Berichtet 98.2% Precision und 99.1% Recall fuer Transformations-Testing; stark fuer formale Nachbearbeitung. Praktische Pipeline-Umsetzung am 2026-05-12 als `turtle_kg_keyword_v15` (deterministische Normalisierung und Turtle-Formalisierung). |  |
| [Semantic NLP-Based Information Extraction from Construction Regulatory Documents for Automated Compliance Checking](https://doi.org/10.1061/(ASCE)CP.1943-5487.0000346) | 2016 | v12, v13, v14, KG-Familie, v5 | Construction-Regulatory-Dokumente, 2009 IBC | quantitative Anforderungen aus Vorschriftentext | Zentrale Bau-Referenz fuer regel-/semantiknahe Extraktion | Mittel (3/5): keine LLM-Arbeit, aber sehr relevant fuer Strukturierung | Pattern-Matching + Ontologie + Conflict-Resolution; berichtet 0.969 Precision und 0.944 Recall. ✅ Teilweise umgesetzt am 2026-05-12 als `text_only_simple_conversion_v26` mit semantischer Clause-Typisierung und Verifikationsschritt. |  |
| [Extending Building Information Models Semiautomatically Using Semantic Natural Language Processing Techniques](https://doi.org/10.1061/(ASCE)CP.1943-5487.0000536) | 2016 | v12, v13, v14, KG-Familie, v11 | regulatorische Baudokumente plus IFC-Schema | Konzepte und Relationen zur BIM-Erweiterung | Wichtig fuer Repo, wenn aus Text nicht nur Werte, sondern strukturierte BIM-/KG-Semantik gebaut werden soll | Hoch (4/5): guter Treffer fuer Schema-Erweiterung und Ontologie-Anbindung | Semantische NLP-, Similarity- und Klassifikationsschritte zur Auswahl passender IFC-Konzepte; sehr nah an KG-Kanonisierung. Umgesetzt am 2026-05-12 als `kg_comprehensive_schema_minimal_turtle_v3` mit additiver schema_extension + deterministischer canonicalization stage. |  |
| [A deep neural network-based method for deep information extraction using transfer learning strategies to support automated compliance checking](https://doi.org/10.1016/j.autcon.2021.103834) | 2021 | v5, v11, v12, v13 | regulatorische Bau-/Compliance-Texte | Deep IE fuer Compliance-Checking | Starkster nicht-LLM Neural-Upgrade-Pfad zwischen klassischem Regelansatz und aktueller LLM-Welle | Mittel bis hoch (4/5): Transfer-Learning-Ideen fuer Verifier-/Classifier-Stufen interessant | Weniger direkt fuer Prompt-Pipelines, aber wichtig als Referenz fuer learned extraction statt nur heuristischer Stufen. Pragmatische Substitute-Stufe umgesetzt am 2026-05-12 als `text_only_simple_conversion_v26` (deterministischer semantic verifier statt learned verifier). |  |
| [Automatic bridge inspection database construction through hybrid information extraction and large language models](https://doi.org/10.1016/j.dibe.2024.100549) | 2024 | v5, v11, KG-Familie | Brueckeninspektionsberichte | strukturierte Inspektionsdatenbank aus Dokumenttext | Einer der besten Brueckenpaper zwischen Baukontext und moderner IE mit LLMs | Mittel bis hoch (4/5): Hybrid-Pipeline statt reinem Prompting | Gute Transferidee fuer Approval-Dokumente: klassische Vorstrukturierung vor LLM-Extraktion |  |
| [A platform-based Natural Language processing-driven strategy for digitalising regulatory compliance processes for the built environment](https://doi.org/10.1016/j.aei.2024.102653) | 2024 | v8, v10, v12, v13, v14, spaeter v11 | reale Built-Environment-Regeldokumente, UK/Grenfell-Kontext | End-to-End-Regelverarbeitung mit Routing und Prozessdigitalisierung | Besonders relevant, wenn das Repo von isolierter Extraktion zu einer groesseren Compliance-Plattform wachsen soll | Hoch (4/5): Routing-, Orchestrierungs- und Provenance-Ideen sind gut uebertragbar | Paper betont explizit, dass viele Systeme die echten Regeldokumente nicht ausreichend verarbeiten; i-ReC ist eine gute Architektur-Referenz. Diente als Sekundaer-Referenz fuer `text_only_simple_conversion_v25`. |  |
| [Using Large Language Models for the Interpretation of Building Regulations](https://doi.org/10.32738/JEPPM-2024-0035) | 2024 | v12, v13, v14, KG-Familie, v11 | Building Regulations in Freitext | Uebersetzung in LegalRuleML | Bester direkter Treffer fuer LLM-gestuetzte Formalisierung von Bauvorschriften | Mittel bis hoch (4/5): Few-shot + System Prompt + Self-Consistency lassen sich direkt als Prompt-Experimente nachbauen | Sehr nah am Repo-Ziel, wenn Turtle/KG spaeter als formale Regelreprasentation erweitert wird. Umgesetzt am 2026-05-12 als `turtle_kg_keyword_v15` mit LLM-gestuetzter Extraktion plus deterministischem Formalize-Ausgabeschritt in Turtle; erweitert fuer comprehensive KG am 2026-05-12 als `kg_comprehensive_schema_minimal_turtle_v3` mit schema extension und canonicalization vor Scoring. |  |
| [Automated Building Information Modeling Compliance Check through a Large Language Model Combined with Deep Learning and Ontology](https://doi.org/10.3390/buildings14071983) | 2024 | v11, KG-Familie, comprehensive KG | regulatorische Texte + BIM-Kontext | strukturierte Regel-/Pruefinformation fuer BIM-Checks | Einer der wichtigsten Hybrid-LLM-Paper fuer aktuelle Bau-Compliance | Hoch (5/5): passt zu multimodaler/ontologischer Zukunftslinie des Repos | Kombiniert LLM, Deep Learning und Ontologie; Deep Learning wird vorangestellt, um regulatorische Texte strukturierter an das LLM zu geben. Praktische Umsetzung am 2026-05-12 als `text_image_multimodal_conversion_v22` mit evidenzgebundenem Compliance-Grounding und deterministischem Violation-Report-Scaffold. |  |
| [Retrieval augmented generation-driven information retrieval and question answering in construction management](https://doi.org/10.1016/j.aei.2025.103158) | 2025 | v8, v10, spaeter v11 | technische Konstruktions- und Managementdokumente | IR/QA statt direkte Regel-Extraktion | Relevant fuer spaetere Retrieval-Schicht ueber Compliance-/Approval-Korpora | Mittel (3/5): gute Blaupause fuer spaetere Systemstufe | Kein direktes Rule-Extraction-Paper, aber wichtig fuer Upstream-Kontextselektion vor Compliance-Extraktion |  |
| [Large Language Model-Driven Code Compliance Checking in Building Information Modeling](https://doi.org/10.3390/electronics14112146) | 2025 | v11, KG-Familie | Building Codes plus BIM/Revit-Umgebung | Code-Interpretation, Python-Skripterzeugung und Violations-Reports | Starker Downstream-Beleg dafuer, wohin eine gute Extraktionsschicht fuehren kann | Mittel bis hoch (4/5): eher Zielarchitektur nach Extraktion als direkte Extraction-Baseline | LLMs interpretieren Codes, erzeugen Skripte und pruefen automatisch u. a. Raumgroessen, Materialnutzung und Platzierungen. Praktische Umsetzung am 2026-05-12 als `text_image_multimodal_conversion_v22` mit strukturiertem check_status plus Evidence-Provenance-Feldern. |  |
| [Fine-tuning a large language model for automated code compliance of building regulations](https://doi.org/10.1016/j.aei.2025.103676) | 2025 | KG-Familie, v11 | Building Regulations | domain-adaptierte Regelinterpretation und Compliance-Auswertung | Direkt relevant fuer spaetere Bau-Compliance-Extraktion | Mittel bis hoch (4/5): Domain-Daten und Evaluationsset noetig | Wichtigster Hinweis aus der neueren Literatur: domanenspezifische Anpassung von LLMs wird im Compliance-Setting zunehmend zentral. Pragmatischer Zwischenstand im Repo: `kg_comprehensive_schema_minimal_turtle_v3` liefert schema-konforme Kanonisierung ohne Fine-Tuning. |  |

### Kurzfazit fuer Compliance-Checking-Literatur

- **Klassische, weiterhin relevante Kernlinie (2012-2016):** Klassifikation -> IE -> Transformation -> Reasoning. Diese Arbeiten sind methodisch sehr nah an v12/v13/v14 und liefern die saubersten Ideen fuer formale Nachbearbeitung.
- **Neuraler Zwischenschritt (2021):** Learned IE mit Transfer Learning ist ein moeglicher Verifier-/Classifier-Upgrade-Pfad, falls rein promptbasierte Extraktion zu instabil bleibt.
- **Aktuelle LLM-Linie (2024-2025):** Der Trend geht klar zu hybriden Setups: LLM + Vorstrukturierung + Ontologie + formale Zielformate. Reine Chat-Prompting-Loesungen sind seltener als LLMs, die in eine mehrstufige Compliance-Architektur eingebettet werden.
- **Direkteste Repo-Uebernahmen:** `Using Large Language Models for the Interpretation of Building Regulations` fuer Text->Formalisierung, `Automated Building Information Modeling Compliance Check through a Large Language Model Combined with Deep Learning and Ontology` fuer Hybrid-Orchestrierung, und die El-Gohary-Linie fuer robuste regelnahe Vorstrukturierung.

## 6. Agentic LLMs / Tool-use / ReAct (text-only)

| Paper | Jahr | Relevante Pipeline(s) | Warum relevant | Implementierung in Pipeline | Kommentare | Schon gelesen |
|---|---:|---|---|---|---|---|
| [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629) | 2023 | v36 | Kanonische Plan-Act-Observe-Loop fuer LLM-Agenten mit Werkzeugen | Hoch (4/5): direkt als bounded loop ueber bestehende Komponenten umsetzbar | ICLR 2023; v36 implementiert eine minimale Variante mit hartem Step- und Token-Budget. ✅ Umgesetzt am 2026-06-01 als `text_only_simple_conversion_v36`. |  |
| [Toolformer: Language Models Can Teach Themselves to Use Tools](https://arxiv.org/abs/2302.04761) | 2023 | v36 | Begruendet die Disziplin eines kleinen, gut definierten Toolsets (statt generischer Function-Calling-Surface) | Mittel (3/5): nur das Tool-Surface-Prinzip, kein Fine-Tuning | NeurIPS 2023; v36 exponiert genau 5 Tools, alle auf bewaehrten v18/v25-Komponenten. ✅ Umgesetzt am 2026-06-01 als `text_only_simple_conversion_v36`. |  |

## Praktische Update-Prioritaet fuer das Repo

1. **Kurzfristig**: v8/v10 um Retrieval-Qualitaetspruefung und bessere Kontextselektion erweitern.
2. **Kurzfristig**: KG-Pipelines um Kanonisierung und schema-nahe Validierung ergaenzen.
3. **Mittelfristig**: v11 nicht nur mit Bildern fuettern, sondern bild-/layoutrelevante Regionen selektieren.
4. **Mittelfristig**: v13/v14 mit verifier stage zwischen locate und extract aufwerten.
5. **Langfristig**: learned retrieval und multimodale RAG-Schicht ueber Approval-Dokumente aufbauen.

