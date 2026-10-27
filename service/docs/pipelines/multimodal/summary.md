# Multimodal Pipeline Family — Summary

> **Navigation**: [Docs Hub](../../README.md) | [Pipeline Inventory](../README.md) | [Global Summary](../../global/summary.md)

---

## Family Overview

The multimodal family (`text_image_multimodal_conversion_vXX`) processes both text and images extracted by the Marker PDF parser. It targets documents where visual elements (tables, diagrams, fire-protection ratings) carry compliance-relevant information.

**Lineage**: v21 → v22

---

## Performance

| Version | Success Rate (approx.) | Key Theme |
|---|---|---|
| v21 | ~10–15% | Baseline: Marker structure + logo filter |
| v22 | ~12–18% | Compliance grounding, violation reports |

Multimodal pipelines consistently underperform text-only at current LLM capability levels. The added complexity of image processing does not yet compensate for the quality loss from splitting attention across modalities.

**Current recommendation**: Use text-only v25/v26 for production; revisit multimodal when vision-capable LLMs with stronger structured-output support are available.

---

## Version Details

### [v21](v21/findings.md) — Marker Structure Integration
- Parses Marker's structured output (text blocks + image references)
- Logo image filter to suppress decorative/header images
- Optimizes v19 multimodal baseline for Marker-derived document inputs
- **Paper basis**: Marker layout analysis, document structure parsing literature

### [v22](v22/findings.md) — Compliance Grounding
- Compliance grounding stage: associates text and image evidence IDs with each claim
- Structured `compliance_violation_report_v22` output scaffold
- Deterministic deviation computation
- First explicit compliance checking in multimodal pipeline

---

## Related Documents

- [Pipeline Inventory](../README.md) — full paper mapping for multimodal family
- [Research: Paper Index](../../research/paper_index.md) — multimodal models section
- [Research: Literature Review](../../research/literature_review.md) — Layout-Analysis, Multi-modal sections
- [Global Performance Guide](../../global/performance_guide.md) — tier rankings including multimodal
