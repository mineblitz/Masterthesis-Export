# Library-Backed New Components and New Pipelines — Implementation Plan

Date: 2026-05-14

> **Important framing:** This document is NOT a migration or replacement plan.
> All existing pipelines and components remain unchanged.
> The goal is to identify which major pipeline parts can be reimplemented using
> mature Python libraries as NEW components, then wire those new components into
> NEW pipelines that run alongside the existing ones for A/B benchmarking.

---

## Scope reviewed

- Documentation: pipeline_inventory_and_paper_mapping.md, experiment_analysis_and_improvement_plan.md, README.md, requirements.txt
- Implemented pipelines (app/services/pipelines/): text-only v1-v28, multimodal v11/v19/v21/v22/v23, turtle/KG v12-v15, cable_v1, pipe_v1, comprehensive v1-v4
- Existing shared components (app/services/components/): structured_document_chunker.py, hybrid_context_ranker.py, retrieval_enhancer_v18–v26_text.py, output_parser_*.py, turtle_triple_scorer_component.py, keyword_context_extractor.py, marker_* components

---

## 1. What is already library-backed in the codebase

These parts are already implemented with third-party libraries and need no new component:

| Current implementation | Library already used |
|---|---|
| PDF text extraction (pdf_text_extractor.py, pdf_text_extractor_v2.py) | pypdf |
| PDF to Markdown conversion (marker_single_pdf_converter.py) | marker-pdf |
| LLM API calls (llm_client.py, llm_client_component.py) | openai SDK |
| Request/response schema validation (models.py, settings.py) | pydantic, pydantic-settings |
| Token counting (token_counter.py) | tiktoken |

---

## 2. Major parts that are currently custom and have mature Python library alternatives

The following table identifies every major self-implemented part, names the libraries that already cover this functionality in Python, and lists which existing pipelines contain that part. The point is: for each of these, a new component backed by the library can be created without touching any existing code.

### 2.1 Document chunking

**Current custom implementation:**
`structured_document_chunker.py` — splits documents by Markdown headings and blank lines into `DocumentChunk` objects. Splitting logic is rule-based (heading detection by `#` prefix or line ending with `:`).

**Limitation of current approach:**
Chunks across dense sections can be too large; chunks at paragraph boundaries can lose cross-section context. The heading detection heuristic is fragile on non-Markdown source formats.

**Python libraries with equivalent or richer functionality:**
- `langchain-text-splitters` — `MarkdownHeaderTextSplitter`, `RecursiveCharacterTextSplitter` with configurable separators and overlap windows. Can emit metadata (heading path) per chunk matching what `DocumentChunk` currently carries.
- `haystack` preprocessors — `DocumentSplitter` with `split_by` options (`word`, `sentence`, `passage`) and `split_overlap` support.
- `unstructured` — `partition_md` / `partition_text` give element-type metadata (Title, NarrativeText, Table, ListItem) and natural document structure.

**Pipelines that use structured_document_chunker.py:**
text_only_simple_conversion_v8, v10, v17, v18, v20, v21, v22, v23, v24, v25, v26;
text_image_multimodal_conversion_v19, v21, v22.

**New component to build:**
`app/services/components/structured_document_chunker_v2.py` (implemented)
— wraps `MarkdownHeaderTextSplitter` (langchain) with the same `DocumentChunk` output type so it is a drop-in for new pipelines only.

---

### 2.2 Lexical ranking (BM25 / keyword scoring)

**Current custom implementation:**
`hybrid_context_ranker.py` — scores chunks by substring hit-count for keywords, conditions, and heading matches, plus a numeric digit presence bonus. Scores are hand-weighted floats.

**Limitation of current approach:**
Substring containment does not account for term frequency, inverse document frequency, or morphological variants. Numeric bonus inflates unrelated numeric tables.

**Python libraries with equivalent or richer functionality:**
- `rank-bm25` — `BM25Okapi` / `BM25Plus` indices compute proper TF-IDF-weighted scores over tokenized chunks. No external service required; pure Python.
- `rapidfuzz` — `process.extract` gives fuzzy lexical matching for query terms against chunk text, tolerating spelling variants and compound German words.
- `whoosh` — in-memory inverted index with BM25F scoring, field boosts (heading vs. body), and phrase queries.

