# Adaptive Resume Generator

A desktop application for creating tailored resumes and cover letters with intelligent content matching.

## Overview

Adaptive Resume Generator helps you create customized resumes by:
- Storing your complete work history and achievements
- Matching your experience to job descriptions
- Generating ATS-friendly PDF resumes
- Tracking job applications
- Creating tailored cover letters

## Features

- **Smart Content Selection**: Paste a job description and get relevant bullet point suggestions
- **Multiple Resume Versions**: Save different versions for different applications
- **Application Tracking**: Keep track of where you've applied and with which resume
- **Combination Format**: Chronological and functional resume layout
- **Cover Letter Generator**: Reusable sections for quick cover letter creation
- **Local Data Storage**: Your data stays on your machine

## Technology Stack

- **Language**: Python 3.11+
- **GUI**: PyQt6
- **Database**: SQLite (with PostgreSQL migration path)
- **PDF Generation**: ReportLab
- **ORM**: SQLAlchemy

## Installation

### Prerequisites
- Python 3.11 or higher
- Git

### Setup

1. Clone the repository:
```bash
git clone https://github.com/AlobarQuest/adaptive-resume-generator.git
cd adaptive-resume-generator
```

2. Create and activate virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. Initialize the database:
```bash
python -m adaptive_resume.database.init_db
```

5. Run the application:
```bash
python -m adaptive_resume.main
```

## Development

See [SETUP.md](docs/SETUP.md) for detailed development environment setup.

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for system design documentation.

## Documentation

- [Project Plan](docs/PROJECT_PLAN.md) - Complete implementation roadmap
- [Architecture](docs/ARCHITECTURE.md) - System design and components
- [Database Schema](docs/DATABASE_SCHEMA.md) - Data model documentation
- [Architecture Decision Records](docs/decisions/) - Key design decisions
- [AI Session Guide](docs/AI_SESSION_GUIDE.md) - Guide for AI-assisted development

## Project Status

Currently in initial development. See [STATUS.md](docs/STATUS.md) for current progress.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Attribution

Created by AlobarQuest (https://github.com/AlobarQuest)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
