# ADR-0005: NLP and Matching Strategy

**Status:** Accepted  
**Date:** 2025-11-04  
**Deciders:** AlobarQuest

## Context

A core feature of the Adaptive Resume Generator is intelligently matching bullet points to job descriptions. When a user pastes a job description, the system should suggest the most relevant achievements from their work history.

### Requirements

**Functional:**
- User pastes job description text
- System analyzes text to understand required skills/experience
- System scores all available bullet points by relevance
- Returns ranked list of bullet points
- Explanation of why bullets were selected (optional)

**Performance:**
- Results in < 2 seconds for typical job descriptions
- Accurate enough to save user time
- Better than manual scanning

**Technical:**
- Works offline (desktop application)
- Reasonable memory footprint (< 500MB)
- No external API calls (privacy)
- Maintainable and upgradeable algorithm

## Decision

We will implement a **progressive sophistication approach**:

### Phase 1 (v1.0): TF-IDF + Tag Matching
- Keyword extraction from job description
- TF-IDF scoring of bullet points
- Tag-based filtering and boosting
- Simple, fast, explainable

### Phase 2 (v1.1+): spaCy NLP
- Named entity recognition
- Skill extraction
- Semantic similarity (word embeddings)
- Context-aware matching

### Phase 3 (v2.0+): Advanced ML (Optional)
- Fine-tuned transformer models
- User feedback learning
- Industry-specific models

## Phase 1 Implementation: TF-IDF + Tags

### Why Start Simple

**Advantages:**
- Fast to implement (fits Week 4 milestone)
- No large model downloads
- Low memory usage
- Fast execution (< 1 second)
- Explainable results
- No external dependencies

**Good Enough For:**
- 80% of matching needs
- Clear keyword matches
- Technical skills matching
- Industry buzzwords

### Algorithm

```python
class SimpleMatchingService:
    def match_bullets(self, job_description, all_bullets):
        # 1. Extract keywords from job description
        keywords = self.extract_keywords(job_description)
        
        # 2. Calculate TF-IDF scores
        vectorizer = TfidfVectorizer()
        job_vector = vectorizer.fit_transform([job_description])
        
        scores = []
        for bullet in all_bullets:
            # Calculate similarity score
            bullet_vector = vectorizer.transform([bullet.content])
            similarity = cosine_similarity(job_vector, bullet_vector)[0][0]
            
            # Boost score based on matching tags
            tag_boost = self.calculate_tag_boost(bullet, keywords)
            
            final_score = similarity * (1 + tag_boost)
            scores.append((bullet, final_score))
        
        # 3. Sort by score, return top matches
        return sorted(scores, key=lambda x: x[1], reverse=True)
```

### Keyword Extraction

**Simple approach:**
```python
def extract_keywords(self, text):
    # Remove common words
    stop_words = set(['the', 'a', 'an', 'in', 'on', 'at', ...])
    
    # Tokenize
    words = text.lower().split()
    
    # Filter and return
    keywords = [w for w in words if w not in stop_words]
    return keywords
```

**Better approach (using nltk):**
```python
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

def extract_keywords(self, text):
    # Tokenize
    tokens = word_tokenize(text.lower())
    
    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    keywords = [t for t in tokens if t not in stop_words]
    
    # Return most frequent terms
    freq = Counter(keywords)
    return [word for word, count in freq.most_common(50)]
```

### Tag-Based Boosting

Tags allow manual categorization:
```python
# Example tags on bullet points
bullet1.tags = ["python", "api-development", "backend"]
bullet2.tags = ["project-management", "agile", "leadership"]
bullet3.tags = ["aws", "cloud", "devops"]

def calculate_tag_boost(self, bullet, keywords):
    """Boost score if bullet tags match keywords"""
    matching_tags = sum(1 for tag in bullet.tags 
                       if tag in keywords)
    return matching_tags * 0.1  # 10% boost per matching tag
```

## Phase 2: spaCy Integration

### When to Upgrade

Upgrade to spaCy when:
- Phase 1 matching accuracy insufficient
- Users request better matching
- After v1.0 release and stabilization

### Why spaCy

**Advantages:**
- Production-ready NLP library
- Pre-trained models available
- Good performance (optimized C)
- Semantic similarity (word vectors)
- Named entity recognition
- Skill extraction capabilities

**Disadvantages:**
- Larger download (~100MB for models)
- Higher memory usage (~300MB)
- Slower initialization
- More complex

### Implementation

