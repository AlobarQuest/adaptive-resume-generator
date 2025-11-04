# ADR-0003: GUI Framework Selection

**Status:** Accepted  
**Date:** 2025-11-04  
**Deciders:** AlobarQuest

## Context

The Adaptive Resume Generator needs a desktop GUI that:
- Works on both Windows and macOS
- Provides a professional, modern appearance
- Supports complex forms and data entry
- Can display previews of generated PDFs
- Offers good user experience for data management tasks
- Allows reasonable development speed

The user has specified:
- Desktop application (not web-based initially)
- Cost-effective development approach
- Future migration to web-based version planned

## Decision

We will use **PyQt6** as the GUI framework for the desktop application.

## Alternatives Considered

### 1. Tkinter
**Pros:**
- Built into Python (no extra dependencies)
- Simple to learn
- Lightweight
- Cross-platform

**Cons:**
- Dated, 1990s appearance
- Limited widgets out of the box
- Not professional-looking by modern standards
- Difficult to create complex layouts
- Poor high-DPI support

**Verdict:** Too basic for a professional application

### 2. wxPython
**Pros:**
- Native widgets on each platform
- Mature framework
- Good documentation

**Cons:**
- Less active development recently
- Smaller community than PyQt
- More verbose code
- Fewer modern UI patterns

**Verdict:** Good option, but PyQt is more actively developed

### 3. Kivy
**Pros:**
- Modern, OpenGL-based rendering
- Great for touch interfaces
- Cross-platform (includes mobile)

**Cons:**
- Mobile-first design philosophy
- Non-native look and feel
- Overkill for desktop-only app
- Steeper learning curve for desktop patterns

**Verdict:** Better for mobile apps, not ideal for desktop productivity tools

### 4. Electron (with Python backend)
**Pros:**
- Web technologies (HTML/CSS/JavaScript)
- Modern UI capabilities
- Large ecosystem

**Cons:**
- Huge bundle size (100+ MB)
- High memory usage
- Slower startup
- Complexity of Python-JavaScript bridge
- Doesn't help with future web migration (different stack)

**Verdict:** Too heavy, doesn't align with migration strategy

### 5. PyQt6 (Selected)
**Pros:**
- Professional, native-looking UI
- Comprehensive widget library
- Excellent documentation
- Large community and ecosystem
- Cross-platform consistency
- Good high-DPI support
- Mature and stable
- Designer tool for visual layout (Qt Designer)
- Model-View architecture for data display

**Cons:**
- GPL or commercial dual licensing
- Larger learning curve
- Bigger application size than Tkinter
- Need to learn Qt concepts

**Verdict:** Best balance of features, appearance, and maintainability

### 6. PySide6 (Qt for Python - official)
**Pros:**
- Same as PyQt6
- LGPL license (more permissive)
- Official Qt binding

**Cons:**
- API almost identical to PyQt6
- Community slightly smaller than PyQt

**Note:** PySide6 and PyQt6 are nearly interchangeable. We chose PyQt6 due to:
- Slightly better community resources
- Longer history and stability
- MIT license on our code + GPL on PyQt6 is acceptable for open-source project

## Rationale

### Why PyQt6 is the Best Choice

**Professional Appearance:**
- Native-looking widgets on Windows and Mac
- Modern Material-style components available
- Customizable styling with QSS (Qt Style Sheets)
- Professional applications like Dropbox, Maya, use Qt

**Rich Widget Library:**
- QTableWidget, QTreeWidget for data display
- QDialog for modal forms
- QTextEdit, QLineEdit for input
- QComboBox, QDateEdit for specialized input
- Custom widgets easy to create

**Layout Management:**
- Flexible layout system (QVBoxLayout, QHBoxLayout, QGridLayout)
- Automatic sizing and scaling
- Responsive design support

**Data Display:**
- Model-View architecture for lists and tables
- Efficient for large datasets
- Built-in sorting and filtering

**Development Tools:**
- Qt Designer for visual UI design
- Qt Creator for debugging
- Extensive documentation
- Many tutorials and examples

**Cross-Platform:**
- Write once, works on Windows and macOS
- Consistent behavior across platforms
- Native file dialogs and system integration

**Future-Proofing:**
- Skills transfer to web development (similar concepts)
- Well-maintained and actively developed
- Large corporate backing (The Qt Company)

## Licensing Considerations

### PyQt6 License Options

1. **GPL v3:** Free, requires our application to be GPL
2. **Commercial:** ~$550/developer, allows proprietary code

### Our Choice: GPL v3

**Reasoning:**
- Project is open-source (MIT license on our code)
- No plans to sell proprietary version
- Users can optionally purchase commercial PyQt6 if they want proprietary use
- MIT code + GPL library = overall GPL application (acceptable)

**Attribution:**
We'll clearly document that:
- Our code is MIT licensed
- PyQt6 dependency is GPL licensed
- Combined application must comply with GPL

**Alternative Path:**
If commercial use becomes important, we can:
- Purchase PyQt6 commercial license
- Or switch to PySide6 (LGPL, more permissive)

## Implementation Approach

### Application Structure

