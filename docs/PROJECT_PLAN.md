# Adaptive Resume Generator - Implementation Plan

**Created:** November 4, 2025  
**Author:** AlobarQuest  
**Status:** Foundation Phase

## Purpose of This Document

This is the master implementation plan for the Adaptive Resume Generator project. This document serves as the "source of truth" for:
- Architecture decisions
- Technology stack rationale
- Database schema design
- Development roadmap
- Future AI session onboarding

**For AI Sessions:** Read this document first to understand the complete project context, design decisions, and implementation approach.

## Project Overview

### Vision
A desktop application that allows users to create tailored, professional resumes by intelligently matching their experience to job descriptions. The system stores comprehensive career history and generates ATS-friendly PDFs with selected, relevant content.

### Key Requirements
1. **Local Desktop Application** - Runs on Windows and Mac
2. **Intelligent Matching** - Suggests relevant bullet points based on job descriptions
3. **PDF Generation** - Creates professional, ATS-friendly resume PDFs
4. **Application Tracking** - Tracks which resumes were sent where
5. **Cover Letters** - Generates tailored cover letters
6. **Future Web Migration** - Architecture supports transition to web-based application

## Technology Stack

### Core Technologies

**Programming Language: Python 3.11+**
- Cross-platform (Windows/Mac)
- Rich ecosystem for desktop and web
- Excellent libraries for PDF, database, GUI
- Easy to maintain and document

**GUI Framework: PyQt6**
- Professional, native-looking interfaces
- Well-documented and mature
- Cross-platform consistency
- Good for desktop-to-web skill transfer

**Database: SQLite → PostgreSQL**
- Start: SQLite (zero config, file-based, perfect for desktop)
- Future: PostgreSQL (when migrating to web)
- SQLAlchemy ORM ensures smooth migration

**PDF Generation: ReportLab**
- Industry standard
- Precise layout control
- ATS-friendly output
- Professional results

**NLP/Matching: spaCy**
- Advanced text matching capabilities
- Can start simple, upgrade sophistication over time
- Good performance for local processing

**ORM: SQLAlchemy**
- Database abstraction
- Makes PostgreSQL migration straightforward
- Excellent documentation
- Type safety with modern Python

**Migrations: Alembic**
- Database version control
- Handles schema changes cleanly
- Integrates with SQLAlchemy

### Development Tools

**Testing:**
- pytest - Unit and integration testing
- pytest-cov - Coverage reporting
- pytest-qt - GUI testing

**Code Quality:**
- black - Code formatting
- flake8 - Linting
- mypy - Type checking

