# Phase 4: Job Posting Analysis - Revised Implementation Plan

**Date:** November 13, 2025
**Status:** Ready to Start
**Approach:** Balanced (MVP + AI Integration)
**Estimated Effort:** 33-37 hours (~5-6 weeks part-time)

---

## Plan Overview

Based on review discussion, this plan takes a **balanced approach**:
- ✅ Include AI integration from the start
- ✅ Full matching engine with original weights
- ✅ Good UI (not minimal, not full-featured)
- ✅ Core features complete and polished
- ⏸️ Defer advanced manual adjustments to Phase 4.5

---

## Goals

### Primary Deliverables
1. Users can upload job postings (PDF, DOCX, TXT, paste)
2. System extracts requirements using spaCy + AI
3. Accomplishments scored with full algorithm
4. Tailored resume generated with top matches
5. Results displayed with skill coverage analysis
6. Gap analysis and recommendations shown

### Success Metrics
- ✅ Processing time <10 seconds per job posting
- ✅ Extraction accuracy >80% (with AI)
- ✅ Top 10 selected items are relevant
- ✅ Skill coverage calculation accurate
- ✅ Users can generate tailored resume in <3 minutes

---

## Revised Timeline

### Week 1: File Parsing & Text Extraction (5-6 hours)

**Phase 4.1: JobPostingParser Service**

**Tasks:**
- [ ] Create `src/adaptive_resume/services/job_posting_parser.py`
- [ ] Implement PDF parsing with pypdf
  - [ ] Extract text from all pages
  - [ ] Handle multi-column layouts
  - [ ] Remove headers/footers/artifacts
- [ ] Implement DOCX parsing with python-docx
  - [ ] Extract paragraphs and tables
  - [ ] Preserve formatting hints
- [ ] Implement TXT file reading
- [ ] Add file validation
  - [ ] Size limits (max 10MB)
  - [ ] Type checking (PDF, DOCX, TXT only)
  - [ ] Encoding detection
- [ ] Create text cleaner
  - [ ] Normalize whitespace
  - [ ] Remove boilerplate (EOE statements)
  - [ ] Fix common encoding issues
- [ ] Write unit tests with sample files
- [ ] Add error handling and logging

**Deliverable:** Working file parser that extracts clean text

**Files Created:**
- `src/adaptive_resume/services/job_posting_parser.py`
- `tests/unit/services/test_job_posting_parser.py`

---

### Week 2: NLP Analysis (8-10 hours)

**Phase 4.2: NLPAnalyzer Service with AI**

**Tasks:**
- [ ] Create `src/adaptive_resume/services/nlp_analyzer.py`
- [ ] Define `JobRequirements` dataclass
  ```python
  @dataclass
  class JobRequirements:
      required_skills: List[str]
      preferred_skills: List[str]
      years_experience: Optional[int]
      education_level: Optional[str]
      key_responsibilities: List[str]
      confidence_score: float
      raw_sections: Dict[str, str]
  ```
- [ ] Implement spaCy-based extraction
  - [ ] Load en_core_web_md model
  - [ ] Named Entity Recognition for skills
  - [ ] Extract years of experience (regex patterns)
  - [ ] Identify requirement sections
  - [ ] Parse education requirements
- [ ] Implement AI-based extraction
  - [ ] Create Claude API prompt template
    ```
    Extract from this job posting:
    1. Required skills (must-have)
    2. Preferred skills (nice-to-have)
    3. Years of experience required
    4. Education requirements
    5. Key responsibilities

    Return as JSON...
    ```
  - [ ] Call Anthropic API with error handling
  - [ ] Parse JSON response
  - [ ] Handle rate limits gracefully
  - [ ] Add retry logic
- [ ] Implement result merging
  - [ ] Combine spaCy + AI results
  - [ ] Deduplicate skills
  - [ ] Prefer AI for nuanced distinctions
  - [ ] Use spaCy as fallback if AI fails
- [ ] Add confidence scoring
- [ ] Write comprehensive unit tests
- [ ] Add integration tests with real job postings
- [ ] Optimize for <5 second processing

**Deliverable:** Service that extracts structured requirements with high accuracy

**Files Created:**
- `src/adaptive_resume/services/nlp_analyzer.py`
- `tests/unit/services/test_nlp_analyzer.py`
- `tests/fixtures/sample_job_postings/` (test data)

---

### Week 3: Matching Engine (10-12 hours)

**Phase 4.3: MatchingEngine Service**

