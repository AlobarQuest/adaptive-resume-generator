"""Service layer for managing professional certifications."""

from __future__ import annotations

from datetime import date
from typing import Iterable, List, Optional

from sqlalchemy.orm import Session

from adaptive_resume.models import Certification, Profile


class CertificationServiceError(Exception):
    """Base exception for certification service errors."""


class CertificationNotFoundError(CertificationServiceError):
    """Raised when a certification record cannot be located."""


class CertificationValidationError(CertificationServiceError):
    """Raised when certification data fails validation."""


class CertificationService:
    """Business logic for CRUD operations on certifications."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_certification(
        self,
        profile_id: int,
        name: str,
        issuing_organization: str,
        issue_date: Optional[date] = None,
        expiration_date: Optional[date] = None,
        credential_id: Optional[str] = None,
        credential_url: Optional[str] = None,
        display_order: Optional[int] = None,
    ) -> Certification:
        self._ensure_profile_exists(profile_id)
        self._validate_required(name, issuing_organization)
        self._validate_dates(issue_date, expiration_date)

        certification = Certification(
            profile_id=profile_id,
            name=name.strip(),
            issuing_organization=issuing_organization.strip(),
            issue_date=issue_date,
            expiration_date=expiration_date,
            credential_id=credential_id.strip() if credential_id else None,
            credential_url=credential_url.strip() if credential_url else None,
            display_order=display_order
            if display_order is not None
            else self._next_display_order(profile_id),
        )
        self.session.add(certification)
        self.session.commit()
        self.session.refresh(certification)
        return certification

    def update_certification(
        self,
        certification_id: int,
        *,
        name: Optional[str] = None,
        issuing_organization: Optional[str] = None,
        issue_date: Optional[date] = None,
        expiration_date: Optional[date] = None,
        credential_id: Optional[str] = None,
        credential_url: Optional[str] = None,
        display_order: Optional[int] = None,
    ) -> Certification:
        certification = self.get_certification_by_id(certification_id)

        if name is not None:
            if not name.strip():
                raise CertificationValidationError("Certification name cannot be empty")
            certification.name = name.strip()

        if issuing_organization is not None:
            if not issuing_organization.strip():
                raise CertificationValidationError("Issuing organization cannot be empty")
            certification.issuing_organization = issuing_organization.strip()

        if issue_date is not None or expiration_date is not None:
            self._validate_dates(issue_date or certification.issue_date, expiration_date or certification.expiration_date)
            if issue_date is not None:
                certification.issue_date = issue_date
            if expiration_date is not None:
                certification.expiration_date = expiration_date

        if credential_id is not None:
            certification.credential_id = credential_id.strip() if credential_id.strip() else None

        if credential_url is not None:
            certification.credential_url = credential_url.strip() if credential_url.strip() else None

        if display_order is not None:
            if display_order < 0:
                raise CertificationValidationError("Display order must be positive")
            certification.display_order = display_order

        self.session.commit()
        self.session.refresh(certification)
        return certification

    def delete_certification(self, certification_id: int) -> None:
        certification = self.get_certification_by_id(certification_id)
        self.session.delete(certification)
        self.session.commit()

    def get_certification_by_id(self, certification_id: int) -> Certification:
        certification = self.session.query(Certification).filter_by(id=certification_id).first()
        if not certification:
            raise CertificationNotFoundError(f"Certification with id {certification_id} not found")
        return certification

    def list_certifications_for_profile(self, profile_id: int) -> List[Certification]:
        return (
            self.session.query(Certification)
            .filter_by(profile_id=profile_id)
            .order_by(Certification.display_order.asc(), Certification.issue_date.desc())
            .all()
        )

    def reorder_certifications(self, profile_id: int, ordered_ids: Iterable[int]) -> None:
        certifications = self.list_certifications_for_profile(profile_id)
        id_map = {cert.id: cert for cert in certifications}
        for position, certification_id in enumerate(ordered_ids):
            if certification_id in id_map:
                id_map[certification_id].display_order = position
        self.session.commit()

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    def _ensure_profile_exists(self, profile_id: int) -> None:
        exists = self.session.query(Profile.id).filter_by(id=profile_id).scalar()
        if not exists:
            raise CertificationValidationError(f"Profile with id {profile_id} does not exist")

    def _validate_required(self, name: str, issuing_organization: str) -> None:
        if not name or not name.strip():
            raise CertificationValidationError("Certification name is required")
        if not issuing_organization or not issuing_organization.strip():
            raise CertificationValidationError("Issuing organization is required")

    def _validate_dates(
        self,
        issue_date: Optional[date],
        expiration_date: Optional[date],
    ) -> None:
        if issue_date and expiration_date and expiration_date < issue_date:
            raise CertificationValidationError("Expiration date cannot be before issue date")

    def _next_display_order(self, profile_id: int) -> int:
        current_max = (
            self.session.query(Certification.display_order)
            .filter_by(profile_id=profile_id)
            .order_by(Certification.display_order.desc())
            .limit(1)
            .scalar()
        )
        return (current_max or 0) + 1


__all__ = [
    "CertificationService",
    "CertificationServiceError",
    "CertificationNotFoundError",
    "CertificationValidationError",
]
