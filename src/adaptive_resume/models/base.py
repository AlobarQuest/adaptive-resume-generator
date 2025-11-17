"""
Database base configuration and session management.

This module provides the SQLAlchemy base class and session factory
for the Adaptive Resume Generator application.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from pathlib import Path
import os

# Single-profile architecture constant
# Desktop app enforces one profile per database
DEFAULT_PROFILE_ID = 1

# Get database path from environment or use default
DATABASE_PATH = os.getenv(
    'ADAPTIVE_RESUME_DB_PATH',
    str(Path.home() / '.adaptive_resume' / 'resume_data.db')
)

# Ensure directory exists
db_dir = Path(DATABASE_PATH).parent
db_dir.mkdir(parents=True, exist_ok=True)

# Create SQLite engine with proper configuration
# check_same_thread=False allows usage across multiple threads (needed for GUI)
# echo=False for production, set to True for debugging SQL
DATABASE_URL = f'sqlite:///{DATABASE_PATH}'

engine = create_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False},
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Thread-safe session
Session = scoped_session(SessionLocal)

# Base class for all models
Base = declarative_base()


def get_session():
    """
    Get a database session.
    
    Returns:
        Session: SQLAlchemy session object
        
    Usage:
        session = get_session()
        try:
            # Use session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    """
    return Session()


def init_db():
    """
    Initialize the database by creating all tables.
    
    This should be called once when the application starts
    or when setting up a new database.
    """
    # Import all models to ensure they're registered with Base
    from adaptive_resume.models import (
        profile, job, bullet_point, tag, skill,
        education, certification, job_application,
        generated_resume, generated_cover_letter, templates
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)


def drop_db():
    """
    Drop all tables from the database.
    
    WARNING: This will delete all data!
    Only use for testing or resetting the database.
    """
    Base.metadata.drop_all(bind=engine)


def get_engine():
    """
    Get the SQLAlchemy engine.
    
    Returns:
        Engine: SQLAlchemy engine object
    """
    return engine


def close_session():
    """
    Close the current session and remove it from the registry.
    """
    Session.remove()
