# Phase 3.6: Resume Import & Auto-Population

**Date:** November 14, 2025
**Status:** Ready to Start
**Priority:** High (User Onboarding Feature)
**Estimated Effort:** 20-25 hours (5 phases)

---

## Plan Overview

This phase enables users to upload their existing resumes and automatically extract information to populate their profile. This dramatically improves the onboarding experience by eliminating manual data entry.

**Approach:**
- ✅ Reuse JobPostingParser infrastructure from Phase 4
- ✅ Hybrid spaCy + AI extraction for accuracy
- ✅ Preview/confirmation workflow for user control
- ✅ Intelligent mapping to existing data models
- ✅ Handle incomplete or ambiguous data gracefully

---

## Goals

### Primary Deliverables
1. Users can upload existing resumes (PDF, DOCX, TXT)
2. System extracts contact info, work history, education, skills, certifications
3. Extracted data mapped to Profile/Job/BulletPoint/Skill/Education models
4. Preview screen shows extracted data with edit capabilities
5. User can review, edit, and confirm before saving
6. Handles multiple formats and layouts

### Success Metrics
- ✅ Extraction accuracy >85% for standard resumes
- ✅ Processing time <15 seconds per resume
- ✅ Correctly identifies 90%+ of work experiences
- ✅ Correctly extracts 80%+ of skills
- ✅ Users can complete onboarding in <5 minutes

---

## Implementation Phases

### Phase 3.6.1: Resume Parser Extension (3-4 hours)

**Component: Extend JobPostingParser for Resume Parsing**

**Tasks:**
- [ ] Extend JobPostingParser or create ResumeParser service
  - [ ] Reuse PDF, DOCX, TXT parsing logic
  - [ ] Add resume-specific text cleaning
  - [ ] Preserve section structure (Experience, Education, Skills)
  - [ ] Handle common resume formats (chronological, functional, hybrid)
- [ ] Add section detection
  - [ ] Identify Experience/Work History section
  - [ ] Identify Education section
  - [ ] Identify Skills section
  - [ ] Identify Contact/Summary section
  - [ ] Identify Certifications section
- [ ] Add validation for resume files
  - [ ] Detect if file is a resume vs job posting
  - [ ] Size limits (max 5MB)
  - [ ] Format validation
- [ ] Write unit tests with sample resumes
- [ ] Add error handling

**Deliverable:** Resume parser that extracts text with section detection

**Files Created:**
- `src/adaptive_resume/services/resume_parser.py` (or extend existing)
- `tests/unit/test_resume_parser.py`
- `tests/fixtures/sample_resumes/` (test data)

---

### Phase 3.6.2: Resume Extractor Service (6-8 hours)

**Component: ResumeExtractor Service with AI**

**Tasks:**
- [ ] Create `src/adaptive_resume/services/resume_extractor.py`
- [ ] Define `ExtractedResume` dataclass
  ```python
  @dataclass
  class ExtractedResume:
      # Contact Information
      first_name: Optional[str]
      last_name: Optional[str]
      email: Optional[str]
      phone: Optional[str]
      location: Optional[str]
      linkedin_url: Optional[str]
      github_url: Optional[str]
      website_url: Optional[str]

      # Work Experience
      jobs: List[ExtractedJob]

      # Education
      education: List[ExtractedEducation]

      # Skills
      skills: List[str]

      # Certifications
      certifications: List[ExtractedCertification]

      # Metadata
      confidence_score: float
      extraction_method: str
  ```
- [ ] Define `ExtractedJob` dataclass
  ```python
  @dataclass
  class ExtractedJob:
      company_name: str
      job_title: str
      location: Optional[str]
      start_date: Optional[str]  # "Jan 2020" or "2020-01"
      end_date: Optional[str]    # "Present" or "Dec 2023"
      is_current: bool
      bullet_points: List[str]
      confidence_score: float
  ```
- [ ] Define `ExtractedEducation` and `ExtractedCertification` dataclasses
- [ ] Implement spaCy-based extraction
  - [ ] Extract contact info using NER and regex
  - [ ] Parse work experience with date patterns
  - [ ] Extract education with degree patterns
  - [ ] Extract skills using noun phrases and entities
  - [ ] Parse certifications
- [ ] Implement AI-based extraction
  - [ ] Create Claude API prompt template for resume parsing
  - [ ] Request structured JSON output
  - [ ] Handle rate limits and retries
  - [ ] Parse AI response into dataclasses
- [ ] Implement hybrid result merging
  - [ ] Combine spaCy + AI results
  - [ ] Prefer AI for ambiguous cases
  - [ ] Use spaCy as fallback
  - [ ] Add confidence scoring