```python
import spacy

class SpacyMatchingService:
    def __init__(self):
        # Load English model with word vectors
        self.nlp = spacy.load("en_core_web_md")
    
    def match_bullets(self, job_description, all_bullets):
        # Parse job description
        job_doc = self.nlp(job_description)
        
        # Extract skills and entities
        skills = self.extract_skills(job_doc)
        
        scores = []
        for bullet in all_bullets:
            bullet_doc = self.nlp(bullet.content)
            
            # Semantic similarity using word vectors
            similarity = job_doc.similarity(bullet_doc)
            
            # Boost for matching skills
            skill_boost = self.calculate_skill_overlap(
                skills, bullet_doc
            )
            
            final_score = similarity * (1 + skill_boost)
            scores.append((bullet, final_score))
        
        return sorted(scores, key=lambda x: x[1], reverse=True)
    
    def extract_skills(self, doc):
        """Extract technical skills and key phrases"""
        # Use named entities and noun chunks
        entities = [ent.text for ent in doc.ents 
                   if ent.label_ in ['ORG', 'PRODUCT', 'TECH']]
        
        # Common technical skills
        tech_keywords = ['python', 'java', 'aws', 'docker', ...]
        found_skills = [token.text for token in doc 
                       if token.text.lower() in tech_keywords]
        
        return set(entities + found_skills)
```

### Skill Extraction

Build skill taxonomy:
```python
SKILL_TAXONOMY = {
    'programming': ['python', 'java', 'javascript', 'c++', ...],
    'frameworks': ['react', 'django', 'flask', 'spring', ...],
    'cloud': ['aws', 'azure', 'gcp', 'kubernetes', ...],
    'databases': ['postgresql', 'mongodb', 'redis', ...],
    'tools': ['git', 'docker', 'jenkins', 'jira', ...],
}

def extract_skills(self, text):
    """Extract skills from text using taxonomy"""
    text_lower = text.lower()
    found_skills = []
    
    for category, skills in SKILL_TAXONOMY.items():
        for skill in skills:
            if skill in text_lower:
                found_skills.append({
                    'skill': skill,
                    'category': category
                })
    
    return found_skills
```

## Alternatives Considered

### 1. Simple Keyword Matching
**Approach:** Just count keyword overlaps

**Pros:**
- Extremely simple
- Fast

**Cons:**
- Miss synonyms (e.g., "led" vs "managed")
- No semantic understanding
- Many false positives

**Verdict:** Too basic, TF-IDF is only slightly more complex but much better

### 2. BERT/Transformers
**Approach:** Use large language models for semantic matching

**Pros:**
- State-of-the-art accuracy
- Deep semantic understanding
- Context-aware

**Cons:**
- Requires GPU for reasonable speed
- Large model files (500MB - 3GB)
- High memory usage (> 2GB)
- Slow on CPU (5-10 seconds)
- Overkill for this task

**Verdict:** Too slow and heavy for desktop app, Phase 1 & 2 sufficient

### 3. Cloud NLP APIs (Google, AWS)
**Approach:** Send text to cloud for analysis

**Pros:**
- State-of-the-art models
- No local resources needed
- Always up-to-date

**Cons:**
- Requires internet connection
- Privacy concerns (sending resume data to cloud)
- API costs
- Latency
- Vendor lock-in

**Verdict:** Violates privacy requirement, unacceptable

### 4. Rule-Based Systems
**Approach:** Hand-crafted rules for matching

**Pros:**
- Complete control
- Explainable
- Fast

**Cons:**
- Labor-intensive to build
- Hard to maintain
- Doesn't scale to edge cases
- Requires domain expertise

**Verdict:** Good complement to ML, but not sufficient alone

## Implementation Strategy

### Phase 1 (Week 4)

**Day 1-2: Basic infrastructure**
- MatchingService class structure
- Text preprocessing utilities
- TF-IDF vectorization setup

**Day 3-4: Matching algorithm**
- Implement scoring function
- Tag-based boosting
- Result ranking and filtering

**Day 5: Testing and refinement**
- Unit tests with sample data
- Manual testing with real job descriptions
- Adjust scoring weights

**Day 6-7: GUI integration**
- Job description input widget
- Bullet point selection interface
- Score visualization (optional)

### Phase 2 (Post v1.0)

**After v1.0 release:**
- Collect user feedback on matching quality
- Identify common failure cases
- Implement spaCy integration
- A/B test against Phase 1
- Gradual rollout

### Data for Testing

