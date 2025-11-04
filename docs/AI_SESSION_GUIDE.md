# AI Assistant Onboarding Guide

## Purpose

This guide helps AI assistants quickly understand the Adaptive Resume Generator project and provide consistent, contextual help across multiple sessions.

## Quick Start Checklist

When starting a new AI session on this project:

- [ ] Read `/docs/PROJECT_PLAN.md` - Complete implementation plan and context
- [ ] Check `/docs/STATUS.md` - Current project status and progress
- [ ] Review recent commits - Understand latest changes
- [ ] Read relevant ADRs in `/docs/decisions/` - Understand key decisions
- [ ] Scan `/docs/ARCHITECTURE.md` - System design overview

## Essential Files to Understand

### 1. PROJECT_PLAN.md (MOST IMPORTANT)
**Location:** `/docs/PROJECT_PLAN.md`

This is the master document containing:
- Complete project vision and requirements
- Technology stack with rationale
- Database schema design
- Implementation roadmap (8-week plan)
- Development guidelines
- Git workflow
- Testing strategy
- Future migration path

**When to reference:** Always start here for full project context.

### 2. STATUS.md
**Location:** `/docs/STATUS.md`

Living document showing:
- Current milestone
- Completed items
- In-progress work
- Blockers
- Next steps
- Recent decisions

**When to reference:** To understand current state before making suggestions.

### 3. ARCHITECTURE.md
**Location:** `/docs/ARCHITECTURE.md`

System design documentation:
- Component overview
- Data flow
- Design principles
- Technology integration
- Security considerations

**When to reference:** When working on system design or integration questions.

### 4. Architecture Decision Records (ADRs)
**Location:** `/docs/decisions/*.md`

Documents key technical decisions:
- ADR-0001: Technology Stack Selection
- ADR-0002: Database Choice and ORM
- ADR-0003: GUI Framework Selection
- ADR-0004: PDF Generation Approach
- ADR-0005: NLP/Matching Strategy

**When to reference:** Before suggesting changes to core technologies or approaches.

### 5. DATABASE_SCHEMA.md
**Location:** `/docs/DATABASE_SCHEMA.md`

Complete database documentation:
- Entity relationships
- Table definitions
- Field descriptions
- Indexes and constraints
- Migration strategy

**When to reference:** When working with data models or database queries.

## Project Context

### What This Project Does

Adaptive Resume Generator is a **desktop application** that:
- Stores comprehensive career history (jobs, skills, education)
- Intelligently matches experience to job descriptions
- Generates tailored, ATS-friendly PDF resumes
- Tracks job applications
- Creates customized cover letters

### Key Requirements to Remember

1. **Desktop-first, web-ready architecture**
   - Currently: PyQt6 GUI for desktop
   - Future: Easy migration to web framework
   - Service layer is GUI-agnostic

2. **Local data storage**
   - SQLite database (no server needed)
   - All data stays on user's machine
   - Privacy-focused

3. **ATS-friendly PDFs**
   - Machine-readable format
   - Professional appearance
   - ReportLab for generation

4. **Intelligent matching**
   - Suggests relevant bullet points based on job description
   - Tag-based categorization
   - NLP-powered (spaCy)

### Technology Stack

**Languages & Frameworks:**
- Python 3.11+ (confirmed working with 3.13.3)
- PyQt6 (desktop GUI)
- SQLAlchemy (ORM)
- ReportLab (PDF generation)
- spaCy (NLP/matching)

**Development Tools:**
- pytest (testing - target 75% coverage)
- black (code formatting)
- flake8 (linting)
- mypy (type checking)
- Alembic (database migrations)

**Version Control:**
- Git with simplified Git Flow
- Branches: `main`, `develop`, `feature/*`

### Design Principles

1. **Separation of Concerns**
   - Models = data structure
   - Services = business logic
   - GUI = presentation
   - Clear layer boundaries

2. **Future-proof Architecture**
   - SQLAlchemy enables database portability
   - Service layer can become REST API
   - Business logic independent of GUI

3. **Test-Driven Development**
   - 75% overall coverage target
   - 90%+ for critical components (models, services)
   - Integration tests for workflows

4. **Documentation-First**
   - ADRs for major decisions
   - Inline code documentation
   - Keep docs updated with code

## How to Help Effectively

### Before Making Suggestions

1. **Check if there's an ADR** covering the topic
2. **Verify current implementation** by checking recent commits
3. **Consider future migration** to web platform
4. **Align with existing patterns** in the codebase

### When Proposing Changes

1. **Explain the rationale** - Why is this better?
2. **Consider tradeoffs** - What are the downsides?
3. **Check ADR alignment** - Does this conflict with documented decisions?
4. **Think migration-ready** - Does this make web transition harder?

### Code Contributions

**Always:**
- Follow existing code structure and patterns
- Add/update tests for new functionality
- Update relevant documentation
- Use type hints for function signatures
- Follow Black formatting standards

**Never:**
- Introduce new dependencies without discussion
- Change core architecture without ADR
- Skip tests for critical functionality
- Leave TODOs without GitHub issues

### Documentation Updates

**Update these when relevant:**
- `STATUS.md` - When completing milestones or encountering blockers
- `DATABASE_SCHEMA.md` - When modifying database structure
- `ARCHITECTURE.md` - When changing system design
- Create new ADR - When making significant technical decisions
- `PROJECT_PLAN.md` - When changing roadmap or priorities

## Common Tasks & How to Handle

### Task: User wants to add a new feature

1. Check if it aligns with project goals in PROJECT_PLAN.md
2. Determine which milestone it fits into
3. Consider database schema changes needed
4. Propose implementation approach
5. Suggest creating ADR if it's a significant change
6. Update STATUS.md to track the work

