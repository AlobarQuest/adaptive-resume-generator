"""
Tag model - Categories for organizing bullet points.

Tags enable intelligent filtering and matching of bullet points
to job descriptions.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from adaptive_resume.models.base import Base


class Tag(Base):
    """
    Tag for categorizing bullet points.
    
    Tags help organize achievements and enable intelligent matching
    when generating resumes for specific job descriptions.
    """
    
    __tablename__ = 'tags'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Tag information
    name = Column(String(100), nullable=False, unique=True, index=True)
    category = Column(String(50), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    bullet_tags = relationship('BulletTag', back_populates='tag')
    
    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}', category='{self.category}')>"
    
    @property
    def bullet_points(self):
        """Get all bullet points with this tag."""
        return [bt.bullet_point for bt in self.bullet_tags]
    
    @property
    def usage_count(self):
        """Get count of how many bullet points use this tag."""
        return len(self.bullet_tags)
    
    def to_dict(self):
        """
        Convert tag to dictionary.
        
        Returns:
            dict: Tag data as dictionary
        """
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class BulletTag(Base):
    """
    Association table linking bullet points to tags.
    
    Many-to-many relationship between BulletPoint and Tag.
    """
    
    __tablename__ = 'bullet_tags'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    bullet_point_id = Column(Integer, ForeignKey('bullet_points.id', ondelete='CASCADE'), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey('tags.id', ondelete='RESTRICT'), nullable=False, index=True)
    
    # Timestamp
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    bullet_point = relationship('BulletPoint', back_populates='bullet_tags')
    tag = relationship('Tag', back_populates='bullet_tags')
    
    # Unique constraint to prevent duplicate tags on same bullet
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )
    
    def __repr__(self):
        return f"<BulletTag(bullet_point_id={self.bullet_point_id}, tag_id={self.tag_id})>"


# Predefined tag categories and names for seeding
PREDEFINED_TAGS = {
    'technical': [
        'programming', 'database', 'cloud', 'security', 'devops',
        'architecture', 'infrastructure', 'networking', 'api'
    ],
    'leadership': [
        'team-management', 'mentoring', 'project-management',
        'strategic-planning', 'stakeholder-management', 'cross-functional'
    ],
    'financial': [
        'budgeting', 'cost-reduction', 'revenue-growth',
        'roi', 'financial-analysis', 'forecasting'
    ],
    'customer': [
        'customer-service', 'client-relations', 'sales',
        'customer-success', 'account-management', 'support'
    ],
    'process': [
        'automation', 'optimization', 'efficiency',
        'process-improvement', 'workflow', 'quality-assurance'
    ],
    'communication': [
        'presentations', 'documentation', 'training',
        'technical-writing', 'public-speaking', 'collaboration'
    ],
    'problem-solving': [
        'troubleshooting', 'debugging', 'analysis',
        'root-cause-analysis', 'innovation', 'creative-solutions'
    ],
    'soft-skills': [
        'leadership', 'communication', 'adaptability',
        'time-management', 'critical-thinking', 'emotional-intelligence'
    ]
}


def seed_tags(session):
    """
    Seed the database with predefined tags.
    
    Args:
        session: SQLAlchemy session
        
    Returns:
        int: Number of tags created
    """
    created_count = 0
    
    for category, tag_names in PREDEFINED_TAGS.items():
        for tag_name in tag_names:
            # Check if tag already exists
            existing = session.query(Tag).filter_by(name=tag_name).first()
            if not existing:
                tag = Tag(name=tag_name, category=category)
                session.add(tag)
                created_count += 1
    
    session.commit()
    return created_count