**Create test corpus:**
- 50+ real job descriptions (various roles)
- User's complete work history
- Expected matches for each job description
- Measure precision/recall

## Scoring Refinement

### Weighted Factors

```python
def calculate_final_score(self, bullet, job_description):
    # Base TF-IDF similarity
    tfidf_score = self.calculate_tfidf_similarity(
        bullet.content, job_description
    )
    
    # Tag matching bonus
    tag_score = self.calculate_tag_match(bullet.tags, job_description)
    
    # Metrics bonus (quantified achievements rank higher)
    metrics_bonus = 0.1 if bullet.is_quantified else 0
    
    # Recency bonus (more recent experience often more relevant)
    recency_bonus = self.calculate_recency_bonus(bullet.job.end_date)
    
    # Combined score
    final_score = (
        tfidf_score * 0.6 +
        tag_score * 0.3 +
        metrics_bonus * 0.05 +
        recency_bonus * 0.05
    )
    
    return final_score
```

### Tuning Weights

Create test set and iterate:
1. Start with equal weights
2. Measure precision/recall
3. Adjust weights
4. Repeat until satisfactory

Target: 80%+ relevance in top 10 results

## Consequences

### Positive

**Phase 1:**
- Fast implementation (fits Week 4)
- Good accuracy for clear matches
- Low resource usage
- No dependencies beyond Python stdlib
- Fast execution (< 1 second)
- Easy to explain to users

**Phase 2:**
- Better accuracy with semantic understanding
- Handle synonyms and context
- More sophisticated skill extraction
- Industry-standard NLP

**Overall:**
- Progressive enhancement approach
- Ship faster with Phase 1
- Upgrade path clear
- Users benefit immediately

### Negative

**Phase 1 Limitations:**
- May miss semantic similarities
- Synonym matching limited
- Context understanding minimal
- May need manual tag management

**Phase 2 Trade-offs:**
- Larger application size
- Higher memory usage
- Slower initialization
- Model updates needed

### Risks and Mitigations

**Risk:** Phase 1 accuracy too low, users frustrated  
**Mitigation:** Enable manual re-ranking, collect feedback, prioritize Phase 2

**Risk:** spaCy models too large for download  
**Mitigation:** Optional download, offer lightweight version

**Risk:** Matching algorithm doesn't generalize across industries  
**Mitigation:** Allow users to adjust weights, customize tags

## Testing Strategy

### Unit Tests
```python
def test_keyword_extraction():
    text = "Senior Python Developer with AWS experience"
    keywords = extract_keywords(text)
    assert "python" in keywords
    assert "aws" in keywords
    assert "developer" in keywords

def test_matching_relevance():
    job_desc = "Looking for React developer"
    bullets = [
        Bullet("Built React applications"),
        Bullet("Managed Python backend"),
    ]
    results = match_bullets(job_desc, bullets)
    assert results[0][0].content == "Built React applications"
```

### Integration Tests
- Real job descriptions from various industries
- User's actual work history
- Measure top-K accuracy
- Collect qualitative feedback

### Performance Tests
- 1000+ bullet points
- Should complete in < 2 seconds
- Memory usage < 500MB

## Future Enhancements

### v1.1-1.5
- spaCy integration
- Better skill extraction
- Industry-specific models
- User feedback loop

### v2.0+
- Fine-tuned models on resume data
- Learn from user selections
- Collaborative filtering (if web version)
- Integration with job boards

## Review Criteria

Review Phase 1 after:
- Week 4 completion
- User feedback from v1.0
- Accuracy metrics from test set

Upgrade to Phase 2 if:
- Phase 1 accuracy < 70%
- Users consistently complain about matching
- Have bandwidth for enhancement

## References

- TF-IDF: https://en.wikipedia.org/wiki/Tf%E2%80%93idf
- spaCy: https://spacy.io/
- Cosine Similarity: https://en.wikipedia.org/wiki/Cosine_similarity
- NLTK: https://www.nltk.org/

## Notes

Progressive sophistication approach is ideal:
- **Ship fast:** Phase 1 is implementable in Week 4
- **Ship well:** TF-IDF + tags covers 80% of cases
- **Improve later:** Clear upgrade path to spaCy
- **Stay focused:** Don't over-engineer v1.0

User (AlobarQuest) with IT background will appreciate:
- Technical transparency
- Clear algorithmic approach
- Ability to customize weights
- Explainable results

The matching feature doesn't need to be perfect—it needs to be helpful. Saving users time scanning their own history is the goal, not achieving 100% accuracy.