- [ ] Add date parsing and normalization
  - [ ] "Jan 2020" → date(2020, 1, 1)
  - [ ] "Present" → is_current = True
  - [ ] Handle various date formats
- [ ] Write comprehensive unit tests
- [ ] Add integration tests with real resumes

**Deliverable:** Service that extracts structured data from resumes

**Files Created:**
- `src/adaptive_resume/services/resume_extractor.py`
- `tests/unit/test_resume_extractor.py`

---

### Phase 3.6.3: Resume Importer Service (4-5 hours)

**Component: ResumeImporter Service**

**Tasks:**
- [ ] Create `src/adaptive_resume/services/resume_importer.py`
- [ ] Implement profile creation/update logic
  - [ ] Create new Profile from extracted contact info
  - [ ] Or update existing Profile if specified
  - [ ] Handle missing contact fields gracefully
- [ ] Implement job/work experience import
  - [ ] Create Job records for each extracted job
  - [ ] Create BulletPoint records for accomplishments
  - [ ] Set display_order based on chronological order
  - [ ] Link to profile
- [ ] Implement education import
  - [ ] Create Education records
  - [ ] Parse degree types and majors
  - [ ] Handle incomplete dates
- [ ] Implement skill import
  - [ ] Create or link to existing Skill records
  - [ ] Avoid duplicates (case-insensitive matching)
  - [ ] Categorize skills if possible
- [ ] Implement certification import
  - [ ] Create Certification records
  - [ ] Parse issuer and dates
- [ ] Add deduplication logic
  - [ ] Don't create duplicate companies
  - [ ] Don't create duplicate skills
  - [ ] Merge similar bullet points
- [ ] Add validation and error handling
  - [ ] Required fields validation
  - [ ] Data type validation
  - [ ] Transaction handling (rollback on error)
- [ ] Write unit tests
- [ ] Write integration tests with database

**Deliverable:** Service that imports extracted data into database

**Files Created:**
- `src/adaptive_resume/services/resume_importer.py`
- `tests/unit/test_resume_importer.py`

---

### Phase 3.6.4: UI Integration (5-6 hours)

**Component: Resume Import Dialog and Preview Screen**

**Tasks:**

**Create Resume Import Dialog:**
- [ ] Create `src/adaptive_resume/gui/dialogs/resume_import_dialog.py`
- [ ] Add file upload area
  - [ ] Browse Files button
  - [ ] Drag-and-drop support
  - [ ] Paste text option (for text resumes)
- [ ] Add processing workflow
  - [ ] Show progress dialog
  - [ ] "Parsing resume..."
  - [ ] "Extracting information..."
  - [ ] "Organizing data..."
- [ ] Wire up services
  - [ ] ResumeParser
  - [ ] ResumeExtractor
  - [ ] ResumeImporter (preview only)
- [ ] Error handling
  - [ ] Invalid file format
  - [ ] Parsing errors
  - [ ] Extraction failures

**Create Preview/Confirmation Screen:**
- [ ] Create `src/adaptive_resume/gui/dialogs/resume_preview_dialog.py`
- [ ] Design preview layout with sections:
  ```
  ┌─────────────────────────────────────┐
  │ Contact Information                 │
  │ [Editable fields]                   │
  ├─────────────────────────────────────┤
  │ Work Experience (3 found)           │
  │ ✓ Company 1 • Title • 2020-Present  │
  │   • 5 bullet points                 │
  │ ✓ Company 2 • Title • 2018-2020     │
  │   • 4 bullet points                 │
  │ [Edit] [Remove]                     │
  ├─────────────────────────────────────┤
  │ Education (2 found)                 │
  │ ✓ University • Degree • 2018        │
  │ [Edit] [Remove]                     │
  ├─────────────────────────────────────┤
  │ Skills (15 found)                   │
  │ ✓ Python ✓ JavaScript ✓ SQL ...    │
  │ [Edit]                              │
  ├─────────────────────────────────────┤
  │ [Cancel] [Import All] [Import Selected] │
  └─────────────────────────────────────┘
  ```
- [ ] Allow editing extracted data
  - [ ] Edit contact info inline
  - [ ] Edit/remove work experiences
  - [ ] Edit/remove education entries
  - [ ] Edit/remove skills
  - [ ] Add missing items manually
- [ ] Add checkbox selection
  - [ ] Select which items to import
  - [ ] "Select All" / "Deselect All"
  - [ ] Individual item checkboxes
- [ ] Add confidence indicators
  - [ ] Show confidence score for each section
  - [ ] Highlight low-confidence items
  - [ ] Warning for missing required fields