**Tasks:**
- [ ] Create `src/adaptive_resume/services/matching_engine.py`
- [ ] Define `ScoredAccomplishment` dataclass
  ```python
  @dataclass
  class ScoredAccomplishment:
      bullet_id: int
      bullet_text: str
      final_score: float
      skill_match_score: float
      semantic_score: float
      recency_score: float
      metrics_score: float
      matched_skills: List[str]
      reasons: List[str]
  ```
- [ ] Implement skill matching component
  - [ ] Direct keyword matching (case-insensitive)
  - [ ] spaCy similarity for synonyms
  - [ ] Technology family detection (React→JavaScript)
  - [ ] Weighted scoring based on match quality
- [ ] Implement semantic similarity component
  - [ ] Load spaCy vectors for accomplishments
  - [ ] Compute cosine similarity with job description
  - [ ] Cache vectors for performance
- [ ] Implement recency scoring
  - [ ] Calculate years since job start
  - [ ] Apply decay function
  - [ ] Handle current roles (is_current flag)
- [ ] Implement achievement metrics detection
  - [ ] Regex for numbers, percentages, money
  - [ ] Action verb detection
  - [ ] Impact word identification
- [ ] Combine scores with weights
  ```python
  WEIGHTS = {
      'skill_match': 0.4,
      'semantic': 0.3,
      'recency': 0.2,
      'metrics': 0.1
  }
  ```
- [ ] Add explainability
  - [ ] Generate "why selected" reasons
  - [ ] Track which skills matched
  - [ ] Show score breakdown
- [ ] Optimize for large profiles (100+ bullets)
- [ ] Write unit tests for each component
- [ ] Write integration tests
- [ ] Document scoring methodology

**Deliverable:** Complete matching engine that scores accomplishments accurately

**Files Created:**
- `src/adaptive_resume/services/matching_engine.py`
- `tests/unit/services/test_matching_engine.py`
- `docs/development/scoring_methodology.md`

---

### Week 4: Resume Generation & Data Models (5-6 hours)

**Phase 4.4: ResumeGenerator Service & Database**

**Tasks:**
- [ ] Create `src/adaptive_resume/services/resume_generator.py`
- [ ] Define `TailoredResume` dataclass
  ```python
  @dataclass
  class TailoredResume:
      profile_id: int
      job_posting_id: int
      selected_accomplishments: List[ScoredAccomplishment]
      skill_coverage: Dict[str, bool]
      coverage_percentage: float
      gaps: List[str]
      recommendations: List[str]
      created_at: datetime
  ```
- [ ] Implement selection algorithm
  - [ ] Sort accomplishments by score
  - [ ] Take top 20-30 items (configurable)
  - [ ] Minimum score threshold: 0.5
  - [ ] Prefer current role (70% of selections)
  - [ ] Limit 5-7 per company
- [ ] Implement skill coverage analysis
  - [ ] Map selected items to required skills
  - [ ] Calculate coverage percentage
  - [ ] Identify missing skills (gaps)
- [ ] Implement recommendations generator
  - [ ] Suggest adding missing skills
  - [ ] Highlight partially covered areas
  - [ ] Identify transferable skills
- [ ] Create database models
  - [ ] `JobPosting` model
  - [ ] `TailoredResume` model
  - [ ] Add relationships to Profile
- [ ] Create Alembic migration
- [ ] Run migration
- [ ] Write unit tests
- [ ] Write integration tests

**Deliverable:** Complete resume generation with database persistence

**Files Created:**
- `src/adaptive_resume/services/resume_generator.py`
- `src/adaptive_resume/models/job_posting.py`
- `src/adaptive_resume/models/tailored_resume.py`
- `alembic/versions/XXXX_add_job_posting_tables.py`
- `tests/unit/services/test_resume_generator.py`

---

### Week 5: UI Integration (8-10 hours)

**Phase 4.5: Upload & Results Screens**

**Tasks:**

**Update Upload Screen:**
- [ ] Enable "Browse Files" button
  - [ ] Add QFileDialog for file selection
  - [ ] Filter to PDF, DOCX, TXT
  - [ ] Display selected file info
- [ ] Implement drag-and-drop
  - [ ] Override dragEnterEvent
  - [ ] Override dropEvent
  - [ ] Show drop indicator
- [ ] Enable "Paste Text" button
  - [ ] Create paste text dialog
  - [ ] Large QTextEdit for input
  - [ ] Character count display
