| Field | Value |
| --- | --- |
| Title | Intelligence Pipeline |
| Audience | ML engineers, service developers |
| Status | Stable |
| Last Updated | 2024-06-15 |

## Summary
The intelligence pipeline provides NLP-driven matching between stored accomplishments and incoming job descriptions. This document outlines how spaCy models, tag taxonomies, and scoring heuristics combine to generate actionable recommendations and maintain human-in-the-loop control.

## Key Takeaways
- spaCy powers entity recognition and similarity scoring, augmented with custom heuristics tuned for resume language.
- Tagging enables deterministic filters that complement probabilistic scores, ensuring recommendations stay relevant and controllable.
- The pipeline is service-oriented: data access happens through repositories, allowing it to move behind a web API without significant refactoring.

## Details
### Pipeline Stages
1. **Text Normalization:** Job descriptions and stored bullet points are cleaned—lowercasing, removing stop words, and preserving key proper nouns.
2. **Feature Extraction:** spaCy pipelines generate embeddings, while keyword classifiers detect domain-specific signals (e.g., cloud providers, leadership verbs).
3. **Scoring:** Cosine similarity scores are combined with heuristic boosts for overlapping tags, recency, and highlighted accomplishments.
4. **Recommendation Assembly:** The top-ranked bullet points are grouped by theme, with metadata about metrics and impact preserved for UI rendering.
5. **Feedback Capture:** User selections and manual edits are logged for future tuning of thresholds and weighting schemes.

### Data Dependencies
- Relies on `tags`, `bullet_tags`, and `bullet_points` tables described in the [Data Model](data_model.md).
- Default tag seeds come from `seed_tags` within `src/adaptive_resume/models/seed.py` (or equivalent helper), keeping taxonomy management centralized.
- Model assets are versioned under `data/` and loaded lazily to keep startup time low.

### Operational Considerations
- **Performance:** Batch processing is used when generating recommendations for multiple job postings; caching avoids recomputing embeddings for unchanged bullet points.
- **Extensibility:** Additional models (e.g., transformer encoders) can wrap the same interface as the spaCy pipeline, enabling A/B experiments.
- **Explainability:** Scores are decomposed into component contributions so the UI can surface "why" a bullet was recommended.
- **Offline Mode:** All processing runs locally; no third-party API calls occur without an explicit opt-in feature flag tracked in the delivery plan.

## Next Steps
- Coordinate enhancements with the [Testing Strategy](../development/testing_strategy.md) to ensure fixtures cover new NLP behaviour.
- Reference the [Product Overview](../product/overview.md) to validate that proposed improvements align with user value.