**Pipelines that use hybrid_context_ranker.py:**
text_only_simple_conversion_v8, v10, v17, v18, v20, v21, v22, v23, v24, v25, v26;
text_image_multimodal_conversion_v19, v21, v22.

**New component to build:**
`app/services/components/bm25_context_ranker.py`
— builds a BM25Okapi index from `DocumentChunk` objects at query time, returns ranked `RankedChunk` list with the same interface as `rank_document_chunks`. New pipelines use this instead of the heuristic ranker.

---

### 2.3 Semantic (embedding) reranking

**Current custom implementation:**
`_semantic_overlap_score` in `retrieval_enhancer_v21_text.py` — approximates semantic overlap by Jaccard intersection of lowercased 3-char tokens. This is a heuristic proxy, not a real embedding similarity.

**Limitation of current approach:**
Token Jaccard has no understanding of synonyms, German morphology, or domain semantics. A chunk containing "Feuerwiderstandsklasse" and a query for "Brandschutzanforderung" scores near zero despite being highly relevant.

**Python libraries with equivalent or richer functionality:**
- `sentence-transformers` — `CrossEncoder` models (e.g. `cross-encoder/ms-marco-MiniLM-L-6-v2` for English, or a multilingual variant) re-score (query, chunk) pairs with a fine-tuned relevance model. `SentenceTransformer` bi-encoder gives fast dense retrieval.
- `faiss-cpu` or `chromadb` — vector store for approximate nearest-neighbor retrieval over chunk embeddings.

**Pipelines that use _semantic_overlap_score:**
text_only_simple_conversion_v21, v22, v23, v24, v25, v26;
text_image_multimodal_conversion_v21, v22.

**New component to build:**
`app/services/components/embedding_reranker.py`
— uses a `SentenceTransformer` bi-encoder to encode chunks once, then a `CrossEncoder` to rerank the top-n BM25 candidates. Returns the same `list[RankedChunk]` interface. New pipelines call this after `bm25_context_ranker.py`.

---

### 2.4 Structured output parsing and schema enforcement

**Current custom implementation:**
`output_parser_component.py`, `output_parser_boolean_map_component.py`, `output_parser_record_list_component.py`, `output_parser_label_component.py` — regex + `json.loads` with repair heuristics. Enforcement of field types, required keys, and value ranges is manual.

**Limitation of current approach:**
JSON repair is brittle and field-by-field; there is no retry-with-schema-correction loop built in. LLMs can omit fields silently.

**Python libraries with equivalent or richer functionality:**
- `instructor` — patches the openai client to force structured output via Pydantic model retries. The LLM is asked to produce JSON matching a schema; if validation fails, the error is fed back automatically for up to N retries.
- `outlines` — constrains LLM token sampling to a JSON schema at generation time (works with local models; relevant for the local gemma-3 setup).
- `pydantic` (already installed) — the schema definitions for `ExtractionResult`, `BooleanMapResult`, `RecordListResult` can be declared as Pydantic models and passed to instructor.

**Pipelines where output parsing is custom:**
Text-only families v1-v27 use `parse_extracted_value`; v28 uses `structured_output_parser_v2`.
Boolean map families (v15, v16) use `parse_extracted_boolean_map`.
KG record families (cable_v1, pipe_v1) use `parse_extracted_record_list`.
Multimodal families (v11, v19, v21, v22, v23) use `parse_extracted_value`.

**New component to build:**
`app/services/components/structured_output_parser_v2.py` (implemented)
— declares Pydantic schemas for structured extraction and uses instructor-based schema enforcement with retry. Provides `parse_scalar_v2` for new pipelines while existing parsers remain unchanged.

---

### 2.5 Turtle / RDF parsing, canonicalization, and scoring

