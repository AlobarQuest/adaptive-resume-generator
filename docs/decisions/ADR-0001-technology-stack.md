# ADR-0001: Technology Stack Selection

**Status:** Accepted  
**Date:** 2025-11-04  
**Deciders:** AlobarQuest

## Context

We need to build a desktop application for creating tailored resumes with the following requirements:
- Cross-platform (Windows and macOS)
- Local data storage (privacy-focused)
- Professional PDF generation
- Intelligent content matching
- Future web migration capability

The technology choices will significantly impact development speed, maintainability, user experience, and our ability to migrate to a web platform later.

## Decision

We will use the following technology stack:

### Core Technologies
- **Python 3.11+** as the primary programming language
- **PyQt6** for desktop GUI framework
- **SQLite** for initial database with **SQLAlchemy** ORM
- **ReportLab** for PDF generation
- **spaCy** for NLP and text matching
- **Alembic** for database migrations

### Development Tools
- **pytest** for testing framework
- **black** for code formatting
- **flake8** for linting
- **mypy** for type checking

## Rationale

### Python 3.11+
**Pros:**
- Excellent cross-platform support
- Rich ecosystem for desktop, database, PDF, and NLP
- Easy to learn and maintain
- Strong community support
- Type hints improve code quality
- Will work seamlessly for future web backend

**Cons:**
- Slower than compiled languages (acceptable for this use case)
- GIL limitations for threading (not relevant for our single-user app)

**Alternatives Considered:**
- **Java:** More verbose, heavier runtime
- **JavaScript/Electron:** Large bundle size, slower startup
- **C#/.NET:** Windows-focused, macOS support weaker

### PyQt6
**Pros:**
- Native-looking UI on all platforms
- Mature and stable
- Comprehensive widget library
- Good documentation
- Professional appearance
- Active development and support

**Cons:**
- GPL/Commercial dual licensing (using GPL for open source)
- Steeper learning curve than simpler frameworks
- Larger application size

**Alternatives Considered:**
- **Tkinter:** Too basic, dated appearance
- **Kivy:** Mobile-focused, less professional for desktop
- **wxPython:** Less active development

### SQLite + SQLAlchemy
**Pros:**
- Zero configuration (file-based)
- Perfect for single-user desktop apps
- No server needed
- Built into Python
- SQLAlchemy provides database portability
- Easy migration path to PostgreSQL for web version

**Cons:**
- Not suitable for concurrent writes (not an issue for desktop)
- Limited to local storage

**Alternatives Considered:**
- **PostgreSQL directly:** Overkill for desktop, requires server
- **NoSQL (MongoDB, etc.):** Relational data fits our domain better
- **Plain SQL:** No ORM means harder migration later

### ReportLab
**Pros:**
- Industry standard for PDF generation in Python
- Precise control over layout
- Can create ATS-friendly PDFs
- Extensive documentation
- Production-proven

**Cons:**
- Lower-level API (more code required)
- Learning curve for complex layouts

**Alternatives Considered:**
- **WeasyPrint:** HTML to PDF, less control over exact positioning
- **FPDF:** Simpler but less powerful
- **pdfkit:** Requires external wkhtmltopdf dependency

### spaCy
**Pros:**
- Modern, fast NLP library
- Pre-trained models available
- Good for keyword extraction and text similarity
- Production-ready
- Can scale from simple to sophisticated matching

**Cons:**
- Larger download size (models)
- More complex than simple keyword matching

**Alternatives Considered:**
- **NLTK:** Older, more academic-focused
- **Simple keyword matching:** Too basic for quality results
- **Transformer models (BERT, etc.):** Overkill, too slow for desktop

## Consequences

### Positive
- **Rapid Development:** Python's ecosystem enables fast prototyping
- **Cross-Platform:** Write once, run on Windows and Mac
- **Future-Proof:** SQLAlchemy and service layer enable web migration
- **Professional Output:** ReportLab produces high-quality PDFs
- **Intelligent Matching:** spaCy enables sophisticated text analysis
- **Maintainable:** Standard tools with good documentation
- **Type Safety:** Type hints and mypy catch errors early

### Negative
- **Application Size:** PyQt6 and spaCy models add ~200MB
- **Startup Time:** Initial load may be 2-3 seconds
- **Learning Curve:** Team must learn PyQt6 and ReportLab
- **GPL License:** PyQt6 GPL requires our code to be GPL or commercial license

### Risks and Mitigations

**Risk:** PyQt6 GPL license limits commercial options  
**Mitigation:** Project is MIT licensed for code, users can choose commercial PyQt6 if needed

**Risk:** spaCy models might be too slow on older machines  
**Mitigation:** Start with simple matching, upgrade sophistication based on performance

**Risk:** ReportLab learning curve delays PDF implementation  
**Mitigation:** Allocate full week (Week 5) for PDF generation milestone

## Migration Path

### To Web Platform (Future)
1. Keep service layer as-is (already GUI-independent)
2. Replace PyQt6 with Flask/FastAPI + React
3. Migrate SQLite to PostgreSQL (SQLAlchemy makes this simple)
4. Add authentication/authorization layer
5. Deploy to cloud hosting

**Estimated Effort:** 4-6 weeks

### If Technology Needs Change
- **GUI Framework:** Service layer is independent, can swap PyQt6
- **Database:** SQLAlchemy ORM abstracts database specifics
- **PDF Library:** PDF generation isolated in service, can replace ReportLab
- **NLP:** Matching algorithm is pluggable, can upgrade spaCy approach

## Review

This decision should be reviewed:
- After completing Week 3 (GUI implementation)
- After completing Week 4 (Matching engine)
- After completing Week 5 (PDF generation)
- Before starting web migration

## References

- Python Documentation: https://docs.python.org/3/
- PyQt6 Documentation: https://www.riverbankcomputing.com/static/Docs/PyQt6/
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
- ReportLab Documentation: https://www.reportlab.com/docs/reportlab-userguide.pdf
- spaCy Documentation: https://spacy.io/usage

## Notes

User (AlobarQuest) has confirmed:
- 25 years IT experience
- Comfortable with modern programming languages
- Prefers desktop GUI initially for cost control
- Plans eventual web migration
- Windows development machine (Python 3.13.3)

Stack chosen to balance user's requirements with best practices for maintainable, future-proof architecture.
