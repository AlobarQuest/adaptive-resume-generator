"""Matching engine for scoring accomplishments against job requirements.

This module implements a sophisticated matching algorithm that scores resume
bullet points against job posting requirements using multiple components:
- Skill matching (keyword + semantic)
- Semantic similarity (spaCy vectors)
- Recency (more recent = higher score)
- Achievement metrics (numbers, percentages, impact)
"""

from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import date, datetime
import re
import logging
import math

# spaCy for semantic similarity
try:
    import spacy
    from spacy.tokens import Doc
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

from adaptive_resume.services.nlp_analyzer import JobRequirements
from adaptive_resume.models.job import Job
from adaptive_resume.models.bullet_point import BulletPoint

logger = logging.getLogger(__name__)


@dataclass
class ScoredAccomplishment:
    """Scored accomplishment with detailed scoring breakdown.

    Attributes:
        bullet_id: Database ID of the bullet point
        bullet_text: The bullet point text
        job_title: Job title where this accomplishment occurred
        company_name: Company name
        final_score: Combined weighted score (0.0-1.0)
        skill_match_score: Skill matching component score
        semantic_score: Semantic similarity score
        recency_score: Recency component score
        metrics_score: Achievement metrics score
        matched_skills: List of skills that matched
        reasons: Human-readable reasons for selection
        job_start_date: Start date of the job
        is_current: Whether this is from current role
    """
    bullet_id: int
    bullet_text: str
    job_title: str = ""
    company_name: str = ""
    final_score: float = 0.0
    skill_match_score: float = 0.0
    semantic_score: float = 0.0
    recency_score: float = 0.0
    metrics_score: float = 0.0
    matched_skills: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    job_start_date: Optional[date] = None
    is_current: bool = False


class MatchingEngineError(Exception):
    """Base exception for matching engine errors."""
    pass


