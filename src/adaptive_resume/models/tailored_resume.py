"""
Tailored resume model - Stores generated tailored resumes.

Represents tailored resumes generated for specific job postings,
including selected accomplishments, skill coverage, and recommendations.
"""

from sqlalchemy import Column, Integer, Text, DateTime, Float, ForeignKey, String, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from adaptive_resume.models.base import Base


class TailoredResumeModel(Base):
    """
    Tailored resume generated for a specific job posting.

    Stores the result of matching a profile against a job posting,
    including selected bullet points, coverage analysis, and gaps.
    """

    __tablename__ = 'tailored_resumes'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    job_posting_id = Column(Integer, ForeignKey('job_postings.id', ondelete='CASCADE'), nullable=False, index=True)

    # Selected accomplishments (stored as JSON array of bullet IDs)
    selected_accomplishment_ids = Column(Text, nullable=False)  # JSON: [1, 5, 7, ...]

    # Full accomplishment data (stored as JSON array of accomplishment objects)
    # Includes text, scores, matched_skills, etc. for PDF generation
    selected_accomplishments_json = Column(Text, nullable=True)  # JSON: [{bullet_id: 1, text: "...", ...}, ...]

    # Skill coverage analysis (stored as JSON)
    skill_coverage_json = Column(Text, nullable=True)  # JSON: {"Python": true, "AWS": false, ...}
    coverage_percentage = Column(Float, nullable=True)  # 0.0-1.0

    # Gaps and recommendations (stored as JSON)
    gaps_json = Column(Text, nullable=True)  # JSON: ["AWS", "Docker"]
    recommendations_json = Column(Text, nullable=True)  # JSON: ["Add more...", ...]

    # Overall match score
    match_score = Column(Float, nullable=True)  # 0.0-1.0

    # Variant support (Phase 6.2)
    variant_name = Column(String(100), nullable=True)  # e.g., "Conservative", "Technical", "Bold"
    variant_number = Column(Integer, nullable=False, default=1)  # Auto-incrementing variant number per job
    parent_variant_id = Column(Integer, ForeignKey('tailored_resumes.id', ondelete='SET NULL'), nullable=True)
    is_primary = Column(Boolean, nullable=False, default=True)  # Is this the primary/default variant?
    notes = Column(Text, nullable=True)  # User notes about this variant
    performance_metrics = Column(Text, nullable=True)  # JSON: {"interview_rate": 0.5, "response_time_days": 7, ...}

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    profile = relationship('Profile', back_populates='tailored_resumes')
    job_posting = relationship('JobPosting', back_populates='tailored_resumes')
    cover_letters = relationship('CoverLetter', back_populates='tailored_resume', cascade='all, delete-orphan')

    # Self-referential relationship for variant parent
    parent_variant = relationship('TailoredResumeModel', remote_side=[id], foreign_keys=[parent_variant_id])

    def __repr__(self):
        return f"<TailoredResumeModel(id={self.id}, profile_id={self.profile_id}, job_posting_id={self.job_posting_id})>"

    @property
    def formatted_coverage(self) -> str:
        """Get formatted coverage percentage."""
        if self.coverage_percentage is not None:
            return f"{self.coverage_percentage * 100:.1f}%"
        return "N/A"

    @property
    def formatted_match_score(self) -> str:
        """Get formatted match score."""
        if self.match_score is not None:
            return f"{self.match_score * 100:.0f}%"
        return "N/A"
