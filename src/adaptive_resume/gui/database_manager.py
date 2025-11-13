"""
Database Manager - Singleton for database session management.

Provides a single database session for the GUI application.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from adaptive_resume.models.base import Base, DATABASE_PATH


class DatabaseManager:
    """
    Singleton database manager for GUI application.
    
    Provides a single database session that persists for the
    lifetime of the application.
    """
    
    _instance = None
    _session = None
    _engine = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def initialize(cls, db_path: str = None):
        """
        Initialize the database connection.
        
        Args:
            db_path: Optional custom database path. If None, uses default.
        """
        if cls._engine is None:
            if db_path is None:
                db_path = DATABASE_PATH
            
            cls._engine = create_engine(f'sqlite:///{db_path}', echo=False)
            Base.metadata.create_all(cls._engine)
            
            SessionLocal = sessionmaker(bind=cls._engine)
            cls._session = SessionLocal()
    
    @classmethod
    def get_session(cls) -> Session:
        """
        Get the database session.
        
        Returns:
            Session: SQLAlchemy session
            
        Raises:
            RuntimeError: If database not initialized
        """
        if cls._session is None:
            cls.initialize()
        
        return cls._session
    
    @classmethod
    def close(cls):
        """Close the database session."""
        if cls._session:
            cls._session.close()
            cls._session = None
        
        if cls._engine:
            cls._engine.dispose()
            cls._engine = None
    
    @classmethod
    def commit(cls):
        """Commit current transaction."""
        if cls._session:
            cls._session.commit()
    
    @classmethod
    def rollback(cls):
        """Rollback current transaction."""
        if cls._session:
            cls._session.rollback()
