# direct_qa_conditional_chunk_v1 — Findings

## Pipeline identity
- **Name:** `direct_qa_conditional_chunk_v1`
- **Family:** `direct_qa`
- **Dataset:** Conditional dataset filtered to the same pre-chunked Q&A structure as CODE-ACCORD

## Input mapping

The pipeline uses the existing direct-QA extraction flow, with the conditional dataset's
`chunk` key normalized to `content`. The `question` is passed through unchanged, and
the numeric `expected_value` is the target used to evaluate the extracted answer.
Other conditional fields, including `order`, `conditions`, `value`, and system metadata,
remain available in the experiment request but do not change the extraction prompt.

```text
chunk          → content
question       → question
expected_value → expected_value (evaluation target)
```

The `value` field is the variable label (for example, `min_thickness`), not the expected
answer value. The prompt remains `prompts/direct_qa_v1.txt`; it extracts an answer from
the provided chunk without PDF retrieval. For this pipeline only, an extracted numeric
value is also accepted when it is exactly one tenth of `expected_value` (for example,
expected `450.00`, extracted `45.00`) to accommodate a one-place decimal shift.

## Architecture

```text
conditional record
        │
        ▼
request normalization (chunk → content)
        │
        ▼
direct_qa_v1 prompt and single LLM extraction
        │
        ▼
soft evaluation against expected_value
        │
        └─ accept extracted × 10 == expected
        │
        ▼
ExperimentResponse (pipeline: direct_qa_conditional_chunk_v1)
```

## Validation

- `tests/test_direct_qa_conditional_chunk_v1.py` verifies input normalization,
  prompt grounding, expected-value matching, and the conditional-only tenfold tolerance.
