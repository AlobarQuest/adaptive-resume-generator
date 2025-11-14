"""Resume generation service for creating tailored resumes.

This module provides functionality to generate tailored resumes based on
job requirements, including accomplishment selection, skill coverage analysis,
and gap identification.
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging

from adaptive_resume.services.nlp_analyzer import JobRequirements
from adaptive_resume.services.matching_engine import (
    MatchingEngine,
    ScoredAccomplishment
)

logger = logging.getLogger(__name__)


@dataclass
class TailoredResume:
    """Tailored resume with accomplishments and analysis.

    Attributes:
        profile_id: Database ID of the profile
        job_posting_id: Database ID of the job posting (if persisted)
        selected_accomplishments: List of selected scored accomplishments
        skill_coverage: Dict mapping skills to coverage status
        coverage_percentage: Overall skill coverage percentage (0.0-1.0)
        gaps: List of skills not covered in selected accomplishments
        recommendations: List of actionable recommendations
        created_at: When this tailored resume was created
        job_title: Target job title
        company_name: Target company name
    """
    profile_id: int
    job_posting_id: Optional[int] = None
    selected_accomplishments: List[ScoredAccomplishment] = field(default_factory=list)
    skill_coverage: Dict[str, bool] = field(default_factory=dict)
    coverage_percentage: float = 0.0
    gaps: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    job_title: str = ""
    company_name: str = ""


class ResumeGeneratorError(Exception):
    """Base exception for resume generator errors."""
    pass


class ResumeGenerator:
    """Service for generating tailored resumes.

    Coordinates the matching engine to score accomplishments, selects
    the best matches, analyzes skill coverage, and generates recommendations.

    Attributes:
        matching_engine: MatchingEngine instance for scoring
    """

    def __init__(self, matching_engine: Optional[MatchingEngine] = None):
        """Initialize resume generator.

        Args:
            matching_engine: Optional MatchingEngine instance (creates default if not provided)
        """
        self.matching_engine = matching_engine or MatchingEngine()

    def generate_tailored_resume(
        self,
        profile_id: int,
        accomplishments: List[tuple],  # List of (BulletPoint, Job) tuples
        requirements: JobRequirements,
        job_description_text: str = "",
        job_title: str = "",
        company_name: str = "",
        max_accomplishments: int = 25,
        min_score: float = 0.3,
        current_role_preference: float = 0.7,
        max_per_company: int = 7
    ) -> TailoredResume:
        """Generate a tailored resume for a specific job posting.

        Args:
            profile_id: Profile ID
            accomplishments: List of (BulletPoint, Job) tuples
            requirements: Extracted job requirements
            job_description_text: Full job description text for semantic matching
            job_title: Target job title
            company_name: Target company name
            max_accomplishments: Maximum accomplishments to select (default: 25)
            min_score: Minimum score threshold (default: 0.3)
            current_role_preference: Fraction from current role (default: 0.7)
            max_per_company: Max bullets per company (default: 7)

        Returns:
            TailoredResume with selected accomplishments and analysis

        Raises:
            ResumeGeneratorError: If generation fails
        """
        if not accomplishments:
            raise ResumeGeneratorError("No accomplishments provided")

        # Step 1: Score all accomplishments
        logger.info(f"Scoring {len(accomplishments)} accomplishments...")
        scored = self.matching_engine.score_accomplishments(
            accomplishments,
            requirements,
            job_description_text
        )

        # Step 2: Select top accomplishments
        logger.info("Selecting top accomplishments...")
        selected = self.matching_engine.select_top_accomplishments(
            scored,
            max_count=max_accomplishments,
            min_score=min_score,
            current_role_preference=current_role_preference,
            max_per_company=max_per_company
        )

        # Step 3: Analyze skill coverage
        logger.info("Analyzing skill coverage...")
        skill_coverage, coverage_pct = self._analyze_skill_coverage(
            selected,
            requirements
        )

        # Step 4: Identify gaps
        logger.info("Identifying skill gaps...")
        gaps = self._identify_gaps(skill_coverage, requirements)

        # Step 5: Generate recommendations
        logger.info("Generating recommendations...")
        recommendations = self._generate_recommendations(
            selected,
            skill_coverage,
            gaps,
            requirements,
            coverage_pct
        )

        # Create tailored resume
        tailored_resume = TailoredResume(
            profile_id=profile_id,
            selected_accomplishments=selected,
            skill_coverage=skill_coverage,
            coverage_percentage=coverage_pct,
            gaps=gaps,
            recommendations=recommendations,
            created_at=datetime.now(),
            job_title=job_title,
            company_name=company_name
        )

        logger.info(
            f"Generated tailored resume with {len(selected)} accomplishments, "
            f"{coverage_pct:.1%} skill coverage"
        )

        return tailored_resume

    def _analyze_skill_coverage(
        self,
        selected: List[ScoredAccomplishment],
        requirements: JobRequirements
    ) -> tuple[Dict[str, bool], float]:
        """Analyze which required skills are covered by selected accomplishments.

        Args:
            selected: Selected accomplishments
            requirements: Job requirements

        Returns:
            Tuple of (skill_coverage_dict, coverage_percentage)
        """
        # Collect all skills mentioned in selected accomplishments
        covered_skills: Set[str] = set()
        for item in selected:
            for skill in item.matched_skills:
                covered_skills.add(skill.lower())

        # Build coverage map for required skills
        skill_coverage = {}
        all_required = set(s.lower() for s in requirements.required_skills)

        for skill in requirements.required_skills:
            skill_lower = skill.lower()
            skill_coverage[skill] = skill_lower in covered_skills

        # Also check preferred skills
        for skill in requirements.preferred_skills:
            skill_lower = skill.lower()
            if skill not in skill_coverage:  # Don't overwrite required
                skill_coverage[skill] = skill_lower in covered_skills

        # Calculate coverage percentage (based on required skills only)
        if all_required:
            covered_count = sum(
                1 for skill in requirements.required_skills
                if skill_coverage.get(skill, False)
            )
            coverage_pct = covered_count / len(all_required)
        else:
            coverage_pct = 1.0  # No requirements = 100% coverage

        return skill_coverage, coverage_pct

    def _identify_gaps(
        self,
        skill_coverage: Dict[str, bool],
        requirements: JobRequirements
    ) -> List[str]:
        """Identify skills that are not covered.

        Args:
            skill_coverage: Skill coverage dictionary
            requirements: Job requirements

        Returns:
            List of missing skill names
        """
        gaps = []

        # Check required skills first
        for skill in requirements.required_skills:
            if not skill_coverage.get(skill, False):
                gaps.append(skill)

        # Then check preferred skills
        for skill in requirements.preferred_skills:
            if not skill_coverage.get(skill, False):
                gaps.append(skill)

        return gaps

    def _generate_recommendations(
        self,
        selected: List[ScoredAccomplishment],
        skill_coverage: Dict[str, bool],
        gaps: List[str],
        requirements: JobRequirements,
        coverage_pct: float
    ) -> List[str]:
        """Generate actionable recommendations for improving the resume.

        Args:
            selected: Selected accomplishments
            skill_coverage: Skill coverage dictionary
            gaps: List of missing skills
            requirements: Job requirements
            coverage_pct: Coverage percentage

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Coverage-based recommendations
        if coverage_pct < 0.5:
            recommendations.append(
                "⚠️ Low skill coverage. Consider adding more relevant experience "
                "or highlighting transferable skills in your bullet points."
            )
        elif coverage_pct < 0.8:
            recommendations.append(
                "💡 Moderate skill coverage. Review your accomplishments to find "
                "more examples that demonstrate the missing skills."
            )
        else:
            recommendations.append(
                "✅ Strong skill match! Your experience aligns well with the requirements."
            )

        # Gap-specific recommendations
        required_gaps = [
            gap for gap in gaps
            if gap in requirements.required_skills
        ]

        if required_gaps:
            if len(required_gaps) <= 3:
                skills_str = ", ".join(required_gaps)
                recommendations.append(
                    f"🎯 Focus on highlighting experience with: {skills_str}"
                )
            else:
                top_gaps = ", ".join(required_gaps[:3])
                recommendations.append(
                    f"🎯 Key missing skills: {top_gaps} (+{len(required_gaps) - 3} more)"
                )

        # Preferred skill gaps (lower priority)
        preferred_gaps = [
            gap for gap in gaps
            if gap in requirements.preferred_skills
        ]

        if preferred_gaps and len(preferred_gaps) <= 3:
            skills_str = ", ".join(preferred_gaps)
            recommendations.append(
                f"💫 Bonus points if you can demonstrate: {skills_str}"
            )

        # Metrics recommendations
        accomplishments_with_metrics = sum(
            1 for item in selected
            if item.metrics_score > 0.5
        )
        metrics_pct = accomplishments_with_metrics / len(selected) if selected else 0

        if metrics_pct < 0.3:
            recommendations.append(
                "📊 Add more quantifiable achievements with percentages, "
                "dollar amounts, or other metrics to strengthen your impact."
            )

        # Recency recommendations
        accomplishments_from_current = sum(
            1 for item in selected
            if item.is_current
        )
        current_pct = accomplishments_from_current / len(selected) if selected else 0

        if current_pct < 0.3 and any(item.is_current for item in selected):
            recommendations.append(
                "⏰ Consider adding more examples from your current role to "
                "emphasize recent, relevant experience."
            )

        # Education/experience mismatch
        if requirements.years_experience:
            recommendations.append(
                f"📅 Required experience: {requirements.years_experience}+ years. "
                "Ensure your resume clearly shows your tenure in relevant roles."
            )

        if requirements.education_level:
            recommendations.append(
                f"🎓 Required education: {requirements.education_level}. "
                "Make sure this is prominently displayed."
            )

        # Transferable skills suggestion
        if coverage_pct < 0.7 and gaps:
            recommendations.append(
                "🔄 Look for transferable skills: similar technologies or concepts "
                "that relate to the missing requirements."
            )

        return recommendations

    def calculate_match_score(self, tailored_resume: TailoredResume) -> float:
        """Calculate overall match score for a tailored resume.

        Combines skill coverage, accomplishment scores, and other factors.

        Args:
            tailored_resume: TailoredResume to score

        Returns:
            Overall match score (0.0-1.0)
        """
        if not tailored_resume.selected_accomplishments:
            return 0.0

        # Component 1: Skill coverage (50% weight)
        skill_coverage_score = tailored_resume.coverage_percentage

        # Component 2: Average accomplishment score (30% weight)
        avg_accomplishment_score = sum(
            item.final_score
            for item in tailored_resume.selected_accomplishments
        ) / len(tailored_resume.selected_accomplishments)

        # Component 3: Number of accomplishments selected (10% weight)
        # More selections up to 20 is better
        selection_count = len(tailored_resume.selected_accomplishments)
        selection_score = min(selection_count / 20.0, 1.0)

        # Component 4: Gap penalty (10% weight)
        gap_score = 1.0 - (len(tailored_resume.gaps) / max(
            len(tailored_resume.skill_coverage), 1
        ))

        # Combine with weights
        overall_score = (
            0.5 * skill_coverage_score +
            0.3 * avg_accomplishment_score +
            0.1 * selection_score +
            0.1 * max(gap_score, 0)
        )

        return min(max(overall_score, 0.0), 1.0)
