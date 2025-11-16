"""
Profile model - User's core professional information.

Represents the user's basic profile including contact information,
professional summary, and relationships to all other career data.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from adaptive_resume.models.base import Base


class Profile(Base):
    """
    User profile containing core professional information.
    
    In v1.0, there is typically one profile per database.
    Future versions may support multiple profiles for different
    career focuses or user accounts.
    """
    
    __tablename__ = 'profiles'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Basic information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(20), nullable=True)
    
    # Location
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    
    # Online presence
    linkedin_url = Column(String(255), nullable=True)
    portfolio_url = Column(String(255), nullable=True)
    
    # Professional summary
    professional_summary = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships (one-to-many)
    jobs = relationship('Job', back_populates='profile', cascade='all, delete-orphan')
    skills = relationship('Skill', back_populates='profile', cascade='all, delete-orphan')
    education = relationship('Education', back_populates='profile', cascade='all, delete-orphan')
    certifications = relationship('Certification', back_populates='profile', cascade='all, delete-orphan')
    job_applications = relationship('JobApplication', back_populates='profile', cascade='all, delete-orphan')
    cover_letter_sections = relationship('CoverLetterSection', back_populates='profile', cascade='all, delete-orphan')
    job_postings = relationship('JobPosting', back_populates='profile', cascade='all, delete-orphan')
    tailored_resumes = relationship('TailoredResumeModel', back_populates='profile', cascade='all, delete-orphan')
    cover_letters = relationship('CoverLetter', back_populates='profile', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Profile(id={self.id}, name='{self.first_name} {self.last_name}', email='{self.email}')>"
    
    @property
    def full_name(self):
        """Get the user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self):
        """
        Convert profile to dictionary.
        
        Returns:
            dict: Profile data as dictionary
        """
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'city': self.city,
            'state': self.state,
            'linkedin_url': self.linkedin_url,
            'portfolio_url': self.portfolio_url,
            'professional_summary': self.professional_summary,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
