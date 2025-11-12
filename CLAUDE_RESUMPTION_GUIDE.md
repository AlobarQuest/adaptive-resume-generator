# CLAUDE Resumption Guide

**Purpose:** This document provides everything a CLaude AI needs to resume work on the Adaptive Resume Generator project effectively.

**Last Updated:** November 12, 2025

---

## 🚀 Quick Start Prompt

Use this prompt to resume work on the project:

```
I need you to continue working on my Adaptive Resume Generator project at:
C:\Users\devon\Projects\adaptive-resume-generator\
Start by reading the CLAUDE_RESUMPTION_GUIDE.md

CRITICAL FILE HANDLING RULES:
1. ALWAYS use filesystem:write_file or create_file for files in C:\Users\devon\...
2. NEVER use bash_tool with Python or shell commands to write Windows files
3. After creating a file, verify it exists using filesystem:list_directory
4. If a tool says "success" but the file doesn't appear, try filesystem:write_file instead

PROJECT CONTEXT - Read these files first:
1. /docs/README.md
2. /docs/product/ai_session_guide.md
2. /docs/development/delivery_plan.md - Master implementation plan and roadmap
2. /docs/development/status_report.md - Current status, completed work, and next tasks
3. /docs/architecture/system_architecure.md - System architecture and design decisions

After reading, please:
1. Summarize the current project status
2. Identify the most recently completed work
3. Recommend the next task based on delivery_plan.md and status_report.md
4. Wait for my confirmation before proceeding

If you encounter any file access issues, stop and explain the problem clearly.
```

---


### ✅ CORRECT - Always Use These Tools

**Creating/Writing Files:**
```python
# Method 1: filesystem:write_file
filesystem:write_file(
    path="C:\\Users\\devon\\Projects\\adaptive-resume-generator\\src\\file.py",
    content="file contents here"
)

# Method 2: create_file
create_file(
    path="C:\\Users\\devon\\Projects\\adaptive-resume-generator\\src\\file.py",
    file_text="file contents here",
    description="Why creating this file"
)
```

**Reading Files:**
```python
# Method 1: filesystem:read_file
filesystem:read_file(
    path="C:\\Users\\devon\\Projects\\adaptive-resume-generator\\docs\\STATUS.md"
)

# Method 2: view (with line range)
view(
    path="C:\\Users\\devon\\Projects\\adaptive-resume-generator\\src\\file.py",
    view_range=[1, 50],
    description="Why viewing this"
)
```

**Modifying Files:**
```python
# Method 1: filesystem:edit_file (for line-based edits)
filesystem:edit_file(
    path="C:\\Users\\devon\\Projects\\adaptive-resume-generator\\file.py",
    edits=[
        {"oldText": "old line", "newText": "new line"}
    ]
)

# Method 2: str_replace (for string replacement)
str_replace(
    path="C:\\Users\\devon\\Projects\\adaptive-resume-generator\\file.py",
    old_str="exact text to replace",
    new_str="replacement text",
    description="Why making this change"
)
```

**Verifying Files:**
```python
# List directory contents
filesystem:list_directory(
    path="C:\\Users\\devon\\Projects\\adaptive-resume-generator\\src\\adaptive_resume\\gui\\dialogs"
)
```

### ❌ INCORRECT - Never Use These for Windows Files

**DO NOT use bash_tool for file operations on Windows paths:**
```bash
# ❌ WRONG - Don't do this!
bash_tool: python3 << 'EOF'
with open('C:\\path\\file.py', 'w') as f:
    f.write(content)
EOF

# ❌ WRONG - Don't do this!
bash_tool: cat > /path/to/file.py << 'EOF'
content here
EOF

# ❌ WRONG - Don't do this!
bash_tool: cp /tmp/file.py C:/path/file.py
```

**Why these fail:**
- bash_tool runs in a Linux container
- Container filesystem ≠ Windows filesystem
- Commands succeed in container but file doesn't appear in Windows
- `filesystem:*` tools have direct access to Windows paths

---

## 🔍 File Writing Issues - Troubleshooting

### Problem: "File created successfully" but doesn't exist

**Symptoms:**
```
Tool says: "Successfully wrote X bytes to C:\path\file.py"
But: filesystem:list_directory doesn't show the file
```

**Cause:** Used bash_tool instead of filesystem tools

**Solution:**
1. Use `filesystem:write_file` or `create_file`
2. Verify with `filesystem:list_directory`
3. If still fails, check path format (backslashes, correct directory)

### Problem: "Access denied" or "path outside allowed directories"

**Symptoms:**
```
Error: Access denied - path outside allowed directories
```

**Cause:** Path not in allowed directories

**Solution:**
1. Check allowed directories: `filesystem:list_allowed_directories`
2. Allowed paths include:
   - `C:\Users\devon\Documents`
   - `C:\Users\devon\Projects` ✅ (our project is here)
   - `C:\Users\devon\Downloads`
   - `C:\Users\devon\Dropbox (Personal)`
   - `C:\local_git`
3. Ensure path starts with an allowed directory

### Problem: Python import cache issues

**Symptoms:**
```
ModuleNotFoundError: No module named 'adaptive_resume.gui.dialogs.job_dialog'
```
But the file exists.

**Cause:** Python's `__pycache__` has stale imports

**Solution:**
Tell user to clear cache:
```powershell
# In PowerShell
cd C:\Users\devon\Projects\adaptive-resume-generator
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
```

Or just have them restart their terminal/Python environment.

---

## 🏗️ Project Context

### Technology Stack

- **Language:** Python 3.13.3
- **GUI Framework:** PyQt6
- **Database:** SQLite with SQLAlchemy ORM
- **Migrations:** Alembic
- **Testing:** pytest (81% coverage)
- **PDF Generation:** ReportLab (planned)
- **NLP/Matching:** spaCy (planned)

### Development Workflow

**Running the Application:**
```powershell
python run_gui.py
```

**Running Tests:**
```powershell
pytest
pytest --cov=adaptive_resume --cov-report=html
```

**Committing Changes:**
```powershell
.\Commit-All.ps1          # Full workflow with prompts
.\Commit-All.ps1 -NoTest  # Skip tests
.\Commit-All.ps1 -NoPush  # Don't push to remote
```

### Git Workflow

- **Branches:** `main` (production), `develop` (current work)
- **Feature branches:** `feature/*`
- **Commit format:** Conventional commits (feat/fix/docs/etc.)
- **Process:** Simplified Git Flow

### Code Style

- **Formatting:** Black (88 char line length)
- **Type hints:** Required for function signatures
- **Docstrings:** Google style for all public functions
- **Imports:** Absolute imports preferred

---