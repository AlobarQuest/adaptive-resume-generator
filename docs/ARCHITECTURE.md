# System Architecture

**Project:** Adaptive Resume Generator  
**Version:** 0.1.0-dev  
**Last Updated:** November 4, 2025  
**Author:** AlobarQuest

## Purpose

This document describes the system architecture of the Adaptive Resume Generator, including:
- High-level system design and component structure
- Layer responsibilities and interactions
- Data flow through the application
- Design patterns and architectural principles
- Component diagrams and relationships

For implementation details, see [PROJECT_PLAN.md](PROJECT_PLAN.md).  
For database specifics, see [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md).

## Architectural Overview

### Design Philosophy

The Adaptive Resume Generator follows a **layered architecture** with clear separation of concerns:

1. **Presentation Layer** - User interface (PyQt6 GUI)
2. **Service Layer** - Business logic and orchestration
3. **Data Access Layer** - Database models and ORM (SQLAlchemy)
4. **Persistence Layer** - SQLite database

This separation enables:
- **Testability:** Each layer can be tested independently
- **Maintainability:** Changes in one layer don't cascade to others
- **Flexibility:** Easy to swap implementations (e.g., GUI → Web, SQLite → PostgreSQL)
- **Reusability:** Services can be used from different interfaces

### Key Architectural Principles

1. **Single Responsibility Principle**
   - Each module has one clear purpose
   - Models handle data structure only
   - Services handle business logic only
   - GUI handles presentation only

2. **Dependency Inversion**
   - High-level modules don't depend on low-level modules
   - Both depend on abstractions (interfaces)
   - Services depend on model interfaces, not implementations