- [ ] Add processing workflow
  - [ ] Show progress dialog
  - [ ] "Parsing file..."
  - [ ] "Analyzing requirements..."
  - [ ] "Matching accomplishments..."
  - [ ] "Generating results..."
- [ ] Wire up services
  - [ ] JobPostingParser
  - [ ] NLPAnalyzer
  - [ ] MatchingEngine
  - [ ] ResumeGenerator
- [ ] Error handling
  - [ ] Invalid file format
  - [ ] Parsing errors
  - [ ] API failures (with retry)
  - [ ] Empty results

**Create Tailoring Results Screen:**
- [ ] Create `src/adaptive_resume/gui/screens/tailoring_results_screen.py`
- [ ] Design header section
  - [ ] Job title and company
  - [ ] Overall match score (%)
  - [ ] Visual indicator (color-coded)
- [ ] Create requirements comparison section
  ```
  ┌─────────────────┬──────────────────┐
  │ Requirements    │ Your Experience  │
  │ ✓ Python (5y)   │ ✓ 7 years        │
  │ ⚠ AWS           │ ⚠ Limited        │
  │ ✗ Kubernetes    │ ✗ Not mentioned  │
  └─────────────────┴──────────────────┘
  ```
- [ ] Display selected accomplishments
  - [ ] List with scores
  - [ ] "Why selected" tooltips
  - [ ] Expandable details
- [ ] Show gap analysis section
  - [ ] List missing skills
  - [ ] Warning indicators
- [ ] Show recommendations section
  - [ ] Actionable suggestions
  - [ ] Info cards
- [ ] Add action buttons
  - [ ] "Generate PDF" (navigate to Review)
  - [ ] "Save Draft"
  - [ ] "Start Over"
- [ ] Wire up navigation
  - [ ] Connect to Review & Print screen
  - [ ] Pass selected accomplishments
- [ ] Add to main window navigation
- [ ] Write UI tests (if possible)

**Deliverable:** Complete working UI flow from upload to results

**Files Created:**
- `src/adaptive_resume/gui/screens/tailoring_results_screen.py`
- Updated: `src/adaptive_resume/gui/screens/job_posting_screen.py`
- Updated: `src/adaptive_resume/gui/main_window.py`

---

### Week 6: Testing & Polish (3-4 hours)

**Phase 4.6: Final Testing & Documentation**

**Tasks:**
- [ ] End-to-end testing
  - [ ] Test with 5+ real job postings
  - [ ] Test all file formats (PDF, DOCX, TXT)
  - [ ] Test paste text workflow
  - [ ] Test error scenarios
- [ ] Performance verification
  - [ ] Processing time <10 seconds
  - [ ] UI remains responsive
  - [ ] No memory leaks
- [ ] Error handling improvements
  - [ ] Better error messages
  - [ ] Graceful degradation
  - [ ] User-friendly warnings
- [ ] Documentation
  - [ ] Update user guide
  - [ ] Add "How to use job analysis" section
  - [ ] Document scoring methodology
  - [ ] API documentation for services
- [ ] Code cleanup
  - [ ] Remove debug logging
  - [ ] Add docstrings
  - [ ] Type hints verification
- [ ] Update CLAUDE.md with Phase 4 info
- [ ] Update status_report.md

**Deliverable:** Production-ready Phase 4 feature

**Files Updated:**
- `docs/user_guide.md` (new/updated)
- `docs/development/scoring_methodology.md`
- `CLAUDE.md`
- `docs/development/status_report.md`

---

## Total Effort Breakdown

| Phase | Description | Hours | Week |
|-------|-------------|-------|------|
| 4.1 | File Parsing | 5-6 | 1 |
| 4.2 | NLP Analysis (with AI) | 8-10 | 2 |
| 4.3 | Matching Engine | 10-12 | 3 |
| 4.4 | Resume Generation & DB | 5-6 | 4 |
| 4.5 | UI Integration | 8-10 | 5 |
| 4.6 | Testing & Polish | 3-4 | 6 |

**Total: 33-37 hours** (approximately 5-6 weeks part-time)

---

## What's Included vs Deferred

### ✅ Included in This Phase

**Core Features:**
- Complete file parsing (PDF, DOCX, TXT, paste)
- AI-powered requirements extraction (spaCy + Claude)
- Full matching engine with all 4 components
- Basic resume generation with selection
- Skill coverage analysis
- Gap identification
- Recommendations
- Complete UI flow (upload → results)
- Error handling and testing