**Current custom implementation:**
`turtle_triple_scorer_component.py` — hand-written Turtle parser using regex for prefix declarations, character-level state machine for quote/angle-bracket nesting, and custom decimal normalization. Also, `kg_comprehensive_schema_minimal_turtle_v3.py` contains inline canonicalization logic (`_canonicalize_qname_locals`, `_canonicalize_numeric_literals`, `_ensure_schema_prefixes`, `_dedupe_turtle_lines`) using `re.sub`.

**Limitation of current approach:**
The custom parser does not handle all valid Turtle syntax (blank node property lists, collections, multi-line string literals). Canonicalization by regex can silently fail on edge cases. Scoring is set-based triple comparison with no SHACL structural constraint checking.

**Python libraries with equivalent or richer functionality:**
- `rdflib` — full Turtle 1.1 parser/serializer; `rdflib.Graph.parse(data=..., format="turtle")` produces a normalized triple set. Serialize back to Turtle with canonical prefixes via `graph.serialize(format="turtle")`.
- `pyshacl` — validates an RDF graph against SHACL shapes; can flag missing required predicates and wrong datatypes.
- `owlrl` — OWL 2 RL reasoning over an rdflib graph for closure/inference if needed.

**Pipelines that use the custom Turtle parser/scorer:**
turtle_kg_conversion_v12, turtle_kg_twostep_v13, turtle_kg_keyword_v14, turtle_kg_keyword_v15;
kg_turtle_extraction_cable_v1, kg_turtle_extraction_pipe_v1;
kg_comprehensive_schema_minimal_turtle_v1, v2, v3.

**New components to build:**
`app/services/components/rdf_turtle_parser.py` (implemented)
— wraps `rdflib.Graph.parse` with a repair pre-pass (fence stripping, minimal prefix injection) and returns a normalized `set[tuple[str,str,str]]` matching the current scorer interface.

`app/services/components/rdf_turtle_scorer.py` (implemented)
— computes precision/recall/F1 by comparing two rdflib graphs; optionally runs pyshacl validation for structural compliance. Returns a dict matching the current `score_triple_sets` output so new pipelines can swap in without changing result models.

`app/services/components/rdf_canonicalizer.py` (implemented)
— replaces the inline canonicalization in `kg_comprehensive_schema_minimal_turtle_v3.py` with rdflib round-trip (parse → serialize) to produce deterministic Turtle. Exposes `canonicalize_turtle(turtle_text, schema_ttl) -> str`.

---

### 2.6 Clause typing and semantic classification

**Current custom implementation:**
`_classify_clause_type_v26` in `retrieval_enhancer_v26_text.py` — keyword-list heuristic that assigns a chunk to one of five categories: `requirement`, `scope`, `exception`, `administrative`, `informational`. Based on German keyword occurrence counting; no learned model.

**Limitation of current approach:**
Keyword lists are manually maintained and miss paraphrases. They have no statistical calibration and cannot generalize to new document styles or clause formulations not covered by the list.

**Python libraries with equivalent or richer functionality:**
- `transformers` (already a requirement in requirements.txt) — a zero-shot or fine-tuned sequence classification model (`pipeline("zero-shot-classification", model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")`) can classify a chunk text into the five clause types without retraining.
- `spaCy` + `spacy-transformers` — sentence-level dependency and NER patterns can augment or replace the keyword heuristic.
- `gliner` — generalist NER model that can extract spans matching custom labels (e.g. "requirement clause", "exception clause") without fine-tuning.

**Pipelines that use `_classify_clause_type_v26`:**
text_only_simple_conversion_v25 (routing prefilter), text_only_simple_conversion_v26 (verifier gate).

**New component to build:**
`app/services/components/clause_classifier_lib.py`
— uses a zero-shot classification pipeline from `transformers` to assign clause types. Accepts the same `(heading, text)` inputs as `_classify_clause_type_v26` and returns the same five-category string. New pipelines use this component; the keyword heuristic in v25/v26 is left as-is.

---

### 2.7 Multimodal evidence selection and layout analysis

**Current custom implementation:**
`multimodal_evidence_selector_v19.py` — heuristic scoring of image candidates based on page position, filename stem, keyword overlap against anchor terms. `logo_image_filter.py` — aspect-ratio and filename pattern heuristics to exclude logo images. `marker_structure_parser.py` — custom regex parser for Marker Markdown image/page-span references.

