"""
JobApplication model - Track job applications.

Represents job applications with company, position, status tracking,
and relationships to generated resumes and cover letters.
"""

from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import date
from adaptive_resume.models.base import Base


class JobApplication(Base):
    """
    Job application tracking.
    
    Tracks applications with company, position, job description,
    status, and links to generated documents.
    """
    
    __tablename__ = 'job_applications'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to profile
    profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Application details
    company_name = Column(String(200), nullable=False)
    position_title = Column(String(200), nullable=False)
    job_description = Column(Text, nullable=True)  # For matching
    
    # Application tracking
    application_date = Column(Date, nullable=False, index=True)
    status = Column(String(50), nullable=False, default='applied', index=True)
    
    # Contact information
    job_url = Column(String(255), nullable=True)
    contact_person = Column(String(200), nullable=True)
    contact_email = Column(String(255), nullable=True)
    
    # Notes and follow-up
    notes = Column(Text, nullable=True)
    follow_up_date = Column(Date, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship('Profile', back_populates='job_applications')
    generated_resumes = relationship('GeneratedResume', back_populates='job_application', cascade='all, delete-orphan')
    generated_cover_letters = relationship('GeneratedCoverLetter', back_populates='job_application', cascade='all, delete-orphan')
    cover_letter = relationship('CoverLetter', back_populates='job_application', uselist=False)
    
    # Valid status values
    STATUS_APPLIED = 'applied'
    STATUS_PHONE_SCREEN = 'phone_screen'
    STATUS_INTERVIEW = 'interview'
    STATUS_OFFER = 'offer'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_WITHDRAWN = 'withdrawn'
    
    VALID_STATUSES = [
        STATUS_APPLIED,
        STATUS_PHONE_SCREEN,
        STATUS_INTERVIEW,
        STATUS_OFFER,
        STATUS_ACCEPTED,
        STATUS_REJECTED,
        STATUS_WITHDRAWN,
    ]
    
    # Constraints
    __table_args__ = (
        CheckConstraint(f"status IN {tuple(VALID_STATUSES)}", name='check_application_status'),
        CheckConstraint('application_date <= CURRENT_DATE', name='check_application_date_not_future'),
    )
    
    def __repr__(self):
        return f"<JobApplication(id={self.id}, company='{self.company_name}', position='{self.position_title}', status='{self.status}')>"
    
    @property
    def days_since_application(self):
        """Get days since application was submitted."""
        if not self.application_date:
            return None
        delta = date.today() - self.application_date
        return delta.days
    
    @property
    def needs_follow_up(self):
        """Check if follow-up is needed."""
        if not self.follow_up_date:
            return False
        return self.follow_up_date <= date.today()
    
    @property
    def is_active(self):
        """Check if application is still active (not accepted, rejected, or withdrawn)."""
        return self.status not in [self.STATUS_ACCEPTED, self.STATUS_REJECTED, self.STATUS_WITHDRAWN]
    
    def to_dict(self):
        """
        Convert job application to dictionary.
        
        Returns:
            dict: Job application data as dictionary
        """
        return {
            'id': self.id,
            'profile_id': self.profile_id,
            'company_name': self.company_name,
            'position_title': self.position_title,
            'job_description': self.job_description,
            'application_date': self.application_date.isoformat() if self.application_date else None,
            'status': self.status,
            'job_url': self.job_url,
            'contact_person': self.contact_person,
            'contact_email': self.contact_email,
            'notes': self.notes,
            'follow_up_date': self.follow_up_date.isoformat() if self.follow_up_date else None,
            'days_since_application': self.days_since_application,
            'needs_follow_up': self.needs_follow_up,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'resume_count': len(self.generated_resumes) if self.generated_resumes else 0,
            'cover_letter_count': len(self.generated_cover_letters) if self.generated_cover_letters else 0,
        }
