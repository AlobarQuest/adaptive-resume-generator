"""
BulletPoint model - Individual achievements and responsibilities.

Represents specific accomplishments, responsibilities, and impacts
for each job position.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from adaptive_resume.models.base import Base


class BulletPoint(Base):
    """
    Achievement or responsibility for a job.
    
    Contains the main content, metrics, impact, and tags
    for intelligent matching to job descriptions.
    """
    
    __tablename__ = 'bullet_points'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to job
    job_id = Column(Integer, ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Content
    content = Column(Text, nullable=False)
    metrics = Column(String(500), nullable=True)
    impact = Column(Text, nullable=True)
    
    # Display and highlighting
    display_order = Column(Integer, nullable=False, default=0)
    is_highlighted = Column(Boolean, nullable=False, default=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    job = relationship('Job', back_populates='bullet_points')
    bullet_tags = relationship('BulletTag', back_populates='bullet_point', cascade='all, delete-orphan')
    
    def __repr__(self):
        preview = self.content[:50] + '...' if len(self.content) > 50 else self.content
        return f"<BulletPoint(id={self.id}, content='{preview}')>"
    
    @property
    def tags(self):
        """Get list of tag objects associated with this bullet point."""
        return [bt.tag for bt in self.bullet_tags]
    
    @property
    def tag_names(self):
        """Get list of tag names associated with this bullet point."""
        return [bt.tag.name for bt in self.bullet_tags if bt.tag]
    
    @property
    def full_text(self):
        """Get full text including content, metrics, and impact."""
        parts = [self.content]
        if self.metrics:
            parts.append(f" ({self.metrics})")
        if self.impact:
            parts.append(f" Impact: {self.impact}")
        return ''.join(parts)
    
    def has_tag(self, tag_name):
        """
        Check if bullet point has a specific tag.
        
        Args:
            tag_name (str): Name of the tag to check
            
        Returns:
            bool: True if bullet has the tag
        """
        return tag_name.lower() in [name.lower() for name in self.tag_names]
    
    def to_dict(self):
        """
        Convert bullet point to dictionary.
        
        Returns:
            dict: Bullet point data as dictionary
        """
        return {
            'id': self.id,
            'job_id': self.job_id,
            'content': self.content,
            'metrics': self.metrics,
            'impact': self.impact,
            'full_text': self.full_text,
            'display_order': self.display_order,
            'is_highlighted': self.is_highlighted,
            'tags': self.tag_names,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
