# HybridRAG Pipeline Design – text_only_simple_conversion_v33

**Status**: Design Phase  
**Date**: 2026-05-18  
**Parent**: text_only_simple_conversion_v32 (scenario ensemble compliance simulation)  
**Theme**: Hybrid Vector+Graph Retrieval for Multi-Hop Regulatory Constraints

---

## 1) Executive Summary

v33 augments v32's proven retrieval and resolution architecture with lightweight graph-based neighborhood expansion. The goal is to improve extraction accuracy for multi-hop regulatory constraints (e.g., "for walls >= 2m, fire resistance must be >= 90 min") that require connecting separate spec passages.

**Key Innovation**: After retrieving top-k chunks via vector/BM25 ranking, extract lightweight entity–predicate triples from those chunks and expand the evidence set by retrieving additional chunks mentioning related entities. This creates implicit multi-hop chains without explicit graph construction.

**Design Principles**:
- Keep v32's strong retrieval stack (ranking, multi-query, diversity selection) unchanged
- Add graph expansion as an **optional, configurable component** (enablement flag)
- Implement confidence-weighted aggregation to combine vector-retrieved and graph-expanded chunks
- Support both "pure vector" (v32 mode) and "hybrid vector+graph" (v33 mode) for A/B testing
- Lightweight extraction: no full KG; focus on extracting entity mentions and linking predicates

---

## 2) Architecture Overview

### 2.1 Data Flow (High-Level)

```
[v32 Retrieval Pipeline]
    ↓
Document → Chunking → Hybrid Ranking → Multi-Query → Diversity Selection → Retrieval QA
    ↓
[NEW: Graph Expansion Layer]
    ↓
Triple Extraction → Entity Expansion → Confidence Weighting & Aggregation
    ↓
[v32 Resolution Pipeline]
    ↓
LLM Generation → Scenario Ensemble → Final Decision
```

### 2.2 Component Breakdown

#### Phase 1: Lightweight Triple Extraction
**Component**: `triple_extractor_v33.py`

