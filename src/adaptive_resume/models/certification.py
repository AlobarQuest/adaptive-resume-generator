"""
Certification model - Professional certifications and licenses.

Represents professional credentials with issue and expiration dates.
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import date
from adaptive_resume.models.base import Base


class Certification(Base):
    """
    Professional certification or license.
    
    Tracks certifications with issuing organization, dates,
    credential IDs, and verification URLs.
    """
    
    __tablename__ = 'certifications'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to profile
    profile_id = Column(Integer, ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Certification details
    name = Column(String(255), nullable=False)
    issuing_organization = Column(String(255), nullable=False)
    
    # Dates
    issue_date = Column(Date, nullable=True)
    expiration_date = Column(Date, nullable=True, index=True)
    
    # Credentials
    credential_id = Column(String(200), nullable=True)
    credential_url = Column(String(255), nullable=True)
    
    # Display ordering
    display_order = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship('Profile', back_populates='certifications')
    
    # Constraints
    __table_args__ = (
        CheckConstraint('expiration_date IS NULL OR issue_date IS NULL OR expiration_date >= issue_date',
                       name='check_certification_dates'),
    )
    
    def __repr__(self):
        return f"<Certification(id={self.id}, name='{self.name}', org='{self.issuing_organization}')>"
    
    @property
    def is_expired(self):
        """Check if certification is expired."""
        if not self.expiration_date:
            return False  # No expiration date means never expires
        return self.expiration_date < date.today()
    
    @property
    def days_until_expiration(self):
        """
        Get days until expiration.
        
        Returns:
            int or None: Days until expiration, None if no expiration date or already expired
        """
        if not self.expiration_date or self.is_expired:
            return None
        
        delta = self.expiration_date - date.today()
        return delta.days
    
    @property
    def status(self):
        """Get certification status."""
        if not self.expiration_date:
            return "Active (No Expiration)"
        
        if self.is_expired:
            return "Expired"
        
        days = self.days_until_expiration
        if days and days <= 90:
            return f"Expiring Soon ({days} days)"
        
        return "Active"
    
    def to_dict(self):
        """
        Convert certification to dictionary.
        
        Returns:
            dict: Certification data as dictionary
        """
        return {
            'id': self.id,
            'profile_id': self.profile_id,
            'name': self.name,
            'issuing_organization': self.issuing_organization,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None,
            'is_expired': self.is_expired,
            'days_until_expiration': self.days_until_expiration,
            'status': self.status,
            'credential_id': self.credential_id,
            'credential_url': self.credential_url,
            'display_order': self.display_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
