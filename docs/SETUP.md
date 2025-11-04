# Development Environment Setup

## Prerequisites

Before setting up the Adaptive Resume Generator, ensure you have:

- **Python 3.11 or higher** (3.13.3 confirmed working)
- **Git** (2.49.0 or higher)
- **Windows 10/11** or **macOS 10.15+**
- **4GB RAM minimum** (8GB recommended)
- **500MB free disk space**

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/AlobarQuest/adaptive-resume-generator.git
cd adaptive-resume-generator
```

### 2. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your command prompt when activated.

### 3. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (for testing and code quality)
pip install -r requirements-dev.txt

# Upgrade pip if needed
python -m pip install --upgrade pip
```

### 4. Initialize Database

```bash
# This will create the initial database schema
python -m adaptive_resume.database.init_db
```

Expected output:
```
Creating database schema...
Database initialized successfully at: data/adaptive_resume.db
```

### 5. Verify Installation

Run the test suite to ensure everything is working:

```bash
pytest
```

All tests should pass. If you see errors, check the troubleshooting section below.

### 6. Run Application

```bash
python -m adaptive_resume.main
```

The GUI should launch. If this is your first time, you'll see an empty application ready for you to add your profile.

## Development Workflow

### Daily Development

1. **Activate virtual environment:**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Mac/Linux
   source venv/bin/activate
   ```

2. **Pull latest changes:**
   ```bash
   git checkout develop
   git pull
   ```

3. **Create feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make changes and test:**
   ```bash
   # Run tests frequently
   pytest
   
   # Check code style
   black src/
   flake8 src/
   ```

5. **Commit changes:**
   ```bash
   git add .
   git commit -m "Clear description of changes"
   ```

6. **Merge to develop:**
   ```bash
   git checkout develop
   git merge feature/your-feature-name
   git push
   ```

### Code Quality Tools

**Black (Code Formatter):**
```bash
# Format all Python files
black src/ tests/

# Check what would be formatted without making changes
black --check src/ tests/
```

**Flake8 (Linter):**
```bash
# Check code style
flake8 src/ tests/

# With specific configuration
flake8 --max-line-length=88 --extend-ignore=E203 src/
```

**MyPy (Type Checker):**
```bash
# Check type hints
mypy src/
```

**Run all quality checks:**
```bash
black src/ tests/ && flake8 src/ tests/ && mypy src/
```

### Testing

**Run all tests:**
```bash
pytest
```

**Run with coverage:**
```bash
pytest --cov=adaptive_resume --cov-report=html
# Open htmlcov/index.html to view coverage report
```

**Run specific test file:**
```bash
pytest tests/test_models.py
```

**Run tests matching a pattern:**
```bash
pytest -k "bullet_point"
```

**Run tests with verbose output:**
```bash
pytest -v
```

**Run tests and stop at first failure:**
```bash
pytest -x
```

### Database Management

**Create migration after model changes:**
```bash
alembic revision --autogenerate -m "Description of changes"
```

**Apply migrations:**
```bash
alembic upgrade head
```

**Rollback migration:**
```bash
alembic downgrade -1
```

**View migration history:**
```bash
alembic history
```

**Reset database (WARNING: destroys all data):**
```bash
# Delete existing database
rm data/adaptive_resume.db  # Mac/Linux
del data\adaptive_resume.db  # Windows

# Recreate from scratch
python -m adaptive_resume.database.init_db
```

## Project Structure

```
adaptive-resume-generator/
├── src/adaptive_resume/        # Main application code
│   ├── models/                 # Database models
│   ├── services/               # Business logic
│   ├── gui/                    # PyQt6 interface
│   ├── database/               # Database connection and migrations
│   └── utils/                  # Utilities and helpers
├── tests/                      # Test files
├── docs/                       # Documentation
├── data/                       # Local database (gitignored)
├── output/                     # Generated PDFs (gitignored)
└── venv/                       # Virtual environment (gitignored)
```

## IDE Setup

### Visual Studio Code

**Recommended Extensions:**
- Python (Microsoft)
- Pylance
- Python Test Explorer
- GitLens
- Better Comments

**Settings (`.vscode/settings.json`):**
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/Scripts/python.exe",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "editor.formatOnSave": true,
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true
    }
}
```

### PyCharm

1. **Open Project:** File → Open → Select `adaptive-resume-generator` folder
2. **Configure Interpreter:** File → Settings → Project → Python Interpreter → Add → Existing environment → Select `venv/Scripts/python.exe`
3. **Enable pytest:** Settings → Tools → Python Integrated Tools → Testing → Default test runner: pytest
4. **Configure Black:** Settings → Tools → Black → Check "On save"

## Troubleshooting

### Virtual Environment Issues

**Problem:** `venv\Scripts\activate` not found
**Solution:** Ensure you created the venv in the project root:
```bash
cd C:\Users\devon\Projects\adaptive-resume-generator
python -m venv venv
```

**Problem:** Permission denied when activating
**Solution (Windows PowerShell):**
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Dependency Installation Issues

**Problem:** pip install fails with SSL errors
**Solution:**
```bash
python -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

**Problem:** PyQt6 installation fails
**Solution:** Try installing Visual C++ Redistributable from Microsoft, then retry

### Database Issues

**Problem:** Database locked error
**Solution:** Close any other instances of the application, then restart

**Problem:** Migration fails
**Solution:** Check `alembic/versions/` for conflicting migrations. May need to reset database.

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'adaptive_resume'`
**Solution:** Ensure you're running from project root and virtual environment is activated:
```bash
cd C:\Users\devon\Projects\adaptive-resume-generator
venv\Scripts\activate
python -m adaptive_resume.main
```

### PyQt6 GUI Issues

**Problem:** Application window doesn't appear
**Solution (Windows):** Check display scaling settings, try running as administrator

**Problem:** Blank/white window
**Solution:** Update graphics drivers

## Environment Variables

Create a `.env` file in project root for configuration (optional):

```bash
# Database path (default: data/adaptive_resume.db)
DATABASE_URL=sqlite:///data/adaptive_resume.db

# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Output directory for PDFs
OUTPUT_DIR=output
```

## Performance Tips

- **First run may be slow** while spaCy downloads language models
- **Database grows with usage** - monitor `data/` directory size
- **PDF generation** is CPU-intensive - expect 1-2 seconds per resume
- **Keep bullet points under 10,000 total** for optimal matching performance

## Getting Help

- **Documentation:** Check `docs/` folder
- **Issues:** Create issue on GitHub
- **AI Sessions:** Point AI to `docs/PROJECT_PLAN.md` for full context

## Next Steps

After setup:
1. Read [USER_GUIDE.md](USER_GUIDE.md) to learn application features
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) to understand system design
3. Check [STATUS.md](STATUS.md) to see current development progress
4. Start contributing by picking an issue from GitHub

## Updating Dependencies

Periodically update dependencies:

```bash
# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade package-name

# Update requirements files
pip freeze > requirements.txt
```

## Uninstallation

To remove the development environment:

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf venv  # Mac/Linux
rmdir /s venv  # Windows

# Remove database and outputs (optional)
rm -rf data/ output/  # Mac/Linux
rmdir /s data output  # Windows
```