- [ ] Implement "Import" action
  - [ ] Validate selections
  - [ ] Call ResumeImporter service
  - [ ] Show success message
  - [ ] Navigate to profile view
- [ ] Add to main window
  - [ ] Add "Import Resume" to File menu
  - [ ] Add to Dashboard quick actions
  - [ ] Add to Profile Management screen

**Deliverable:** Complete import workflow with preview and editing

**Files Created:**
- `src/adaptive_resume/gui/dialogs/resume_import_dialog.py`
- `src/adaptive_resume/gui/dialogs/resume_preview_dialog.py`
- Updated: `src/adaptive_resume/gui/main_window.py`

---

### Phase 3.6.5: Testing & Polish (2-3 hours)

**Component: Final Testing & Documentation**

**Tasks:**
- [ ] End-to-end testing
  - [ ] Test with 10+ real resumes (various formats)
  - [ ] Test PDF resumes (single column, two column)
  - [ ] Test DOCX resumes (various templates)
  - [ ] Test TXT resumes
  - [ ] Test edge cases (unusual formats, missing sections)
- [ ] Accuracy verification
  - [ ] Verify contact info extraction >90%
  - [ ] Verify work experience extraction >85%
  - [ ] Verify education extraction >85%
  - [ ] Verify skills extraction >80%
- [ ] Error handling improvements
  - [ ] Better error messages
  - [ ] Graceful degradation for poor-quality scans
  - [ ] Handle malformed resumes
- [ ] UI/UX polish
  - [ ] Loading indicators
  - [ ] Clear instructions
  - [ ] Helpful tooltips
  - [ ] Keyboard shortcuts
- [ ] Documentation
  - [ ] Update user guide with import instructions
  - [ ] Add "How to import resume" section
  - [ ] Document supported formats
  - [ ] Add troubleshooting guide
- [ ] Update documentation files
  - [ ] Update CLAUDE.md
  - [ ] Update status_report.md
  - [ ] Create phase_3_6_resume_import_plan.md

**Deliverable:** Production-ready resume import feature

**Files Updated:**
- `docs/user_guide.md`
- `docs/development/resume_import_guide.md` (new)
- `CLAUDE.md`
- `docs/development/status_report.md`

---

## Total Effort Breakdown

| Phase | Description | Hours |
|-------|-------------|-------|
| 3.6.1 | Resume Parser Extension | 3-4 |
| 3.6.2 | Resume Extractor Service | 6-8 |
| 3.6.3 | Resume Importer Service | 4-5 |
| 3.6.4 | UI Integration | 5-6 |
| 3.6.5 | Testing & Polish | 2-3 |

**Total: 20-26 hours**

---

## Technical Decisions

### Reusing Phase 4 Infrastructure

```python
# Reuse file parsing from Phase 4
from adaptive_resume.services.job_posting_parser import JobPostingParser

class ResumeParser:
    def __init__(self):
        self.file_parser = JobPostingParser()

    def parse_resume(self, file_path: str) -> str:
        # Reuse PDF/DOCX/TXT parsing
        raw_text = self.file_parser.parse_file(file_path)
        # Add resume-specific cleaning
        return self._clean_resume_text(raw_text)
```

### AI Prompt for Resume Extraction

```
Extract the following information from this resume:

1. Contact Information:
   - First name, last name
   - Email, phone number
   - Location (city, state)
   - LinkedIn, GitHub, website URLs

2. Work Experience (for each job):
   - Company name
   - Job title
   - Location
   - Start date, end date (or "Present")
   - Bullet points/accomplishments

3. Education (for each):
   - School name
   - Degree type and major
   - Graduation date
   - GPA (if present)

4. Skills:
   - List all technical and professional skills

5. Certifications (for each):
   - Certification name
   - Issuing organization
   - Issue date

Return as JSON with confidence scores for each section.
```

### Date Parsing Strategy

```python
# Handle various date formats
patterns = [
    r"(\w{3})\s+(\d{4})",           # "Jan 2020"
    r"(\d{1,2})/(\d{4})",           # "01/2020"
    r"(\d{4})",                     # "2020"
    r"(\w{3,9})\s+(\d{1,2}),?\s+(\d{4})"  # "January 1, 2020"
]

# Special handling
if date_str.lower() in ["present", "current", "now"]:
    is_current = True
    end_date = None
```

### Deduplication Strategy

