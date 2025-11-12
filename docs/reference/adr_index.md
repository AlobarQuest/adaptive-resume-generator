| Field | Value |
| --- | --- |
| Title | Architecture Decision Record Index |
| Audience | Engineers, decision-makers |
| Status | Stable |
| Last Updated | 2024-06-15 |

## Summary
This index catalogs the accepted Architecture Decision Records (ADRs) that guide the Adaptive Resume Generator. Review the summaries below before proposing changes so new work respects historical context.

## Key Takeaways
- Five ADRs cover the technology stack, persistence strategy, GUI framework, PDF generation, and NLP approach.
- ADRs live in `docs/decisions/ADR-XXXX-*.md`; link to them from pull requests when referencing or amending decisions.
- Introduce a new ADR whenever a design shift has architectural impact or revisits an accepted choice.

## Details
| ADR | Topic | Summary |
| --- | --- | --- |
| [ADR-0001](../decisions/ADR-0001-technology-stack.md) | Technology Stack | Confirms Python 3.11+, PyQt6, SQLite→PostgreSQL with SQLAlchemy, ReportLab, spaCy, and Alembic as the core tooling. |
| [ADR-0002](../decisions/ADR-0002-database-and-orm.md) | Database & ORM | Documents the SQLite starting point, PostgreSQL migration path, SQLAlchemy usage, and Alembic-driven schema management. |
| [ADR-0003](../decisions/ADR-0003-gui-framework.md) | GUI Framework | Selects PyQt6 for native cross-platform UX, notes licensing considerations, and compares alternatives (Tkinter, Kivy, wxPython). |
| [ADR-0004](../decisions/ADR-0004-pdf-generation.md) | PDF Generation | Chooses ReportLab for precise, ATS-friendly output with template reuse and future styling extensions. |
| [ADR-0005](../decisions/ADR-0005-nlp-matching-strategy.md) | NLP Matching | Defines spaCy-based TF-IDF + tag heuristics for initial matching, with room to layer advanced models later. |

## Next Steps
- When a decision changes, author a superseding ADR and update this index accordingly.
- Reference relevant ADRs from the [Delivery Plan](../development/delivery_plan.md) so roadmap updates reflect architectural intent.
