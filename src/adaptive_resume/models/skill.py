"""
Skill model - User's skills with proficiency tracking.

Represents technical and soft skills with categories,
proficiency levels, and experience duration.
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from adaptive_resume.models.base import Base


class Skill(Base):
    """
    User skill with proficiency and experience.
    
    Tracks both technical and soft skills with categories,
    proficiency levels, and years of experience.
    """
    
    __tablename__ = 'skills'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to profile
    profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Skill information
    skill_name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=True, index=True)
    proficiency_level = Column(String(50), nullable=True)  # Beginner, Intermediate, Advanced, Expert
    years_experience = Column(Numeric(4, 1), nullable=True)  # e.g., 5.5 years
    
    # Display ordering
    display_order = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship('Profile', back_populates='skills')
    
    # Valid proficiency levels
    PROFICIENCY_LEVELS = ['Beginner', 'Intermediate', 'Advanced', 'Expert']
    
    def __repr__(self):
        return f"<Skill(id={self.id}, name='{self.skill_name}', level='{self.proficiency_level}')>"
    
    @property
    def experience_display(self):
        """Get formatted experience string."""
        if not self.years_experience:
            return "Experience not specified"
        
        years = float(self.years_experience)
        if years < 1:
            months = int(years * 12)
            return f"{months} months"
        elif years == 1:
            return "1 year"
        else:
            return f"{years:.1f} years"
    
    def to_dict(self):
        """
        Convert skill to dictionary.
        
        Returns:
            dict: Skill data as dictionary
        """
        return {
            'id': self.id,
            'profile_id': self.profile_id,
            'skill_name': self.skill_name,
            'category': self.category,
            'proficiency_level': self.proficiency_level,
            'years_experience': float(self.years_experience) if self.years_experience else None,
            'experience_display': self.experience_display,
            'display_order': self.display_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# Common skill categories for reference
SKILL_CATEGORIES = [
    'Programming Languages',
    'Frameworks & Libraries',
    'Databases',
    'Cloud Platforms',
    'Tools & Software',
    'Methodologies',
    'Soft Skills',
    'Domain Knowledge',
    'Operating Systems',
    'Development Tools',
    'Testing & QA',
    'Project Management',
    'Design & UX',
    'Data Science & Analytics',
    'Security & Compliance',
]
