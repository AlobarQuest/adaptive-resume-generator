# ADR-0004: PDF Generation Approach

**Status:** Accepted  
**Date:** 2025-11-04  
**Deciders:** AlobarQuest

## Context

The core function of Adaptive Resume Generator is creating professional, tailored PDF resumes. Requirements:

**Functional Requirements:**
- Generate professional-looking resume PDFs
- Support combination chronological/functional format
- Create cover letter PDFs with matching styling
- Allow multiple template styles
- Support common resume sections (summary, experience, skills, education)
- Enable precise control over layout and spacing

**Technical Requirements:**
- ATS-friendly (Applicant Tracking System compatible)
- Machine-readable text (not images)
- Consistent fonts and formatting
- Proper text encoding (Unicode support)
- Reasonable file sizes (< 500KB per resume)
- Fast generation (< 2 seconds per document)

**Quality Requirements:**
- Professional appearance
- Consistent with industry standards
- Print-ready quality
- Proper page breaks
- Margins and spacing appropriate

## Decision

We will use **ReportLab** as the primary PDF generation library.

## Alternatives Considered

### 1. ReportLab (Selected)
**Pros:**
- Industry-standard Python PDF library
- Precise control over every element
- Can create ATS-friendly, machine-readable PDFs
- Excellent documentation
- Production-proven in major applications
- Canvas-based drawing for exact positioning
- Support for tables, flowables, styles
- Can embed fonts
- Fast generation

**Cons:**
- Lower-level API requires more code
- Steeper learning curve
- Manual layout calculations needed
- More verbose than HTML-based solutions

**Verdict:** Best for precise, professional PDF generation

### 2. WeasyPrint
**Pros:**
- HTML/CSS to PDF conversion
- Easier to style (use CSS)
- Familiar web technologies
- Good for complex layouts

**Cons:**
- Less precise control than ReportLab
- Requires GTK+ libraries (platform issues)
- Slower rendering
- Harder to ensure ATS compatibility
- HTML/CSS adds abstraction layer

**Verdict:** Good for web-style documents, but less control for resume layouts

### 3. FPDF/PyFPDF
**Pros:**
- Simple, high-level API
- Easy to learn
- Lightweight

**Cons:**
- Less powerful than ReportLab
- Limited styling options
- Fewer features for complex layouts
- Smaller community and ecosystem
- UTF-8 support more limited

**Verdict:** Too simple for professional resume requirements

### 4. pdfkit (wkhtmltopdf wrapper)
**Pros:**
- HTML/CSS based
- Renders like a browser
- Good for web content

**Cons:**
- Requires external wkhtmltopdf binary
- Distribution complexity
- Harder to ensure consistent results
- ATS compatibility uncertain
- Platform-specific issues

**Verdict:** External dependency and distribution complexity not worth it

### 5. borb
**Pros:**
- Modern, pure Python
- High-level and low-level APIs
- Can read and write PDFs

**Cons:**
- Newer library (less battle-tested)
- Smaller community
- Documentation still growing
- Less proven in production

**Verdict:** Interesting, but ReportLab more established

## Rationale

### Why ReportLab is Best for Resumes

**Precise Control:**
Resumes require exact positioning of elements:
- Headers with contact info
- Section headers at specific positions
- Bullet points with proper indentation
- Skills in columns or rows
- Dates aligned consistently

ReportLab's canvas API allows pixel-perfect control:
```python
canvas.drawString(x, y, text)
canvas.drawRightString(x, y, text)  # Right-aligned
canvas.rect(x, y, width, height)     # For boxes, lines
```

**ATS Compatibility:**
Applicant Tracking Systems parse PDFs to extract text. ReportLab:
- Creates true text (not images)
- Maintains proper text order
- Uses standard PDF structure
- Embeds fonts correctly
- Ensures machine readability

**Template System:**
We can create reusable templates with ReportLab:
```python
class ResumeTemplate:
    def __init__(self, canvas, pagesize):
        self.canvas = canvas
        self.width, self.height = pagesize
        self.define_styles()
        
    def draw_header(self, profile):
        # Consistent header across resumes
        pass
        
    def draw_experience_section(self, jobs):
        # Format job history
        pass
```

**Performance:**
ReportLab generates PDFs quickly:
- Direct PDF generation (no HTML parsing)
- Efficient rendering
- Small file sizes
- Can generate 100s of PDFs per minute

**Production Ready:**
ReportLab powers:
- BitTorrent's invoice system
- Financial reports in banking
- Healthcare documentation systems
- Government forms and documents