### Task: User reports a bug

1. Identify which component is affected (model/service/GUI)
2. Check if tests exist for that functionality
3. Suggest adding test to reproduce bug first
4. Provide fix that passes the test
5. Consider if this reveals a larger issue

### Task: User wants to refactor code

1. Understand the motivation for refactoring
2. Check if it affects interfaces between components
3. Ensure tests exist before refactoring
4. Verify all tests pass after refactoring
5. Update documentation if interfaces changed

### Task: User needs help understanding the codebase

1. Start with high-level architecture
2. Explain the relevant component
3. Show how data flows through the system
4. Point to specific code examples
5. Reference relevant ADRs for context

### Task: Database schema change needed

1. Check DATABASE_SCHEMA.md for current design
2. Ensure change maintains referential integrity
3. Consider migration path for existing data
4. Update SQLAlchemy models
5. Create Alembic migration
6. Update DATABASE_SCHEMA.md documentation
7. Add tests for new schema

## Development Workflow Reference

### Git Workflow
```bash
# Daily work
git checkout develop
git pull
git checkout -b feature/feature-name
# ... make changes ...
git add .
git commit -m "Description"
git checkout develop
git merge feature/feature-name
git push

# Release
git checkout main
git merge develop
git tag -a v1.0.0 -m "Release 1.0.0"
git push --tags
```

### Testing Workflow
```bash
# Run tests
pytest

# With coverage
pytest --cov=adaptive_resume --cov-report=html

# Specific test
pytest tests/test_matching.py -v

# Check code quality
black src/ tests/
flake8 src/ tests/
mypy src/
```

### Running the Application
```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Run application
python -m adaptive_resume.main
```

## Key Milestones

Refer to STATUS.md for current position in this timeline:

1. **Foundation** (Week 1) - Project setup, documentation, database schema
2. **Core Data** (Week 2) - CRUD operations for all entities
3. **Basic GUI** (Week 3) - User can input and view data
4. **Matching** (Week 4) - Intelligent bullet point suggestions
5. **PDF Generation** (Week 5) - Create professional resumes
6. **Cover Letters** (Week 6) - Generate tailored cover letters
7. **Application Tracking** (Week 7) - Track where resumes were sent
8. **Polish** (Week 8) - Testing, documentation, v1.0 release

## Testing Priorities

**Critical (90%+ coverage required):**
- Database models and relationships
- Matching algorithm
- Resume and cover letter builders
- Data validation

**Important (75%+ coverage):**
- PDF generation
- Service layer business logic
- File operations

**Nice to have (50%+):**
- GUI components
- Utility functions

## Red Flags to Watch For

**⚠️ Stop and discuss if user wants to:**
- Change database from SQLite to something else (violates ADR-0002)
- Use a different GUI framework (violates ADR-0003)
- Add cloud synchronization (violates privacy principle)
- Skip writing tests for new features
- Introduce breaking changes without migration path

**✅ Encourage user to:**
- Write tests first (TDD)
- Document decisions with ADRs
- Update STATUS.md regularly
- Keep commits small and focused
- Follow existing code patterns

## Communication Guidelines

**Be concise and direct:**
- User prefers brief, friendly responses
- Skip disclaimers and apologies
- State "I don't know" when uncertain
- Don't invent information

**Provide context:**
- Reference relevant documentation
- Explain why, not just what
- Link to ADRs for technical decisions
- Show examples from existing code

**Ask for clarification:**
- When requirements are ambiguous
- Before making assumptions
- When multiple approaches are valid

## Useful Code Patterns

### Database Model Pattern
```python
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Job(Base):
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey('profiles.id'))
    company_name = Column(String(255), nullable=False)
    
    # Relationships
    profile = relationship("Profile", back_populates="jobs")
    bullet_points = relationship("BulletPoint", back_populates="job")
```

### Service Pattern
```python
from typing import List, Tuple
from ..models import BulletPoint

class MatchingService:
    """Matches bullet points to job descriptions."""
    
    def get_matching_bullets(
        self, 
        job_description: str, 
        bullets: List[BulletPoint]
    ) -> List[Tuple[BulletPoint, float]]:
        """
        Score and rank bullets by relevance.
        
        Returns:
            List of (bullet, relevance_score) tuples
        """
        # Implementation
        pass
```

### GUI Dialog Pattern
```python
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel

class JobEditorDialog(QDialog):
    """Dialog for editing job information."""
    
    def __init__(self, job=None, parent=None):
        super().__init__(parent)
        self.job = job
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        # Add widgets
        self.setLayout(layout)
```

## Emergency Contacts

**If you encounter:**
- **Conflicting information in docs** → Check git history, ask user which is current
- **Unclear requirements** → Ask user for clarification
- **Security concerns** → Bring to user's attention immediately
- **Major architectural questions** → Reference PROJECT_PLAN.md and relevant ADRs

## Quick Reference Links

- **GitHub Repo:** https://github.com/AlobarQuest/adaptive-resume-generator
- **Project Plan:** `/docs/PROJECT_PLAN.md`
- **Current Status:** `/docs/STATUS.md`
- **Architecture:** `/docs/ARCHITECTURE.md`
- **Setup Guide:** `/docs/SETUP.md`
- **ADRs:** `/docs/decisions/`

## Final Reminders

1. **Always read PROJECT_PLAN.md first** in new sessions
2. **Check STATUS.md** to understand current state
3. **Follow existing patterns** in the codebase
4. **Update documentation** alongside code changes
5. **Write tests** for new functionality
6. **Ask for clarification** when uncertain
7. **Think migration-ready** for web transition
8. **Respect user's preferences** for communication style

---

**Last Updated:** 2025-11-04  
**For Questions:** Reference PROJECT_PLAN.md or ask the user directly
