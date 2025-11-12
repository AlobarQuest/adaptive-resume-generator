# Documentation End State Specification

The documentation refresh is complete when the structure, metadata, and content conventions below are satisfied.

## Directory Layout
```
docs/
├── README.md                     # Documentation landing page
├── ai_documentation_refactor_plan.md
├── documentation_end_state_spec.md
├── product/
│   ├── overview.md               # What the Adaptive Resume Generator does and for whom
│   └── ai_session_guide.md       # Operational workflow for AI-assisted writing sessions
├── architecture/
│   ├── system_architecture.md    # Layered architecture, interactions, and design principles
│   ├── data_model.md             # Database schema and persistence contracts
│   └── intelligence_pipeline.md  # NLP and model orchestration internals
├── development/
│   ├── setup_guide.md            # Environment, tooling, and project bootstrapping
│   ├── testing_strategy.md       # Pytest usage, fixtures, coverage expectations
│   ├── delivery_plan.md          # Project roadmap, milestones, and sequencing
│   └── status_report.md          # Current state, risks, and next actions
└── reference/
    └── adr_index.md              # Links to ADRs in docs/decisions/
```

## Shared Document Template
Every markdown document (except this spec and the refactor plan) must begin with the following metadata table:

```
| Field | Value |
| --- | --- |
| Title | <Document Title> |
| Audience | <Primary readers> |
| Status | <Draft/In Review/Stable> |
| Last Updated | <ISO date> |
```

After the metadata table, each document must contain sections in the following order:

1. `## Summary` – 2-3 sentences describing the purpose of the document.
2. `## Key Takeaways` – Bullet list of the most important points.
3. `## Details` – One or more subsections providing the full narrative for the topic.
4. `## Next Steps` – Links or references to related docs, TODOs, or processes.

## Cross-Linking Rules
- Use relative links to connect documents within `docs/`.
- The landing page (`docs/README.md`) must include an organized table listing all documents grouped by section.
- Each document's `Next Steps` section should reference at least one other relevant document.

## Content Migration Notes
- Existing markdown files in `docs/` should be rewritten or relocated so their content maps to the new structure. Avoid verbatim duplication; refocus paragraphs to match the new section headings.
- ADR files in `docs/decisions/` remain untouched, but `reference/adr_index.md` should summarize and link to them.
