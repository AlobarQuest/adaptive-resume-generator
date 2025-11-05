"""
Models package for Adaptive Resume Generator.

This package contains all SQLAlchemy ORM models for the application.
Import models from this package to use them throughout the application.

Usage:
    from adaptive_resume.models import Profile, Job, BulletPoint
    
    # Or import everything
    from adaptive_resume.models import *
"""

from adaptive_resume.models.base import Base, get_session, init_db, drop_db, get_engine, close_session
from adaptive_resume.models.profile import Profile
from adaptive_resume.models.job import Job
from adaptive_resume.models.bullet_point import BulletPoint
from adaptive_resume.models.tag import Tag, BulletTag, PREDEFINED_TAGS, seed_tags
from adaptive_resume.models.skill import Skill, SKILL_CATEGORIES
from adaptive_resume.models.education import Education
from adaptive_resume.models.certification import Certification
from adaptive_resume.models.job_application import JobApplication
from adaptive_resume.models.generated_resume import GeneratedResume, GeneratedCoverLetter
from adaptive_resume.models.templates import ResumeTemplate, CoverLetterSection, create_default_template

__all__ = [
    # Base
    'Base',
    'get_session',
    'init_db',
    'drop_db',
    'get_engine',
    'close_session',
    
    # Core models
    'Profile',
    'Job',
    'BulletPoint',
    'Tag',
    'BulletTag',
    'Skill',
    'Education',
    'Certification',
    
    # Application tracking
    'JobApplication',
    'GeneratedResume',
    'GeneratedCoverLetter',
    
    # Templates
    'ResumeTemplate',
    'CoverLetterSection',
    
    # Utility functions
    'seed_tags',
    'create_default_template',
    
    # Constants
    'PREDEFINED_TAGS',
    'SKILL_CATEGORIES',
]

# Version
__version__ = '0.1.0'
