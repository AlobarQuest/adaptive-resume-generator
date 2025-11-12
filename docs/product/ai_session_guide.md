| Field | Value |
| --- | --- |
| Title | AI Session Facilitation Guide |
| Audience | AI collaborators, human facilitators |
| Status | Stable |
| Last Updated | 2024-06-15 |

## Summary
This guide equips human facilitators and AI collaborators with the shared context they need before joining a working session on the Adaptive Resume Generator. It highlights the canonical documentation, enumerates the key product constraints, and describes how to provide value without drifting from established decisions.

## Key Takeaways
- Always ground suggestions in the authoritative docs listed in the quick-start checklist to keep sessions consistent.
- Remember the core requirements: desktop-first delivery, local data privacy, ATS-friendly exports, and NLP-driven matching.
- Propose changes through the existing delivery plan and ADR process so historical decisions remain traceable.

## Details
### Quick-Start Checklist
Before engaging in a session, confirm you have reviewed:
- [`docs/development/delivery_plan.md`](../development/delivery_plan.md) – canonical roadmap, milestones, and sequencing.
- [`docs/development/status_report.md`](../development/status_report.md) – current progress, risks, and open blockers.
- [`docs/architecture/system_architecture.md`](../architecture/system_architecture.md) – end-to-end design and layer responsibilities.
- [`docs/architecture/data_model.md`](../architecture/data_model.md) – schema contracts for persistence and services.
- [`docs/reference/adr_index.md`](../reference/adr_index.md) – decisions that must be honored or revisited explicitly.

### Project Context Recap
The Adaptive Resume Generator is a Python 3.11+ desktop application (PyQt6) that stores a full career profile, intelligently matches experiences to job descriptions, and produces ATS-friendly PDFs via ReportLab. SQLAlchemy models wrap a local SQLite database today with a migration path to PostgreSQL. spaCy powers the matching pipeline, and pytest with a 75%+ coverage goal enforces quality.

### Collaboration Workflow
1. **Establish Objective:** Clarify which milestone task or bug the session addresses by referencing the delivery plan and status report.
2. **Gather Constraints:** Review relevant ADRs so proposals respect technology choices (e.g., PyQt6, SQLite, ReportLab, spaCy).
3. **Ideate with Guardrails:** When brainstorming, ensure the layered architecture is preserved—UI delegates to services, services consume repositories, and migrations keep data portable.
4. **Document Outcomes:** Summarize recommendations and link to follow-up issues or ADR drafts so the project history stays verifiable.

### Best Practices for AI Contributions
- **Stay Privacy-Conscious:** Data never leaves the user's machine; avoid designs that imply remote storage without an explicit migration plan.
- **Maintain Testability:** Suggest service-level changes that can be exercised through pytest fixtures (see `tests/conftest.py`).
- **Prefer Evolution Over Reinvention:** Align with the delivery plan rather than replacing it; propose adjustments as deltas with clear rationale.
- **Highlight Risks Early:** Flag dependencies on unverified models, third-party APIs, or UI changes that impact accessibility.

## Next Steps
- Consult the [Product Overview](overview.md) when you need a refresher on personas and value propositions.
- Coordinate implementation work using the [Delivery Plan](../development/delivery_plan.md) and raise ADRs when significant design shifts emerge.
