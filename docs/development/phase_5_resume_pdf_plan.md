# Phase 5: Resume Generation & PDF Printing

**Status:** Planning Complete, Ready to Start
**Priority:** High
**Estimated Effort:** 25-30 hours
**Dependencies:** Phase 4 (TailoredResume data structure)

## Overview

Implement professional PDF resume generation using ReportLab, allowing users to export their tailored resumes with multiple template options, live preview, and direct printing capabilities.

## Goals

1. Generate professional PDF resumes from TailoredResume data
2. Provide multiple resume template options (Classic, Modern, Compact)
3. Allow users to preview before downloading/printing
4. Support direct printing and PDF download
5. Maintain professional typography and layout standards
6. Ensure ATS-friendly formatting options

## User Value

- **Professional output**: Publication-quality PDF resumes
- **Template flexibility**: Choose style that fits industry/preference
- **Quick turnaround**: From job posting to PDF in minutes
- **Print-ready**: No manual formatting needed
- **ATS-compatible**: Clean, parseable structure

## Architecture

```
┌─────────────────────────────────────────────────┐
│         User Interface (PyQt6)                  │
│  ┌────────────────┐  ┌─────────────────────┐   │
│  │ Resume Preview │  │ Export/Print Dialog │   │
│  │    Dialog      │  │                     │   │
│  └────────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│     PDF Generation Service Layer                │
│  ┌──────────────────────────────────────────┐  │
│  │  ResumePDFGenerator                       │  │
│  │  - generate_pdf(tailored_resume, template)│  │
│  │  - preview_pdf(...)                       │  │
│  │  - print_pdf(...)                         │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│         Template System                          │
│  ┌──────────────┐  ┌──────────────┐            │
│  │ BaseTemplate │  │ TemplateSpec │            │
│  └──────────────┘  └──────────────┘            │
│         │                                        │
│    ┌────┴────┬──────────┬──────────┐           │
│    ▼         ▼          ▼          ▼           │
│  Classic  Modern   Compact   ATS-Friendly      │
│ Template Template Template   Template          │
└─────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│         ReportLab PDF Generation                │
│  - Canvas, Flowables, Styles                    │
│  - Typography, Spacing, Layout                  │
└─────────────────────────────────────────────────┘
```

## Implementation Phases

### Phase 5.1: PDF Template Foundation (6-7 hours) ✅ COMPLETED

**Component:** Base template system and infrastructure

**Tasks:**
- [x] Create `src/adaptive_resume/pdf/` directory structure
- [x] Create base template classes:
  ```python
  # src/adaptive_resume/pdf/base_template.py
  class ResumeSection(Enum):
      HEADER = "header"
      SUMMARY = "summary"
      EXPERIENCE = "experience"
      EDUCATION = "education"
      SKILLS = "skills"
      CERTIFICATIONS = "certifications"

  @dataclass
  class TemplateSpec:
      """Template specification with fonts, colors, spacing."""
      name: str
      font_family: str = "Helvetica"
      font_size_name: int = 16
      font_size_heading: int = 12
      font_size_body: int = 10
      margin_top: float = 0.75  # inches
      margin_bottom: float = 0.75
      margin_left: float = 0.75
      margin_right: float = 0.75
      line_spacing: float = 1.2
      section_spacing: float = 0.25
      primary_color: str = "#000000"
      accent_color: str = "#0066CC"

  class BaseResumeTemplate(ABC):
      """Abstract base class for resume templates."""

      def __init__(self, spec: TemplateSpec):
          self.spec = spec
          self.styles = self._create_styles()

      @abstractmethod
      def build_resume(self, canvas, tailored_resume, profile) -> None:
          """Build the complete resume PDF."""
          pass

      def _create_styles(self) -> dict:
          """Create paragraph styles for this template."""
          pass

      def _build_header(self, canvas, profile) -> float:
          """Build header section, return height used."""
          pass

      def _build_section(self, canvas, section: ResumeSection, content, y_position) -> float:
          """Build a resume section, return new y_position."""
          pass
  ```

- [ ] Create template registry:
  ```python
  # src/adaptive_resume/pdf/template_registry.py
  class TemplateRegistry:
      """Registry for available resume templates."""

      _templates: Dict[str, Type[BaseResumeTemplate]] = {}

      @classmethod
      def register(cls, name: str, template_class: Type[BaseResumeTemplate]):
          """Register a template."""
          cls._templates[name] = template_class

      @classmethod
      def get_template(cls, name: str) -> Type[BaseResumeTemplate]:
          """Get template by name."""
          return cls._templates.get(name)

      @classmethod
      def list_templates(cls) -> List[str]:
          """List all available templates."""
          return list(cls._templates.keys())
  ```

