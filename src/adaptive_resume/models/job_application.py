"""
JobApplication model - Track job applications.

Represents job applications with company, position, status tracking,
and relationships to generated resumes and cover letters.
"""

from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, CheckConstraint, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import date, datetime
from adaptive_resume.models.base import Base
import json


class JobApplication(Base):
    """
    Job application tracking.
    
    Tracks applications with company, position, job description,
    status, and links to generated documents.
    """
    
    __tablename__ = 'job_applications'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    job_posting_id = Column(Integer, ForeignKey('job_postings.id', ondelete='SET NULL'), nullable=True, index=True)
    tailored_resume_id = Column(Integer, ForeignKey('tailored_resumes.id', ondelete='SET NULL'), nullable=True)

    # Application details
    company_name = Column(String(200), nullable=False, index=True)
    position_title = Column(String(200), nullable=False)
    job_description = Column(Text, nullable=True)
    job_url = Column(String(500), nullable=True)

    # Application tracking
    application_method = Column(String(50), nullable=True)  # "company_site", "linkedin", "indeed", etc.
    discovered_date = Column(Date, nullable=True)  # When job was found
    application_date = Column(Date, nullable=True, index=True)  # When applied
    status = Column(String(50), nullable=False, default='discovered', index=True)
    substatus = Column(String(100), nullable=True)  # "phone_screen", "technical", "onsite", etc.
    priority = Column(String(20), nullable=True, default='medium')  # "high", "medium", "low"

    # Timeline tracking
    first_response_date = Column(Date, nullable=True)
    interview_dates = Column(Text, nullable=True)  # JSON array of interview dates and types
    offer_date = Column(Date, nullable=True)
    rejection_date = Column(Date, nullable=True)
    acceptance_date = Column(Date, nullable=True)

    # Contact information
    contact_person = Column(String(200), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    recruiter_name = Column(String(200), nullable=True)
    recruiter_email = Column(String(255), nullable=True)
    last_contact_date = Column(Date, nullable=True)
    next_followup_date = Column(Date, nullable=True)

    # Job details
    salary_range = Column(String(100), nullable=True)
    location = Column(String(200), nullable=True)
    remote_option = Column(Boolean, nullable=True)  # True=remote, False=onsite, None=hybrid/unknown
    referral_source = Column(String(200), nullable=True)

    # Notes and tracking
    notes = Column(Text, nullable=True)

    # Calculated/tracked metrics
    response_time_days = Column(Integer, nullable=True)  # Days from application to first response
    interview_count = Column(Integer, nullable=True, default=0)
    total_time_to_outcome_days = Column(Integer, nullable=True)  # Days from application to final outcome

    # Legacy field mapping (for backward compatibility)
    follow_up_date = Column(Date, nullable=True)  # Maps to next_followup_date
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship('Profile', back_populates='job_applications')
    job_posting = relationship('JobPosting', backref='applications')
    tailored_resume = relationship('TailoredResumeModel', backref='applications')
    generated_resumes = relationship('GeneratedResume', back_populates='job_application', cascade='all, delete-orphan')
    generated_cover_letters = relationship('GeneratedCoverLetter', back_populates='job_application', cascade='all, delete-orphan')
    cover_letter = relationship('CoverLetter', back_populates='job_application', uselist=False)

    # Valid status values (expanded pipeline)
    STATUS_DISCOVERED = 'discovered'
    STATUS_INTERESTED = 'interested'
    STATUS_APPLIED = 'applied'
    STATUS_SCREENING = 'screening'
    STATUS_INTERVIEW = 'interview'
    STATUS_OFFER_RECEIVED = 'offer_received'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_WITHDRAWN = 'withdrawn'

    VALID_STATUSES = [
        STATUS_DISCOVERED,
        STATUS_INTERESTED,
        STATUS_APPLIED,
        STATUS_SCREENING,
        STATUS_INTERVIEW,
        STATUS_OFFER_RECEIVED,
        STATUS_ACCEPTED,
        STATUS_REJECTED,
        STATUS_WITHDRAWN,
    ]

    # Valid priority values
    PRIORITY_HIGH = 'high'
    PRIORITY_MEDIUM = 'medium'
    PRIORITY_LOW = 'low'

    VALID_PRIORITIES = [PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW]
    
    # Constraints
    __table_args__ = (
        CheckConstraint(f"status IN {tuple(VALID_STATUSES)}", name='check_application_status'),
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

    def add_interview(self, interview_date: date, interview_type: str = "general", notes: str = ""):
        """Add an interview to the interview_dates JSON array."""
        interviews = self.get_interviews()
        interviews.append({
            'date': interview_date.isoformat() if isinstance(interview_date, date) else interview_date,
            'type': interview_type,
            'notes': notes
        })
        self.interview_dates = json.dumps(interviews)
        self.interview_count = len(interviews)

    def get_interviews(self):
        """Get list of interviews from JSON."""
        if not self.interview_dates:
            return []
        try:
            return json.loads(self.interview_dates)
        except (json.JSONDecodeError, TypeError):
            return []

    def calculate_response_time(self):
        """Calculate and update response_time_days."""
        if self.application_date and self.first_response_date:
            delta = self.first_response_date - self.application_date
            self.response_time_days = delta.days

    def calculate_time_to_outcome(self):
        """Calculate and update total_time_to_outcome_days."""
        if not self.application_date:
            return

        outcome_date = self.acceptance_date or self.rejection_date
        if outcome_date:
            delta = outcome_date - self.application_date
            self.total_time_to_outcome_days = delta.days
    
    def to_dict(self):
        """
        Convert job application to dictionary.

        Returns:
            dict: Job application data as dictionary
        """
        return {
            'id': self.id,
            'profile_id': self.profile_id,
            'job_posting_id': self.job_posting_id,
            'tailored_resume_id': self.tailored_resume_id,
            'company_name': self.company_name,
            'position_title': self.position_title,
            'job_description': self.job_description,
            'job_url': self.job_url,
            'application_method': self.application_method,
            'discovered_date': self.discovered_date.isoformat() if self.discovered_date else None,
            'application_date': self.application_date.isoformat() if self.application_date else None,
            'status': self.status,
            'substatus': self.substatus,
            'priority': self.priority,
            'first_response_date': self.first_response_date.isoformat() if self.first_response_date else None,
            'interviews': self.get_interviews(),
            'interview_count': self.interview_count,
            'offer_date': self.offer_date.isoformat() if self.offer_date else None,
            'rejection_date': self.rejection_date.isoformat() if self.rejection_date else None,
            'acceptance_date': self.acceptance_date.isoformat() if self.acceptance_date else None,
            'contact_person': self.contact_person,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'recruiter_name': self.recruiter_name,
            'recruiter_email': self.recruiter_email,
            'last_contact_date': self.last_contact_date.isoformat() if self.last_contact_date else None,
            'next_followup_date': self.next_followup_date.isoformat() if self.next_followup_date else None,
            'salary_range': self.salary_range,
            'location': self.location,
            'remote_option': self.remote_option,
            'referral_source': self.referral_source,
            'notes': self.notes,
            'response_time_days': self.response_time_days,
            'total_time_to_outcome_days': self.total_time_to_outcome_days,
            'days_since_application': self.days_since_application,
            'needs_follow_up': self.needs_follow_up,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'resume_count': len(self.generated_resumes) if self.generated_resumes else 0,
            'cover_letter_count': len(self.generated_cover_letters) if self.generated_cover_letters else 0,
        }
