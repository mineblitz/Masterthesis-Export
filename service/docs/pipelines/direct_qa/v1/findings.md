# direct_qa_v1 — Findings

## Pipeline Identity
- **Name:** `direct_qa_v1`
- **Family:** direct_qa
- **Date:** 2026-07-31
- **Dataset:** ACCORD-NLP/CODE-ACCORD-Entities (and similar pre-chunked Q&A datasets)

## Design

### Motivation
Existing pipelines (text_only_simple_conversion family) are designed around
document retrieval from PDFs.  The ACCORD-NLP/CODE-ACCORD-Entities dataset
already provides the text chunk (`content`) and the question (`question`)
directly in each record, making PDF retrieval unnecessary.

### Architecture
```
payload.content + payload.question
        │
        ▼
prompt_loader  (loads direct_qa_v1.txt)
        │
        ▼
prompt_builder  (substitutes {{QUESTION}} and {{CONTENT}})
        │
        ▼
llm_client      (one LLM call)
        │
        ▼
output_parser   (extracts "extracted_value" from JSON response)
        │
        ▼
soft_evaluate_match  (3-level soft check)
        │
        ▼
ExperimentResponse
```

### Soft Matcher (3 levels)
| Level | Rule | Example |
|-------|------|---------|
| 1 | Exact numeric equality (float epsilon 1e-9) or case-folded string | `90` == `90` |
| 2 | Expected number found anywhere inside extracted string | `"90%"` matches `"90"` |
| 3 | Expected string contained inside extracted string (case-insensitive) | `"at least 90 mm"` matches `"90"` |

### Prompt
- File: `prompts/direct_qa_v1.txt`
- Language: English
- Placeholders: `{{QUESTION}}`, `{{CONTENT}}`
- Output: strict JSON `{ "extracted_value": ..., "reason": ... }`

## Model Changes
- `app/models.py`: `system`, `system_name` now default to `""`;
  `approval_links` now defaults to `[]`.  New optional fields:
  `content: str | None` and `question: str | None`.
  All existing pipelines are unaffected (they still supply these fields explicitly).

## Tests
- `tests/test_direct_qa_v1.py` — 8 tests covering:
  - Soft matcher unit tests (5 cases)
  - Pipeline integration with mocked LLM (7 cases)

## Dataset Record Format
```json
{
  "content": "Each air terminal should have a free area of at least 90 ...",
  "question": "Welcher konkrete Zahlen- oder Messwert ...",
  "expected_value": "90",
  "value": "value"
}
```

## Known Limitations
- No document retrieval; relies entirely on the provided chunk being sufficient context.
- Numeric soft match uses first number found in expected string — may misbehave with
  multi-number expected values (not present in this dataset family).