3. **DRY (Don't Repeat Yourself)**
   - Shared utilities for common operations
   - Template-based generation
   - Reusable UI components

4. **SOLID Principles**
   - Open/Closed: Open for extension, closed for modification
   - Liskov Substitution: Subtypes are substitutable
   - Interface Segregation: Many specific interfaces over one general
   - Dependency Inversion: Depend on abstractions

5. **Future-Proof Design**
   - Database abstraction enables migration
   - Service layer ready for API exposure
   - Business logic independent of GUI framework

## System Layers

### Layer 1: Presentation (GUI)

**Technology:** PyQt6  
**Location:** `adaptive_resume/gui/`  
**Purpose:** User interface and user experience

```
adaptive_resume/gui/
├── main_window.py          # Main application window
├── dialogs/
│   ├── profile_dialog.py   # Edit user profile
│   ├── job_dialog.py       # Add/edit job entries
│   ├── skill_dialog.py     # Manage skills
│   ├── education_dialog.py # Manage education
│   └── cert_dialog.py      # Manage certifications
├── widgets/
│   ├── bullet_selector.py  # Select/rank bullet points
│   ├── job_card.py         # Display job summary
│   ├── skill_widget.py     # Skill display/edit
│   └── preview_widget.py   # PDF preview
└── utils/
    ├── validators.py       # Input validation
    └── formatters.py       # Display formatting
```

**Responsibilities:**
- Display data to the user
- Capture user input
- Validate input format (not business rules)
- Trigger service layer operations
- Display results and feedback
- Handle user interactions

**Does NOT:**
- Directly access the database
- Contain business logic
- Perform calculations or matching
- Generate PDFs

**Key Components:**

1. **MainWindow**
   - Central application hub
   - Navigation between sections
   - Menu bar and toolbar
   - Status bar for feedback

2. **Dialogs**
   - Modal windows for editing
   - Form validation
   - Save/Cancel operations
   - Call service layer for persistence

3. **Widgets**
   - Reusable UI components
   - Display complex data structures
   - Handle specific interactions
   - Emit signals for parent handling

### Layer 2: Services (Business Logic)

**Location:** `adaptive_resume/services/`  
**Purpose:** Business logic, orchestration, and processing

```
adaptive_resume/services/
├── matching_service.py     # Match bullets to job descriptions
├── resume_builder.py       # Assemble resume content
├── cover_letter_builder.py # Assemble cover letter content
├── pdf_generator.py        # Generate PDF documents
├── data_service.py         # CRUD operations orchestration
└── export_service.py       # Export/import data
```

**Responsibilities:**
- Implement business rules
- Orchestrate complex operations
- Call multiple models/services
- Perform calculations and analysis
- Generate content
- Validate business logic

**Does NOT:**
- Know about GUI components
- Directly manipulate UI
- Store state (mostly stateless)

**Key Services:**

1. **MatchingService**
   ```python
   class MatchingService:
       def match_bullets_to_job(
           job_description: str,
           available_bullets: List[BulletPoint]
       ) -> List[Tuple[BulletPoint, float]]:
           """Match and rank bullets by relevance"""
   ```
   - Parse job descriptions
   - Extract keywords and requirements
   - Score bullet points by relevance
   - Return ranked matches

2. **ResumeBuilder**
   ```python
   class ResumeBuilder:
       def build_resume(
           profile: Profile,
           selected_bullets: List[BulletPoint],
           template: ResumeTemplate
       ) -> ResumeData:
           """Assemble resume content"""
   ```
   - Organize selected content
   - Apply formatting rules
   - Validate completeness
   - Prepare data for PDF generation

3. **PDFGenerator**
   ```python
   class PDFGenerator:
       def generate_resume_pdf(
           resume_data: ResumeData,
           output_path: str
       ) -> str:
           """Generate PDF resume"""
   ```
   - Create PDF using ReportLab
   - Apply template styling
   - Ensure ATS compatibility
   - Return file path

4. **CoverLetterBuilder**
   ```python
   class CoverLetterBuilder:
       def build_cover_letter(
           profile: Profile,
           sections: List[CoverLetterSection],
           job_info: dict
       ) -> CoverLetterData:
           """Assemble cover letter content"""
   ```
   - Select relevant sections
   - Customize for job/company
   - Format content
   - Prepare for PDF generation

5. **DataService**
   ```python
   class DataService:
       def save_profile(profile: Profile) -> Profile:
           """Save profile with validation"""
       
       def get_all_jobs() -> List[Job]:
           """Retrieve all jobs for user"""
   ```
   - Centralize CRUD operations
   - Add business logic validation
   - Handle transactions
   - Manage relationships

### Layer 3: Models (Data Access)

**Technology:** SQLAlchemy ORM  
**Location:** `adaptive_resume/models/`  
**Purpose:** Data structure and database access

```
adaptive_resume/models/
├── __init__.py
├── base.py                 # SQLAlchemy base and session
├── profile.py              # User profile model
├── job.py                  # Job history model
├── bullet_point.py         # Achievement/responsibility model
├── skill.py                # Skills model
├── education.py            # Education model
├── certification.py        # Certification model
├── tag.py                  # Tag model for categorization
├── job_application.py      # Application tracking model
├── generated_resume.py     # Resume history model
├── generated_cover_letter.py # Cover letter history model
└── templates.py            # Resume/cover letter templates
```

**Responsibilities:**
- Define data structure
- Map to database tables
- Define relationships
- Provide query methods
- Handle database constraints

**Does NOT:**
- Contain business logic
- Know about GUI
- Perform complex calculations
- Generate documents

**Key Models:**

1. **Profile**
   - User's core information
   - Contact details
   - Professional summary
   - Has many: Jobs, Skills, Education, Certifications

2. **Job**
   - Work history entry
   - Company, title, dates
   - Has many: BulletPoints
   - Belongs to: Profile

3. **BulletPoint**
   - Individual achievement/responsibility
   - Metrics and impact
   - Has many: Tags (many-to-many)
   - Belongs to: Job

4. **Tag**
   - Categorizes bullet points
   - Enables smart filtering
   - Examples: technical, leadership, financial

5. **JobApplication**
   - Tracks applications
   - Links to generated documents
   - Status and notes

### Layer 4: Persistence (Database)

**Technology:** SQLite (v3)  
**Location:** User's local filesystem  
**Purpose:** Data storage

**Database File:**
- Default: `~/.adaptive_resume/resume_data.db`
- User configurable location
- Single file for portability

**Migration Management:**
- Alembic for version control
- Schema changes tracked
- Rollback capability

## Component Interactions

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Main Window  │  │   Dialogs    │  │   Widgets    │     │
│  │              │  │              │  │              │     │
│  │ - Navigation │  │ - Editors    │  │ - Selectors  │     │
│  │ - Menu/Tool  │  │ - Forms      │  │ - Displays   │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer (Business Logic)            │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Matching   │  │   Resume     │  │ Cover Letter │      │
│  │  Service    │  │   Builder    │  │   Builder    │      │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                  │               │
│  ┌──────┴──────┐  ┌──────┴───────┐  ┌──────┴───────┐      │
│  │    PDF      │  │     Data     │  │    Export    │      │
│  │  Generator  │  │   Service    │  │   Service    │      │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                  │               │
└─────────┼─────────────────┼──────────────────┼───────────────┘
          │                 │                  │
          ▼                 ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                 Data Access Layer (Models)                   │
│                                                              │
│  ┌─────────┐  ┌──────┐  ┌────────────┐  ┌────────┐        │
│  │ Profile │  │ Job  │  │ BulletPoint│  │  Tag   │        │
│  └────┬────┘  └───┬──┘  └──────┬─────┘  └───┬────┘        │
│       │           │            │             │              │
│  ┌────┴────┐  ┌───┴──────┐  ┌─┴──────────┐ │              │
│  │  Skill  │  │Education │  │Certification│ │              │
│  └─────────┘  └──────────┘  └─────────────┘ │              │
│                                              │              │
│  ┌──────────────┐  ┌────────────────┐  ┌────┴──────────┐  │
│  │    Job       │  │   Generated    │  │   Generated   │  │
│  │ Application  │  │    Resume      │  │ Cover Letter  │  │
│  └──────┬───────┘  └────────┬───────┘  └───────┬───────┘  │
│         │                   │                   │           │
└─────────┼───────────────────┼───────────────────┼───────────┘
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                   Persistence Layer                          │
│                                                              │
│              SQLite Database (resume_data.db)                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Interaction Patterns

#### Pattern 1: Creating a New Job Entry

```
1. User clicks "Add Job" in GUI
   │
   ▼
2. GUI opens JobDialog
   │
   ▼
3. User fills form and clicks "Save"
   │
   ▼
4. JobDialog validates input format
   │
   ▼
5. JobDialog calls DataService.save_job()
   │
   ▼
6. DataService validates business rules
   │
   ▼
7. DataService creates/updates Job model
   │
   ▼
8. Job model saves to database via SQLAlchemy
   │
   ▼
9. DataService returns success/failure
   │
   ▼
10. JobDialog shows feedback to user
    │
    ▼
11. JobDialog closes and MainWindow refreshes
```

#### Pattern 2: Generating a Resume

```
1. User pastes job description in GUI
   │
   ▼
2. GUI calls MatchingService.match_bullets_to_job()
   │
   ▼
3. MatchingService queries BulletPoint models
   │
   ▼
4. MatchingService scores and ranks bullets
   │
   ▼
5. GUI displays ranked bullets in BulletSelector
   │
   ▼
6. User selects/reorders bullets
   │
   ▼
7. User clicks "Generate Resume"
   │
   ▼
8. GUI calls ResumeBuilder.build_resume()
   │
   ▼
9. ResumeBuilder assembles content from models
   │
   ▼
10. ResumeBuilder calls PDFGenerator.generate_resume_pdf()
    │
    ▼
11. PDFGenerator creates PDF with ReportLab
    │
    ▼
12. PDFGenerator returns file path
    │
    ▼
13. GUI shows preview and save options
    │
    ▼
14. DataService saves GeneratedResume record
    │
    ▼
15. GUI updates application tracking
```

#### Pattern 3: Loading Application History

```
1. User opens "Applications" view
   │
   ▼
2. GUI calls DataService.get_all_applications()
   │
   ▼
3. DataService queries JobApplication models
   │
   ▼
4. SQLAlchemy loads applications with relationships
   │
   ▼
5. DataService returns application list
   │
   ▼
6. GUI displays applications in table/list
   │
   ▼
7. User clicks on an application
   │
   ▼
8. GUI loads related GeneratedResume
   │
   ▼
9. GUI displays resume details and opens PDF
```

## Data Flow Architecture

### Data Flow Diagram

```
┌──────────────┐
│     User     │
└──────┬───────┘
       │ Input
       ▼
┌──────────────────────────────────────────┐
│          GUI Layer                       │
│  - Collect input                         │
│  - Format validation                     │
│  - Display results                       │
└──────┬───────────────────────────────────┘
       │ Validated data / Service calls
       ▼
┌──────────────────────────────────────────┐
│        Service Layer                     │
│  - Business logic validation             │
│  - Process/transform data                │
│  - Orchestrate operations                │
│  - Apply algorithms (matching, scoring)  │
└──────┬───────────────────────────────────┘
       │ Model operations (CRUD)
       ▼
┌──────────────────────────────────────────┐
│        Data Access Layer                 │
│  - Query construction                    │
│  - Relationship management               │
│  - Transaction handling                  │
└──────┬───────────────────────────────────┘
       │ SQL queries (via ORM)
       ▼
┌──────────────────────────────────────────┐
│        Database (SQLite)                 │
│  - Persist data                          │
│  - Enforce constraints                   │
│  - Manage transactions                   │
└──────────────────────────────────────────┘
```

### Data Transformation Pipeline

**User Input → Database:**
```
Raw Input (GUI)
    → Sanitize/Format (GUI validators)
    → Business Validation (Service layer)
    → Model Instance (SQLAlchemy)
    → SQL Statement (ORM)
    → Database Record
```

**Database → Display:**
```
Database Query (SQL)
    → Model Objects (SQLAlchemy)
    → Business Processing (Service layer)
    → Display Format (GUI formatters)
    → Visual Presentation (PyQt6)
```

**Job Description → Resume:**
```
Job Description Text (GUI)
    → Parse/Extract Keywords (MatchingService)
    → Score BulletPoints (MatchingService)
    → Rank Results (MatchingService)
    → User Selection (GUI)
    → Assemble Content (ResumeBuilder)
    → Generate Layout (PDFGenerator)
    → PDF File (ReportLab)
```

## Design Patterns Used

### 1. Model-View-Controller (MVC) Variant

**Model:** SQLAlchemy models (data structure)  
**View:** PyQt6 GUI components (presentation)  
**Controller:** Service layer (business logic)

**Why:** Separates concerns, enables independent testing and modification

### 2. Repository Pattern

**Implementation:** DataService acts as repository  
**Purpose:** Abstract database operations from business logic

```python
class DataService:
    def get_all_jobs(self) -> List[Job]:
        """Repository method for jobs"""
        return session.query(Job).all()
```

**Benefits:**
- Business logic doesn't know about database
- Easy to swap data sources
- Centralized query logic

### 3. Builder Pattern

**Implementation:** ResumeBuilder, CoverLetterBuilder  
**Purpose:** Construct complex objects step by step

```python
resume = (ResumeBuilder()
    .set_profile(profile)
    .add_bullets(selected_bullets)
    .add_skills(top_skills)
    .apply_template(template)
    .build())
```

**Benefits:**
- Flexible construction process
- Reusable building steps
- Clear, readable code

### 4. Strategy Pattern

**Implementation:** Matching algorithms  
**Purpose:** Interchangeable matching strategies

```python
class TFIDFMatcher(MatcherStrategy):
    def match(self, job_desc, bullets):
        # TF-IDF implementation
        
class SpaCyMatcher(MatcherStrategy):
    def match(self, job_desc, bullets):
        # spaCy implementation
```

**Benefits:**
- Easy to add new matching algorithms
- Can switch strategies at runtime
- Each algorithm independently testable

### 5. Template Method Pattern

**Implementation:** PDF generation  
**Purpose:** Define skeleton of algorithm, subclasses fill in details

```python
class PDFTemplate:
    def generate(self, data):
        self.add_header(data)
        self.add_content(data)  # Subclass implements
        self.add_footer(data)
```

**Benefits:**
- Consistent PDF structure
- Easy to create new templates
- Reuse common operations

### 6. Observer Pattern

**Implementation:** PyQt6 Signals/Slots  
**Purpose:** Notify interested parties of changes

```python
class JobDialog(QDialog):
    job_saved = pyqtSignal(Job)  # Signal
    
    def save_job(self):
        job = self.data_service.save_job(...)
        self.job_saved.emit(job)  # Notify observers
```

**Benefits:**
- Loose coupling between components
- Multiple listeners possible
- Event-driven architecture

## Error Handling Strategy

### Error Categories

1. **Validation Errors**
   - Invalid input format
   - Business rule violations
   - Handled at GUI and Service layers
   - User-friendly messages displayed

2. **Database Errors**
   - Connection failures
   - Constraint violations
   - Transaction failures
   - Logged and user notified

3. **File System Errors**
   - PDF generation failures
   - Permission issues
   - Disk space problems
   - Graceful degradation

4. **External Service Errors**
   - Future: API calls
   - Network failures
   - Timeout handling

### Error Flow

```
Error Occurs
    │
    ▼
Caught at appropriate layer
    │
    ▼
Logged with context
    │
    ▼
Wrapped in domain exception
    │
    ▼
Propagated to caller
    │
    ▼
GUI displays user-friendly message
    │
    ▼
User can retry or cancel
```

### Exception Hierarchy

```python
class AdaptiveResumeError(Exception):
    """Base exception"""
    pass

class ValidationError(AdaptiveResumeError):
    """Input validation failed"""
    pass

class DatabaseError(AdaptiveResumeError):
    """Database operation failed"""
    pass

class PDFGenerationError(AdaptiveResumeError):
    """PDF creation failed"""
    pass
```

## Performance Considerations

### Database Optimization

1. **Indexes**
   - Primary keys on all tables
   - Foreign key indexes
   - Frequently queried fields (job.title, bulletpoint.content)

2. **Query Optimization**
   - Use SQLAlchemy eager loading for relationships
   - Limit result sets when possible
   - Batch operations where applicable

3. **Connection Management**
   - Single session per operation
   - Proper session cleanup
   - Connection pooling (future)

### GUI Responsiveness

1. **Async Operations**
   - Long-running tasks don't block UI
   - Use QThread for PDF generation
   - Progress indicators for user feedback

2. **Lazy Loading**
   - Load data as needed
   - Pagination for large lists
   - Virtual scrolling for many items

3. **Caching**
   - Cache frequently accessed data
   - Invalidate on changes
   - Memory-conscious limits

### Matching Performance

1. **Algorithm Efficiency**
   - Start simple (TF-IDF)
   - Optimize based on profiling
   - Consider caching match results

2. **Bulk Processing**
   - Process all bullets at once
   - Avoid repeated parsing
   - Reuse NLP models

## Security Considerations

### Current (Desktop Application)

1. **Local Data Only**
   - No network transmission
   - User controls all data
   - No cloud storage

2. **File Permissions**
   - Appropriate file permissions on database
   - PDFs saved with user permissions
   - Configuration files protected

3. **Input Sanitization**
   - Validate all user input
   - Prevent SQL injection (ORM handles this)
   - Sanitize file paths

### Future (Web Application)

1. **Authentication**
   - User login required
   - Password hashing (bcrypt)
   - Session management

2. **Authorization**
   - Users only access their data
   - Role-based access control
   - API authentication

3. **Data Protection**
   - HTTPS only
   - Database encryption at rest
   - Secure password storage
   - GDPR compliance

## Testing Architecture

### Test Layers

```
┌─────────────────────────────────────────┐
│        End-to-End Tests                 │
│  - Full application workflows           │
│  - GUI integration                      │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│        Integration Tests                │
│  - Service + Model interactions         │
│  - Database operations                  │
│  - Multi-component workflows            │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│          Unit Tests                     │
│  - Individual functions                 │
│  - Class methods                        │
│  - Isolated components                  │
└─────────────────────────────────────────┘
```

### Test Structure

```
tests/
├── unit/
│   ├── test_models.py          # Model unit tests
│   ├── test_services.py        # Service unit tests
│   └── test_utils.py           # Utility unit tests
├── integration/
│   ├── test_data_service.py    # Service + DB tests
│   ├── test_resume_builder.py  # Builder integration
│   └── test_matching.py        # Matching integration
└── e2e/
    ├── test_job_workflow.py    # Create job end-to-end
    └── test_resume_generation.py # Resume gen end-to-end
```

### Testing Strategy

1. **Unit Tests (90%+ coverage for critical components)**
   - Test each function/method in isolation
   - Mock dependencies
   - Fast execution

2. **Integration Tests (Service + Model)**
   - Test component interactions
   - Use test database
   - Verify data flow

3. **GUI Tests (50%+ coverage)**
   - Test critical workflows
   - Use pytest-qt
   - Verify user interactions

4. **End-to-End Tests**
   - Test complete user scenarios
   - Verify entire stack
   - Slower, fewer tests

## Scalability & Future Growth

### Current Limitations (v1.0)

- Single user per database
- Desktop only
- Local processing only
- SQLite limitations (~1TB max, single writer)

### Growth Path

#### Phase 1: Multi-User Desktop (v2.0)
- Multiple profiles per database
- Profile switching
- Data isolation between users

#### Phase 2: Web Application (v3.0)
- Replace PyQt6 with Flask/FastAPI
- PostgreSQL database
- User authentication
- Cloud deployment
- Real-time collaboration

#### Phase 3: Advanced Features (v4.0+)
- AI-powered matching (ML models)
- Resume analysis and suggestions
- Integration with job boards
- Team features for career coaches
- Mobile applications

### Migration Strategy

**Desktop → Web:**

1. **Service Layer:** Unchanged (already abstracted)
2. **Models:** Minimal changes (SQLAlchemy handles DB swap)
3. **API:** Add REST endpoints calling services
4. **Frontend:** New web UI calling API
5. **Database:** Migrate SQLite → PostgreSQL

**Estimated effort:** 4-6 weeks with current architecture

## Configuration Management

### Application Configuration

```python
# config.py
class Config:
    DATABASE_PATH = "~/.adaptive_resume/resume_data.db"
    PDF_OUTPUT_DIR = "~/.adaptive_resume/resumes/"
    LOG_LEVEL = "INFO"
    LOG_FILE = "~/.adaptive_resume/app.log"
```

### User Preferences

```python
# User-configurable settings
- Default resume template
- PDF output directory
- Application theme
- Matching sensitivity
```

### Environment-Specific Config

```python
# Development
DEBUG = True
DATABASE_PATH = "./dev_resume_data.db"

# Production
DEBUG = False
DATABASE_PATH = "~/.adaptive_resume/resume_data.db"

# Testing
DATABASE_PATH = ":memory:"  # In-memory SQLite
```

## Logging & Monitoring

### Logging Strategy

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('~/.adaptive_resume/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

### What to Log

1. **Application Events**
   - Startup/shutdown
   - Configuration loading
   - Database initialization

2. **User Actions**
   - Job created/updated/deleted
   - Resume generated
   - PDF saved

3. **Errors**
   - All exceptions with stack traces
   - Validation failures
   - Database errors

4. **Performance**
   - Matching algorithm execution time
   - PDF generation time
   - Database query performance

## Deployment Architecture

### Development Environment

```
Developer Machine
├── Python 3.11+ installed
├── Project cloned from GitHub
├── Virtual environment created
├── Dependencies installed
└── SQLite database created locally
```

### Production Distribution

#### Windows
```
Executable Package (PyInstaller)
├── adaptive_resume.exe
├── Dependencies bundled
├── Database created on first run
└── User data in %APPDATA%\AdaptiveResume\
```

#### macOS
```
Application Bundle (.app)
├── Adaptive Resume.app
├── Dependencies bundled
├── Database created on first run
└── User data in ~/Library/Application Support/AdaptiveResume/
```

### Directory Structure (Installed)

```
~/.adaptive_resume/          (macOS/Linux)
%APPDATA%\AdaptiveResume\   (Windows)
├── resume_data.db          # SQLite database
├── resumes/                # Generated PDFs
│   ├── 2025-11-04_TechCorp_Senior_Dev.pdf
│   └── 2025-11-05_StartupCo_Lead.pdf
├── cover_letters/          # Generated cover letters
├── backups/                # Database backups
├── logs/
│   └── app.log            # Application logs
└── config.json            # User preferences
```

## Summary

The Adaptive Resume Generator uses a **layered architecture** with clear separation between:

1. **GUI (PyQt6)** - Presentation only
2. **Services** - Business logic and orchestration
3. **Models (SQLAlchemy)** - Data structure and access
4. **Database (SQLite)** - Persistence

This architecture enables:
- **Testability** - Each layer tested independently
- **Maintainability** - Clear responsibilities
- **Flexibility** - Easy to swap implementations
- **Scalability** - Ready for web migration

**Key Design Decisions:**
- Use proven design patterns (MVC, Repository, Builder, Strategy)
- Service layer is framework-agnostic (web-ready)
- Database abstraction via SQLAlchemy ORM
- Clear error handling at each layer
- Comprehensive testing strategy
- Future-proof for growth

---

**Next Steps:**
1. Review [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) for data model details
2. See [PROJECT_PLAN.md](PROJECT_PLAN.md) for implementation roadmap
3. Check [ADRs](decisions/) for architectural decision rationale
4. Start implementing models following this architecture

**Questions?** Refer to:
- **Implementation details:** [PROJECT_PLAN.md](PROJECT_PLAN.md)
- **Database specifics:** [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)
- **Setup instructions:** [SETUP.md](SETUP.md)
- **Decision rationale:** [docs/decisions/ADR-*.md](decisions/)
