# Phase 4: Job Posting Analysis - Implementation Plan

**Date:** November 13, 2025
**Status:** Planning
**Target Completion:** TBD

---

## Overview

Phase 4 implements the core intelligence pipeline that transforms the Adaptive Resume Generator from a data management tool into an intelligent resume tailoring assistant. Users will upload job postings (PDF, DOCX, TXT, or paste text), and the system will analyze requirements, match them against stored experience, and automatically generate a tailored resume.

---

## Goals

### Primary Goals
1. **Job Posting Ingestion:** Support multiple input formats (PDF, DOCX, TXT, plain text)
2. **Requirement Extraction:** Parse and extract skills, qualifications, and key requirements
3. **Experience Matching:** Score user's accomplishments against job requirements
4. **Intelligent Tailoring:** Automatically select and highlight relevant experience
5. **Skill Gap Analysis:** Identify missing qualifications and suggest additions

### Secondary Goals
1. **User Control:** Allow manual overrides and adjustments
2. **Explainability:** Show why certain accomplishments were selected
3. **Performance:** Process job postings in <5 seconds
4. **Accuracy:** >80% relevance in top recommendations

---

## Architecture

### High-Level Flow

```
┌─────────────────┐
│  User Uploads   │
│  Job Posting    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  File Parser    │ ← PDF, DOCX, TXT extraction
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Text Cleaner   │ ← Normalize, remove boilerplate
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  NLP Analyzer   │ ← Extract skills, requirements
│  (spaCy + AI)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Matching       │ ← Score user's accomplishments
│  Engine         │    against requirements
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Resume         │ ← Select top N accomplishments
│  Generator      │    per role/company
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Preview &      │ ← Show tailored resume
│  Adjust         │    with explanations
└─────────────────┘
```

### Component Breakdown

#### 1. File Parser Service (`services/job_posting_parser.py`)
**Purpose:** Extract raw text from various file formats

**Dependencies:**
- `pypdf` or `PyPDF2` for PDF parsing
- `python-docx` for DOCX parsing
- Built-in for TXT

**Methods:**
- `parse_file(file_path: str) -> str` - Main entry point
- `_parse_pdf(file_path: str) -> str`
- `_parse_docx(file_path: str) -> str`
- `_parse_txt(file_path: str) -> str`

**Error Handling:**
- Unsupported file format → Friendly error message
- Corrupted files → Fallback to partial extraction
- Empty content → Prompt user to paste text manually

---

#### 2. Text Cleaner (`services/text_cleaner.py`)
**Purpose:** Normalize job posting text

**Operations:**
- Remove boilerplate (EOE statements, apply instructions)
- Normalize whitespace
- Fix encoding issues
- Preserve section headers (Requirements, Qualifications, etc.)

**Methods:**
- `clean_job_posting(raw_text: str) -> str`
- `_remove_boilerplate(text: str) -> str`
- `_normalize_whitespace(text: str) -> str`

---

#### 3. NLP Analyzer (`services/nlp_analyzer.py`)
**Purpose:** Extract structured requirements from job posting

**Two-Tier Approach:**

**Tier 1: spaCy (Fast, Local)**
- Named Entity Recognition (skills, tools, frameworks)
- Part-of-speech tagging
- Dependency parsing
- Pre-trained word embeddings for similarity

**Tier 2: AI Enhancement (Optional, Accurate)**
- Use Claude API to extract:
  - Required skills (must-have)
  - Preferred skills (nice-to-have)
  - Years of experience requirements
  - Education requirements
  - Key responsibilities
  - Company culture indicators

**Output Structure:**
```python
@dataclass
class JobRequirements:
    required_skills: List[str]
    preferred_skills: List[str]
    years_experience: Optional[int]
    education_level: Optional[str]
    key_responsibilities: List[str]
    raw_sections: Dict[str, str]  # For reference
    confidence_score: float
```

**Methods:**
- `analyze_job_posting(text: str, use_ai: bool = True) -> JobRequirements`
- `_extract_with_spacy(text: str) -> JobRequirements`
- `_extract_with_ai(text: str) -> JobRequirements`
- `_merge_results(spacy_result, ai_result) -> JobRequirements`

---

#### 4. Matching Engine (`services/matching_engine.py`)
**Purpose:** Score user's accomplishments against job requirements

**Scoring Algorithm:**

```
Final Score = (
    0.4 × Skill Match Score +
    0.3 × Semantic Similarity +
    0.2 × Recency Bonus +
    0.1 × Achievement Metrics
)
```

**Skill Match Score:**
- Direct keyword match: 1.0
- Synonym match (spaCy): 0.8
- Related technology (ML model): 0.6
- No match: 0.0

**Semantic Similarity:**
- spaCy word embeddings (cosine similarity)
- Sentence-level comparison between accomplishment and job responsibilities

**Recency Bonus:**
- Current role: 1.0
- Within 2 years: 0.8
- Within 5 years: 0.6
- Older: 0.4

**Achievement Metrics:**
- Has numbers (%, $, X increase): +0.2
- Action verb start: +0.1
- Impact statement: +0.1