class MatchingEngine:
    """Service for matching accomplishments to job requirements.

    Uses a weighted scoring algorithm with four components:
    - Skill match (40%): Direct keyword and semantic skill matching
    - Semantic similarity (30%): Overall meaning similarity
    - Recency (20%): How recent the accomplishment is
    - Metrics (10%): Presence of quantifiable achievements

    Attributes:
        nlp: spaCy language model (if available)
        weights: Component weights for final score calculation
        technology_families: Mapping of tech to related technologies
    """

    # Component weights (must sum to 1.0)
    DEFAULT_WEIGHTS = {
        'skill_match': 0.4,
        'semantic': 0.3,
        'recency': 0.2,
        'metrics': 0.1
    }

    # Technology families for broader matching
    # e.g., if job mentions "React", also match "JavaScript"
    TECHNOLOGY_FAMILIES = {
        'react': {'javascript', 'js', 'frontend', 'web'},
        'vue': {'javascript', 'js', 'frontend', 'web'},
        'angular': {'javascript', 'typescript', 'frontend', 'web'},
        'django': {'python', 'web', 'backend'},
        'flask': {'python', 'web', 'backend'},
        'fastapi': {'python', 'web', 'backend'},
        'spring': {'java', 'backend'},
        'express': {'javascript', 'node', 'backend'},
        'postgresql': {'sql', 'database', 'rdbms'},
        'mysql': {'sql', 'database', 'rdbms'},
        'mongodb': {'database', 'nosql'},
        'redis': {'database', 'cache', 'nosql'},
        'kubernetes': {'docker', 'containers', 'devops', 'cloud'},
        'docker': {'containers', 'devops'},
        'aws': {'cloud', 'devops'},
        'azure': {'cloud', 'devops'},
        'gcp': {'cloud', 'devops'},
    }

    # Action verbs that indicate strong achievements
    ACTION_VERBS = {
        'developed', 'built', 'created', 'implemented', 'designed',
        'led', 'managed', 'architected', 'optimized', 'improved',
        'increased', 'decreased', 'reduced', 'enhanced', 'delivered',
        'launched', 'deployed', 'migrated', 'scaled', 'automated'
    }

    # Impact words that strengthen achievements
    IMPACT_WORDS = {
        'reduced', 'increased', 'improved', 'enhanced', 'optimized',
        'streamlined', 'accelerated', 'delivered', 'achieved', 'exceeded',
        'eliminated', 'saved', 'generated', 'boosted', 'transformed'
    }

    # Patterns for detecting metrics
    METRIC_PATTERNS = [
        r'\d+%',  # Percentages: 50%
        r'\$[\d,]+(?:\.\d{2})?[KMB]?',  # Money: $100K, $1.5M
        r'\d+[KMB]',  # Large numbers: 10K, 5M
        r'\d+x',  # Multipliers: 2x, 10x
        r'\d+\+',  # Plus numbers: 100+
        r'\d{1,3}(?:,\d{3})+',  # Comma-separated: 1,000
    ]

    def __init__(self, weights: Optional[Dict[str, float]] = None, model_name: str = "en_core_web_md"):
        """Initialize matching engine.

        Args:
            weights: Optional custom weights for scoring components
            model_name: spaCy model name to use (default: en_core_web_md)
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self.model_name = model_name
        self.nlp = None
        self.spacy_available = SPACY_AVAILABLE

        # Validate weights
        if not math.isclose(sum(self.weights.values()), 1.0, rel_tol=1e-5):
            raise MatchingEngineError(
                f"Weights must sum to 1.0, got {sum(self.weights.values())}"
            )

        # Initialize spaCy if available
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load(model_name)
                logger.info(f"Loaded spaCy model: {model_name}")
            except OSError:
                logger.warning(
                    f"spaCy model '{model_name}' not found. "
                    "Semantic scoring will be degraded."
                )
                self.spacy_available = False

        # Vector cache for performance
        self._vector_cache: Dict[str, any] = {}

    def score_accomplishments(
        self,
        accomplishments: List[Tuple[BulletPoint, Job]],
        requirements: JobRequirements,
        job_description_text: str = ""
    ) -> List[ScoredAccomplishment]:
        """Score a list of accomplishments against job requirements.

        Args:
            accomplishments: List of (BulletPoint, Job) tuples to score
            requirements: Extracted job requirements
            job_description_text: Full job description text for semantic matching

        Returns:
            List of ScoredAccomplishment objects, sorted by final_score (descending)
        """
        if not accomplishments:
            return []

        # Prepare job description vector once for semantic matching
        job_vector = self._get_or_cache_vector(job_description_text) if job_description_text else None

        # Prepare combined skills list
        all_required_skills = set(s.lower() for s in requirements.required_skills)
        all_preferred_skills = set(s.lower() for s in requirements.preferred_skills)
        all_skills = all_required_skills | all_preferred_skills

        scored = []
        for bullet, job in accomplishments:
            score = self._score_single_accomplishment(
                bullet, job, requirements, all_skills, job_vector
            )
            scored.append(score)

        # Sort by final score descending
        scored.sort(key=lambda x: x.final_score, reverse=True)

        return scored

    def _score_single_accomplishment(
        self,
        bullet: BulletPoint,
        job: Job,
        requirements: JobRequirements,
        all_skills: Set[str],
        job_vector: Optional[any]
    ) -> ScoredAccomplishment:
        """Score a single accomplishment.

        Args:
            bullet: BulletPoint to score
            job: Job where this bullet occurred
            requirements: Job requirements
            all_skills: Set of all skills (required + preferred)
            job_vector: Pre-computed job description vector

        Returns:
            ScoredAccomplishment with detailed scoring
        """
        # Calculate component scores
        skill_score, matched_skills = self._calculate_skill_match(bullet.bullet_text, all_skills)
        semantic_score = self._calculate_semantic_similarity(bullet.bullet_text, job_vector)
        recency_score = self._calculate_recency_score(job.start_date, job.is_current)
        metrics_score = self._calculate_metrics_score(bullet.bullet_text)

        # Calculate final weighted score
        final_score = (
            self.weights['skill_match'] * skill_score +
            self.weights['semantic'] * semantic_score +
            self.weights['recency'] * recency_score +
            self.weights['metrics'] * metrics_score
        )

        # Generate reasons
        reasons = self._generate_reasons(
            skill_score, semantic_score, recency_score, metrics_score,
            matched_skills, job.is_current
        )

        return ScoredAccomplishment(
            bullet_id=bullet.id,
            bullet_text=bullet.bullet_text,
            job_title=job.job_title,
            company_name=job.company_name,
            final_score=final_score,
            skill_match_score=skill_score,
            semantic_score=semantic_score,
            recency_score=recency_score,
            metrics_score=metrics_score,
            matched_skills=matched_skills,
            reasons=reasons,
            job_start_date=job.start_date,
            is_current=job.is_current
        )

    def _calculate_skill_match(self, bullet_text: str, required_skills: Set[str]) -> Tuple[float, List[str]]:
        """Calculate skill matching score.

        Uses three methods:
        1. Direct keyword matching (case-insensitive)
        2. Technology family matching (e.g., React -> JavaScript)
        3. Semantic similarity for synonyms (via spaCy)

        Args:
            bullet_text: Bullet point text
            required_skills: Set of required skill keywords (lowercase)

        Returns:
            Tuple of (score, matched_skills)
        """
        if not required_skills:
            return 0.0, []

        text_lower = bullet_text.lower()
        matched = []
        match_scores = []

        for skill in required_skills:
            skill_lower = skill.lower()

            # Method 1: Direct keyword match
            if self._skill_in_text(skill_lower, text_lower):
                matched.append(skill)
                match_scores.append(1.0)  # Perfect match
                continue

            # Method 2: Technology family match
            family_match = False
            if skill_lower in self.TECHNOLOGY_FAMILIES:
                family = self.TECHNOLOGY_FAMILIES[skill_lower]
                for family_member in family:
                    if self._skill_in_text(family_member, text_lower):
                        matched.append(skill)
                        match_scores.append(0.7)  # Partial match via family
                        family_match = True
                        break
            if family_match:
                continue

            # Method 3: Semantic similarity (if spaCy available)
            if self.spacy_available and self.nlp:
                similarity = self._calculate_skill_similarity(skill_lower, bullet_text)
                if similarity > 0.6:  # Threshold for semantic match
                    matched.append(skill)
                    match_scores.append(similarity * 0.8)  # Semantic match worth less

        # Calculate final score based on match quality and quantity
        if not match_scores:
            return 0.0, []

        # Average match quality, with bonus for matching many skills
        avg_quality = sum(match_scores) / len(match_scores)
        coverage = min(len(matched) / max(len(required_skills), 1), 1.0)

        # Combined score: 70% quality, 30% coverage
        final_score = 0.7 * avg_quality + 0.3 * coverage

        return min(final_score, 1.0), matched

    def _skill_in_text(self, skill: str, text: str) -> bool:
        """Check if skill keyword appears in text with word boundaries.

        Args:
            skill: Skill keyword (lowercase)
            text: Text to search (lowercase)

        Returns:
            True if skill found
        """
        # Use word boundaries for better matching
        pattern = r'\b' + re.escape(skill) + r'\b'
        return bool(re.search(pattern, text))

    def _calculate_skill_similarity(self, skill: str, bullet_text: str) -> float:
        """Calculate semantic similarity between skill and bullet text.

        Args:
            skill: Skill keyword
            bullet_text: Bullet point text

        Returns:
            Similarity score (0.0-1.0)
        """
        if not self.spacy_available or not self.nlp:
            return 0.0

        try:
            skill_doc = self.nlp(skill)
            bullet_doc = self.nlp(bullet_text)

            # Check if vectors are available
            if not skill_doc.has_vector or not bullet_doc.has_vector:
                return 0.0

            similarity = skill_doc.similarity(bullet_doc)
            return max(0.0, min(similarity, 1.0))

        except Exception as e:
            logger.debug(f"Skill similarity calculation failed: {e}")
            return 0.0

    def _calculate_semantic_similarity(self, bullet_text: str, job_vector: Optional[any]) -> float:
        """Calculate semantic similarity between bullet and job description.

        Args:
            bullet_text: Bullet point text
            job_vector: Pre-computed job description vector

        Returns:
            Similarity score (0.0-1.0)
        """
        if not self.spacy_available or not self.nlp or job_vector is None:
            return 0.0

        try:
            bullet_doc = self.nlp(bullet_text)

            if not bullet_doc.has_vector:
                return 0.0

            # Compute cosine similarity
            similarity = bullet_doc.similarity(job_vector)
            return max(0.0, min(similarity, 1.0))

        except Exception as e:
            logger.debug(f"Semantic similarity calculation failed: {e}")
            return 0.0

    def _calculate_recency_score(self, start_date: date, is_current: bool) -> float:
        """Calculate recency score with decay function.

        Current roles get maximum score. Past roles decay over time.

        Args:
            start_date: Job start date
            is_current: Whether this is a current role

        Returns:
            Recency score (0.0-1.0)
        """
        if is_current:
            return 1.0  # Current role = maximum recency

        if not start_date:
            return 0.3  # Unknown date = low score

        # Calculate years since start
        today = date.today()
        years_ago = (today - start_date).days / 365.25

        # Exponential decay: score = e^(-years/5)
        # This gives: 1 year ago = 0.82, 3 years = 0.55, 5 years = 0.37, 10 years = 0.13
        decay_rate = 5.0  # Half-life of 5 years
        score = math.exp(-years_ago / decay_rate)

        return max(0.0, min(score, 1.0))

    def _calculate_metrics_score(self, bullet_text: str) -> float:
        """Calculate achievement metrics score.

        Looks for:
        - Numbers, percentages, money values
        - Action verbs
        - Impact words

        Args:
            bullet_text: Bullet point text

        Returns:
            Metrics score (0.0-1.0)
        """
        score = 0.0
        text_lower = bullet_text.lower()

        # Check for quantifiable metrics (0.5 points)
        has_metrics = any(re.search(pattern, bullet_text) for pattern in self.METRIC_PATTERNS)
        if has_metrics:
            score += 0.5

        # Check for action verbs (0.25 points)
        words = text_lower.split()
        if any(verb in words for verb in self.ACTION_VERBS):
            score += 0.25

        # Check for impact words (0.25 points)
        if any(word in text_lower for word in self.IMPACT_WORDS):
            score += 0.25

        return min(score, 1.0)

    def _generate_reasons(
        self,
        skill_score: float,
        semantic_score: float,
        recency_score: float,
        metrics_score: float,
        matched_skills: List[str],
        is_current: bool
    ) -> List[str]:
        """Generate human-readable reasons for why item was scored.

        Args:
            skill_score: Skill match score
            semantic_score: Semantic similarity score
            recency_score: Recency score
            metrics_score: Metrics score
            matched_skills: List of matched skills
            is_current: Whether from current role

        Returns:
            List of reason strings
        """
        reasons = []

        # Skill matching
        if skill_score > 0.7:
            if len(matched_skills) == 1:
                reasons.append(f"Strong match for: {matched_skills[0]}")
            elif len(matched_skills) > 1:
                skills_str = ", ".join(matched_skills[:3])
                if len(matched_skills) > 3:
                    skills_str += f" +{len(matched_skills) - 3} more"
                reasons.append(f"Matches required skills: {skills_str}")
        elif skill_score > 0.4:
            reasons.append("Partial skill match")

        # Semantic similarity
        if semantic_score > 0.6:
            reasons.append("Closely related to job description")
        elif semantic_score > 0.4:
            reasons.append("Somewhat related to role")

        # Recency
        if is_current:
            reasons.append("Current role (most recent)")
        elif recency_score > 0.7:
            reasons.append("Recent experience")

        # Metrics
        if metrics_score > 0.7:
            reasons.append("Strong quantifiable achievements")
        elif metrics_score > 0.4:
            reasons.append("Contains measurable results")

        return reasons if reasons else ["General relevance"]

    def _get_or_cache_vector(self, text: str) -> Optional[any]:
        """Get or compute spaCy vector for text, with caching.

        Args:
            text: Text to vectorize

        Returns:
            spaCy Doc object, or None if unavailable
        """
        if not self.spacy_available or not self.nlp:
            return None

        # Check cache
        cache_key = text[:100]  # Use first 100 chars as key
        if cache_key in self._vector_cache:
            return self._vector_cache[cache_key]

        # Compute and cache
        try:
            doc = self.nlp(text)
            if doc.has_vector:
                self._vector_cache[cache_key] = doc
                return doc
        except Exception as e:
            logger.debug(f"Vector computation failed: {e}")

        return None

    def select_top_accomplishments(
        self,
        scored: List[ScoredAccomplishment],
        max_count: int = 25,
        min_score: float = 0.3,
        current_role_preference: float = 0.7,
        max_per_company: int = 7
    ) -> List[ScoredAccomplishment]:
        """Select top accomplishments based on scores and constraints.

        Args:
            scored: List of scored accomplishments (sorted by score)
            max_count: Maximum number to select
            min_score: Minimum score threshold
            current_role_preference: Fraction of selections from current role (0.0-1.0)
            max_per_company: Maximum bullets per company

        Returns:
            Selected accomplishments
        """
        if not scored:
            return []

        selected = []
        company_counts: Dict[str, int] = {}

        # Filter by minimum score
        candidates = [s for s in scored if s.final_score >= min_score]

        # Calculate target from current role
        current_role_items = [s for s in candidates if s.is_current]
        target_current = int(max_count * current_role_preference)

        # Select from current role first (up to target)
        for item in current_role_items[:target_current]:
            company = item.company_name
            if company_counts.get(company, 0) < max_per_company:
                selected.append(item)
                company_counts[company] = company_counts.get(company, 0) + 1

        # Fill remaining slots from all candidates
        remaining_slots = max_count - len(selected)
        for item in candidates:
            if len(selected) >= max_count:
                break

            # Skip if already selected
            if item in selected:
                continue

            # Check company limit
            company = item.company_name
            if company_counts.get(company, 0) >= max_per_company:
                continue

            selected.append(item)
            company_counts[company] = company_counts.get(company, 0) + 1

        return selected

    @property
    def is_spacy_available(self) -> bool:
        """Check if spaCy is available for semantic matching."""
        return self.spacy_available and self.nlp is not None
