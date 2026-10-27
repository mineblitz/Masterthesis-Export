# text_only_simple_conversion_v18 Research Distillation

## Inputs
- Corrective Retrieval Augmented Generation (2024)
- Enhancing Retrieval-Augmented Generation: Best Practices (2025)
- Longtriever (inspiration only; lightweight adaptation)

## Implementable ideas selected

### 1) Multi-query formulation and coverage-driven retrieval
- Use multiple semantically related query variants rather than a single keyword list.
- Practical adaptation: derive variants from value + condition pairs + system descriptors + canonical search terms.
- Benefit: better recall under vocabulary mismatch.

### 2) Diversity-aware context selection
- Avoid top-k that over-concentrates on one section/document.
- Practical adaptation: constrained greedy selection with per-document and per-heading caps.
- Benefit: broader evidence set and reduced redundancy.

### 3) Evidence-aware reweighting
- Retrieval quality is improved by prioritizing chunks with stronger extraction evidence.
- Practical adaptation: lightweight heuristic evidence score from numeric/condition/header cues.
- Benefit: better precision for numeric extraction tasks.

### 4) Corrective bounded retry policy
- CRAG-style corrective behavior should be explicit and bounded.
- Practical adaptation: trigger retry for low retrieval quality, low evidence, or null extraction; cap retries to avoid runaway cost.
- Benefit: improved robustness while preserving predictability.

## Out-of-scope for v18 (deferred)
- Training or integrating a dense long-context retriever (Longtriever full approach).
- External index infrastructure or embeddings service.
- Multi-stage re-ranking models requiring additional dependencies.

## Research reviewer gate result
ACCEPT

Rationale:
- All selected ideas are implementable with current repository primitives.
- No schema break required.
- Directly aligned with v8/v10/v17 retrieval lineage and required mission constraints.
