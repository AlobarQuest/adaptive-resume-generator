# Project Status

**Last Updated:** November 9, 2025
**Current Phase:** Matching Engine Preparation (Week 4)
**Version:** 0.1.0
**Project Lead:** AlobarQuest

## Current Milestone: Matching Engine Prep (Week 4)

**Goal:** Stand up the job description matching pipeline that will rank bullet points with TF-IDF scoring and tag heuristics.
**Target Completion:** Week 4 (In Progress)

## Completed Items ✅

### Week 1 – Foundation
- [x] Repository, licensing, and Git Flow structure established (`README.md`, `.gitignore`, `LICENSE`).
- [x] Core documentation suite drafted (project plan, architecture, setup, ADRs in `docs/`).
- [x] SQLAlchemy base, models, and Alembic migration created to capture the full schema (`src/adaptive_resume/models/`, `alembic/versions/d8eaf3acb5a7_initial_schema_with_all_models.py`).
- [x] Pytest and tooling configuration defined in `pyproject.toml` with shared fixtures in `tests/conftest.py`.

### Week 2 – Core Data Management
- [x] Profile and job domain services with validation and CRUD workflows (`src/adaptive_resume/services/profile_service.py`, `src/adaptive_resume/services/job_service.py`).
- [x] Skill, education, and certification services implementing ordering and input validation (`src/adaptive_resume/services/skill_service.py`, `src/adaptive_resume/services/education_service.py`, `src/adaptive_resume/services/certification_service.py`).
- [x] Unit coverage for all service layers, including negative cases and reordering logic (`tests/unit/test_profile_service.py`, `tests/unit/test_job_service.py`, `tests/unit/test_skill_service.py`, `tests/unit/test_education_service.py`, `tests/unit/test_certification_service.py`).
- [x] Model-focused tests verifying relationships and helpers (`tests/unit/test_profile.py`, `tests/unit/test_job.py`, `tests/unit/test_bullet_point.py`).

### Week 3 – Basic GUI
- [x] PyQt6 main window coordinating profile/job navigation, toolbar actions, and status feedback (`src/adaptive_resume/gui/main_window.py`).
- [x] Profile and job dialogs supporting CRUD operations with inline bullet point management (`src/adaptive_resume/gui/dialogs/profile_dialog.py`, `src/adaptive_resume/gui/dialogs/job_dialog.py`).
- [x] Skills and education panels backed by service lookups plus a skills summary view for quick aggregation (`src/adaptive_resume/gui/widgets/skills_panel.py`, `src/adaptive_resume/gui/widgets/education_panel.py`, `src/adaptive_resume/gui/views/skills_summary_view.py`).
- [x] Job-focused view wiring job/bullet selections and placeholder application view for future expansion (`src/adaptive_resume/gui/views/jobs_view.py`, `src/adaptive_resume/gui/views/applications_view.py`).
- [x] GUI smoke tests instantiating the main window and dialogs (`tests/unit/test_gui_main_window.py`, `tests/unit/test_gui_dialogs.py`).

### Tooling & Ops
- [x] Optional dependency groups declared for GUI, PDF, and NLP extras (`pyproject.toml`).
- [x] Git user and branching strategy confirmed.

## In Progress 🚧

- [ ] Matching engine service combining TF-IDF scoring with tag heuristics.
- [ ] Resume assembly helpers to feed GUI previews and PDF rendering.
- [ ] Analytics over skills/education data to support future matching weights.
- [ ] Broader GUI interaction tests (multi-dialog flows, bulk updates) ahead of matching integration.

## Next Steps ▶️

1. Implement the Week 4 matching engine pipeline (description ingestion, keyword extraction, scoring service) with accompanying unit tests.
2. Extend orchestration utilities so the GUI preview panes can consume assembled resume data.
3. Document GUI architecture decisions (signal/slot wiring, widget composition) and expand user help content.
4. Begin the PDF groundwork by defining resume template contracts and placeholder render hooks.

## Milestone Checklist

### ✅ Week 1: Foundation
### ✅ Week 2: Core Data Management
### ✅ Week 3: Basic GUI
### 🔄 Week 4: Matching Engine
- [ ] Job description parser
- [ ] Keyword extraction
- [ ] TF-IDF matching algorithm
- [ ] Tag-based filtering
- [ ] Scoring system
- [ ] Matching service tests

### Week 5: PDF Generation
- [ ] ReportLab template setup
- [ ] Resume layout implementation
- [ ] ATS-friendly formatting
- [ ] Resume builder service
- [ ] PDF preview in GUI

### Week 6: Cover Letters
- [ ] Cover letter section management
- [ ] Section editor with tags
- [ ] Cover letter template
- [ ] Cover letter builder service
- [ ] PDF generation

### Week 7: Application Tracking
- [ ] Job application CRUD
- [ ] Link applications to resumes/cover letters
- [ ] Status tracking
- [ ] Search and filter
- [ ] Application history view

### Week 8: Polish & Release
- [ ] Comprehensive testing
- [ ] Bug fixes
- [ ] Performance optimization
- [ ] User guide documentation
- [ ] Packaging for distribution
- [ ] Version 1.0.0 release

## Blockers

**Current:** None

## Technical Decisions Made

### Confirmed Decisions
1. Public repository with MIT License.
2. Technology stack:
   - Python 3.13.3
   - PyQt6 for desktop GUI
   - SQLite with SQLAlchemy ORM
   - ReportLab for PDF generation
   - spaCy for NLP/matching (Phase 2)
   - TF-IDF + tags for initial matching (Phase 1)
3. Git Flow strategy: main, develop, feature/*.
4. Test coverage targets: 75% overall, 90%+ for critical components.
5. Platform support: Windows and macOS.
6. Package management: `pyproject.toml` with setuptools.
7. Database migrations: Alembic with autogenerate support.

### Pending Decisions
- Specific resume template design choices.
- Cover letter template layouts.
- Exact matching algorithm parameters.
- GUI color scheme and styling.
