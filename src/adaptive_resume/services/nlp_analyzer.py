"""NLP-based job posting analyzer service.

This module provides functionality to extract structured requirements from job
postings using a hybrid approach: spaCy for fast entity extraction and Claude AI
for nuanced understanding.
"""

from typing import List, Optional, Dict, Set
from dataclasses import dataclass, field
import re
import logging
import json

# spaCy for NLP
try:
    import spacy
    from spacy.tokens import Doc
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

# Anthropic for AI extraction
from anthropic import Anthropic
from adaptive_resume.config.settings import Settings

logger = logging.getLogger(__name__)


@dataclass
class JobRequirements:
    """Structured representation of job posting requirements.

    Attributes:
        required_skills: List of must-have skills
        preferred_skills: List of nice-to-have skills
        years_experience: Minimum years of experience required
        education_level: Required education level (e.g., "Bachelor's", "Master's")
        key_responsibilities: List of main job responsibilities
        confidence_score: Confidence in extraction accuracy (0.0-1.0)
        raw_sections: Dictionary of identified text sections
        extraction_method: Method used for extraction ("spacy", "ai", "hybrid")
    """
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    years_experience: Optional[int] = None
    education_level: Optional[str] = None
    key_responsibilities: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    raw_sections: Dict[str, str] = field(default_factory=dict)
    extraction_method: str = "unknown"


class NLPAnalyzerError(Exception):
    """Base exception for NLP analyzer errors."""
    pass


