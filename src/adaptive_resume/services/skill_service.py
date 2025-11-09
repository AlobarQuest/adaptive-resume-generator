"""Service layer for managing skill records."""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable, List, Optional

from sqlalchemy.orm import Session

from adaptive_resume.models import Profile, Skill


class SkillServiceError(Exception):
    """Base exception for skill service failures."""


class SkillNotFoundError(SkillServiceError):
    """Raised when a requested skill cannot be located."""


class SkillValidationError(SkillServiceError):
    """Raised when provided skill data is invalid."""


class SkillService:
    """Business logic for creating, updating, and ordering skills."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------
    def create_skill(
        self,
        profile_id: int,
        skill_name: str,
        category: Optional[str] = None,
        proficiency_level: Optional[str] = None,
        years_experience: Optional[float] = None,
        display_order: Optional[int] = None,
    ) -> Skill:
        self._ensure_profile_exists(profile_id)
        self._validate_skill(skill_name, proficiency_level, years_experience)

        skill = Skill(
            profile_id=profile_id,
            skill_name=skill_name.strip(),
            category=category.strip() if category else None,
            proficiency_level=proficiency_level.strip() if proficiency_level else None,
            years_experience=self._to_decimal(years_experience),
            display_order=display_order
            if display_order is not None
            else self._next_display_order(profile_id),
        )
        self.session.add(skill)
        self.session.commit()
        self.session.refresh(skill)
        return skill

    def update_skill(
        self,
        skill_id: int,
        *,
        skill_name: Optional[str] = None,
        category: Optional[str] = None,
        proficiency_level: Optional[str] = None,
        years_experience: Optional[float] = None,
        display_order: Optional[int] = None,
    ) -> Skill:
        skill = self.get_skill_by_id(skill_id)

        if skill_name is not None:
            if not skill_name.strip():
                raise SkillValidationError("Skill name cannot be empty")
            skill.skill_name = skill_name.strip()

        if category is not None:
            skill.category = category.strip() if category.strip() else None

        if proficiency_level is not None:
            self._validate_proficiency(proficiency_level)
            skill.proficiency_level = proficiency_level.strip() if proficiency_level.strip() else None

        if years_experience is not None:
            if years_experience < 0:
                raise SkillValidationError("Years of experience must be positive")
            skill.years_experience = self._to_decimal(years_experience)

        if display_order is not None:
            if display_order < 0:
                raise SkillValidationError("Display order must be positive")
            skill.display_order = display_order

        self.session.commit()
        self.session.refresh(skill)
        return skill

    def delete_skill(self, skill_id: int) -> None:
        skill = self.get_skill_by_id(skill_id)
        self.session.delete(skill)
        self.session.commit()

    def get_skill_by_id(self, skill_id: int) -> Skill:
        skill = self.session.query(Skill).filter_by(id=skill_id).first()
        if not skill:
            raise SkillNotFoundError(f"Skill with id {skill_id} not found")
        return skill

    def list_skills_for_profile(self, profile_id: int) -> List[Skill]:
        return (
            self.session.query(Skill)
            .filter_by(profile_id=profile_id)
            .order_by(Skill.display_order.asc(), Skill.skill_name.asc())
            .all()
        )

    def reorder_skills(self, profile_id: int, ordered_ids: Iterable[int]) -> None:
        skills = self.list_skills_for_profile(profile_id)
        id_map = {skill.id: skill for skill in skills}
        for position, skill_id in enumerate(ordered_ids):
            if skill_id in id_map:
                id_map[skill_id].display_order = position
        self.session.commit()

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    def _ensure_profile_exists(self, profile_id: int) -> None:
        exists = self.session.query(Profile.id).filter_by(id=profile_id).scalar()
        if not exists:
            raise SkillValidationError(f"Profile with id {profile_id} does not exist")

    def _validate_skill(
        self,
        skill_name: str,
        proficiency_level: Optional[str],
        years_experience: Optional[float],
    ) -> None:
        if not skill_name or not skill_name.strip():
            raise SkillValidationError("Skill name is required")
        if proficiency_level:
            self._validate_proficiency(proficiency_level)
        if years_experience is not None and years_experience < 0:
            raise SkillValidationError("Years of experience must be positive")

    def _validate_proficiency(self, level: str) -> None:
        level = level.strip()
        if level and level not in Skill.PROFICIENCY_LEVELS:
            raise SkillValidationError(
                f"Invalid proficiency level '{level}'. Expected one of {Skill.PROFICIENCY_LEVELS}"
            )

    def _next_display_order(self, profile_id: int) -> int:
        current_max = (
            self.session.query(Skill.display_order)
            .filter_by(profile_id=profile_id)
            .order_by(Skill.display_order.desc())
            .limit(1)
            .scalar()
        )
        return (current_max or 0) + 1

    def _to_decimal(self, value: Optional[float]) -> Optional[Decimal]:
        if value is None:
            return None
        return Decimal(str(round(value, 1)))


__all__ = [
    "SkillService",
    "SkillServiceError",
    "SkillNotFoundError",
    "SkillValidationError",
]
