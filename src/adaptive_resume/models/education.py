"""
Education model - Academic history and credentials.

Represents degrees, certifications, and academic achievements.
"""

from sqlalchemy import Column, Integer, String, Text, Date, Numeric, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from adaptive_resume.models.base import Base


class Education(Base):
    """
    Educational background entry.
    
    Tracks degrees, institutions, dates, GPA, honors, and
    relevant coursework.
    """
    
    __tablename__ = 'education'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to profile
    profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Education details
    institution = Column(String(255), nullable=False)
    degree = Column(String(200), nullable=False)
    field_of_study = Column(String(200), nullable=True)
    
    # Dates
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True, index=True)
    
    # Academic performance
    gpa = Column(Numeric(3, 2), nullable=True)  # e.g., 3.75
    honors = Column(String(500), nullable=True)
    relevant_coursework = Column(Text, nullable=True)
    
    # Display ordering
    display_order = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship('Profile', back_populates='education')
    
    # Constraints
    __table_args__ = (
        CheckConstraint('end_date IS NULL OR start_date IS NULL OR end_date >= start_date', 
                       name='check_education_dates'),
        CheckConstraint('gpa IS NULL OR (gpa >= 0.0 AND gpa <= 4.0)', 
                       name='check_gpa_range'),
    )
    
    def __repr__(self):
        return f"<Education(id={self.id}, degree='{self.degree}', institution='{self.institution}')>"
    
    @property
    def date_range(self):
        """Get formatted date range string."""
        if not self.start_date and not self.end_date:
            return "Dates not specified"
        
        start = self.start_date.strftime('%Y') if self.start_date else 'Unknown'
        end = self.end_date.strftime('%Y') if self.end_date else 'Present'
        
        if start == end:
            return start
        return f"{start} - {end}"
    
    @property
    def gpa_display(self):
        """Get formatted GPA string."""
        if not self.gpa:
            return None
        return f"{float(self.gpa):.2f}"
    
    def to_dict(self):
        """
        Convert education to dictionary.
        
        Returns:
            dict: Education data as dictionary
        """
        return {
            'id': self.id,
            'profile_id': self.profile_id,
            'institution': self.institution,
            'degree': self.degree,
            'field_of_study': self.field_of_study,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'date_range': self.date_range,
            'gpa': float(self.gpa) if self.gpa else None,
            'gpa_display': self.gpa_display,
            'honors': self.honors,
            'relevant_coursework': self.relevant_coursework,
            'display_order': self.display_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