class NLPAnalyzer:
    """Service for analyzing job postings and extracting requirements.

    Uses a hybrid approach combining spaCy's fast NLP with Claude AI's
    nuanced understanding for optimal accuracy.

    Attributes:
        nlp: spaCy language model (if available)
        ai_service_enabled: Whether AI extraction is available
        api_key: Anthropic API key (optional)
    """

    # Common skill keywords and patterns
    SKILL_KEYWORDS = {
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'go', 'rust',
        'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
        'react', 'vue', 'angular', 'django', 'flask', 'fastapi', 'spring', 'express',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins',
        'git', 'github', 'gitlab', 'jira', 'agile', 'scrum', 'ci/cd',
        'machine learning', 'deep learning', 'nlp', 'computer vision', 'ai',
        'rest', 'graphql', 'microservices', 'api', 'linux', 'unix',
    }

    # Years of experience patterns
    EXPERIENCE_PATTERNS = [
        r'(\d+)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)',
        r'(?:experience|exp).*?(\d+)\+?\s*(?:years?|yrs?)',
        r'(\d+)\+?\s*(?:years?|yrs?)',
    ]

    # Education level keywords
    EDUCATION_LEVELS = {
        "bachelor's": ["bachelor", "bs", "ba", "b.s.", "b.a."],
        "master's": ["master", "ms", "ma", "m.s.", "m.a.", "mba"],
        "phd": ["phd", "ph.d.", "doctorate", "doctoral"],
        "associate": ["associate", "as", "a.s.", "aa", "a.a."],
    }

    # AI extraction prompt template
    AI_EXTRACTION_PROMPT = """Analyze this job posting and extract structured information.

Job Posting:
{job_text}

Extract the following information and return ONLY a JSON object (no markdown, no explanations):

{{
  "required_skills": ["list", "of", "required", "skills"],
  "preferred_skills": ["list", "of", "preferred", "skills"],
  "years_experience": 5,
  "education_level": "Bachelor's degree",
  "key_responsibilities": ["list", "of", "main", "responsibilities"]
}}

Guidelines:
- required_skills: Skills explicitly marked as "required", "must have", or in a "requirements" section
- preferred_skills: Skills marked as "preferred", "nice to have", "bonus", or "plus"
- years_experience: Minimum years mentioned (use the number only, or null if not specified)
- education_level: Required degree level (or null if not specified)
- key_responsibilities: Main job duties (keep to 5-7 most important ones)
- Be specific with technology names (e.g., "React" not just "frontend framework")
- Separate similar technologies (e.g., ["Python", "Django"] not ["Python/Django"])
- Only include information explicitly stated in the posting

Return ONLY the JSON object, nothing else."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "en_core_web_md"):
        """Initialize NLP analyzer with optional AI support.

        Args:
            api_key: Optional Anthropic API key for AI-enhanced extraction
            model_name: spaCy model name to use (default: en_core_web_md)
        """
        self.model_name = model_name
        self.nlp = None
        self.spacy_available = SPACY_AVAILABLE

        # Initialize spaCy if available
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load(model_name)
                logger.info(f"Loaded spaCy model: {model_name}")
            except OSError:
                logger.warning(
                    f"spaCy model '{model_name}' not found. "
                    "Install with: python -m spacy download en_core_web_md"
                )
                self.spacy_available = False

        # Initialize AI service
        self.settings = Settings()
        self.api_key = api_key or self.settings.get_api_key()
        self.ai_service_enabled = bool(self.api_key) and self.settings.get('ai_enhancement_enabled', True)

        if self.ai_service_enabled:
            self.client = Anthropic(api_key=self.api_key)
            logger.info("AI extraction enabled")
        else:
            self.client = None
            logger.info("AI extraction disabled (using spaCy only)")

    def analyze(self, job_text: str, use_ai: bool = True) -> JobRequirements:
        """Analyze job posting and extract structured requirements.

        Uses a hybrid approach: always runs spaCy (fast), then optionally
        enhances with AI for better accuracy.

        Args:
            job_text: Cleaned job posting text
            use_ai: Whether to use AI enhancement (default: True)

        Returns:
            JobRequirements object with extracted information

        Raises:
            NLPAnalyzerError: If analysis fails completely
        """
        if not job_text or not job_text.strip():
            raise NLPAnalyzerError("Job text is empty")

        # Always try spaCy extraction first (fast, free, offline)
        spacy_results = self._extract_with_spacy(job_text)

        # Try AI extraction if enabled and requested
        if use_ai and self.ai_service_enabled:
            try:
                ai_results = self._extract_with_ai(job_text)
                # Merge results, preferring AI for nuanced distinctions
                merged_results = self._merge_results(spacy_results, ai_results)
                merged_results.extraction_method = "hybrid"
                return merged_results
            except Exception as e:
                logger.warning(f"AI extraction failed, falling back to spaCy: {e}")
                spacy_results.extraction_method = "spacy"
                return spacy_results
        else:
            spacy_results.extraction_method = "spacy"
            return spacy_results

    def _extract_with_spacy(self, job_text: str) -> JobRequirements:
        """Extract requirements using spaCy NLP.

        Fast, rule-based extraction using entity recognition and patterns.

        Args:
            job_text: Job posting text

        Returns:
            JobRequirements with spaCy-extracted information
        """
        if not self.spacy_available or not self.nlp:
            # Return minimal results if spaCy not available
            return JobRequirements(
                confidence_score=0.3,
                extraction_method="fallback"
            )

        # Process text with spaCy
        doc = self.nlp(job_text)

        # Extract skills using keyword matching and NER
        skills = self._extract_skills_spacy(doc, job_text)

        # Extract years of experience
        years_exp = self._extract_years_experience(job_text)

        # Extract education level
        education = self._extract_education_level(job_text)

        # Extract responsibilities (sentences with action verbs)
        responsibilities = self._extract_responsibilities_spacy(doc)

        # Identify sections in raw text
        sections = self._identify_sections(job_text)

        # Calculate confidence based on what we found
        confidence = self._calculate_spacy_confidence(skills, years_exp, education, responsibilities)

        return JobRequirements(
            required_skills=skills.get('required', []),
            preferred_skills=skills.get('preferred', []),
            years_experience=years_exp,
            education_level=education,
            key_responsibilities=responsibilities,
            confidence_score=confidence,
            raw_sections=sections,
            extraction_method="spacy"
        )

    def _extract_skills_spacy(self, doc: Doc, job_text: str) -> Dict[str, List[str]]:
        """Extract skills using spaCy and keyword matching.

        Args:
            doc: spaCy processed document
            job_text: Original job text

        Returns:
            Dictionary with 'required' and 'preferred' skill lists
        """
        all_skills: Set[str] = set()
        text_lower = job_text.lower()

        # Method 1: Keyword matching
        for skill in self.SKILL_KEYWORDS:
            # Use word boundaries for better matching
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                all_skills.add(skill.title())

        # Method 2: Entity recognition (ORG, PRODUCT for technologies)
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'PRODUCT', 'GPE']:
                # Check if it might be a technology/skill
                ent_text = ent.text.strip()
                if len(ent_text) > 2 and ent_text.lower() not in ['we', 'our', 'the', 'you']:
                    all_skills.add(ent_text)

        # Method 3: Noun chunks that might be skills
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.strip().lower()
            if any(tech in chunk_text for tech in ['development', 'programming', 'framework', 'database']):
                all_skills.add(chunk.text.strip())

        # Split into required vs preferred based on context
        required_skills = []
        preferred_skills = []

        for skill in all_skills:
            # Simple heuristic: if mentioned in "preferred" section, mark as preferred
            if self._is_in_preferred_section(skill, text_lower):
                preferred_skills.append(skill)
            else:
                required_skills.append(skill)

        return {
            'required': sorted(required_skills),
            'preferred': sorted(preferred_skills)
        }

    def _extract_years_experience(self, job_text: str) -> Optional[int]:
        """Extract years of experience requirement.

        Args:
            job_text: Job posting text

        Returns:
            Number of years required, or None if not found
        """
        text_lower = job_text.lower()

        for pattern in self.EXPERIENCE_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    years = int(match.group(1))
                    if 0 < years <= 50:  # Sanity check
                        return years
                except (ValueError, IndexError):
                    continue

        return None

    def _extract_education_level(self, job_text: str) -> Optional[str]:
        """Extract education level requirement.

        Args:
            job_text: Job posting text

        Returns:
            Education level string, or None if not found
        """
        text_lower = job_text.lower()

        # Check for each education level
        for level, keywords in self.EDUCATION_LEVELS.items():
            for keyword in keywords:
                # Handle periods in abbreviations like "b.s." or "m.s."
                pattern = r'\b' + re.escape(keyword).replace(r'\.', r'\.?') + r'\b'
                if re.search(pattern, text_lower):
                    return level.title()

        return None

    def _extract_responsibilities_spacy(self, doc: Doc) -> List[str]:
        """Extract key responsibilities using spaCy.

        Args:
            doc: spaCy processed document

        Returns:
            List of responsibility statements
        """
        responsibilities = []

        # Action verbs commonly used in job responsibilities
        action_verbs = {
            'develop', 'design', 'implement', 'build', 'create', 'maintain',
            'manage', 'lead', 'collaborate', 'work', 'write', 'test',
            'deploy', 'optimize', 'improve', 'analyze', 'ensure', 'support'
        }

        for sent in doc.sents:
            sent_text = sent.text.strip()
            # Look for sentences starting with action verbs
            if sent.root.lemma_.lower() in action_verbs:
                if 20 < len(sent_text) < 200:  # Reasonable length
                    responsibilities.append(sent_text)

        # Limit to top 7 responsibilities
        return responsibilities[:7]

    def _identify_sections(self, job_text: str) -> Dict[str, str]:
        """Identify common sections in job posting.

        Args:
            job_text: Job posting text

        Returns:
            Dictionary mapping section names to text content
        """
        sections = {}
        lines = job_text.split('\n')

        current_section = 'general'
        current_content = []

        section_markers = {
            'requirements': ['requirements', 'qualifications', 'required skills', 'must have'],
            'preferred': ['preferred', 'nice to have', 'bonus', 'plus'],
            'responsibilities': ['responsibilities', 'duties', 'you will', 'role'],
            'benefits': ['benefits', 'we offer', 'perks', 'compensation'],
        }

        for line in lines:
            line_lower = line.lower().strip()

            # Check if this line is a section header
            matched_section = None
            for section_name, markers in section_markers.items():
                if any(marker in line_lower for marker in markers):
                    matched_section = section_name
                    break

            if matched_section:
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = matched_section
                current_content = []
            else:
                current_content.append(line)

        # Save final section
        if current_content:
            sections[current_section] = '\n'.join(current_content)

        return sections

    def _is_in_preferred_section(self, skill: str, job_text_lower: str) -> bool:
        """Check if skill appears in a 'preferred' section.

        Args:
            skill: Skill name
            job_text_lower: Lowercased job text

        Returns:
            True if skill is in preferred section
        """
        # Simple heuristic: look for preferred markers near the skill
        context_window = 200  # characters
        skill_lower = skill.lower()

        preferred_markers = ['preferred', 'nice to have', 'bonus', 'plus', 'desired']

        skill_pos = job_text_lower.find(skill_lower)
        if skill_pos == -1:
            return False

        # Check context around the skill
        start = max(0, skill_pos - context_window)
        end = min(len(job_text_lower), skill_pos + context_window)
        context = job_text_lower[start:end]

        return any(marker in context for marker in preferred_markers)

    def _calculate_spacy_confidence(
        self,
        skills: Dict[str, List[str]],
        years_exp: Optional[int],
        education: Optional[str],
        responsibilities: List[str]
    ) -> float:
        """Calculate confidence score for spaCy extraction.

        Args:
            skills: Extracted skills dictionary
            years_exp: Years of experience
            education: Education level
            responsibilities: Responsibilities list

        Returns:
            Confidence score (0.0-1.0)
        """
        score = 0.0

        # Skills found: +0.4
        if skills['required'] or skills['preferred']:
            skill_count = len(skills['required']) + len(skills['preferred'])
            score += min(0.4, skill_count * 0.06)

        # Years found: +0.2
        if years_exp is not None:
            score += 0.2

        # Education found: +0.2
        if education is not None:
            score += 0.2

        # Responsibilities found: +0.2
        if responsibilities:
            score += min(0.2, len(responsibilities) * 0.04)

        return min(1.0, score)

    def _extract_with_ai(self, job_text: str) -> JobRequirements:
        """Extract requirements using Claude AI.

        More accurate and nuanced than spaCy, but requires API key and costs money.

        Args:
            job_text: Job posting text

        Returns:
            JobRequirements with AI-extracted information

        Raises:
            Exception: If AI API call fails
        """
        if not self.ai_service_enabled or not self.client:
            raise NLPAnalyzerError("AI service not available")

        # Truncate very long postings to save costs
        max_length = 4000
        if len(job_text) > max_length:
            job_text = job_text[:max_length] + "\n[truncated...]"

        prompt = self.AI_EXTRACTION_PROMPT.format(job_text=job_text)

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse JSON response
            content = response.content[0].text
            content = content.replace('```json', '').replace('```', '').strip()

            data = json.loads(content)

            return JobRequirements(
                required_skills=data.get('required_skills', []),
                preferred_skills=data.get('preferred_skills', []),
                years_experience=data.get('years_experience'),
                education_level=data.get('education_level'),
                key_responsibilities=data.get('key_responsibilities', []),
                confidence_score=0.9,  # AI extraction is generally high confidence
                raw_sections={},
                extraction_method="ai"
            )

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Response content: {content if 'content' in locals() else 'N/A'}")
            raise NLPAnalyzerError(f"Failed to parse AI response: {e}") from e
        except Exception as e:
            logger.error(f"AI extraction error: {e}")
            raise NLPAnalyzerError(f"AI extraction failed: {e}") from e

    def _merge_results(
        self,
        spacy_results: JobRequirements,
        ai_results: JobRequirements
    ) -> JobRequirements:
        """Merge spaCy and AI results for best accuracy.

        Strategy:
        - Prefer AI for structured data (skills, education, years)
        - Combine and deduplicate skills from both sources
        - Use AI's responsibilities if available, otherwise spaCy's
        - Higher confidence score from hybrid approach

        Args:
            spacy_results: Results from spaCy extraction
            ai_results: Results from AI extraction

        Returns:
            Merged JobRequirements
        """
        # Merge required skills (deduplicate, case-insensitive)
        required_skills = self._merge_skill_lists(
            spacy_results.required_skills,
            ai_results.required_skills
        )

        # Merge preferred skills
        preferred_skills = self._merge_skill_lists(
            spacy_results.preferred_skills,
            ai_results.preferred_skills
        )

        # Prefer AI for years and education (more accurate parsing)
        years_exp = ai_results.years_experience or spacy_results.years_experience
        education = ai_results.education_level or spacy_results.education_level

        # Prefer AI responsibilities if available
        responsibilities = (
            ai_results.key_responsibilities
            if ai_results.key_responsibilities
            else spacy_results.key_responsibilities
        )

        # Use spaCy's section identification
        sections = spacy_results.raw_sections

        # Calculate hybrid confidence (average, with boost for agreement)
        confidence = (spacy_results.confidence_score + ai_results.confidence_score) / 2
        if spacy_results.years_experience == ai_results.years_experience:
            confidence += 0.05
        confidence = min(1.0, confidence)

        return JobRequirements(
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            years_experience=years_exp,
            education_level=education,
            key_responsibilities=responsibilities,
            confidence_score=confidence,
            raw_sections=sections,
            extraction_method="hybrid"
        )

    def _merge_skill_lists(self, list1: List[str], list2: List[str]) -> List[str]:
        """Merge two skill lists, removing duplicates (case-insensitive).

        Args:
            list1: First skill list
            list2: Second skill list

        Returns:
            Merged and deduplicated list
        """
        # Use case-insensitive deduplication
        skills_dict = {}

        for skill in list1 + list2:
            key = skill.lower()
            if key not in skills_dict:
                skills_dict[key] = skill

        return sorted(skills_dict.values())

    @property
    def is_spacy_available(self) -> bool:
        """Check if spaCy is available and loaded."""
        return self.spacy_available and self.nlp is not None

    @property
    def is_ai_available(self) -> bool:
        """Check if AI extraction is available."""
        return self.ai_service_enabled