## Implementation Strategy

### Architecture

```
┌─────────────────────────────────────┐
│   PDF Generator Service             │
│   - Accepts resume data             │
│   - Selects template                │
│   - Orchestrates generation         │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│   Resume Template                   │
│   - Defines layout structure        │
│   - Section positioning             │
│   - Style definitions               │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│   ReportLab Canvas                  │
│   - Low-level PDF generation        │
│   - Drawing primitives              │
│   - Font management                 │
└─────────────────────────────────────┘
```

### Template Components

**1. Page Setup:**
```python
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Standard letter size (8.5" x 11")
canvas = Canvas(filename, pagesize=letter)
width, height = letter  # 612 x 792 points
```

**2. Style Definitions:**
```python
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

styles = getSampleStyleSheet()

# Custom styles for resume
name_style = ParagraphStyle(
    'Name',
    parent=styles['Heading1'],
    fontSize=24,
    textColor=colors.HexColor('#2c3e50'),
    alignment=TA_CENTER,
    spaceAfter=6
)

heading_style = ParagraphStyle(
    'SectionHeading',
    parent=styles['Heading2'],
    fontSize=14,
    textColor=colors.HexColor('#34495e'),
    spaceBefore=12,
    spaceAfter=6,
    borderWidth=0,
    borderPadding=0,
    borderColor=colors.HexColor('#95a5a6'),
    borderRadius=None,
)
```

**3. Layout System:**
```python
class ResumeLayout:
    # Margins
    MARGIN_LEFT = 50
    MARGIN_RIGHT = 50
    MARGIN_TOP = 50
    MARGIN_BOTTOM = 50
    
    # Content area
    CONTENT_WIDTH = letter[0] - MARGIN_LEFT - MARGIN_RIGHT
    CONTENT_HEIGHT = letter[1] - MARGIN_TOP - MARGIN_BOTTOM
    
    # Section spacing
    SECTION_SPACING = 20
    ITEM_SPACING = 10
    
    # Column layout (for skills)
    NUM_COLUMNS = 3
    COLUMN_WIDTH = CONTENT_WIDTH / NUM_COLUMNS
```

**4. Combination Format:**

Chronological + Functional elements:
- Header with contact info (functional)
- Professional summary (functional)
- Skills section (functional)
- Experience section (chronological)
- Education (chronological)

### Code Example

```python
class CombinationResumeTemplate:
    def generate(self, profile, selected_jobs, selected_skills):
        canvas = Canvas(f"output/{profile.name}_resume.pdf", 
                       pagesize=letter)
        
        y = letter[1] - self.MARGIN_TOP
        
        # Header
        y = self.draw_header(canvas, profile, y)
        
        # Summary
        y = self.draw_summary(canvas, profile.summary, y)
        
        # Skills (functional)
        y = self.draw_skills(canvas, selected_skills, y)
        
        # Experience (chronological)
        for job in selected_jobs:
            y = self.draw_job(canvas, job, y)
            if y < 100:  # New page if needed
                canvas.showPage()
                y = letter[1] - self.MARGIN_TOP
        
        # Education
        y = self.draw_education(canvas, profile.education, y)
        
        canvas.save()
        return f"output/{profile.name}_resume.pdf"
```

## ATS Compatibility Strategy

### What Makes a PDF ATS-Friendly

**1. True Text (Not Images):**
- Use ReportLab text functions, not images
- Ensure text is selectable in PDF reader

**2. Logical Reading Order:**
- Top to bottom, left to right
- Section headers before content
- Consistent structure

**3. Standard Fonts:**
- Use common fonts (Arial, Times, Helvetica)
- Embed fonts in PDF
- Avoid decorative fonts

**4. Simple Formatting:**
- No text in headers/footers (ATS may ignore)
- No text in tables (unless necessary)
- No text wrapping around images
- Clear section breaks

**5. Machine-Readable Structure:**
- Use spaces/tabs, not absolute positioning for columns
- Proper line breaks between sections
- Consistent indentation

### Implementation
```python
# Good: ATS-friendly text
canvas.drawString(x, y, "Software Engineer")

# Bad: Image with text (ATS can't read)
canvas.drawImage("title.png", x, y, width, height)

# Good: Use standard embedded fonts
canvas.setFont("Helvetica", 11)

# Bad: Custom fonts that may not be readable
canvas.setFont("FancyFont", 11)
```

## Consequences

### Positive

