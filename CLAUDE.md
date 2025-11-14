# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Adaptive Resume Generator is a PyQt6 desktop application that helps job seekers create tailored resumes by storing their complete work history and intelligently matching it to job descriptions. The application uses SQLite for local storage and optionally integrates with the Anthropic Claude API for AI-powered bullet point enhancement.

**Key Technologies**: Python 3.11+, PyQt6, SQLAlchemy, SQLite, Alembic (migrations), ReportLab (PDF generation), spaCy (NLP)

## Common Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
pip install -e .[dev,gui,pdf,nlp,job-analysis]

# Download spaCy language model (required for job posting analysis)
python -m spacy download en_core_web_md
```

### Running the Application
```bash
# Run the GUI application
python -m adaptive_resume.main

# Alternative entry point
python run_gui.py
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=adaptive_resume --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py

# Run specific test
pytest tests/unit/test_models.py::test_profile_creation
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

### Database Management
```bash
# Initialize database (creates tables)
python -m adaptive_resume.database.init_db

# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

## Architecture Overview

### Layered Architecture
The application follows a strict layered architecture:

1. **Presentation Layer** (`src/adaptive_resume/gui/`): PyQt6 UI components
   - `main_window.py`: Central application window with profile/job management
   - `dialogs/`: Modal dialogs for data entry (ProfileDialog, JobDialog, BulletEnhancementDialog, SettingsDialog)
   - `views/`: Reusable view components (JobsView, SkillsSummaryView, ApplicationsView)
   - `widgets/`: Custom widgets (SkillsPanel, EducationPanel)
   - `screens/`: Full-screen UI components
   - `database_manager.py`: Singleton session manager for GUI

2. **Service Layer** (`src/adaptive_resume/services/`): Business logic orchestration
   - Services handle all business operations and coordinate between UI and data layers
   - Each domain entity has a corresponding service (ProfileService, JobService, SkillService, etc.)
   - `ai_enhancement_service.py`: Claude API integration for bullet enhancement
   - `bullet_enhancer.py`: Rule-based bullet point enhancement
   - **Job Posting Analysis Pipeline** (Phase 4):
     - `job_posting_parser.py`: Parse job postings from PDF, DOCX, TXT files
     - `nlp_analyzer.py`: Extract requirements using spaCy + AI hybrid approach
     - `matching_engine.py`: Score accomplishments with 4-component algorithm
     - `resume_generator.py`: Generate tailored resumes with skill coverage analysis

3. **Data Layer** (`src/adaptive_resume/models/`): SQLAlchemy ORM models
   - `base.py`: Database configuration, session factory, and Base class
   - Domain models: Profile, Job, BulletPoint, Skill, Education, Certification, JobApplication
   - **Phase 4 models**: JobPosting, TailoredResumeModel (for storing analysis results)
   - All models inherit from `Base` defined in `base.py`

4. **Configuration** (`src/adaptive_resume/config/`):
   - `settings.py`: Application settings with encrypted API key storage
   - Uses `~/.adaptive_resume/settings.json` for persistence

5. **Utilities** (`src/adaptive_resume/utils/`):
   - `encryption.py`: Fernet-based encryption for API keys

### Database Session Management
- **GUI applications**: Use `DatabaseManager.get_session()` singleton pattern (in `gui/database_manager.py`)
- **Services/Tests**: Use `get_session()` from `models/base.py` for scoped sessions
- Database location: `~/.adaptive_resume/resume_data.db` (configurable via `ADAPTIVE_RESUME_DB_PATH` env var)

### Key Architectural Patterns
- **Dependency Injection**: Services receive session objects, making them testable
- **Service-Oriented**: All business logic lives in services, not in models or UI
- **Repository Pattern**: Services interact with models through SQLAlchemy sessions
- **Separation of Concerns**: UI code never directly touches models; always goes through services

## Important Implementation Details

### AI Enhancement Integration
- AI enhancement is **optional** and requires an Anthropic API key
- API keys are encrypted using Fernet and stored in `~/.adaptive_resume/settings.json`
- Users can enable/disable AI independently of storing the key
- The AI service gracefully degrades when no key is present
- Current model: `claude-sonnet-4-20250514`

### Profile and Job Management
- Each Profile can have multiple Jobs, Skills, Education entries, and Certifications
- Jobs contain BulletPoints for achievement tracking
- BulletPoints can be enhanced using AI or rule-based methods
- The `display_order` field controls presentation order in the UI

### Database Migrations
- Use Alembic for all schema changes
- Migration files are in `alembic/versions/`
- Always test migrations with both SQLite and PostgreSQL compatibility in mind
- Configuration in `alembic.ini` and `alembic/env.py`

### Testing Strategy
- Unit tests in `tests/unit/`
- Use pytest fixtures for database setup
- Services are tested with in-memory SQLite databases
- GUI components have limited test coverage (PyQt6 testing complexity)

## Project Structure Conventions

```
src/adaptive_resume/
├── gui/              # All PyQt6 UI code
│   ├── dialogs/      # Modal dialog windows
│   ├── views/        # Reusable view components
│   ├── widgets/      # Custom widgets
│   └── screens/      # Full-screen components
├── models/           # SQLAlchemy ORM models
├── services/         # Business logic layer
├── config/           # Settings and configuration
├── utils/            # Shared utilities
└── main.py           # Application entry point

tests/
├── unit/             # Unit tests
└── conftest.py       # Pytest fixtures