**Limitation of current approach:**
Selection ignores image content entirely; a page with many keywords but no relevant table scores equally to a page with the answer in a specification table. Logo filtering by aspect ratio is unreliable on complex documents.

**Python libraries with equivalent or richer functionality:**
- `docling` — layout-aware document converter producing typed blocks (Text, Table, Figure, SectionHeading) with bounding boxes and confidence scores. Figures and tables can be filtered and ranked by structural type rather than filename heuristics.
- `unstructured` — `partition_pdf` gives per-element classification with layout model outputs; table elements carry a `text_as_html` field enabling structured evidence extraction.
- `rapidfuzz` — can replace the custom `_normalize_for_match` substring search with fuzzy token matching for anchor-to-image-region linking.

**Pipelines that use the custom multimodal evidence stack:**
text_image_multimodal_conversion_v11, v19, v21, v22.

**New components to build:**
`app/services/components/layout_document_parser.py` (implemented)
— wraps `docling` (or `unstructured`) to produce a typed list of document blocks (text, table, figure) with page numbers and bounding boxes. Replaces the Marker structure parser for new pipelines only.

`app/services/components/multimodal_evidence_selector_v23.py` (implemented)
— selects diverse text+image evidence using layout block types and semantic similarity (from `embedding_reranker.py`) rather than filename heuristics and hand-weighted position scores. Returns the same `ImageSelectionResult` interface so the compliance report builder (v22) can be reused unchanged.

---

## 3. New pipelines to build using these new components

The following table shows the current status of library-backed pipelines and remaining planned candidates.

| New pipeline | New components used | Existing pipeline(s) to compare against | Task target |
|---|---|---|---|
| **text_only_simple_conversion_v28** ✅ | bm25_context_ranker, embedding_reranker, structured_document_chunker_v2, structured_output_parser_v2 | text_only_simple_conversion_v27 | simpleMinMaxExtraction, conditionBasedExtraction |
| **kg_comprehensive_schema_minimal_turtle_v4** ✅ | rdf_turtle_parser, rdf_turtle_scorer, rdf_canonicalizer | kg_comprehensive_schema_minimal_turtle_v3 | KG comprehensive schema extraction |
| **text_image_multimodal_conversion_v23** ✅ | layout_document_parser, multimodal_evidence_selector_v23, bm25_context_ranker | text_image_multimodal_conversion_v22 | conditionBasedExtraction (multimodal) |
| kg_turtle_keyword_v16 (planned) | rdf_turtle_parser, rdf_turtle_scorer, bm25_context_ranker | turtle_kg_keyword_v15 | conditionKGExtraction |
| text_only_simple_conversion_v29 (planned) | clause_classifier_lib, structured_output_parser_v2 | text_only_simple_conversion_v28 | conditionBasedExtraction, compliance routing |

---

## 4. Step-by-step build plan for each new pipeline

---

### Pipeline A: text_only_simple_conversion_v28

**Goal:** Replace the heuristic lexical ranker and token-Jaccard reranker with library-grade BM25 + cross-encoder, and replace regex JSON parsing with instructor-enforced schema output.

**Step 1 — Add dependencies to requirements.txt:**
```
rank-bm25
sentence-transformers
instructor
```

**Step 2 — Create new components:**

`app/services/components/bm25_context_ranker.py`
- Input: `list[DocumentChunk]`, `list[str]` query variants
- Implementation: tokenize each chunk text and each query term; build `BM25Okapi` index at call time; score each chunk; return `list[RankedChunk]` sorted descending.
- No changes to existing `hybrid_context_ranker.py`.

`app/services/components/embedding_reranker.py`
- Input: `list[RankedChunk]`, `str` query, `int` top_n
- Implementation: load a multilingual cross-encoder (e.g. `cross-encoder/ms-marco-MiniLM-L-6-v2`); score (query, chunk.text) pairs; return reranked `list[RankedChunk]` top_n.
- Model is loaded once at module level to avoid re-init per request.

