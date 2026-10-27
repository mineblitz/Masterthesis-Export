"""
Triple Extractor for HybridRAG v33.

Lightweight pattern-based extraction of entity–predicate–entity triples from document chunks.
Supports entity detection via lexicon + patterns, predicate identification via regulatory verbs,
and confidence scoring based on keyword frequency, unit consistency, and redundancy.
"""

import re
from dataclasses import dataclass, field
from typing import Optional
import time


@dataclass
class Triple:
    """Represents a single subject–predicate–object triple extracted from a chunk."""
    subject: str
    predicate: str
    object_: str
    source_chunk_id: str
    confidence: float
    numeric_signal: bool = False


@dataclass
class TripleExtractionResult:
    """Result of triple extraction from a set of chunks."""
    triples: list[Triple]
    entity_set: set[str] = field(default_factory=set)
    predicate_freq: dict[str, int] = field(default_factory=dict)
    extraction_time_ms: float = 0.0


# Domain-specific entity patterns
NUMERIC_PATTERN = r"(\d+(?:\.\d+)?)\s*(?:mm|cm|m|hours?|h|min|minutes?|%|degrees?|°)"
REQUIREMENT_KEYWORDS = {
    "must", "shall", "must be", "shall be",
    "minimum", "maximum", "at least", "up to",
    "greater than", "less than", "equal to",
    ">", "<", ">=", "<=", "=",
    "erforderlich", "muss", "soll",  # German
    "mindestens", "höchstens",  # German
}

REGULATORY_VERBS = {
    "must be", "shall be", "must have", "shall have",
    "is", "are", "requires", "requires that",
    "shall", "must", "should", "recommended",
    "cannot be", "shall not",
    "muss", "darf nicht", "erforderlich",  # German
    "soll", "muss sein",  # German
}

PREDICATE_KEYWORDS = {
    "must be": ("requirement", 0.9),
    "shall be": ("requirement", 0.9),
    "minimum": ("constraint", 0.85),
    "maximum": ("constraint", 0.85),
    "at least": ("constraint", 0.8),
    "up to": ("constraint", 0.8),
    "is": ("state", 0.7),
    "are": ("state", 0.7),
    "greater than": ("comparison", 0.8),
    "less than": ("comparison", 0.8),
    "equal to": ("equivalence", 0.75),
    "requires": ("obligation", 0.85),
    "muss": ("obligation", 0.9),
    "darf nicht": ("prohibition", 0.9),
    "erforderlich": ("requirement", 0.9),
}


