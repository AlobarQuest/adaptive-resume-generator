| Field | Value |
| --- | --- |
| Title | Development Setup Guide |
| Audience | Engineers, contributors |
| Status | Stable |
| Last Updated | 2024-06-15 |

## Summary
Follow this guide to configure a local environment for the Adaptive Resume Generator. It covers prerequisites, dependency installation, database initialization, and daily workflows so contributors can ship confidently across Windows, macOS, and Linux.

## Key Takeaways
- Use Python 3.11+ and a virtual environment to isolate dependencies; PyQt6, SQLAlchemy, ReportLab, and spaCy power the app.
- Initialize the SQLite database with the provided script and verify the installation by running the pytest suite.
- Adopt the documented branch and quality workflow (black, flake8, mypy, pytest) before opening pull requests.

## Details
### Prerequisites
- Python 3.11 or newer (3.13.3 verified)
- Git 2.49+
- Windows 10/11 or macOS 10.15+/modern Linux distribution
- 4 GB RAM minimum (8 GB recommended)
- 500 MB free disk space

### Initial Setup Steps
1. **Clone the Repository**
   ```bash
   git clone https://github.com/AlobarQuest/adaptive-resume-generator.git
   cd adaptive-resume-generator
   ```
2. **Create and Activate a Virtual Environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```
3. **Install Dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install -e .[dev,gui,pdf,nlp]
   ```
4. **Initialize the Database**
   ```bash
   python -m adaptive_resume.database.init_db
   ```
   Expected output: `Database initialized successfully at: data/adaptive_resume.db`
5. **Verify the Environment**
   ```bash
   pytest
   ```
   All tests should pass. Investigate failures before continuing.
6. **Launch the Application**
   ```bash
   python -m adaptive_resume.main
   ```
   A PyQt6 window opens ready for profile data entry.

### Daily Development Workflow
1. Activate your virtual environment.
2. Sync with the latest changes on `develop` and branch from it (`feature/<description>`).
3. Implement changes, running `pytest`, `black`, `flake8`, and `mypy` regularly.
4. Commit with descriptive messages and push the feature branch for review.

### Tooling Reference
- **Formatting:** `black src/ tests/`
- **Linting:** `flake8 src/ tests/`
- **Type Checking:** `mypy src/`
- **Testing:** `pytest` (optionally `pytest --cov=adaptive_resume --cov-report=html` for coverage)
- **Migrations:**
  ```bash
  alembic revision --autogenerate -m "Describe change"
  alembic upgrade head
  ```

### Troubleshooting Tips
- Missing GUI dependencies: ensure `pip install -e .[gui]` ran successfully on the active interpreter.
- Database errors after model changes: run migrations or delete the local `data/adaptive_resume.db` and reinitialize.
- spaCy model issues: install required language models via `python -m spacy download en_core_web_md` as prompted.

## Next Steps
- Review the [Testing Strategy](testing_strategy.md) to align on expectations for automated coverage.
- Track active tasks using the [Delivery Plan](delivery_plan.md) and [Status Report](status_report.md).
