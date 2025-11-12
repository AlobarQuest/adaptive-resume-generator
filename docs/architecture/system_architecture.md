| Field | Value |
| --- | --- |
| Title | System Architecture |
| Audience | Engineers, solution architects |
| Status | Stable |
| Last Updated | 2024-06-15 |

## Summary
The Adaptive Resume Generator follows a layered architecture that isolates presentation, orchestration, persistence, and intelligence concerns. This document captures the guiding principles, major components, and runtime interactions that allow the desktop app to scale toward future web and API channels without rewriting core services.

## Key Takeaways
- Four primary layers—Presentation, Services, Data Access, and Persistence—communicate through clearly defined interfaces.
- Cross-cutting utilities handle configuration, error handling, and formatting so the service layer remains focused on business workflows.
- The architecture intentionally mirrors a future client/server split, allowing PyQt6 screens to be replaced by web clients while reusing the same services and repositories.

## Details
### Architectural Principles
1. **Separation of Concerns:** UI code in `src/adaptive_resume/gui/` focuses on interaction patterns; services coordinate workflows; repositories encapsulate database access.
2. **Dependency Inversion:** High-level policies (services) depend on abstractions, not concrete SQLAlchemy sessions, which keeps the door open for alternative data stores or HTTP adapters.
3. **Future-Proof Design:** Every module assumes an eventual migration to PostgreSQL and RESTful delivery—configuration, migrations, and validation are already structured to support that evolution.
4. **Testability:** Layers are small and composable so pytest fixtures can exercise services in isolation using in-memory SQLite or mocked interfaces.

### Component Overview
- **Presentation Layer (PyQt6):** Main window, dialogs for profiles/jobs/skills, preview panes, and AI session wizards live under `gui/`. Widgets perform lightweight validation before delegating to services.
- **Service Layer:** Modules in `src/adaptive_resume/services/` orchestrate resume assembly, job matching, PDF rendering, and application tracking. Services expose synchronous methods today but are written to support asynchronous variants.
- **Data Access Layer:** SQLAlchemy models and repositories in `src/adaptive_resume/models/` translate between domain entities and relational tables. Repositories expose CRUD operations plus domain-specific queries (e.g., fetching highlighted bullet points).
- **Persistence Layer:** Uses SQLite for local, zero-dependency storage. Alembic migrations live in `alembic/` and target both SQLite and PostgreSQL-compatible SQL. Configuration toggles (e.g., `DATABASE_URL`) are sourced from environment variables or `.env` files.
- **Intelligence Pipeline:** The NLP components in `src/adaptive_resume/intelligence/` score bullet relevance, manage spaCy pipelines, and store reusable tag taxonomies. They are invoked by services but isolated so they can be deployed behind an API later.

### Runtime Flow
1. A PyQt6 action (e.g., "Match to Job") triggers a service call with user input and selected profile context.
2. The service validates the request, retrieves data via repositories, and invokes the intelligence pipeline to score and rank bullet points.
3. Results are mapped back into view models for the GUI or passed to the PDF generator to build tailored outputs.
4. Persistence updates commit through SQLAlchemy sessions; events such as application submissions are logged for status tracking.

### Cross-Cutting Concerns
- **Configuration:** Centralized in `src/adaptive_resume/config.py`; leverages `python-dotenv` when available.
- **Error Handling:** Services raise domain exceptions so the GUI can present actionable feedback without exposing stack traces.
- **Logging and Telemetry:** Structured logging prepares the app for future observability pipelines without polluting UI code.
- **Security & Privacy:** Local storage ensures sensitive data never leaves the device. Encryption-at-rest is planned for the hosted deployment and is tracked in the delivery plan.

## Next Steps
- Dive into the [Data Model](data_model.md) for table-by-table contracts and relationships.
- Explore the [Intelligence Pipeline](intelligence_pipeline.md) to understand how NLP scoring integrates with services.
