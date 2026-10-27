"""
Hybrid Chunk Aggregator for HybridRAG v33.

Merges vector-retrieved chunks with graph-expanded neighborhood chunks using
confidence-weighted aggregation. Deduplicates by chunk ID and produces final
ranked list of evidence chunks.
"""

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AggregatedChunk:
    """Represents a chunk in the final aggregated evidence set."""
    chunk: object  # DocumentChunk
    vector_weight: Optional[float] = None  # Weight from original vector retrieval
    expansion_weight: Optional[float] = None  # Weight from graph expansion
    combined_weight: float = 0.0  # Final weight (max of vector/expansion or sum)
    is_graph_expanded: bool = False  # True if this chunk came from graph expansion


@dataclass
class HybridAggregationResult:
    """Result of hybrid chunk aggregation."""
    aggregated_chunks: list[AggregatedChunk] = field(default_factory=list)
    original_chunk_count: int = 0
    expansion_chunk_count: int = 0
    deduplication_count: int = 0
    average_weight: float = 0.0
    weight_distribution: dict[str, float] = field(default_factory=dict)
    aggregation_time_ms: float = 0.0


class HybridChunkAggregatorV33:
    """
    Aggregate vector-retrieved and graph-expanded chunks with confidence weighting.
    Deduplicates and produces final ranked evidence list.
    """

    def __init__(
        self,
        neighborhood_discount_factor: float = 0.6,
        max_aggregated_chunks: int = 15,
    ):
        """
        Initialize the hybrid aggregator.

        Args:
            neighborhood_discount_factor: Discount applied to graph-expanded chunks
                (e.g., 0.6 = graph chunks get 60% of equivalent vector chunk's weight)
            max_aggregated_chunks: Maximum number of chunks in final aggregated set
        """
        self.neighborhood_discount_factor = neighborhood_discount_factor
        self.max_aggregated_chunks = max_aggregated_chunks

    def aggregate(
        self,
        selected_chunks: list,
        neighborhood_chunks: list,
    ) -> HybridAggregationResult:
        """
        Aggregate vector-retrieved and graph-expanded chunks.

        Args:
            selected_chunks: List of RankedChunk objects from vector retrieval
            neighborhood_chunks: List of NeighborhoodChunk objects from graph expansion

        Returns:
            HybridAggregationResult with aggregated chunks and statistics
        """
        start_time = time.time()

        # Build a map of chunk_id -> (chunk, weight, is_expanded) for deduplication
        chunk_map = {}

        # Process vector-retrieved chunks
        original_count = 0
        for ranked_chunk in selected_chunks:
            chunk_id = ranked_chunk.id if hasattr(ranked_chunk, 'id') else str(ranked_chunk)
            
            # Normalize vector weight: score / max_score
            vector_weight = self._normalize_vector_weight(ranked_chunk)
            
            chunk_map[chunk_id] = {
                'chunk': ranked_chunk.chunk if hasattr(ranked_chunk, 'chunk') else ranked_chunk,
                'vector_weight': vector_weight,
                'expansion_weight': None,
                'is_graph_expanded': False,
            }
            original_count += 1

        # Process neighborhood-expanded chunks
        expansion_count = 0
        deduplication_count = 0
        for neighbor_chunk in neighborhood_chunks:
            chunk = neighbor_chunk.chunk
            chunk_id = chunk.id if hasattr(chunk, 'id') else str(chunk)

            # Apply discount to expansion weight
            expansion_weight = neighbor_chunk.expansion_score * self.neighborhood_discount_factor

            if chunk_id in chunk_map:
                # Chunk already exists from vector retrieval; update if higher weight
                existing = chunk_map[chunk_id]
                if expansion_weight > (existing['expansion_weight'] or 0.0):
                    existing['expansion_weight'] = expansion_weight
                deduplication_count += 1
            else:
                # New chunk from expansion
                chunk_map[chunk_id] = {
                    'chunk': chunk,
                    'vector_weight': None,
                    'expansion_weight': expansion_weight,
                    'is_graph_expanded': True,
                }
                expansion_count += 1

        # Compute combined weights and sort
        aggregated = []
        for chunk_id, data in chunk_map.items():
            # Combined weight: prefer vector weight, use expansion as fallback
            if data['vector_weight'] is not None:
                combined_weight = data['vector_weight']
            else:
                combined_weight = data['expansion_weight'] or 0.0

            aggregated_chunk = AggregatedChunk(
                chunk=data['chunk'],
                vector_weight=data['vector_weight'],
                expansion_weight=data['expansion_weight'],
                combined_weight=combined_weight,
                is_graph_expanded=data['is_graph_expanded'],
            )
            aggregated.append(aggregated_chunk)

        # Sort by combined weight (descending)
        aggregated.sort(key=lambda x: x.combined_weight, reverse=True)

        # Limit to max chunks
        aggregated = aggregated[:self.max_aggregated_chunks]

        # Compute statistics
        average_weight = (
            sum(c.combined_weight for c in aggregated) / len(aggregated)
            if aggregated
            else 0.0
        )

        weight_distribution = self._compute_weight_distribution(aggregated)

        aggregation_time_ms = (time.time() - start_time) * 1000

        return HybridAggregationResult(
            aggregated_chunks=aggregated,
            original_chunk_count=original_count,
            expansion_chunk_count=expansion_count,
            deduplication_count=deduplication_count,
            average_weight=average_weight,
            weight_distribution=weight_distribution,
            aggregation_time_ms=aggregation_time_ms,
        )

    def _normalize_vector_weight(self, ranked_chunk: object) -> float:
        """
        Normalize vector chunk weight to [0.0, 1.0] range.

        Assumes ranked_chunk has a 'score' attribute. If score is already in [0, 1],
        use directly. Otherwise, clip to [0, 1].

        Args:
            ranked_chunk: RankedChunk object with score attribute

        Returns:
            Normalized weight in [0.0, 1.0]
        """
        score = getattr(ranked_chunk, 'score', 0.5)
        
        # If score is very high (e.g., >10), normalize to [0, 1]
        if score > 1.0:
            # Assume scores are in range [0, 100] or similar
            score = min(1.0, score / 100.0)
        
        return max(0.0, min(1.0, score))

    def _compute_weight_distribution(self, aggregated_chunks: list[AggregatedChunk]) -> dict[str, float]:
        """
        Compute histogram of weight ranges.

        Returns:
            Dict with keys like "0.0-0.25", "0.25-0.5", etc., and percentages as values
        """
        if not aggregated_chunks:
            return {}

        ranges = [
            (0.0, 0.25, "0.0-0.25"),
            (0.25, 0.5, "0.25-0.5"),
            (0.5, 0.75, "0.5-0.75"),
            (0.75, 1.0, "0.75-1.0"),
        ]

        distribution = {}
        total = len(aggregated_chunks)

        for low, high, label in ranges:
            count = sum(
                1 for c in aggregated_chunks
                if low <= c.combined_weight < high
            )
            percentage = (count / total) * 100.0
            distribution[label] = round(percentage, 1)

        return distribution