- [x] Create common PDF utilities:
  ```python
  # src/adaptive_resume/pdf/pdf_utils.py
  def format_date_range(start_date, end_date, is_current) -> str:
      """Format date range for resume display."""
      pass

  def wrap_text(text: str, width: int, style) -> List[str]:
      """Wrap text to fit width."""
      pass

  def draw_horizontal_line(canvas, x, y, width, color, thickness=1):
      """Draw a horizontal line."""
      pass
  ```

- [x] Write unit tests for template foundation

**Deliverable:** Template infrastructure ready for implementations ✅

**Files Created:**
- ✅ `src/adaptive_resume/pdf/__init__.py`
- ✅ `src/adaptive_resume/pdf/base_template.py`
- ✅ `src/adaptive_resume/pdf/template_registry.py`
- ✅ `src/adaptive_resume/pdf/pdf_utils.py`
- ✅ `tests/unit/test_base_template.py`

**Tests:** 57 passing (34 PDF utils, 23 base template/registry)

---

### Phase 5.2: Classic Template Implementation (5-6 hours) ✅ COMPLETED

**Component:** Professional classic resume template

**Tasks:**
- [x] Create `src/adaptive_resume/pdf/templates/classic_template.py`
- [x] Implement classic layout:
  ```
  ┌─────────────────────────────────────┐
  │ JOHN DOE                            │
  │ john.doe@email.com | 555-1234       │
  │ linkedin.com/in/johndoe             │
  ├─────────────────────────────────────┤
  │ PROFESSIONAL SUMMARY                │
  │ Experienced software engineer...    │
  │                                     │
  │ EXPERIENCE                          │
  │ Senior Software Engineer            │
  │ Tech Corp | San Francisco, CA       │
  │ Jan 2020 - Present                  │
  │ • Developed microservices...        │
  │ • Led team of 5 engineers...        │
  │                                     │
  │ Software Engineer                   │
  │ StartupXYZ | Remote                 │
  │ Jun 2018 - Dec 2019                 │
  │ • Built REST APIs...                │
  │                                     │
  │ EDUCATION                           │
  │ BS Computer Science                 │
  │ UC Berkeley | 2018 | GPA: 3.75      │
  │                                     │
  │ SKILLS                              │
  │ Python • JavaScript • React • AWS   │
  │                                     │
  │ CERTIFICATIONS                      │
  │ AWS Certified Developer (2021)      │
  └─────────────────────────────────────┘
  ```
- [x] Features:
  - Clean serif font (Times-Roman/Times-Bold)
  - Traditional section headers (bold, uppercase)
  - Bullet points for accomplishments
  - Clear date formatting
  - Skills as comma-separated list or grouped
  - Single column layout
  - Professional spacing and margins
- [x] Register with TemplateRegistry
- [x] Write unit tests (30 comprehensive tests)

**Deliverable:** Professional classic template ready to use ✅

**Files Created:**
- ✅ `src/adaptive_resume/pdf/templates/__init__.py`
- ✅ `src/adaptive_resume/pdf/templates/classic_template.py` (640 lines)
- ✅ `tests/unit/test_classic_template.py` (30 tests)

**Tests:** 87 passing total (34 utils + 23 base/registry + 30 classic template)

---

### Phase 5.3: Resume PDF Generator Service (6-7 hours)

**Component:** Main service for PDF generation

**Tasks:**
- [ ] Create `src/adaptive_resume/services/resume_pdf_generator.py`:
  ```python
  class ResumePDFGenerator:
      """Service for generating resume PDFs from TailoredResume data."""

      def __init__(self, session: Session):
          self.session = session

      def generate_pdf(
          self,
          tailored_resume: TailoredResume,
          template_name: str = "classic",
          output_path: Optional[str] = None,
          include_gaps: bool = False,
          include_recommendations: bool = False
      ) -> bytes:
          """Generate PDF resume.

          Args:
              tailored_resume: TailoredResume with selected accomplishments
              template_name: Name of template to use
              output_path: Optional file path to save PDF
              include_gaps: Whether to include skill gaps section
              include_recommendations: Whether to include recommendations

          Returns:
              PDF as bytes
          """
          pass

      def preview_pdf(
          self,
          tailored_resume: TailoredResume,
          template_name: str = "classic"
      ) -> bytes:
          """Generate PDF for preview (returns bytes)."""
          pass

      def save_pdf(
          self,
          tailored_resume: TailoredResume,
          file_path: str,
          template_name: str = "classic"
      ) -> None:
          """Save PDF to file."""
          pass
  ```

