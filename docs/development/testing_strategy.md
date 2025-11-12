| Field | Value |
| --- | --- |
| Title | Testing Strategy |
| Audience | Engineers, QA contributors |
| Status | Stable |
| Last Updated | 2024-06-15 |

## Summary
Pytest drives automated validation for the Adaptive Resume Generator. This strategy explains the test topology, fixture design, coverage expectations, and how contributors should run and extend the suite to keep quality above the 75% baseline.

## Key Takeaways
- Tests run against an in-memory SQLite database with fixtures that seed canonical data (profiles, jobs, bullet points, tags).
- Target at least 75% line coverage overall and >90% on critical models and services, using `pytest --cov` when the plugin is available.
- Follow the Arrange-Act-Assert pattern and keep tests isolated—each test file declares intent clearly through descriptive names.

## Details
### Test Layout
```
tests/
├── conftest.py        # Shared fixtures (database engine, sessions, seeded data)
├── unit/              # Model and service tests
│   ├── test_profile.py
│   ├── test_job.py
│   └── test_bullet_point.py
└── integration/       # Reserved for UI/service workflows
```

### Fixtures
- `engine`: Creates an in-memory SQLite engine and ensures metadata is created/dropped per test.
- `session`: Provides a scoped SQLAlchemy session with automatic cleanup.
- `seeded_session`: Seeds default tags by calling `seed_tags(session)`.
- `sample_*` fixtures (profile, job, bullet point, skill, education, certification, job_application): Supply representative data for reuse across tests.

### Coverage Expectations
- Run `pytest` on every change; prefer `pytest --cov=adaptive_resume --cov-report=term-missing` locally when `pytest-cov` is installed.
- Maintain >75% overall coverage and strive for >90% in `adaptive_resume.models` and service modules.
- Add regression tests for bugs and ensure integration tests cover multi-layer workflows such as resume generation.

### Running the Suite
```bash
pytest                      # default run
pytest -v                   # verbose output
pytest -k "bullet_point"     # filter by keyword
pytest tests/unit/test_job.py::TestJobModel::test_duration_months
pytest --cov=adaptive_resume --cov-report=html
```
After generating HTML coverage, open `htmlcov/index.html` for a navigable report.

### Best Practices
- Keep fixtures focused; create new ones when behavior diverges to avoid brittle shared state.
- Use factory helpers or builders inside tests to clarify intent rather than overloading fixtures with branching logic.
- Validate both happy-path and failure scenarios (e.g., constraint violations, cascade deletes) to surface regressions early.
- When the behavior depends on time ranges or counts, document the rationale in assertions to aid future reviewers.

## Next Steps
- Confirm your environment is prepared by following the [Development Setup Guide](setup_guide.md).
- Align upcoming work with the [Delivery Plan](delivery_plan.md) so new features include corresponding tests.