**Version Control:**
- Git with simplified Git Flow
- Branches: main, develop, feature/*

## Architecture Overview

### Design Principles

1. **Separation of Concerns**
   - Models handle data structure
   - Services handle business logic
   - GUI handles presentation
   - Clear boundaries between layers

2. **Single Responsibility**
   - Each module has one clear purpose
   - Easy to test and maintain
   - Reduces coupling

3. **DRY (Don't Repeat Yourself)**
   - Reusable components
   - Shared utilities
   - Template-based generation

4. **Future-Proof Architecture**
   - Database ORM enables migration
   - Business logic independent of GUI
   - API-ready service layer

### System Components

```
┌─────────────────────────────────────────────────┐
│              GUI Layer (PyQt6)                  │
│  - Main Window                                  │
│  - Dialogs (Job, Skill, Profile editors)       │
│  - Widgets (Bullet selector, Preview)          │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│           Services Layer                        │
│  - Matching Service (Job desc → bullets)       │
│  - Resume Builder (Assemble resume)            │
│  - Cover Letter Builder                         │
│  - PDF Generator                                │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│           Models Layer (SQLAlchemy)             │
│  - Profile, Jobs, BulletPoints                 │
│  - Skills, Education, Certifications           │
│  - Applications, Resumes, CoverLetters         │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│              Database (SQLite)                  │
│  - Local file storage                           │
│  - No external dependencies                     │
└─────────────────────────────────────────────────┘
```

### Data Flow

1. **User Input** → GUI collects data
2. **Validation** → Utils validate input
3. **Persistence** → Models save to database
4. **Retrieval** → Services query models
5. **Processing** → Services apply business logic
6. **Generation** → PDF generator creates output
7. **Display** → GUI shows results/preview

## Database Schema

### Entity Relationship Overview

```
Profile (1) ─────< Jobs (many)
                    │
                    └─< BulletPoints (many) >─── Tags (many-to-many)
                    
Profile (1) ─────< Skills (many)
Profile (1) ─────< Education (many)
Profile (1) ─────< Certifications (many)

JobApplications (many) ───> GeneratedResumes (1)
JobApplications (many) ───> GeneratedCoverLetters (1)

GeneratedResumes ───> ResumeTemplates
GeneratedCoverLetters ───> CoverLetterTemplates
```

### Core Tables

**profiles**
- User's core information (name, contact, summary)
- Single profile per database (could extend to multiple)

**jobs**
- Work history entries
- Company, title, dates, location
- Links to bullet points

**bullet_points**
- Individual achievements/responsibilities
- Belongs to one job
- Can have multiple tags
- Contains metrics and impact

**tags**
- Categorizes bullet points
- Categories: technical, leadership, financial, customer-service, etc.
- Enables smart matching

**skills**
- User's skills with proficiency levels
- Categorized (programming, management, tools, etc.)
- Years of experience tracked

**education**
- Academic history
- Degrees, institutions, dates
- Relevant coursework and achievements

**certifications**
- Professional certifications and licenses
- Issue and expiration dates
- Credential IDs and URLs

**job_applications**
- Tracks where resumes were sent
- Stores job description for matching
- Application status (applied, interview, offer, etc.)
- Links to generated documents

**generated_resumes**
- History of created resumes
- Which bullet points were selected (JSON)
- Which template was used
- File path for retrieval

**resume_templates**
- Layout configurations
- Font, colors, section ordering
- Supports multiple template styles

**cover_letter_sections**
- Reusable paragraphs for cover letters
- Tagged for matching to job types
- Opening, body, and closing sections

**generated_cover_letters**
- History of created cover letters
- Which sections were used
- Company and position info

See [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) for complete schema details.

## Implementation Roadmap

### Phase 1: Foundation (Week 1)
**Goal:** Project setup and documentation

- [x] GitHub repository created
- [x] Project structure established
- [x] License (MIT) added
- [x] Git Flow documented
- [ ] All ADRs written
- [ ] Database schema implemented
- [ ] SQLAlchemy models created
- [ ] Alembic migrations configured

**Deliverables:**
- Complete documentation set
- Database structure ready
- Development environment reproducible

### Phase 2: Core Data Management (Week 2)
**Goal:** CRUD operations for all entities

- [ ] Profile management
- [ ] Jobs CRUD with relationship to profile
- [ ] Bullet points CRUD with tagging
- [ ] Skills management
- [ ] Education and certifications
- [ ] Unit tests for all models (90%+ coverage)

**Deliverables:**
- All data can be created, read, updated, deleted
- Tests verify data integrity
- Database properly constrainted

### Phase 3: Basic GUI (Week 3)
**Goal:** User can input and view their data

- [ ] Main window with navigation
- [ ] Profile editor dialog
- [ ] Job editor with inline bullet point management
- [ ] Skills editor with categories
- [ ] Education and certification editors
- [ ] Data display views (list jobs, skills, etc.)

**Deliverables:**
- Functional desktop application
- Users can manage all their data
- Basic UI/UX patterns established

### Phase 4: Matching Engine (Week 4)
**Goal:** Intelligent bullet point suggestion

- [ ] Job description text parser
- [ ] Keyword extraction
- [ ] TF-IDF based matching (initial approach)
- [ ] Tag-based filtering
- [ ] Scoring algorithm for relevance
- [ ] Unit tests for matching (95%+ coverage)

**Deliverables:**
- Paste job description → get ranked bullet points
- Algorithm tested and accurate
- Foundation for future ML improvements

### Phase 5: PDF Generation (Week 5)
**Goal:** Create professional resume PDFs

- [ ] ReportLab template setup
- [ ] Combination chronological/functional layout
- [ ] Header with contact info
- [ ] Professional summary section
- [ ] Skills section
- [ ] Experience section with selected bullets
- [ ] Education and certifications
- [ ] ATS-friendly formatting
- [ ] Resume builder service
- [ ] PDF preview in GUI

**Deliverables:**
- Generate professional PDF resumes
- Output is ATS-friendly
- Template system for future layouts

### Phase 6: Cover Letters (Week 6)
**Goal:** Generate tailored cover letters

- [ ] Cover letter section management
- [ ] Section editor with tags
- [ ] Cover letter template (ReportLab)
- [ ] Company/position customization
- [ ] Cover letter builder service
- [ ] PDF generation
- [ ] Preview in GUI

**Deliverables:**
- Generate professional cover letters
- Reusable section library
- Coordinate with resume styling

### Phase 7: Application Tracking (Week 7)
**Goal:** Track job applications

- [ ] Job application CRUD
- [ ] Link applications to resumes and cover letters
- [ ] Status tracking (applied, interview, offer, rejected)
- [ ] Notes and follow-up dates
- [ ] Search and filter applications
- [ ] Application history view

**Deliverables:**
- Complete application tracking system
- Easy to see application history
- Know which resume was sent where

### Phase 8: Polish & Testing (Week 8)
**Goal:** Production-ready v1.0

- [ ] Comprehensive integration testing
- [ ] User acceptance testing
- [ ] Bug fixes from testing
- [ ] Performance optimization
- [ ] User guide documentation
- [ ] Installation documentation
- [ ] Packaging for distribution (Windows exe, Mac app)

**Deliverables:**
- Version 1.0.0 release
- 75%+ overall test coverage
- User documentation complete
- Ready for public use

## Development Guidelines

### Git Workflow (Simplified Git Flow)

**Branch Structure:**
- `main` - Production releases only (tagged with versions)
- `develop` - Current development work
- `feature/*` - Individual features

**Daily Workflow:**
```bash
# Start work
git checkout develop
git pull

# Create feature branch
git checkout -b feature/bullet-point-editor

# Work and commit frequently
git add .
git commit -m "Add bullet point CRUD operations"

# When feature complete
git checkout develop
git merge feature/bullet-point-editor
git push

# Delete feature branch
git branch -d feature/bullet-point-editor
```

**Release Workflow:**
```bash
# When ready to release
git checkout main
git merge develop
git tag -a v1.0.0 -m "Version 1.0.0 - Initial Release"
git push origin main --tags
```

**Commit Message Guidelines:**
- Use present tense: "Add feature" not "Added feature"
- Be specific: "Add bullet point tagging" not "Update code"
- Reference issues when applicable: "Fix #123: Database connection error"

### Code Style

**Python Style:**
- Follow PEP 8
- Use Black for formatting (automated)
- Maximum line length: 88 characters (Black default)
- Use type hints for function signatures

**Example:**
```python
def get_matching_bullet_points(
    job_description: str, 
    all_bullets: List[BulletPoint]
) -> List[Tuple[BulletPoint, float]]:
    """
    Match bullet points to a job description.
    
    Args:
        job_description: The job posting text
        all_bullets: List of all available bullet points
        
    Returns:
        List of (bullet_point, score) tuples, sorted by relevance
    """
    # Implementation
    pass
```

**Documentation:**
- All public functions have docstrings
- Complex logic has inline comments
- Each module has a module-level docstring

### Testing Strategy

**Test Coverage Targets:**
- Overall: 75%
- Database models: 90%+
- Business logic (services): 90%+
- Matching algorithm: 95%+
- PDF generation: 85%+
- GUI: 50% (focus on critical workflows)

**Test Organization:**
```
tests/
├── test_models.py           # Database model tests
├── test_services.py         # Business logic tests
├── test_matching.py         # Matching algorithm tests
├── test_pdf_generation.py   # PDF output tests
└── test_gui.py             # GUI integration tests
```

**Running Tests:**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=adaptive_resume --cov-report=html

# Run specific test file
pytest tests/test_matching.py

# Run tests matching a pattern
pytest -k "test_bullet_point"
```

### Documentation Updates

**When to Update Documentation:**

1. **Architecture Decision Records (ADRs):** Create new ADR when:
   - Choosing between technology alternatives
   - Changing a significant design pattern
   - Adding a major new feature
   - Reversing a previous decision

2. **DATABASE_SCHEMA.md:** Update when:
   - Adding/removing tables
   - Changing relationships
   - Adding significant indexes
   - Modifying constraints

3. **STATUS.md:** Update when:
   - Completing a milestone
   - Starting new work
   - Encountering blockers
   - Making significant progress

4. **API_REFERENCE.md:** Update when:
   - Adding public functions to services
   - Changing function signatures
   - Adding new services/modules

## Future Migration Path

### Desktop → Web Transition

**Architecture Advantages:**
- Service layer is GUI-agnostic
- SQLAlchemy ORM makes database swap easy
- Business logic can be exposed as REST API

**Migration Steps (Future):**
1. Keep service layer unchanged
2. Replace PyQt6 GUI with web framework (Flask/FastAPI)
3. Migrate SQLite to PostgreSQL
4. Add authentication/authorization
5. Deploy to cloud hosting
6. Add user accounts and data isolation

**Estimated Effort:** 4-6 weeks with current architecture

## Key Design Decisions

See individual ADRs in `docs/decisions/` for detailed rationale:

1. **ADR-0001:** Technology Stack Selection
2. **ADR-0002:** Database Choice and ORM
3. **ADR-0003:** GUI Framework Selection
4. **ADR-0004:** PDF Generation Approach
5. **ADR-0005:** NLP/Matching Strategy

## Security & Privacy

**Current (Desktop v1):**
- All data stored locally
- No cloud synchronization
- No telemetry or tracking
- User controls all data

**Future (Web version):**
- User authentication required
- Data encrypted at rest
- HTTPS for all communication
- GDPR compliance considerations
- User data export/deletion capabilities

## Success Criteria

**Version 1.0 Success:**
- User can manage complete career history
- Matching algorithm provides relevant suggestions
- PDFs are professional and ATS-friendly
- Application tracking is functional
- 75%+ test coverage achieved
- Documentation is complete and accurate

**Long-term Success:**
- Active user community
- Contributions from other developers
- Successful web migration
- Positive user feedback and adoption

## Getting Help

**For AI Sessions:**
1. Read this document first
2. Check [STATUS.md](STATUS.md) for current state
3. Review recent commits for context
4. Read relevant ADRs for decision context
5. Follow existing code patterns

**For Human Developers:**
1. Start with [README.md](../README.md)
2. Follow [SETUP.md](SETUP.md) for environment setup
3. Read [ARCHITECTURE.md](ARCHITECTURE.md) for system design
4. Check [USER_GUIDE.md](USER_GUIDE.md) for application usage

## Appendix

### Glossary

- **ATS:** Applicant Tracking System - software that parses resumes
- **TF-IDF:** Term Frequency-Inverse Document Frequency - text matching algorithm
- **ORM:** Object-Relational Mapping - database abstraction layer
- **CRUD:** Create, Read, Update, Delete - basic data operations
- **ADR:** Architecture Decision Record - design decision documentation

### References

- Python Documentation: https://docs.python.org/3/
- PyQt6 Documentation: https://www.riverbankcomputing.com/static/Docs/PyQt6/
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
- ReportLab Documentation: https://www.reportlab.com/docs/reportlab-userguide.pdf
- Git Flow: https://nvie.com/posts/a-successful-git-branching-model/

### Change Log

- 2025-11-04: Initial project plan created
- 2025-11-04: Repository created and initial structure established