`app/services/components/structured_document_chunker_v2.py`
- Input: `str` full docs text
- Implementation: wrap `langchain_text_splitters.MarkdownHeaderTextSplitter` with headers `[("#","h1"),("##","h2"),("###","h3")]`; produce `DocumentChunk` objects with heading metadata.
- Returns same `list[DocumentChunk]` type as existing chunker.

`app/services/components/structured_output_parser_v2.py`
- Declares Pydantic models for scalar extraction and enforces schema output via instructor.
- Uses provider-aware OpenAI-compatible client resolution and `instructor.from_openai(..., mode=JSON)`.
- Provides `parse_scalar_v2(prompt, llm, temperature, max_retries)`.

**Step 3 — Create pipeline file:**
`app/services/pipelines/text_only_simple_conversion_v28.py`
- Follows same structure as modern text-only pipelines (prompt load -> source resolve -> chunk -> rank -> rerank -> parse -> match).
- Chunking: calls `build_structured_document_chunks_v2`.
- Ranking: calls `rank_bm25` instead of `rank_document_chunks`.
- Reranking: calls `embedding_reranker.rerank` on BM25 candidates and forwards top-k context to prompt builder v5.
- Parsing: calls `parse_scalar_v2` instead of `parse_extracted_value`.

**Step 4 — Register:** Add `run_text_only_simple_conversion_v28` to `app/services/experiment_runner.py`.

**Step 5 — Tests:**
`tests/test_text_only_simple_conversion_v28.py`
- Contract test: mock LLM returns malformed JSON → instructor retry loop triggers → valid float extracted.
- Regression test: two frozen payloads from simpleMinMaxExtraction with known correct outputs.

**Step 6 — Benchmark:** Run against v26 on simpleMinMaxExtraction and conditionBasedExtraction.

---

### Pipeline B: kg_comprehensive_schema_minimal_turtle_v4

**Goal:** Replace the hand-written Turtle parser and regex canonicalization with rdflib, and add SHACL validation before scoring.

**Step 1 — Add dependencies to requirements.txt:**
```
rdflib
pyshacl
```

**Step 2 — Create new components:**

`app/services/components/rdf_turtle_parser.py`
- Input: `str` raw Turtle text (possibly with markdown fences or malformed prefix declarations)
- Implementation:
  1. Strip markdown fences (reuse existing `_strip_markdown_fences` logic).
  2. Attempt `rdflib.Graph().parse(data=text, format="turtle")`.
  3. On parse error: inject missing `xsd:` prefix and retry once.
  4. On second failure: raise with diagnostic message.
- Returns: `rdflib.Graph` and `set[tuple[str,str,str]]` (normalized N-Triples string representation).
- Does NOT modify `turtle_triple_scorer_component.py`.

`app/services/components/rdf_turtle_scorer.py`
- Input: two `rdflib.Graph` objects (predicted, expected)
- Implementation: serialize both to N-Triples (`graph.serialize(format="nt")`), parse into triple sets, compute precision/recall/F1.
- Returns: same dict shape as `score_triple_sets` in `turtle_triple_scorer_component.py` so result models are unchanged.

`app/services/components/rdf_canonicalizer.py`
- Input: `str` raw Turtle text, `str` schema Turtle text
- Implementation: parse both with rdflib; add schema namespace bindings to output graph; serialize back to Turtle with `graph.serialize(format="turtle")`.
- Returns: `str` canonical Turtle, `dict` stats (prefixes added, triples before/after dedup).
- Does NOT modify the inline canonicalization in `kg_comprehensive_schema_minimal_turtle_v3.py`.

**Step 3 — Create pipeline file:**
`app/services/pipelines/kg_comprehensive_schema_minimal_turtle_v4.py`
- Follows same hierarchical structure as v3 (schema extension merge → PDF extract → presence detection → subtype detection → value extraction → assembly → canonicalize → score).
- Canonicalization stage: calls `rdf_canonicalizer.canonicalize_turtle` instead of inline regex canonicalization.
- Scoring stage: calls `rdf_turtle_scorer.score_graphs` with rdflib graph parsing.
- Optional SHACL gate: if `run_shacl_validation: true` is set in request extras, calls pyshacl before accepting the assembled Turtle.

