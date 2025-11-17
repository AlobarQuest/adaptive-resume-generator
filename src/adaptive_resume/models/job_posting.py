"""
Job posting model - Stores uploaded job postings with analysis.

Represents job postings that users upload for tailored resume generation,
including the raw text, parsed requirements, and analysis metadata.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from adaptive_resume.models.base import Base


class JobPosting(Base):
    """
    Job posting uploaded by user for analysis.

    Stores job posting text and extracted requirements for matching
    against profile accomplishments.
    """

    __tablename__ = 'job_postings'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to profile
    profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)

    # Job details
    company_name = Column(String(200), nullable=True)
    job_title = Column(String(200), nullable=True)
    location = Column(String(200), nullable=True)  # Job location (e.g., "Remote", "New York, NY")
    salary_range = Column(String(200), nullable=True)  # Salary/pay rate (e.g., "$80k-$100k", "$50/hr")
    application_url = Column(String(500), nullable=True)  # URL to submit application
    source = Column(String(50), nullable=True)  # How it was added: 'paste', 'upload', 'import'
    notes = Column(Text, nullable=True)  # User notes about the posting

    # Raw text
    raw_text = Column(Text, nullable=False)  # Original uploaded text
    cleaned_text = Column(Text, nullable=True)  # Cleaned/normalized text

    # Extracted requirements (stored as JSON text)
    requirements_json = Column(Text, nullable=True)  # JobRequirements serialized

    # Analysis metadata
    analysis_method = Column(String(50), nullable=True)  # 'spacy', 'ai', 'hybrid'
    confidence_score = Column(Float, nullable=True)  # Analysis confidence

    # Timestamps
    uploaded_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    analyzed_at = Column(DateTime, nullable=True)

    # Relationships
    profile = relationship('Profile', back_populates='job_postings')
    tailored_resumes = relationship(
        'TailoredResumeModel',
        back_populates='job_posting',
        cascade='all, delete-orphan'
    )
    cover_letters = relationship(
        'CoverLetter',
        back_populates='job_posting',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f"<JobPosting(id={self.id}, title='{self.job_title}', company='{self.company_name}')>"

    @property
    def has_analysis(self) -> bool:
        """Check if job posting has been analyzed."""
        return self.requirements_json is not None