docs/
├── product/          # Product documentation
├── architecture/     # Technical architecture docs
├── development/      # Development guides
└── reference/        # Decision records and references

alembic/              # Database migrations
```

## Documentation References

### Product & Architecture
- **Product Overview**: `docs/product/overview.md` - Vision, audiences, and roadmap
- **System Architecture**: `docs/architecture/system_architecture.md` - Detailed architecture
- **Setup Guide**: `docs/development/setup_guide.md` - Development environment setup
- **AI Session Guide**: `docs/product/ai_session_guide.md` - Guide for AI-assisted development
- **Status Report**: `docs/development/status_report.md` - Current project status and progress

### UI/UX Design
- **UI Complete Specification**: `docs/design/ui_complete_specification.md` - **Primary design document** with detailed implementation plan (✅ Complete)
  - Left navigation menu + right working area pattern
  - 5 main screens: Dashboard, Companies & Roles, Skills & Education, Job Posting Upload, Review & Print
  - 7-phase implementation plan (14-19 hours estimated)
- **UI Redesign Requirements**: `docs/design/ui_redesign_requirements.md` - Requirements gathering and problem identification
- **UI Redesign from Mockups**: `docs/design/ui_redesign_from_mockups.md` - Alternative tab-based design approach
- **Visual Mockups**: `Visual Look and Feel Idea/` directory contains 5 UI mockup images

### Phase 3.6: Resume Import & Auto-Population (Ready to Start)
- **Phase 3.6 Plan**: `docs/development/phase_3_6_resume_import_plan.md` - Resume import implementation plan (20-26 hours)
  - 5 phases: Resume Parser Extension, Resume Extractor Service, Resume Importer Service, UI Integration, Testing
  - Hybrid spaCy + AI extraction for contact info, work history, education, skills, certifications
  - Preview/confirmation workflow with editing capabilities
  - Reuses Phase 4 parsing infrastructure
  - Intelligent deduplication to avoid duplicate companies/skills
  - Dramatically improves onboarding time (<5 minutes vs 30+ minutes manual entry)

### Phase 4: Job Posting Analysis (✅ COMPLETED)
- **Phase 4 Revised Plan**: `docs/development/phase_4_plan_revised.md` - Implementation completed successfully
  - 6 phases: File Parsing, NLP Analysis, Matching Engine, Resume Generation, UI Integration, Testing
  - Hybrid spaCy + AI approach for requirement extraction
  - Full matching engine with 4-component scoring (skill 40%, semantic 30%, recency 20%, metrics 10%)
  - Complete UI integration with background processing
  - **106 tests passing** (25 parser, 28 analyzer, 34 matching, 19 generator)
  - Database migration applied for JobPosting and TailoredResumeModel
  - New screens: JobPostingScreen (upload/paste), TailoringResultsScreen (results display)
- **Phase 4 Original Plan**: `docs/development/phase_4_plan.md` - Initial comprehensive plan (reference only)

## Development Notes

### When Adding New Models
1. Create model in `src/adaptive_resume/models/`
2. Import in `models/__init__.py`
3. Create corresponding service in `src/adaptive_resume/services/`
4. Generate migration: `alembic revision --autogenerate -m "Add ModelName"`
5. Apply migration: `alembic upgrade head`
6. Add tests in `tests/unit/`

### When Adding New GUI Features
1. **Review the UI design docs first**: Check `docs/design/ui_complete_specification.md` for the planned UI architecture
2. Create dialog/view/widget in appropriate `gui/` subdirectory
3. Connect to existing services (never create new database logic in GUI)
4. Use signals/slots for event handling
5. Import and wire up in `main_window.py` if needed
6. Follow existing patterns for layout and styling

### UI/UX Implementation Notes
- **Current UI State**: Traditional desktop layout with profile sidebar (being redesigned)
- **Target UI Design**: Left navigation menu + right working area (see `ui_complete_specification.md`)
- **Navigation Pattern**: Fixed left sidebar (~200px) with menu items, main content on right
- **Planned Screens**:
  - Dashboard (opening/stats screen)
  - Companies & Roles (primary work area with bullet enhancement)
  - Skills & Education (general info management)
  - Job Posting Upload (✅ Phase 4 - implemented)
  - Tailoring Results (✅ Phase 4 - implemented)
  - Review & Print (Phase 5 - future)
- When implementing new UI features, align with the target design to avoid rework

### When Working with Services
- Services should be stateless except for the session reference
- Always handle exceptions and provide meaningful error messages
- Use transactions appropriately (commit/rollback)
- Services coordinate workflows but don't contain UI logic

### Code Style
- Follow PEP 8 conventions
- Use Black for formatting (line length: 88)
- Type hints are encouraged but not strictly enforced (`disallow_untyped_defs = false`)
- Docstrings for all public classes and functions

## Common Pitfalls

1. **Don't mix session patterns**: Use `DatabaseManager` in GUI, `get_session()` elsewhere
2. **Don't put business logic in models**: Models are data containers; logic goes in services
3. **Don't access database directly from UI**: Always use services as intermediaries
4. **Don't forget to commit**: Services need explicit `session.commit()` calls
5. **Don't skip migrations**: Always use Alembic for schema changes

## Future Architecture Notes

The codebase is designed to migrate from desktop SQLite to hosted web + PostgreSQL:
- Services are written to support async variants
- Configuration uses environment variables for portability
- No hard dependencies on PyQt6 outside `gui/` directory
- Intelligence pipeline is isolated for future API exposure
