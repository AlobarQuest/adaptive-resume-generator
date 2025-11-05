"""
GeneratedResume and GeneratedCoverLetter models.

Tracks history of generated documents with configuration and file paths.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import json
from adaptive_resume.models.base import Base


class GeneratedResume(Base):
    """
    History of generated resumes.
    
    Tracks which bullets and skills were selected, which template
    was used, and the file path for retrieval.
    """
    
    __tablename__ = 'generated_resumes'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    job_application_id = Column(Integer, ForeignKey('job_applications.id', ondelete='CASCADE'), nullable=True, index=True)
    resume_template_id = Column(Integer, ForeignKey('resume_templates.id', ondelete='RESTRICT'), nullable=False)
    
    # File information
    file_path = Column(String(500), nullable=False)
    
    # Configuration (JSON)
    selected_bullets = Column(Text, nullable=False)  # JSON array of bullet_point IDs
    selected_skills = Column(Text, nullable=True)    # JSON array of skill IDs
    custom_summary = Column(Text, nullable=True)
    
    # Timestamps
    generated_at = Column(DateTime, nullable=False, server_default=func.now())
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    job_application = relationship('JobApplication', back_populates='generated_resumes')
    resume_template = relationship('ResumeTemplate', back_populates='generated_resumes')
    
    def __repr__(self):
        return f"<GeneratedResume(id={self.id}, file='{self.file_path}')>"
    
    def get_selected_bullet_ids(self):
        """
        Get list of selected bullet point IDs.
        
        Returns:
            list: List of integer bullet point IDs
        """
        try:
            return json.loads(self.selected_bullets) if self.selected_bullets else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_selected_bullet_ids(self, bullet_ids):
        """
        Set selected bullet point IDs.
        
        Args:
            bullet_ids (list): List of integer bullet point IDs
        """
        self.selected_bullets = json.dumps(bullet_ids)
    
    def get_selected_skill_ids(self):
        """
        Get list of selected skill IDs.
        
        Returns:
            list: List of integer skill IDs
        """
        try:
            return json.loads(self.selected_skills) if self.selected_skills else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_selected_skill_ids(self, skill_ids):
        """
        Set selected skill IDs.
        
        Args:
            skill_ids (list): List of integer skill IDs
        """
        self.selected_skills = json.dumps(skill_ids)
    
    def to_dict(self):
        """
        Convert generated resume to dictionary.
        
        Returns:
            dict: Generated resume data as dictionary
        """
        return {
            'id': self.id,
            'job_application_id': self.job_application_id,
            'resume_template_id': self.resume_template_id,
            'file_path': self.file_path,
            'selected_bullets': self.get_selected_bullet_ids(),
            'selected_skills': self.get_selected_skill_ids(),
            'custom_summary': self.custom_summary,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class GeneratedCoverLetter(Base):
    """
    History of generated cover letters.
    
    Tracks which sections were used and the file path for retrieval.
    """
    
    __tablename__ = 'generated_cover_letters'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    job_application_id = Column(Integer, ForeignKey('job_applications.id', ondelete='CASCADE'), nullable=True, index=True)
    
    # File information
    file_path = Column(String(500), nullable=False)
    
    # Sections used (references to cover_letter_sections)
    opening_section_id = Column(Integer, ForeignKey('cover_letter_sections.id', ondelete='RESTRICT'), nullable=True)
    body_sections = Column(Text, nullable=False)  # JSON array of section IDs
    closing_section_id = Column(Integer, ForeignKey('cover_letter_sections.id', ondelete='RESTRICT'), nullable=True)
    
    # Custom content
    custom_content = Column(Text, nullable=True)
    
    # Timestamps
    generated_at = Column(DateTime, nullable=False, server_default=func.now())
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    job_application = relationship('JobApplication', back_populates='generated_cover_letters')
    opening_section = relationship('CoverLetterSection', foreign_keys=[opening_section_id])
    closing_section = relationship('CoverLetterSection', foreign_keys=[closing_section_id])
    
    def __repr__(self):
        return f"<GeneratedCoverLetter(id={self.id}, file='{self.file_path}')>"
    
    def get_body_section_ids(self):
        """
        Get list of body section IDs.
        
        Returns:
            list: List of integer section IDs
        """
        try:
            return json.loads(self.body_sections) if self.body_sections else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_body_section_ids(self, section_ids):
        """
        Set body section IDs.
        
        Args:
            section_ids (list): List of integer section IDs
        """
        self.body_sections = json.dumps(section_ids)
    
    def to_dict(self):
        """
        Convert generated cover letter to dictionary.
        
        Returns:
            dict: Generated cover letter data as dictionary
        """
        return {
            'id': self.id,
            'job_application_id': self.job_application_id,
            'file_path': self.file_path,
            'opening_section_id': self.opening_section_id,
            'body_sections': self.get_body_section_ids(),
            'closing_section_id': self.closing_section_id,
            'custom_content': self.custom_content,
            'generated_at': self.generated_at.isoformat() if self.generated_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