```python
# Avoid creating duplicate companies
existing_companies = session.query(Job.company_name).distinct().all()
if extracted_job.company_name in existing_companies:
    # Use existing company name (preserves capitalization)
    extracted_job.company_name = existing_companies[extracted_job.company_name]

# Avoid duplicate skills (case-insensitive)
existing_skills = {s.name.lower(): s for s in session.query(Skill).all()}
for skill_name in extracted_skills:
    if skill_name.lower() in existing_skills:
        # Link to existing skill
        profile.skills.append(existing_skills[skill_name.lower()])
    else:
        # Create new skill
        new_skill = Skill(name=skill_name)
        profile.skills.append(new_skill)
```

---

## Success Criteria

### Phase 3.6 is Complete When:

**Functionality:**
- ✅ Users can upload PDF/DOCX/TXT resumes
- ✅ System extracts contact info with >90% accuracy
- ✅ System extracts work experience with >85% accuracy
- ✅ System extracts education with >85% accuracy
- ✅ System extracts skills with >80% accuracy
- ✅ Preview screen shows all extracted data
- ✅ Users can edit/remove items before import
- ✅ Import creates all records in database correctly
- ✅ No duplicate companies or skills created

**Performance:**
- ✅ Processing time <15 seconds per resume
- ✅ UI stays responsive during processing
- ✅ No memory leaks with large resumes

**Quality:**
- ✅ All services have unit tests
- ✅ Integration tests pass
- ✅ End-to-end workflow tested with 10+ resumes
- ✅ Error handling comprehensive
- ✅ Documentation complete

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Resume format variety | Test with 20+ real resumes; provide manual edit fallback |
| Low extraction accuracy | Hybrid AI + spaCy approach; allow preview/editing |
| PDF parsing issues (scanned images) | Detect and warn user; suggest OCR or manual entry |
| Date parsing ambiguity | Multiple regex patterns; flag uncertain dates for review |
| Duplicate data | Intelligent deduplication; show conflicts in preview |
| AI API costs | Cache results; allow spaCy-only mode; batch processing |

---

## What's Included vs Future Enhancements

### ✅ Included in Phase 3.6

**Core Features:**
- Resume file upload (PDF, DOCX, TXT)
- Contact information extraction
- Work experience extraction with bullets
- Education extraction
- Skills extraction
- Certifications extraction
- Preview/confirmation dialog
- Edit extracted data before import
- Intelligent deduplication
- Error handling and validation

**AI Integration:**
- Claude API for extraction
- Hybrid spaCy + AI approach
- Fallback to spaCy only
- Confidence scoring

**Quality:**
- Unit tests for all services
- Integration tests
- End-to-end testing
- Documentation

### ⏸️ Future Enhancements (Phase 3.7)

**Advanced Features:**
- OCR support for scanned PDFs
- Multi-language resume support
- Resume format detection and templates
- Smart merging with existing profile data
- Import from LinkedIn (OAuth integration)
- Import from Indeed/Monster profiles
- Batch import (multiple resumes)
- Import history tracking
- "Re-import" to update existing data
- Custom field mapping

---

## Integration Points

### Existing Services to Reuse
- `JobPostingParser` - File parsing logic
- `NLPAnalyzer` - spaCy NLP infrastructure
- `AIEnhancementService` - Claude API integration
- `ProfileService`, `JobService` - Data persistence
- `DatabaseManager` - Session management

### New Services to Create
- `ResumeParser` - Resume-specific parsing
- `ResumeExtractor` - Extract structured data
- `ResumeImporter` - Import to database

### UI Integration Points
- Dashboard: Add "Import Resume" quick action
- Profile Management: Add "Import Resume" button
- File menu: Add "Import Resume..." menu item
- First-run experience: Show import option on startup

---

## Testing Strategy

### Unit Tests
- Resume parsing (various formats)
- Contact info extraction
- Work experience extraction
- Education extraction
- Skills extraction
- Date parsing
- Deduplication logic
- Database import

### Integration Tests
- End-to-end import workflow
- AI extraction with mock responses
- Database transactions
- Error recovery

### Manual Testing
- Test with 10+ real resumes
- Various resume templates
- Edge cases (unusual formats)
- Performance with large resumes

---

## Next Steps

1. Review and approve this plan
2. Create sample resumes for testing (10+ examples)
3. Start Phase 3.6.1: Resume Parser Extension
4. Implement phases sequentially
5. Commit progress after each phase
6. Update documentation

---

## Notes

- **Priority:** High - This is a critical onboarding feature
- **Timeline Realistic:** 20-26 hours across 5 phases (self-paced)
- **Reuses Infrastructure:** Leverages Phase 4 parsing and NLP code
- **User Value:** Dramatically reduces onboarding time from 30+ minutes to <5 minutes
- **Extensible:** Can add LinkedIn import, OCR, etc. in Phase 3.7

Ready to begin Phase 3.6.1: Resume Parser Extension!