class TripleExtractorV33:
    """
    Extract lightweight triples from document chunks using pattern matching
    and semantic anchoring.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.3,
        max_triples_per_chunk: int = 10,
    ):
        """
        Initialize the triple extractor.

        Args:
            confidence_threshold: Minimum confidence score for accepting a triple (0.0–1.0)
            max_triples_per_chunk: Maximum number of triples to extract per chunk
        """
        self.confidence_threshold = confidence_threshold
        self.max_triples_per_chunk = max_triples_per_chunk

    def extract(self, chunks: list) -> TripleExtractionResult:
        """
        Extract triples from a list of chunks.

        Args:
            chunks: List of DocumentChunk objects with .id and .text attributes

        Returns:
            TripleExtractionResult with triples, entity set, and statistics
        """
        start_time = time.time()
        triples = []
        entity_set = set()
        predicate_freq = {}

        for chunk in chunks:
            chunk_triples = self._extract_from_chunk(chunk.id, chunk.text)
            
            # Filter by confidence threshold
            filtered_triples = [
                t for t in chunk_triples
                if t.confidence >= self.confidence_threshold
            ]

            # Limit per chunk
            filtered_triples = filtered_triples[:self.max_triples_per_chunk]

            triples.extend(filtered_triples)

            # Build entity set and predicate frequency
            for triple in filtered_triples:
                entity_set.add(triple.subject)
                entity_set.add(triple.object_)
                predicate_freq[triple.predicate] = predicate_freq.get(triple.predicate, 0) + 1

        extraction_time_ms = (time.time() - start_time) * 1000

        return TripleExtractionResult(
            triples=triples,
            entity_set=entity_set,
            predicate_freq=predicate_freq,
            extraction_time_ms=extraction_time_ms,
        )

    def _extract_from_chunk(self, chunk_id: str, text: str) -> list[Triple]:
        """
        Extract triples from a single chunk.

        Args:
            chunk_id: Unique identifier for the chunk
            text: Text content of the chunk

        Returns:
            List of Triple objects (pre-filtering; some may have low confidence)
        """
        triples = []
        text_lower = text.lower()

        # Strategy 1: Requirement keyword + entity + numeric value
        for req_keyword in REQUIREMENT_KEYWORDS:
            if req_keyword in text_lower:
                numeric_matches = re.finditer(NUMERIC_PATTERN, text, re.IGNORECASE)
                for match in numeric_matches:
                    numeric_value = match.group(1)
                    unit = match.group(0).replace(numeric_value, "").strip()

                    # Find predicates near this numeric value
                    for pred_keyword, (pred_type, pred_conf) in PREDICATE_KEYWORDS.items():
                        if pred_keyword in text_lower:
                            # Calculate confidence
                            confidence = self._compute_triple_confidence(
                                subject="value",
                                predicate=pred_keyword,
                                object_=f"{numeric_value} {unit}" if unit else numeric_value,
                                text_lower=text_lower,
                                has_numeric=True,
                            )
                            if confidence > 0.0:
                                triple = Triple(
                                    subject="specification",
                                    predicate=pred_keyword,
                                    object_=f"{numeric_value} {unit}" if unit else numeric_value,
                                    source_chunk_id=chunk_id,
                                    confidence=confidence,
                                    numeric_signal=True,
                                )
                                triples.append(triple)

        # Strategy 2: Entity-predicate-entity from requirement keywords
        for req_keyword in ["must be", "shall be", "is"]:
            pattern = rf"{req_keyword}\s+([A-Za-z0-9\s\-]+?)(?:\s+(?:and|or|,)|\.|\Z)"
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entity_str = match.group(1).strip()
                if len(entity_str) < 100:  # Sanity check
                    confidence = self._compute_triple_confidence(
                        subject="requirement",
                        predicate=req_keyword,
                        object_=entity_str,
                        text_lower=text_lower,
                        has_numeric=bool(re.search(r"\d", entity_str)),
                    )
                    if confidence > 0.0:
                        triple = Triple(
                            subject="requirement",
                            predicate=req_keyword,
                            object_=entity_str,
                            source_chunk_id=chunk_id,
                            confidence=confidence,
                            numeric_signal=bool(re.search(r"\d", entity_str)),
                        )
                        triples.append(triple)

        # Strategy 3: Direct predicate keyword extraction
        for pred_keyword, (pred_type, pred_conf) in PREDICATE_KEYWORDS.items():
            if pred_keyword in text_lower:
                pattern = rf"(?:the\s+)?([A-Za-z0-9\s\-]+?)\s+{re.escape(pred_keyword)}\s+([A-Za-z0-9\s\-\.]+?)(?:\s+(?:and|or|,)|\.|\Z)"
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    subject = match.group(1).strip()
                    obj = match.group(2).strip()
                    if len(subject) < 100 and len(obj) < 100:
                        confidence = self._compute_triple_confidence(
                            subject=subject,
                            predicate=pred_keyword,
                            object_=obj,
                            text_lower=text_lower,
                            has_numeric=bool(re.search(r"\d", obj)),
                        )
                        if confidence > 0.0:
                            triple = Triple(
                                subject=subject,
                                predicate=pred_keyword,
                                object_=obj,
                                source_chunk_id=chunk_id,
                                confidence=confidence,
                                numeric_signal=bool(re.search(r"\d", obj)),
                            )
                            triples.append(triple)

        return triples

    def _compute_triple_confidence(
        self,
        subject: str,
        predicate: str,
        object_: str,
        text_lower: str,
        has_numeric: bool,
    ) -> float:
        """
        Compute confidence score for a triple.

        Factors:
        1. Predicate confidence (known verbs score higher)
        2. Numeric signal consistency
        3. Redundancy (appears multiple times)
        4. Unit consistency (if numeric)

        Args:
            subject: Subject of triple
            predicate: Predicate of triple
            object_: Object of triple
            text_lower: Lowercase version of full text
            has_numeric: Whether the object contains numeric values

        Returns:
            Confidence score in [0.0, 1.0]
        """
        confidence = 0.0

        # Factor 1: Predicate confidence from lookup table
        if predicate.lower() in PREDICATE_KEYWORDS:
            _, pred_conf = PREDICATE_KEYWORDS[predicate.lower()]
            confidence += 0.4 * pred_conf  # Up to 0.4 from predicate
        else:
            confidence += 0.1  # Unknown predicates get minimal credit

        # Factor 2: Numeric signal
        if has_numeric:
            if re.search(NUMERIC_PATTERN, object_):
                confidence += 0.3  # Up to 0.3 from numeric consistency
            else:
                confidence += 0.15

        # Factor 3: Keyword support (requirement context)
        req_support = sum(
            1 for kw in REQUIREMENT_KEYWORDS
            if kw in text_lower
        )
        confidence += min(0.2, 0.05 * req_support)  # Up to 0.2 from keyword support

        # Factor 4: Redundancy bonus (entity appears multiple times)
        entity_mentions = text_lower.count(subject.lower()) + text_lower.count(object_.lower())
        if entity_mentions > 1:
            confidence += min(0.1, 0.05 * (entity_mentions - 1))  # Up to 0.1 redundancy

        # Cap at 1.0
        return min(1.0, confidence)