**Inputs**:
- `selected_chunks`: List[RankedChunk] (from v32's diversity selector)
- `payload`: ExperimentRequest (target value, conditions)

**Process**:
1. For each selected chunk, identify:
   - **Entity mentions**: Named entities, numeric quantities, product names (lightweight NER using patterns + condition anchors)
   - **Predicates**: Linking phrases ("must be", "shall be", "is at least", "maximum", "minimum") and condition-based relationships
2. Extract candidate triples as tuples: `(entity, predicate, entity_or_value)`
3. Score each triple by:
   - Presence of keywords/conditions from payload
   - Numeric signal strength
   - Predicate confidence (known regulatory verbs score higher)
4. Filter low-confidence triples (confidence < 0.3)

**Outputs**:
```python
@dataclass
class Triple:
    subject: str
    predicate: str
    object_: str
    source_chunk_id: str
    confidence: float
    numeric_signal: bool

@dataclass
class TripleExtractionResult:
    triples: list[Triple]
    entity_set: set[str]  # Unique entities across triples
    predicate_freq: dict[str, int]  # Predicate frequency
    extraction_time_ms: float
```

---

#### Phase 2: Graph-Aware Neighborhood Expansion
**Component**: `graph_neighborhood_retriever_v33.py`

**Inputs**:
- `entity_set`: Set[str] (entities from triple extraction)
- `all_chunks`: List[DocumentChunk] (full document chunks, already indexed)
- `selected_chunks`: List[RankedChunk] (original vector-retrieved chunks)
- `payload`: ExperimentRequest

**Process**:
1. For each entity in the entity set:
   - Search all chunks for additional mentions (normalized text matching)
   - Retrieve chunks containing the entity but not already in selected_chunks
   - Rank these new chunks by:
     - Entity co-occurrence (how many entities from entity_set appear)
     - Numeric signal (presence of quantities)
     - Keyword overlap with payload
2. Limit neighborhood size: `|expanded_chunks| ≤ α × |selected_chunks|` (e.g., α=0.5, max +50% more chunks)
3. Label each new chunk with expansion reason: `"entity_neighborhood:<entity>"` or `"predicate_link:<predicate>"`

**Outputs**:
```python
@dataclass
class NeighborhoodChunk:
    chunk: DocumentChunk
    expansion_reason: str  # "entity_neighborhood:<entity>" or "predicate_link"
    expansion_score: float  # 0.0–1.0, combining co-occurrence and keyword overlap
    is_original_vector_chunk: bool

@dataclass
class NeighborhoodExpansionResult:
    neighborhood_chunks: list[NeighborhoodChunk]
    expansion_count: int
    average_expansion_score: float
    entity_coverage: dict[str, int]  # Per-entity chunk count
```

---

#### Phase 3: Confidence-Weighted Aggregation
**Component**: `hybrid_chunk_aggregator_v33.py`

**Inputs**:
- `selected_chunks`: List[RankedChunk] (original)
- `neighborhood_chunks`: List[NeighborhoodChunk] (expanded)
- `payload`: ExperimentRequest

**Process**:
1. Assign confidence weights:
   - Original vector chunks: `weight_v = ranked_chunk.score / max(scores)` (normalize by max score)
   - Neighborhood chunks: `weight_n = 0.6 × expansion_score` (discount neighborhood chunks relative to original)
2. Combine into unified evidence set with weights:
   ```python
   combined_chunks = [
       (chunk, weight) for chunk, weight in [
           *[(c.chunk, weight_v) for c in selected_chunks],
           *[(c.chunk, weight_n) for c in neighborhood_chunks]
       ]
   ]
   ```
3. Deduplicate by `chunk_id`: if same chunk appears via vector + graph, take the higher weight
4. Sort by weighted score and limit to `max_total_chunks` (configurable, default 15)

**Outputs**:
```python
@dataclass
class AggregatedChunk:
    chunk: DocumentChunk
    vector_weight: float | None  # From original retrieval
    expansion_weight: float | None  # From graph expansion
    combined_weight: float
    is_graph_expanded: bool

@dataclass
class HybridAggregationResult:
    aggregated_chunks: list[AggregatedChunk]
    original_chunk_count: int
    expansion_chunk_count: int
    deduplication_count: int
    average_weight: float
    weight_distribution: dict[str, float]  # Histogram of weight ranges
```

---

### 2.3 Integration Points with v32

**Point 1: Diversity Selection → Triple Extraction**  
After v32's `select_consistent_diverse_chunks_v29()` completes, pass the selected chunks to triple extraction.

**Point 2: Triple Extraction → Neighborhood Expansion**  
Use entity set and predicates to inform entity-based chunk retrieval.

**Point 3: Neighborhood Expansion → Aggregation**  
Merge original ranked chunks with neighborhood chunks via confidence-weighted aggregation.

**Point 4: Aggregation → Prompt Building**  
Pass aggregated chunks to the prompt builder (replaces original selected_chunks in v32 flow).

**Point 5: Prompt → LLM → Scenario Ensemble**  
The rest of v32 pipeline remains unchanged (LLM, scenario ensemble, final decision).

---

## 3) Data Structures

### 3.1 Configuration Flags

Add to `ExperimentRequest` or resolve from `payload.extra`:

```python
# In resolve_*_extra() calls:
hybrid_rag_enabled: bool = _resolve_bool_extra(
    payload, "hybrid_rag_enabled", default=False
)
triple_extraction_confidence_threshold: float = _resolve_float_extra(
    payload, "triple_extraction_confidence_threshold", default=0.3, minimum=0.0, maximum=1.0
)
entity_expansion_alpha: float = _resolve_float_extra(
    payload, "entity_expansion_alpha", default=0.5, minimum=0.1, maximum=2.0
)
neighborhood_discount_factor: float = _resolve_float_extra(
    payload, "neighborhood_discount_factor", default=0.6, minimum=0.2, maximum=1.0
)
max_aggregated_chunks: int = _resolve_int_extra(
    payload, "max_aggregated_chunks", default=15, minimum=5, maximum=30
)
```

### 3.2 Component Log Integration

Each HybridRAG component logs details to ComponentLog:

```python
# Triple Extraction
_finish_component(
    triple_extraction_component,
    status="success",
    details={
        "triple_count": len(extraction_result.triples),
        "entity_count": len(extraction_result.entity_set),
        "confidence_threshold": triple_confidence_threshold,
        "top_predicates": dict(sorted(extraction_result.predicate_freq.items(), key=lambda x: -x[1])[:5]),
    }
)

# Neighborhood Expansion
_finish_component(
    neighborhood_component,
    status="success",
    details={
        "expansion_count": expansion_result.expansion_count,
        "average_expansion_score": expansion_result.average_expansion_score,
        "entity_coverage": expansion_result.entity_coverage,
        "expansion_alpha": entity_expansion_alpha,
    }
)

# Aggregation
_finish_component(
    aggregation_component,
    status="success",
    details={
        "original_chunk_count": agg_result.original_chunk_count,
        "expansion_chunk_count": agg_result.expansion_chunk_count,
        "deduplication_count": agg_result.deduplication_count,
        "final_chunk_count": len(agg_result.aggregated_chunks),
        "average_combined_weight": agg_result.average_weight,
    }
)
```

---

## 4) File Structure & Implementation Plan

### 4.1 New Files to Create

```
app/services/components/
├── triple_extractor_v33.py              # Triple extraction from chunks
├── graph_neighborhood_retriever_v33.py  # Entity-based expansion
└── hybrid_chunk_aggregator_v33.py       # Confidence weighting & aggregation

app/services/pipelines/
└── text_only_simple_conversion_v33.py   # Main pipeline orchestrator

tests/
├── test_triple_extractor_v33.py         # Unit tests for triple extraction
├── test_graph_neighborhood_retriever_v33.py  # Tests for entity expansion
├── test_hybrid_chunk_aggregator_v33.py  # Tests for aggregation
└── test_text_only_simple_conversion_v33_flow.py  # End-to-end flow tests

prompts/
└── text_only_v14.txt                    # (If prompt needs updates for hybrid context)
```

### 4.2 Modifications to Existing Files

```
app/services/experiment_runner.py
├── Import run_text_only_simple_conversion_v33
├── Add v33 to pipeline router (line ~134)
└── Add v33 to help message (line ~184)
```

### 4.3 Implementation Order

1. **Triple Extractor** (`triple_extractor_v33.py`)
   - Pattern-based entity identification
   - Predicate detection (regulatory verbs)
   - Triple confidence scoring
   - Unit tests

2. **Neighborhood Retriever** (`graph_neighborhood_retriever_v33.py`)
   - Entity-based chunk search
   - Neighborhood ranking and size limiting
   - Expansion reason labeling
   - Unit tests

3. **Hybrid Aggregator** (`hybrid_chunk_aggregator_v33.py`)
   - Confidence weighting
   - Deduplication logic
   - Final ranking and limiting
   - Unit tests

4. **Pipeline Integration** (`text_only_simple_conversion_v33.py`)
   - Reuse v32 structure
   - Insert HybridRAG layer as optional component
   - Component logging
   - Conditional flow (if hybrid_rag_enabled, else skip to v32 flow)

5. **Experiment Runner Registration**
   - Add import and routing

6. **Findings Document**
   - Write findings after implementation and testing

---

## 5) Design Rationale

### 5.1 Why Lightweight Triples?

- **Full KG construction is expensive**: We avoid explicit graph databases and SPARQL queries.
- **Pattern-based extraction is fast**: Regex + keyword matching can identify entities and predicates in milliseconds.
- **Sufficient for multi-hop**: Two-hop connections (A → B → C) emerge naturally from entity overlap in triples.

### 5.2 Why Confidence Weighting?

- **Vector-retrieved chunks are higher quality**: They ranked higher by BM25/embedding models.
- **Graph-expanded chunks add diversity but lower confidence**: They fill gaps in the entity space.
- **Weighting preserves both signals**: The aggregated context balances breadth (graph expansion) and precision (vector retrieval).

### 5.3 Why Support Both Modes?

- **Pure mode (v32)**: Baseline for A/B testing.
- **Hybrid mode (v33)**: Test if graph expansion helps or hurts.
- **Configuration flag**: Allows toggling without code changes, enabling fair comparison.

### 5.4 Literature Alignment

- **Graph Retrieval-Augmented Generation (2025)**: Hybrid architectures section; entity-based expansion strategies.
- **Retrieval-Augmented Generation for LLMs (2024)**: Re-ranking and diversity emphasis.
- **Long²RAG (2024)**: Multi-hop constraint handling in long documents.

---

## 6) Success Criteria

### 6.1 Implementation Completeness

- [ ] Triple extractor produces valid triples with confidence scores
- [ ] Neighborhood retriever expands entity mentions without exceeding size limits
- [ ] Aggregator deduplicates and weights chunks correctly
- [ ] Pipeline integrates without breaking v32 behavior in pure mode
- [ ] All unit tests pass with >95% code coverage

### 6.2 Functional Validation

- [ ] Hybrid mode retrieves more contextually related chunks than v32
- [ ] Confidence weights correctly discount neighborhood vs. vector chunks
- [ ] Multi-hop questions benefit from entity expansion (measured in findings)
- [ ] No regression in simple (single-hop) questions

### 6.3 Experimental Readiness

- [ ] Pipeline registered in experiment_runner.py
- [ ] Configuration parameters documented
- [ ] Findings document explains approach and trade-offs

---

## 7) Configuration Parameters (Summary)

| Parameter | Default | Type | Purpose |
|-----------|---------|------|---------|
| `hybrid_rag_enabled` | False | bool | Enable/disable hybrid mode |
| `triple_extraction_confidence_threshold` | 0.3 | float | Minimum triple confidence |
| `entity_expansion_alpha` | 0.5 | float | Max expansion = α × original chunks |
| `neighborhood_discount_factor` | 0.6 | float | Weight discount for graph chunks |
| `max_aggregated_chunks` | 15 | int | Final context chunk limit |

---

## 8) Risk Mitigation

### 8.1 Risk: Graph Expansion Adds Noise

**Mitigation**: 
- Confidence threshold filters low-quality triples (default 0.3)
- Neighborhood discount weights favor original retrieval
- Limited expansion size (alpha=0.5) prevents explosion

### 8.2 Risk: Triple Extraction Overhead

**Mitigation**:
- Pattern-based (no ML model), runs in <50ms
- Disabled by default; enabled only if flag is set
- Early exit if entity_set is empty

### 8.3 Risk: Deduplication Logic is Faulty

**Mitigation**:
- Unit tests with known duplicate scenarios
- Weight comparison ensures higher score is preserved
- Detailed logging in component output

---

## 9) Next Steps (Post-Design)

1. **Research Agent**: Validate design against literature; extract entity extraction and graph expansion best practices.
2. **Implementation Agent**: Implement components in order; write unit tests; integrate into pipeline.
3. **Review Agent**: Evaluate correctness, performance, and improvement opportunities.
4. **Findings Document**: Summarize results and lessons learned.

---

## Appendix: Glossary

- **HybridRAG**: Combination of vector/dense + graph-based retrieval-augmented generation
- **Triple**: A tuple (subject, predicate, object) extracted from text
- **Entity**: Named or recognized object (person, location, product, numeric value)
- **Predicate**: Relationship or regulatory verb linking entities
- **Neighborhood Expansion**: Retrieving chunks mentioning entities from initial triples
- **Confidence Weighting**: Scoring chunks by their retrieval method and reliability
- **A/B Testing**: Comparing v32 (pure) vs. v33 (hybrid) modes

---

**Document Status**: DESIGN_COMPLETE  
**Next Approval Gate**: Architecture Soundness Review