**Step 4 — Register and test.**
`tests/test_kg_comprehensive_schema_minimal_turtle_v4.py`
- Test: malformed Turtle from LLM (missing prefix) -> rdf_turtle_parser repairs and parses -> scoring proceeds.
- Test: SHACL shapes reject Turtle missing required predicate → pipeline returns `shacl_violation` status.

**Step 5 — Benchmark:** Run against v3 on the same KG datasets.

---

### Pipeline C: text_image_multimodal_conversion_v23

**Goal:** Replace filename/position heuristics for evidence selection with layout-model-backed block classification.

**Step 1 — Add dependencies to requirements.txt:**
```
docling
rapidfuzz
```

**Step 2 — Create new components:**

`app/services/components/layout_document_parser.py`
- Input: `str` path to PDF or Marker markdown file
- Implementation: use `docling.DocumentConverter` to parse the PDF into typed blocks (Text, Table, Figure, SectionHeading); fall back to Marker markdown if PDF is not available.
- Returns: list of `LayoutBlock(type, page_number, text, image_path | None, confidence)`.

`app/services/components/multimodal_evidence_selector_v23.py`
- Input: `list[LayoutBlock]`, query variants, `int` top_n
- Implementation:
  1. Score text blocks with `bm25_context_ranker` (new component from Pipeline A).
  2. Score figure/table blocks: use `rapidfuzz.fuzz.token_sort_ratio` between block caption/heading and query variants.
  3. Apply document diversity cap (same logic as existing selector, but over `LayoutBlock` types).
  4. Return top_n combined text+image evidence items.
- Does NOT modify `multimodal_evidence_selector_v19.py`.

**Step 3 — Create pipeline file:**
`app/services/pipelines/text_image_multimodal_conversion_v23.py`
- Follows same structure as v22 (Marker load → structure parse → clean → evidence select → multimodal LLM call → parse → compliance report).
- Evidence selection: calls `layout_document_parser` + `multimodal_evidence_selector_v23` instead of `collect_multimodal_image_candidates` + `select_diverse_image_evidence`.
- Compliance report builder (v22) and structured output parser are reused unchanged.

**Step 4 — Register and test.**

**Step 5 — Benchmark:** Run against v22 on multimodal conditionBasedExtraction.

---

## 5. Summary: implemented and remaining files

| File | Status | Depends on |
|---|---|---|
| app/services/components/bm25_context_ranker.py | implemented | rank-bm25 |
| app/services/components/embedding_reranker.py | implemented | sentence-transformers |
| app/services/components/structured_document_chunker_v2.py | implemented | langchain-text-splitters |
| app/services/components/structured_output_parser_v2.py | implemented | instructor, pydantic |
| app/services/components/rdf_turtle_parser.py | implemented | rdflib |
| app/services/components/rdf_turtle_scorer.py | implemented | rdflib, pyshacl |
| app/services/components/rdf_canonicalizer.py | implemented | rdflib |
| app/services/components/layout_document_parser.py | implemented | docling |
| app/services/components/multimodal_evidence_selector_v23.py | implemented | rapidfuzz, bm25_context_ranker |
| app/services/pipelines/text_only_simple_conversion_v28.py | implemented | bm25_context_ranker, embedding_reranker, structured_document_chunker_v2, structured_output_parser_v2 |
| app/services/pipelines/kg_comprehensive_schema_minimal_turtle_v4.py | implemented | rdf_turtle_parser, rdf_turtle_scorer, rdf_canonicalizer |
| app/services/pipelines/text_image_multimodal_conversion_v23.py | implemented | layout_document_parser, multimodal_evidence_selector_v23 |
| app/services/components/clause_classifier_lib.py | planned | transformers |
| app/services/pipelines/kg_turtle_keyword_v16.py | planned | rdf_turtle_parser, rdf_turtle_scorer, bm25_context_ranker |

Existing files modified in implementation include requirements.txt and app/services/experiment_runner.py, plus newly added component/pipeline modules listed above.