**Quality:**
- Professional, polished output
- Print-ready quality
- Consistent formatting
- Industry-standard appearance

**Technical:**
- ATS-compatible by design
- Fast PDF generation (< 2 seconds)
- Small file sizes (100-300 KB)
- Reliable, battle-tested library
- No external dependencies

**Development:**
- Full control over layout
- Can implement any design
- Template system extensible
- Easy to modify and iterate

**Users:**
- PDFs work with all readers
- Print correctly
- Pass ATS screening
- Professional appearance helps applications

### Negative

**Complexity:**
- Lower-level API means more code
- Manual layout calculations
- Need to handle page breaks manually
- Steeper learning curve than HTML/CSS

**Development Time:**
- Week 5 milestone dedicated to PDF generation
- Templates take time to perfect
- Testing on various PDF readers needed
- Fine-tuning spacing and alignment

**Maintenance:**
- Layout changes require code updates
- New templates need development
- Must maintain ATS compatibility with changes

### Risks and Mitigations

**Risk:** ReportLab learning curve delays implementation  
**Mitigation:** Allocate full Week 5, start with simple template, iterate

**Risk:** Layout bugs across different PDF readers  
**Mitigation:** Test with Adobe Reader, Foxit, Preview (Mac), Chrome PDF viewer

**Risk:** ATS compatibility issues  
**Mitigation:** Follow ATS best practices, test with ATS checkers, get user feedback

**Risk:** Template customization becomes complex  
**Mitigation:** Start with one solid template, add more later if needed

## Testing Strategy

### Unit Tests
```python
def test_resume_generation():
    profile = create_test_profile()
    jobs = create_test_jobs()
    template = CombinationResumeTemplate()
    
    pdf_path = template.generate(profile, jobs, [])
    
    assert os.path.exists(pdf_path)
    assert os.path.getsize(pdf_path) < 500000  # < 500KB
```

### Visual Testing
- Generate sample resumes
- Manual review for alignment, spacing
- Print test (ensure print quality)
- Different page lengths (1 page, 2 page, 3 page)

### ATS Testing
- Use online ATS checkers
- Verify text extraction
- Check reading order
- Test with Jobscan or similar tools

### Cross-Platform Testing
- Windows PDF readers (Adobe, Foxit, Edge)
- Mac Preview
- Linux PDF viewers
- Mobile PDF apps

## Future Enhancements

### Phase 1 (v1.0)
- One combination chronological/functional template
- Black and white, professional styling
- Standard fonts (Helvetica, Times)

### Phase 2 (v1.1+)
- Multiple template styles (modern, traditional, creative)
- Color schemes (while maintaining ATS compatibility)
- More flexible section ordering
- Optional photo (for non-US resumes)

### Phase 3 (v2.0+)
- Custom template designer (GUI)
- Template marketplace
- Import templates from files
- Export to other formats (DOCX, HTML)

## Migration Path

### If ReportLab Becomes Inadequate

**Option 1: WeasyPrint**
- More design flexibility with CSS
- Trade-off: less control, external dependencies
- Effort: 2-3 weeks to rewrite PDF generator

**Option 2: borb**
- Modern alternative
- Similar to ReportLab but newer API
- Effort: 1-2 weeks to migrate

**Option 3: Commercial PDF library**
- If advanced features needed (forms, digital signatures)
- Options: PyPDF2 + reportlab, or commercial tools
- Cost: $500-2000/year

### For Web Version

- ReportLab works server-side (no changes needed)
- Generate PDF on backend, send to browser
- Same templates, same code
- Only difference: serving PDFs via HTTP

## Review Criteria

Review this decision if:
- Users report ATS rejection issues
- PDF generation takes > 5 seconds
- Layout becomes too complex to manage
- Need features ReportLab can't provide
- Industry standards change (e.g., new resume formats)

## References

- ReportLab Documentation: https://www.reportlab.com/docs/reportlab-userguide.pdf
- ReportLab Open Source: https://www.reportlab.com/opensource/
- ATS Resume Tips: https://www.jobscan.co/blog/ats-resume/
- PDF Specification: https://www.adobe.com/devnet/pdf/pdf_reference.html

## Notes

ReportLab choice aligns with project goals:
- **Professional output:** Resume quality directly impacts user success
- **ATS compatibility:** Critical for job applications
- **Control:** Precise layouts possible
- **Future-proof:** Works for both desktop and web versions
- **Proven:** Used by major production systems

The learning curve is offset by the quality and reliability of output. Week 5 milestone provides adequate time for implementation and refinement.