- [ ] Implement data transformation:
  - Convert TailoredResume to PDF-friendly structure
  - Group accomplishments by job/company
  - Format dates consistently
  - Extract profile data from database
  - Handle missing/optional fields gracefully

- [ ] Implement PDF generation:
  - Create ReportLab canvas
  - Select and instantiate template
  - Pass data to template for rendering
  - Return PDF bytes or save to file

- [ ] Add error handling:
  - Missing required data
  - Template not found
  - File I/O errors
  - PDF generation failures

- [ ] Write comprehensive unit tests

**Deliverable:** Functional PDF generation service

**Files Created:**
- `src/adaptive_resume/services/resume_pdf_generator.py`
- `tests/unit/test_resume_pdf_generator.py`

---

### Phase 5.4: Additional Templates (4-5 hours)

**Component:** Modern and Compact template implementations

**Tasks:**

**Modern Template:**
- [ ] Create `src/adaptive_resume/pdf/templates/modern_template.py`
- [ ] Features:
  - Sans-serif font (Helvetica, Arial)
  - Color accents (configurable)
  - Horizontal lines as section dividers
  - Icons for contact info (optional)
  - Skills as pills/badges
  - Slightly tighter spacing
  - Contemporary feel
- [ ] Register and test

**Compact Template:**
- [ ] Create `src/adaptive_resume/pdf/templates/compact_template.py`
- [ ] Features:
  - Smaller fonts (9-10pt body)
  - Reduced margins (0.5 inches)
  - Tighter line spacing
  - Abbreviated date formats
  - Maximum information density
  - Ideal for senior roles with lots of experience
- [ ] Register and test

**ATS-Friendly Template:**
- [ ] Create `src/adaptive_resume/pdf/templates/ats_template.py`
- [ ] Features:
  - Simple, clean layout (no tables, columns)
  - Standard fonts only
  - Clear section headers
  - No graphics or colors
  - Maximum parsability for ATS systems
  - Left-aligned text only
- [ ] Register and test

**Deliverable:** 3 additional template options

**Files Created:**
- `src/adaptive_resume/pdf/templates/modern_template.py`
- `src/adaptive_resume/pdf/templates/compact_template.py`
- `src/adaptive_resume/pdf/templates/ats_template.py`
- Tests for each template

---

### Phase 5.5: UI Integration (5-6 hours)

**Component:** GUI dialogs for PDF preview, export, and printing

**Tasks:**

**Create Resume Preview Dialog:**
- [ ] Create `src/adaptive_resume/gui/dialogs/resume_pdf_preview_dialog.py`
- [ ] Features:
  - PDF preview widget (QPdfView or embedded viewer)
  - Template selector dropdown
  - Options checkboxes (include gaps, include recommendations)
  - Zoom controls (25%, 50%, 100%, 150%, 200%, Fit Width, Fit Page)
  - Navigation (multi-page support)
  - Export button (Save As PDF)
  - Print button
  - Close button
- [ ] Wire up template switching (regenerate preview on change)
- [ ] Wire up options toggling (regenerate preview on change)

**Create Export Dialog:**
- [ ] File save dialog with PDF filter
- [ ] Default filename: `[FirstName]_[LastName]_Resume_[CompanyName].pdf`
- [ ] Success notification

**Integrate with Results Screen:**
- [ ] Add "Generate PDF Resume" button to TailoringResultsScreen
- [ ] Wire up to ResumePDFGenerator service
- [ ] Show ResumePreviewDialog on click
- [ ] Handle errors gracefully

**Add to Main Menu:**
- [ ] Add File → Export Resume as PDF menu item
- [ ] Enable only when tailored resume exists
- [ ] Wire up to preview dialog

**Deliverable:** Complete PDF workflow in UI

**Files Created:**
- `src/adaptive_resume/gui/dialogs/resume_pdf_preview_dialog.py`
- Updated `src/adaptive_resume/gui/screens/tailoring_results_screen.py`
- Updated `src/adaptive_resume/gui/main_window.py`