**Methods:**
- `match_profile_to_job(profile_id: int, job_requirements: JobRequirements) -> List[ScoredAccomplishment]`
- `_score_accomplishment(bullet: BulletPoint, requirements: JobRequirements) -> float`
- `_calculate_skill_match(bullet_text: str, required_skills: List[str]) -> float`
- `_calculate_semantic_similarity(bullet_text: str, job_text: str) -> float`

---

#### 5. Resume Generator (`services/resume_generator.py`)
**Purpose:** Create tailored resume data structure

**Selection Strategy:**
- Top 5-7 accomplishments per role
- Must include at least 1 accomplishment per company (if relevant)
- Prioritize current role (70% of selections)
- Ensure skill coverage (every required skill mentioned at least once)

**Output:**
```python
@dataclass
class TailoredResume:
    profile_id: int
    job_requirements: JobRequirements
    selected_accomplishments: List[ScoredAccomplishment]
    skill_coverage: Dict[str, bool]  # Which required skills are covered
    gaps: List[str]  # Skills not covered by experience
    recommendations: List[str]  # Suggested additions
```

**Methods:**
- `generate_tailored_resume(profile_id: int, job_requirements: JobRequirements) -> TailoredResume`
- `_select_top_accomplishments(scored: List[ScoredAccomplishment]) -> List[ScoredAccomplishment]`
- `_analyze_skill_coverage(selected: List, required: List[str]) -> Dict[str, bool]`
- `_generate_recommendations(gaps: List[str]) -> List[str]`

---

## Data Model Changes

### New Models

#### JobPosting
```python
class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    company_name = Column(String(200), nullable=False)
    job_title = Column(String(200), nullable=False)
    raw_text = Column(Text, nullable=False)
    cleaned_text = Column(Text)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Extracted requirements (JSON)
    requirements_json = Column(Text)  # Serialized JobRequirements

    # Analysis metadata
    analysis_method = Column(String(50))  # "spacy", "ai", "hybrid"
    confidence_score = Column(Float)

    # Relationships
    profile = relationship("Profile", back_populates="job_postings")
    tailored_resumes = relationship("TailoredResume", back_populates="job_posting")
```

#### TailoredResume
```python
class TailoredResume(Base):
    __tablename__ = "tailored_resumes"

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"))

    # Selected accomplishments (JSON array of IDs with scores)
    selected_accomplishment_ids = Column(Text)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    skill_coverage_json = Column(Text)
    gaps_json = Column(Text)

    # Relationships
    profile = relationship("Profile", back_populates="tailored_resumes")
    job_posting = relationship("JobPosting", back_populates="tailored_resumes")
```

### Migrations Required
- Add `job_postings` table
- Add `tailored_resumes` table
- Add relationships to Profile model

---

## UI Changes

### Upload Job Posting Screen
**Current State:** Placeholder with disabled buttons

**New Implementation:**
1. **File Upload:**
   - Enable "Browse Files" button
   - Implement drag-and-drop handler
   - Show file info (name, size, type)

2. **Text Paste:**
   - Enable "Paste Text" button
   - Open dialog with large text area
   - Auto-detect and clean pasted content

3. **Processing:**
   - Show progress indicator during analysis
   - Display extracted requirements for review
   - Allow manual editing of extracted requirements

4. **Results:**
   - Navigate to new "Tailoring Results" screen
   - Show matched accomplishments with scores
   - Highlight skill gaps

### New Screen: Tailoring Results
**Location:** Between Upload and Review screens

**Layout:**
```
┌─────────────────────────────────────────┐
│  Tailoring Results                      │
├─────────────────────────────────────────┤
│  Job: Senior Software Engineer          │
│  Company: Acme Corp                     │
│  Match Score: 85%                       │
├──────────────────┬──────────────────────┤
│ Requirements     │ Your Experience      │
│ ───────────────  │ ──────────────────  │
│ ✓ Python (5y)    │ ✓ 7 years Python    │
│ ✓ React          │ ✓ 3 years React     │
│ ⚠ AWS            │ ⚠ Limited AWS       │
│ ✗ Kubernetes     │ ✗ Not mentioned     │
├──────────────────┴──────────────────────┤
│ Selected Accomplishments (12)           │
│ ─────────────────────────────────────  │
│ [Score: 0.95] Built Python ETL...      │
│ [Score: 0.89] Developed React...       │
│ [Score: 0.82] Optimized database...    │
├─────────────────────────────────────────┤
│ [Adjust Selection] [Preview Resume]    │
└─────────────────────────────────────────┘
```

---

## Dependencies

### Required Packages
```toml
# Add to pyproject.toml [project.optional-dependencies]

job-analysis = [
    "pypdf>=3.17.0",           # PDF parsing
    "python-docx>=1.1.0",      # DOCX parsing
    "spacy>=3.6.0",            # NLP analysis
    "scikit-learn>=1.3.0",     # Similarity scoring
    "anthropic>=0.7.0",        # Optional AI enhancement
]
```

### spaCy Model
```bash
# Download English language model
python -m spacy download en_core_web_md
```

---

## Implementation Phases