**AI Integration:**
- Claude API for requirements extraction
- Merged results (spaCy + AI)
- Fallback to spaCy if AI fails
- Rate limit handling
- Cost-effective prompting

**Quality:**
- Unit tests for all services
- Integration tests
- End-to-end testing
- Documentation
- Error handling

### ⏸️ Deferred to Phase 4.5 (Future)

**Advanced Features:**
- Manual adjustment UI (drag-and-drop reorder)
- Custom skill mapping
- Advanced selection algorithms (diversity optimization)
- Multiple weight profiles (senior, career changer, etc.)
- Performance optimizations (caching, lazy loading)
- Batch processing (multiple jobs at once)
- Job comparison (which job am I best for?)
- Export results to spreadsheet

---

## Technical Decisions

### AI Integration Strategy

**Hybrid Approach (spaCy + AI):**
```python
def analyze_job_posting(text: str) -> JobRequirements:
    # Always run spaCy (fast, free)
    spacy_results = _extract_with_spacy(text)

    # Try AI if available (accurate, costs ~$0.01)
    try:
        ai_results = _extract_with_ai(text)
        # Merge: prefer AI for nuanced items, spaCy for entities
        return _merge_results(spacy_results, ai_results)
    except Exception as e:
        # Fallback to spaCy only
        logger.warning(f"AI extraction failed: {e}")
        return spacy_results
```

**Benefits:**
- Always works (spaCy fallback)
- High accuracy when AI available
- Reasonable costs (~$0.01 per analysis)
- User can disable AI in settings if desired

### Scoring Weights

**Keeping original weights:**
```python
WEIGHTS = {
    'skill_match': 0.4,    # Keyword matching
    'semantic': 0.3,       # Meaning similarity
    'recency': 0.2,        # Recent is better
    'metrics': 0.1         # Quantifiable impact
}
```

We can add alternative profiles in Phase 4.5 if needed.

### Database Schema

**New Tables:**
```sql
CREATE TABLE job_postings (
    id INTEGER PRIMARY KEY,
    profile_id INTEGER REFERENCES profiles(id),
    company_name VARCHAR(200),
    job_title VARCHAR(200),
    raw_text TEXT,
    cleaned_text TEXT,
    requirements_json TEXT,
    uploaded_at TIMESTAMP,
    analysis_method VARCHAR(50),
    confidence_score FLOAT
);

CREATE TABLE tailored_resumes (
    id INTEGER PRIMARY KEY,
    profile_id INTEGER REFERENCES profiles(id),
    job_posting_id INTEGER REFERENCES job_postings(id),
    selected_accomplishment_ids TEXT,  -- JSON array
    skill_coverage_json TEXT,
    gaps_json TEXT,
    created_at TIMESTAMP
);
```

---

## Success Criteria

### Phase 4 is Complete When:

**Functionality:**
- ✅ Users can upload PDF/DOCX/TXT job postings
- ✅ Paste text option works
- ✅ System extracts requirements with >80% accuracy (AI-assisted)
- ✅ All accomplishments scored correctly
- ✅ Top 20-30 items selected intelligently
- ✅ Skill coverage calculated and displayed
- ✅ Gaps identified with recommendations
- ✅ Results screen shows clear information
- ✅ Can proceed to PDF generation (Review screen)

**Performance:**
- ✅ Processing time <10 seconds
- ✅ UI stays responsive
- ✅ No crashes or major bugs

**Quality:**
- ✅ All services have unit tests
- ✅ Integration tests pass
- ✅ End-to-end workflow tested
- ✅ Error handling comprehensive
- ✅ Documentation complete

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| AI API costs exceed budget | User can disable AI, use spaCy only; cache results |
| PDF parsing fails | Provide paste text fallback; test diverse samples |
| Matching accuracy low | Manual review of top results; iterative tuning |
| Performance issues | Profile and optimize; add caching where needed |
| API rate limits | Exponential backoff; queue requests; clear errors |

---

## Next Steps

1. ✅ Review and approve this plan
2. ✅ Verify dependencies installed
3. ✅ Download test job postings (5-10 samples)
4. Start Phase 4.1: File Parsing
5. Commit progress after each phase

---

## Notes

- **Balanced Approach:** Includes AI for accuracy, skips advanced UI for speed
- **Timeline Realistic:** 35 hours = ~6 hours/week for 6 weeks (part-time sustainable)
- **Iterative:** Can ship after each phase if needed
- **Extensible:** Phase 4.5 can add advanced features without breaking existing code

Ready to begin Phase 4.1: File Parsing!
