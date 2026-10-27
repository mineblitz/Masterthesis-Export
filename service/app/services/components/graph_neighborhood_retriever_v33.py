"""
Graph Neighborhood Retriever for HybridRAG v33.

Expands retrieved chunks by finding additional chunks that mention entities
extracted from the initial retrieval set. Uses entity co-occurrence and keyword
overlap for ranking expanded chunks.
"""

import time
from dataclasses import dataclass, field
from typing import Optional
import re


@dataclass
class NeighborhoodChunk:
    """Represents a chunk retrieved via graph neighborhood expansion."""
    chunk: object  # DocumentChunk
    expansion_reason: str
    expansion_score: float  # 0.0–1.0
    is_original_vector_chunk: bool = False


@dataclass
class NeighborhoodExpansionResult:
    """Result of graph neighborhood expansion."""
    neighborhood_chunks: list[NeighborhoodChunk] = field(default_factory=list)
    expansion_count: int = 0
    average_expansion_score: float = 0.0
    entity_coverage: dict[str, int] = field(default_factory=dict)
    expansion_time_ms: float = 0.0


class GraphNeighborhoodRetrieverV33:
    """
    Expand retrieved chunks by finding additional chunks mentioning extracted entities.
    Uses lightweight entity co-occurrence matching and keyword overlap scoring.
    """

    def __init__(
        self,
        expansion_alpha: float = 0.5,
        entity_overlap_threshold: int = 1,
        max_chunk_length: int = 10000,
    ):
        """
        Initialize the neighborhood retriever.

        Args:
            expansion_alpha: Max expansion = alpha × |original_chunks| (e.g., 0.5 = 50%)
            entity_overlap_threshold: Minimum # of entities required in neighborhood chunk
            max_chunk_length: Skip chunks longer than this (sanity check)
        """
        self.expansion_alpha = expansion_alpha
        self.entity_overlap_threshold = entity_overlap_threshold
        self.max_chunk_length = max_chunk_length

    def expand(
        self,
        entity_set: set[str],
        selected_chunks: list,
        all_chunks: list,
        payload: object,
        condition_keywords: Optional[set[str]] = None,
    ) -> NeighborhoodExpansionResult:
        """
        Expand retrieved chunks via entity co-occurrence.

        Args:
            entity_set: Set of entities extracted from selected_chunks
            selected_chunks: Original vector-retrieved chunks (RankedChunk objects)
            all_chunks: Full set of document chunks to search
            payload: ExperimentRequest (for accessing condition keywords)
            condition_keywords: Optional set of keywords from payload conditions

        Returns:
            NeighborhoodExpansionResult with expanded chunks and statistics
        """
        start_time = time.time()

        # Build set of chunk IDs already selected (avoid re-retrieving)
        selected_chunk_ids = {
            chunk.id if hasattr(chunk, 'id') else str(chunk)
            for chunk in selected_chunks
        }

        # Compute expansion budget
        max_expansions = max(1, int(len(selected_chunks) * self.expansion_alpha))

        # Search for neighborhood chunks
        candidate_expansions = []
        entity_coverage = {entity: 0 for entity in entity_set}

        for candidate_chunk in all_chunks:
            # Skip already-selected chunks
            chunk_id = candidate_chunk.id if hasattr(candidate_chunk, 'id') else str(candidate_chunk)
            if chunk_id in selected_chunk_ids:
                continue

            # Skip overly long chunks
            chunk_text = candidate_chunk.text if hasattr(candidate_chunk, 'text') else str(candidate_chunk)
            if len(chunk_text) > self.max_chunk_length:
                continue

            # Count entity overlaps
            overlapping_entities = self._find_overlapping_entities(
                entity_set, chunk_text
            )

            # Skip if below threshold
            if len(overlapping_entities) < self.entity_overlap_threshold:
                continue

            # Score the expansion
            expansion_score = self._compute_expansion_score(
                overlapping_entities=overlapping_entities,
                entity_set=entity_set,
                chunk_text=chunk_text,
                condition_keywords=condition_keywords,
            )

            if expansion_score > 0.0:
                # Determine primary expansion reason
                primary_entity = max(
                    overlapping_entities,
                    key=lambda e: chunk_text.lower().count(e.lower())
                )
                expansion_reason = f"entity_neighborhood:{primary_entity}"

                candidate_expansions.append({
                    'chunk': candidate_chunk,
                    'expansion_score': expansion_score,
                    'expansion_reason': expansion_reason,
                    'overlapping_entities': overlapping_entities,
                })

                # Track entity coverage
                for entity in overlapping_entities:
                    entity_coverage[entity] = entity_coverage.get(entity, 0) + 1

        # Sort by expansion score and take top-k
        candidate_expansions.sort(
            key=lambda x: x['expansion_score'],
            reverse=True
        )
        top_expansions = candidate_expansions[:max_expansions]

        # Build neighborhood chunks
        neighborhood_chunks = [
            NeighborhoodChunk(
                chunk=exp['chunk'],
                expansion_reason=exp['expansion_reason'],
                expansion_score=exp['expansion_score'],
                is_original_vector_chunk=False,
            )
            for exp in top_expansions
        ]

        # Compute average expansion score
        avg_expansion_score = (
            sum(c.expansion_score for c in neighborhood_chunks) / len(neighborhood_chunks)
            if neighborhood_chunks
            else 0.0
        )

        expansion_time_ms = (time.time() - start_time) * 1000

        return NeighborhoodExpansionResult(
            neighborhood_chunks=neighborhood_chunks,
            expansion_count=len(neighborhood_chunks),
            average_expansion_score=avg_expansion_score,
            entity_coverage=entity_coverage,
            expansion_time_ms=expansion_time_ms,
        )

    def _find_overlapping_entities(self, entity_set: set[str], chunk_text: str) -> list[str]:
        """
        Find which entities from entity_set appear in chunk_text.

        Uses case-insensitive matching with word boundaries.

        Args:
            entity_set: Set of extracted entities
            chunk_text: Text of candidate chunk

        Returns:
            List of overlapping entities
        """
        overlapping = []
        chunk_lower = chunk_text.lower()

        for entity in entity_set:
            entity_lower = entity.lower()

            # Try exact match first (case-insensitive)
            if entity_lower in chunk_lower:
                overlapping.append(entity)
            # Try word-boundary match for multi-word entities
            elif " " in entity_lower:
                if re.search(
                    r'\b' + re.escape(entity_lower) + r'\b',
                    chunk_lower
                ):
                    overlapping.append(entity)

        return overlapping

    def _compute_expansion_score(
        self,
        overlapping_entities: list[str],
        entity_set: set[str],
        chunk_text: str,
        condition_keywords: Optional[set[str]] = None,
    ) -> float:
        """
        Compute expansion score for a candidate chunk.

        Factors:
        1. Entity co-occurrence ratio (# overlapping / # original entities)
        2. Keyword overlap (condition-related keywords)
        3. Numeric signal (presence of quantities)

        Args:
            overlapping_entities: Entities that appear in the chunk
            entity_set: Original entity set
            chunk_text: Text of the chunk
            condition_keywords: Optional condition keywords from payload

        Returns:
            Expansion score in [0.0, 1.0]
        """
        score = 0.0

        # Factor 1: Entity co-occurrence (0.0–0.5)
        if len(entity_set) > 0:
            cooc_ratio = len(overlapping_entities) / len(entity_set)
            score += 0.5 * cooc_ratio

        # Factor 2: Keyword overlap (0.0–0.3)
        if condition_keywords:
            matching_keywords = sum(
                1 for kw in condition_keywords
                if kw.lower() in chunk_text.lower()
            )
            keyword_score = min(0.3, 0.05 * matching_keywords)
            score += keyword_score

        # Factor 3: Numeric signal (0.0–0.2)
        numeric_matches = re.findall(r"\d+(?:\.\d+)?", chunk_text)
        if numeric_matches:
            score += 0.2

        return min(1.0, score)