---

### Phase 5.6: Testing & Polish (3-4 hours)

**Component:** Comprehensive testing and quality improvements

**Tasks:**

**End-to-End Testing:**
- [ ] Test with real TailoredResume data
- [ ] Test all 4 templates (Classic, Modern, Compact, ATS)
- [ ] Test with varying amounts of content:
  - Minimal (1 job, 1 education)
  - Normal (3-5 jobs, 2 education, 10 skills)
  - Extensive (8+ jobs, multiple education/certs, 20+ skills)
- [ ] Test multi-page resumes
- [ ] Test edge cases (missing fields, long text, special characters)
- [ ] Test PDF file size and quality

**Typography & Layout Polish:**
- [ ] Review all templates for professional appearance
- [ ] Ensure consistent spacing and alignment
- [ ] Fix any text overflow or wrapping issues
- [ ] Verify font sizes are readable
- [ ] Check margins and page breaks
- [ ] Test print output (actual printer)

**Performance:**
- [ ] Measure PDF generation time
- [ ] Optimize if generation takes >2 seconds
- [ ] Cache fonts/styles where possible

**Error Handling:**
- [ ] Test with malformed data
- [ ] Test with missing profile data
- [ ] Test with no accomplishments
- [ ] Ensure graceful degradation

**Documentation:**
- [ ] Update CLAUDE.md with Phase 5 completion
- [ ] Update status_report.md
- [ ] Add PDF generation guide for users
- [ ] Document template customization options

**Deliverable:** Production-ready PDF generation feature

**Files Updated:**
- `docs/CLAUDE.md`
- `docs/development/status_report.md`
- `docs/user_guide.md` (PDF generation section)

---

## Total Effort Breakdown

| Phase | Description | Hours |
|-------|-------------|-------|
| 5.1 | PDF Template Foundation | 6-7 |
| 5.2 | Classic Template Implementation | 5-6 |
| 5.3 | Resume PDF Generator Service | 6-7 |
| 5.4 | Additional Templates (Modern, Compact, ATS) | 4-5 |
| 5.5 | UI Integration | 5-6 |
| 5.6 | Testing & Polish | 3-4 |
| **Total** | **Complete PDF Generation** | **29-35 hours** |

## Technical Decisions

### Why ReportLab?
- Industry-standard Python PDF library
- Excellent typography control
- Supports complex layouts
- Good documentation
- Already installed in project

### Template Approach
- Inheritance-based templates for code reuse
- Registry pattern for template selection
- Spec-based configuration for easy customization
- Separation of content and presentation

### Data Flow
1. User triggers PDF generation from TailoringResultsScreen
2. ResumePDFGenerator fetches Profile and related data from database
3. Combines with TailoredResume accomplishments
4. Passes to selected template
5. Template renders PDF using ReportLab
6. PDF displayed in preview dialog
7. User exports/prints PDF

## Success Criteria

- [ ] All 4 templates generate professional PDFs
- [ ] PDFs are ATS-compatible (at least ATS template)
- [ ] Generation takes <2 seconds for typical resume
- [ ] Preview shows accurate representation
- [ ] Export saves valid PDF files
- [ ] Print produces correct output
- [ ] All unit tests pass (target: 40+ tests)
- [ ] No major layout issues or text overflow
- [ ] Professional typography and spacing

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| ReportLab complexity | Start with simple layouts, iterate incrementally |
| Multi-page layout issues | Test with extensive content early, use ReportLab Platypus flowables |
| Font availability | Use standard fonts (Times, Helvetica), provide fallbacks |
| PDF size bloat | Compress images, use standard fonts (not embedded), optimize content |
| Print preview accuracy | Test on actual printers, use standard page sizes |
| ATS parsing failures | Research ATS best practices, keep ATS template extremely simple |

## Future Enhancements (Post-Phase 5)

- Custom template builder (user-defined colors, fonts)
- Two-column layouts
- Cover letter templates
- Import custom fonts
- Export to DOCX format
- LaTeX template option
- Template marketplace/sharing
- A/B testing of templates for response rates

## References

- ReportLab User Guide: https://www.reportlab.com/docs/reportlab-userguide.pdf
- ATS Resume Best Practices: https://www.jobscan.co/ats-resume
- Resume Design Inspiration: https://www.canva.com/resumes/templates/

---

**Ready to start implementation!**
