"""
Template models for resumes and cover letters.

Stores layout configurations and reusable content sections.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import json
from adaptive_resume.models.base import Base


class ResumeTemplate(Base):
    """
    Resume layout template.
    
    Stores configuration for PDF generation including fonts,
    colors, margins, and section ordering.
    """
    
    __tablename__ = 'resume_templates'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Template information
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    layout_config = Column(Text, nullable=False)  # JSON configuration
    is_default = Column(Boolean, nullable=False, default=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    generated_resumes = relationship('GeneratedResume', back_populates='resume_template')
    
    def __repr__(self):
        return f"<ResumeTemplate(id={self.id}, name='{self.name}', default={self.is_default})>"
    
    def get_layout_config(self):
        """
        Get layout configuration as dictionary.
        
        Returns:
            dict: Layout configuration
        """
        try:
            return json.loads(self.layout_config) if self.layout_config else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_layout_config(self, config_dict):
        """
        Set layout configuration from dictionary.
        
        Args:
            config_dict (dict): Layout configuration
        """
        self.layout_config = json.dumps(config_dict, indent=2)
    
    def to_dict(self):
        """
        Convert template to dictionary.
        
        Returns:
            dict: Template data as dictionary
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'layout_config': self.get_layout_config(),
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class CoverLetterSection(Base):
    """
    Reusable cover letter section.
    
    Stores opening, body, and closing sections that can be
    mixed and matched for different applications.
    """
    
    __tablename__ = 'cover_letter_sections'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to profile
    profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Section information
    section_type = Column(String(50), nullable=False, index=True)  # opening, body, closing
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    tags = Column(Text, nullable=True)  # JSON array of tags for matching
    is_favorite = Column(Boolean, nullable=False, default=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship('Profile', back_populates='cover_letter_sections')
    
    # Valid section types
    TYPE_OPENING = 'opening'
    TYPE_BODY = 'body'
    TYPE_CLOSING = 'closing'
    
    VALID_TYPES = [TYPE_OPENING, TYPE_BODY, TYPE_CLOSING]
    
    def __repr__(self):
        return f"<CoverLetterSection(id={self.id}, type='{self.section_type}', title='{self.title}')>"
    
    def get_tags(self):
        """
        Get tags as list.
        
        Returns:
            list: List of tag strings
        """
        try:
            return json.loads(self.tags) if self.tags else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_tags(self, tag_list):
        """
        Set tags from list.
        
        Args:
            tag_list (list): List of tag strings
        """
        self.tags = json.dumps(tag_list)
    
    def has_tag(self, tag_name):
        """
        Check if section has a specific tag.
        
        Args:
            tag_name (str): Tag name to check
            
        Returns:
            bool: True if section has the tag
        """
        return tag_name.lower() in [t.lower() for t in self.get_tags()]
    
    def to_dict(self):
        """
        Convert section to dictionary.
        
        Returns:
            dict: Section data as dictionary
        """
        return {
            'id': self.id,
            'profile_id': self.profile_id,
            'section_type': self.section_type,
            'title': self.title,
            'content': self.content,
            'tags': self.get_tags(),
            'is_favorite': self.is_favorite,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


def create_default_template(session):
    """
    Create the default resume template.
    
    Args:
        session: SQLAlchemy session
        
    Returns:
        ResumeTemplate: The created default template
    """
    # Check if default already exists
    existing = session.query(ResumeTemplate).filter_by(name='Professional').first()
    if existing:
        return existing
    
    default_config = {
        "page_size": "letter",
        "margins": {
            "top": 0.5,
            "bottom": 0.5,
            "left": 0.75,
            "right": 0.75
        },
        "fonts": {
            "header": {"family": "Helvetica-Bold", "size": 16},
            "name": {"family": "Helvetica-Bold", "size": 24},
            "section_header": {"family": "Helvetica-Bold", "size": 12},
            "body": {"family": "Helvetica", "size": 10}
        },
        "colors": {
            "primary": "#000000",
            "secondary": "#333333",
            "accent": "#0066cc"
        },
        "sections_order": [
            "contact",
            "summary",
            "skills",
            "experience",
            "education",
            "certifications"
        ],
        "bullet_style": "bullet",
        "line_spacing": 1.15
    }
    
    template = ResumeTemplate(
        name='Professional',
        description='Clean, professional resume template optimized for ATS systems',
        is_default=True
    )
    template.set_layout_config(default_config)
    
    session.add(template)
    session.commit()
    
    return template