```python
# Main window architecture
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        
    def setup_ui(self):
        # Central widget with navigation
        # Stacked widget for different views
        pass
```

### Common Patterns

**Dialog Forms:**
```python
class JobEditorDialog(QDialog):
    """Modal dialog for editing job information"""
    
    def __init__(self, job=None, parent=None):
        super().__init__(parent)
        self.job = job
        self.setup_form()
        
    def setup_form(self):
        layout = QFormLayout()
        self.company_edit = QLineEdit()
        layout.addRow("Company:", self.company_edit)
        # ...
        self.setLayout(layout)
```

**Data Display:**
```python
class JobListWidget(QWidget):
    """Display list of jobs with filtering"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.table = QTableWidget()
        self.setup_table()
        
    def setup_table(self):
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Company", "Title", "Start Date", "End Date"
        ])
```

### Styling

Use Qt Style Sheets (QSS) for custom styling:
```python
# Modern, professional color scheme
stylesheet = """
    QMainWindow {
        background-color: #f5f5f5;
    }
    QPushButton {
        background-color: #0078d4;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #106ebe;
    }
"""
app.setStyleSheet(stylesheet)
```

## Consequences

### Positive

**For Users:**
- Professional, native-looking application
- Familiar UI patterns (standard dialogs, menus)
- Responsive and fast interface
- Good keyboard navigation and shortcuts
- Accessible (screen reader support)

**For Development:**
- Rich widget library reduces custom coding
- Qt Designer speeds up UI development
- Good documentation and examples
- Large community for troubleshooting
- Proven in production applications

**For Maintenance:**
- Clear separation of UI and business logic
- Well-structured model-view patterns
- Easy to refactor and test
- Type hints work well with PyQt6

### Negative

**Application Size:**
- PyQt6 adds ~50-70 MB to application
- Distribution packages will be larger
- Initial download is bigger

**Learning Curve:**
- Qt concepts (signals/slots, layouts) take time to learn
- More complex than simple frameworks
- Need to understand Qt object lifecycle

**Licensing:**
- GPL requirement for free version
- Must clearly communicate licensing
- Commercial license needed for proprietary use

**Platform Differences:**
- Some minor behavioral differences between platforms
- Need to test on both Windows and Mac
- File path handling differences

### Risks and Mitigations

**Risk:** GPL licensing causes issues for users wanting proprietary use  
**Mitigation:** Clear documentation, option to use PySide6 or commercial PyQt6

**Risk:** Learning curve delays development  
**Mitigation:** Start with simple layouts in Week 3, gradually increase complexity

**Risk:** Application size too large  
**Mitigation:** Acceptable tradeoff for professional UI, optimize with PyInstaller

**Risk:** Platform-specific bugs  
**Mitigation:** Test on both platforms regularly, use CI/CD

## Migration Path

### To Web Application (Future)

**What Changes:**
- Replace PyQt6 GUI with web framework (Flask + React)
- HTML/CSS instead of Qt widgets
- JavaScript event handlers instead of Qt signals/slots

**What Stays the Same:**
- All business logic in service layer
- Database models unchanged
- PDF generation service unchanged
- Matching algorithm unchanged

**Skills Transfer:**
- Layout concepts similar (flexbox ≈ QHBoxLayout)
- Form handling patterns analogous
- Event-driven programming same concept
- Model-view patterns applicable

**Estimated Effort:** 4-6 weeks to rebuild GUI in web tech

### If PyQt6 Becomes Problematic

**Option 1: Switch to PySide6**
- Nearly identical API
- Change imports: `from PyQt6` → `from PySide6`
- LGPL license (more permissive)
- Effort: 1-2 days

**Option 2: Switch to wxPython**
- More significant refactor
- Different API and patterns
- Effort: 2-3 weeks

**Option 3: Web-Based Earlier**
- Skip desktop refinement
- Move to web sooner than planned
- Effort: 4-6 weeks

## Testing Strategy

### GUI Testing
- Use pytest-qt for automated GUI testing
- Test critical user flows (add job, generate resume)
- Mock database calls in GUI tests
- Test keyboard shortcuts and navigation

### Manual Testing
- Test on Windows and macOS regularly
- Verify high-DPI display handling
- Check accessibility features
- User acceptance testing

## Review Criteria

Review this decision if:
- GPL licensing becomes blocker for adoption
- Application size causes download issues
- Cross-platform bugs become unmanageable
- Web migration becomes urgent (skip desktop polish)
- User feedback indicates UI issues

## References

- PyQt6 Documentation: https://www.riverbankcomputing.com/static/Docs/PyQt6/
- Qt Documentation: https://doc.qt.io/qt-6/
- Python Qt Tutorial: https://realpython.com/python-pyqt-gui-calculator/
- pytest-qt: https://pytest-qt.readthedocs.io/

## Notes

User preferences considered:
- Professional appearance required (PyQt6 excels here)
- Cost-effective (GPL is free)
- Desktop-first approach (PyQt6 purpose-built for desktop)
- Future web migration (service layer architecture enables this)

PyQt6 provides the best balance of:
- Professional UI quality
- Development productivity
- Cross-platform support
- Future flexibility

The GPL licensing is acceptable for an open-source project with MIT-licensed code.