### Phase 4.1: File Parsing (Week 1)
**Estimate:** 4-6 hours

- [ ] Create `JobPostingParser` service
- [ ] Implement PDF parsing
- [ ] Implement DOCX parsing
- [ ] Implement text paste functionality
- [ ] Add file upload to UI
- [ ] Add error handling and validation
- [ ] Write unit tests

**Deliverable:** Users can upload job postings and see raw text

---

### Phase 4.2: NLP Analysis (Week 1-2)
**Estimate:** 8-10 hours

- [ ] Create `NLPAnalyzer` service
- [ ] Implement spaCy-based extraction
- [ ] Implement AI-based extraction (optional)
- [ ] Create `JobRequirements` data model
- [ ] Add requirements preview UI
- [ ] Write unit tests with sample job postings
- [ ] Optimize performance (<5 sec analysis)

**Deliverable:** Extract and display job requirements

---

### Phase 4.3: Matching Engine (Week 2-3)
**Estimate:** 10-12 hours

- [ ] Create `MatchingEngine` service
- [ ] Implement skill matching algorithm
- [ ] Implement semantic similarity scoring
- [ ] Add recency and achievement bonuses
- [ ] Create scoring test suite
- [ ] Tune weights based on test data
- [ ] Document scoring methodology

**Deliverable:** Score accomplishments against job requirements

---

### Phase 4.4: Resume Generation (Week 3)
**Estimate:** 6-8 hours

- [ ] Create `ResumeGenerator` service
- [ ] Implement selection algorithm
- [ ] Analyze skill coverage
- [ ] Generate gap analysis
- [ ] Create recommendations engine
- [ ] Add data models (JobPosting, TailoredResume)
- [ ] Create Alembic migration

**Deliverable:** Generate tailored resume data structure

---

### Phase 4.5: UI Integration (Week 4)
**Estimate:** 8-10 hours

- [ ] Create `TailoringResultsScreen`
- [ ] Wire up file upload handlers
- [ ] Add progress indicators
- [ ] Implement requirements editor
- [ ] Show matched accomplishments with scores
- [ ] Display skill coverage and gaps
- [ ] Add manual adjustment controls
- [ ] Connect to Review & Print workflow

**Deliverable:** Complete user workflow from upload to tailored resume

---

### Phase 4.6: Polish & Testing (Week 4)
**Estimate:** 6-8 hours

- [ ] End-to-end testing with real job postings
- [ ] Performance optimization
- [ ] Error handling improvements
- [ ] User feedback collection
- [ ] Documentation updates
- [ ] Tutorial/help text

**Deliverable:** Production-ready Phase 4 feature

---

## Total Estimated Effort

**Time:** 42-54 hours (approximately 1-1.5 months part-time)

**Breakdown:**
- Phase 4.1: 4-6 hours
- Phase 4.2: 8-10 hours
- Phase 4.3: 10-12 hours
- Phase 4.4: 6-8 hours
- Phase 4.5: 8-10 hours
- Phase 4.6: 6-8 hours

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| PDF parsing fails on complex formats | High | Medium | Provide manual paste fallback, test with diverse samples |
| AI API costs too high | Medium | Low | Make AI optional, use spaCy as default, cache results |
| Matching accuracy below expectations | High | Medium | Manual override controls, user feedback loop, iterative tuning |
| Performance issues with large profiles | Medium | Low | Pagination, lazy loading, database indexing |
| spaCy model too large for distribution | Low | Low | Document separate download, provide instructions |

---

## Success Metrics

### Phase 4 Complete When:
- ✅ Users can upload PDF/DOCX/TXT job postings
- ✅ System extracts requirements with >70% accuracy
- ✅ Matching engine scores accomplishments
- ✅ Tailored resumes show clear skill coverage
- ✅ Processing time <5 seconds
- ✅ User can manually adjust selections
- ✅ Skill gaps clearly identified
- ✅ All changes tested and documented

### User Value Delivered:
- 10x faster resume tailoring (5 min → 30 sec)
- Higher quality matches than manual selection
- Clear visibility into skill gaps
- Confidence in application materials

---

## Future Enhancements (Post-Phase 4)

1. **Machine Learning:**
   - Train custom model on user's accepted/rejected recommendations
   - Personalized scoring weights per user
   - Industry-specific models

2. **Advanced Features:**
   - Multi-job comparison (which job am I best suited for?)
   - Cover letter generation based on requirements
   - LinkedIn profile optimization
   - Interview prep based on job requirements

3. **Integration:**
   - Browser extension to capture job postings
   - ATS format export
   - LinkedIn import of experience

---

## References

- [Intelligence Pipeline Architecture](../architecture/intelligence_pipeline.md)
- [Product Overview](../product/overview.md)
- [UI Complete Specification](../design/ui_complete_specification.md)
- [Status Report](status_report.md)

---

## Next Steps

1. Review and approve this plan
2. Install required dependencies (`pip install -e .[job-analysis]`)
3. Download spaCy model (`python -m spacy download en_core_web_md`)
4. Begin Phase 4.1: File Parsing
5. Set up test data (sample job postings)
