"""
Cover Letter model - AI-generated cover letters for job applications.

Stores generated cover letters with metadata about generation parameters,
user edits, and usage tracking.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from adaptive_resume.models.base import Base


class CoverLetter(Base):
    """
    AI-generated or user-created cover letter for a job application.

    Stores the full cover letter text along with metadata about how it was
    generated, what template was used, and tracks user modifications.
    """

    __tablename__ = 'cover_letters'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    job_posting_id = Column(Integer, ForeignKey('job_postings.id', ondelete='SET NULL'), nullable=True, index=True)
    tailored_resume_id = Column(Integer, ForeignKey('tailored_resumes.id', ondelete='SET NULL'), nullable=True, index=True)

    # Content
    content = Column(Text, nullable=False)  # Full cover letter text
    opening_paragraph = Column(Text, nullable=True)  # Separated for easy regeneration
    body_paragraphs = Column(JSON, nullable=True)  # Array of body paragraph texts
    closing_paragraph = Column(Text, nullable=True)  # Separated for easy regeneration

    # Metadata
    template_id = Column(String(50), nullable=True)  # e.g., "professional", "enthusiastic"
    tone = Column(String(50), nullable=True)  # "formal", "conversational", "enthusiastic"
    length = Column(String(20), nullable=True)  # "short", "medium", "long"
    focus_areas = Column(JSON, nullable=True)  # ["leadership", "technical", "results"]

    # AI generation tracking
    ai_generated = Column(Boolean, default=False, nullable=False)
    ai_prompt_used = Column(Text, nullable=True)  # Store the prompt for reference
    ai_model = Column(String(100), nullable=True)  # e.g., "claude-sonnet-4-20250514"

    # User modification tracking
    user_edited = Column(Boolean, default=False, nullable=False)
    edit_history = Column(JSON, nullable=True)  # Array of edit timestamps and summaries

    # Usage tracking
    used_in_application_id = Column(Integer, ForeignKey('job_applications.id', ondelete='SET NULL'), nullable=True, index=True)

    # Additional metadata
    company_name = Column(String(200), nullable=True)  # Cached from job posting
    job_title = Column(String(200), nullable=True)  # Cached from job posting
    word_count = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    profile = relationship('Profile', back_populates='cover_letters')
    job_posting = relationship('JobPosting', back_populates='cover_letters')
    tailored_resume = relationship('TailoredResumeModel', back_populates='cover_letters')
    job_application = relationship('JobApplication', back_populates='cover_letter', uselist=False)

    def __repr__(self):
        return f"<CoverLetter(id={self.id}, job_title='{self.job_title}', template='{self.template_id}')>"

    def to_dict(self):
        """
        Convert cover letter to dictionary.

        Returns:
            dict: Cover letter data as dictionary
        """
        return {
            'id': self.id,
            'profile_id': self.profile_id,
            'job_posting_id': self.job_posting_id,
            'tailored_resume_id': self.tailored_resume_id,
            'content': self.content,
            'opening_paragraph': self.opening_paragraph,
            'body_paragraphs': self.body_paragraphs,
            'closing_paragraph': self.closing_paragraph,
            'template_id': self.template_id,
            'tone': self.tone,
            'length': self.length,
            'focus_areas': self.focus_areas,
            'ai_generated': self.ai_generated,
            'ai_model': self.ai_model,
            'user_edited': self.user_edited,
            'used_in_application_id': self.used_in_application_id,
            'company_name': self.company_name,
            'job_title': self.job_title,
            'word_count': self.word_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
