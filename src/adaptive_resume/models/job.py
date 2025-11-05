"""
Job model - Work history entries.

Represents employment history with company, title, dates, and
relationship to bullet points.
"""

from sqlalchemy import Column, Integer, String, Text, Date, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from adaptive_resume.models.base import Base


class Job(Base):
    """
    Employment history entry.
    
    Tracks job positions with company name, title, dates, and
    related bullet points describing achievements and responsibilities.
    """
    
    __tablename__ = 'jobs'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to profile
    profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Job details
    company_name = Column(String(200), nullable=False)
    job_title = Column(String(200), nullable=False)
    location = Column(String(200), nullable=True)
    
    # Dates
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=True)
    is_current = Column(Boolean, nullable=False, default=False)
    
    # Description
    description = Column(Text, nullable=True)
    
    # Display ordering
    display_order = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship('Profile', back_populates='jobs')
    bullet_points = relationship('BulletPoint', back_populates='job', cascade='all, delete-orphan')
    
    # Constraints
    __table_args__ = (
        CheckConstraint('end_date IS NULL OR end_date >= start_date', name='check_job_dates'),
        CheckConstraint('NOT is_current OR end_date IS NULL', name='check_current_job_no_end_date'),
    )
    
    def __repr__(self):
        return f"<Job(id={self.id}, title='{self.job_title}', company='{self.company_name}')>"
    
    @property
    def date_range(self):
        """Get formatted date range string."""
        start = self.start_date.strftime('%B %Y') if self.start_date else 'Unknown'
        if self.is_current:
            end = 'Present'
        elif self.end_date:
            end = self.end_date.strftime('%B %Y')
        else:
            end = 'Unknown'
        return f"{start} - {end}"
    
    @property
    def duration_months(self):
        """Calculate duration in months."""
        if not self.start_date:
            return 0
        
        from datetime import date
        end = self.end_date if self.end_date else date.today()
        
        months = (end.year - self.start_date.year) * 12
        months += end.month - self.start_date.month
        return max(0, months)
    
    def to_dict(self):
        """
        Convert job to dictionary.
        
        Returns:
            dict: Job data as dictionary
        """
        return {
            'id': self.id,
            'profile_id': self.profile_id,
            'company_name': self.company_name,
            'job_title': self.job_title,
            'location': self.location,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_current': self.is_current,
            'date_range': self.date_range,
            'duration_months': self.duration_months,
            'description': self.description,
            'display_order': self.display_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'bullet_points_count': len(self.bullet_points) if self.bullet_points else 0,
        }
