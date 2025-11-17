"""Service layer for managing education history."""

from __future__ import annotations

from datetime import date
from typing import Iterable, List, Optional

from sqlalchemy.orm import Session

from adaptive_resume.models import Education, Profile
from adaptive_resume.models.base import DEFAULT_PROFILE_ID


class EducationServiceError(Exception):
    """Base exception for education service failures."""


class EducationNotFoundError(EducationServiceError):
    """Raised when an education record cannot be located."""


class EducationValidationError(EducationServiceError):
    """Raised when provided education data is invalid."""


class EducationService:
    """Business logic for CRUD operations on education entries."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_education(
        self,
        institution: str,
        degree: str,
        field_of_study: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        gpa: Optional[float] = None,
        honors: Optional[str] = None,
        relevant_coursework: Optional[str] = None,
        display_order: Optional[int] = None,
        profile_id: int = DEFAULT_PROFILE_ID,
    ) -> Education:
        self._ensure_profile_exists(profile_id)
        self._validate_dates(start_date, end_date)
        self._validate_required(institution, degree)

        education = Education(
            profile_id=profile_id,
            institution=institution.strip(),
            degree=degree.strip(),
            field_of_study=field_of_study.strip() if field_of_study else None,
            start_date=start_date,
            end_date=end_date,
            gpa=gpa,
            honors=honors.strip() if honors else None,
            relevant_coursework=relevant_coursework.strip() if relevant_coursework else None,
            display_order=display_order
            if display_order is not None
            else self._next_display_order(profile_id),
        )
        self.session.add(education)
        self.session.commit()
        self.session.refresh(education)
        return education

    def update_education(
        self,
        education_id: int,
        *,
        institution: Optional[str] = None,
        degree: Optional[str] = None,
        field_of_study: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        gpa: Optional[float] = None,
        honors: Optional[str] = None,
        relevant_coursework: Optional[str] = None,
        display_order: Optional[int] = None,
    ) -> Education:
        education = self.get_education_by_id(education_id)

        if institution is not None:
            if not institution.strip():
                raise EducationValidationError("Institution cannot be empty")
            education.institution = institution.strip()

        if degree is not None:
            if not degree.strip():
                raise EducationValidationError("Degree cannot be empty")
            education.degree = degree.strip()

        if field_of_study is not None:
            education.field_of_study = field_of_study.strip() if field_of_study.strip() else None

        if start_date is not None or end_date is not None:
            self._validate_dates(start_date or education.start_date, end_date or education.end_date)
            if start_date is not None:
                education.start_date = start_date
            if end_date is not None:
                education.end_date = end_date

        if gpa is not None:
            if gpa < 0 or gpa > 4:
                raise EducationValidationError("GPA must be between 0.0 and 4.0")
            education.gpa = gpa

        if honors is not None:
            education.honors = honors.strip() if honors.strip() else None

        if relevant_coursework is not None:
            education.relevant_coursework = (
                relevant_coursework.strip() if relevant_coursework.strip() else None
            )

        if display_order is not None:
            if display_order < 0:
                raise EducationValidationError("Display order must be positive")
            education.display_order = display_order

        self.session.commit()
        self.session.refresh(education)
        return education

    def delete_education(self, education_id: int) -> None:
        education = self.get_education_by_id(education_id)
        self.session.delete(education)
        self.session.commit()

    def get_education_by_id(self, education_id: int) -> Education:
        education = self.session.query(Education).filter_by(id=education_id).first()
        if not education:
            raise EducationNotFoundError(f"Education with id {education_id} not found")
        return education

    def list_education_for_profile(self, profile_id: int = DEFAULT_PROFILE_ID) -> List[Education]:
        return (
            self.session.query(Education)
            .filter_by(profile_id=profile_id)
            .order_by(Education.display_order.asc(), Education.start_date.desc())
            .all()
        )

    def reorder_education(self, ordered_ids: Iterable[int], profile_id: int = DEFAULT_PROFILE_ID) -> None:
        education_entries = self.list_education_for_profile(profile_id)
        id_map = {entry.id: entry for entry in education_entries}
        for position, education_id in enumerate(ordered_ids):
            if education_id in id_map:
                id_map[education_id].display_order = position
        self.session.commit()

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    def _ensure_profile_exists(self, profile_id: int) -> None:
        exists = self.session.query(Profile.id).filter_by(id=profile_id).scalar()
        if not exists:
            raise EducationValidationError(f"Profile with id {profile_id} does not exist")

    def _validate_dates(
        self, start_date: Optional[date], end_date: Optional[date]
    ) -> None:
        if start_date and end_date and end_date < start_date:
            raise EducationValidationError("End date cannot be before start date")

    def _validate_required(self, institution: str, degree: str) -> None:
        if not institution or not institution.strip():
            raise EducationValidationError("Institution is required")
        if not degree or not degree.strip():
            raise EducationValidationError("Degree is required")

    def _next_display_order(self, profile_id: int) -> int:
        current_max = (
            self.session.query(Education.display_order)
            .filter_by(profile_id=profile_id)
            .order_by(Education.display_order.desc())
            .limit(1)
            .scalar()
        )
        return (current_max or 0) + 1


__all__ = [
    "EducationService",
    "EducationServiceError",
    "EducationNotFoundError",
    "EducationValidationError",
]
