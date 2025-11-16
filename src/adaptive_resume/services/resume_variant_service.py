"""
Resume Variant Service - Manage multiple resume variants per job posting.

Provides functionality for creating, managing, and comparing different
versions of tailored resumes for the same job posting.
"""

import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from adaptive_resume.models.tailored_resume import TailoredResumeModel


class VariantComparison:
    """Container for variant comparison data."""

    def __init__(
        self,
        variants: List[TailoredResumeModel],
        accomplishment_diffs: Dict[str, Any],
        skill_diffs: Dict[str, Any],
        metadata: Dict[str, Any]
    ):
        self.variants = variants
        self.accomplishment_diffs = accomplishment_diffs
        self.skill_diffs = skill_diffs
        self.metadata = metadata


class ResumeVariantService:
    """Service for managing resume variants."""

    def __init__(self, session: Session):
        """Initialize the service with a database session."""
        self.session = session

    def create_variant(
        self,
        base_resume_id: int,
        variant_name: str,
        modifications: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None
    ) -> TailoredResumeModel:
        """
        Create a new variant from an existing tailored resume.

        Args:
            base_resume_id: ID of the resume to use as base
            variant_name: Name for the new variant (e.g., "Conservative", "Technical")
            modifications: Optional dict with fields to modify
            notes: Optional notes about this variant

        Returns:
            The newly created variant

        Raises:
            ValueError: If base resume not found or variant name already exists
        """
        # Get the base resume
        base_resume = self.session.query(TailoredResumeModel).filter_by(
            id=base_resume_id
        ).first()

        if not base_resume:
            raise ValueError(f"Base resume with ID {base_resume_id} not found")

        # Check if variant name already exists for this job posting
        existing_variant = self.session.query(TailoredResumeModel).filter_by(
            job_posting_id=base_resume.job_posting_id,
            variant_name=variant_name
        ).first()

        if existing_variant:
            raise ValueError(
                f"Variant with name '{variant_name}' already exists for this job posting"
            )

        # Get next variant number for this job posting
        next_number = self._get_next_variant_number(base_resume.job_posting_id)

        # Create new variant with cloned data
        new_variant = TailoredResumeModel(
            profile_id=base_resume.profile_id,
            job_posting_id=base_resume.job_posting_id,
            selected_accomplishment_ids=base_resume.selected_accomplishment_ids,
            skill_coverage_json=base_resume.skill_coverage_json,
            coverage_percentage=base_resume.coverage_percentage,
            gaps_json=base_resume.gaps_json,
            recommendations_json=base_resume.recommendations_json,
            match_score=base_resume.match_score,
            variant_name=variant_name,
            variant_number=next_number,
            parent_variant_id=base_resume_id,
            is_primary=False,  # New variants are not primary by default
            notes=notes
        )

        # Apply modifications if provided
        if modifications:
            for key, value in modifications.items():
                if hasattr(new_variant, key):
                    setattr(new_variant, key, value)

        self.session.add(new_variant)
        self.session.commit()
        self.session.refresh(new_variant)

        return new_variant

    def list_variants(self, job_posting_id: int) -> List[TailoredResumeModel]:
        """
        Get all variants for a job posting, ordered by variant number.

        Args:
            job_posting_id: ID of the job posting

        Returns:
            List of TailoredResumeModel instances
        """
        variants = self.session.query(TailoredResumeModel).filter_by(
            job_posting_id=job_posting_id
        ).order_by(TailoredResumeModel.variant_number).all()

        return variants

    def compare_variants(
        self,
        variant_ids: List[int]
    ) -> VariantComparison:
        """
        Compare 2-3 resume variants side-by-side.

        Args:
            variant_ids: List of 2-3 variant IDs to compare

        Returns:
            VariantComparison object with comparison data

        Raises:
            ValueError: If wrong number of variants or variants not found
        """
        if len(variant_ids) < 2 or len(variant_ids) > 3:
            raise ValueError("Must compare between 2 and 3 variants")

        # Fetch variants
        variants = []
        for variant_id in variant_ids:
            variant = self.session.query(TailoredResumeModel).filter_by(
                id=variant_id
            ).first()
            if not variant:
                raise ValueError(f"Variant with ID {variant_id} not found")
            variants.append(variant)

        # Verify all variants are for the same job posting
        job_posting_ids = set(v.job_posting_id for v in variants)
        if len(job_posting_ids) > 1:
            raise ValueError("All variants must be for the same job posting")

        # Compare accomplishments
        accomplishment_diffs = self._compare_accomplishments(variants)

        # Compare skill coverage
        skill_diffs = self._compare_skill_coverage(variants)

        # Gather metadata
        metadata = {
            "variant_count": len(variants),
            "job_posting_id": variants[0].job_posting_id,
            "variants_info": [
                {
                    "id": v.id,
                    "name": v.variant_name or f"Variant {v.variant_number}",
                    "variant_number": v.variant_number,
                    "is_primary": v.is_primary,
                    "match_score": v.match_score,
                    "coverage_percentage": v.coverage_percentage,
                    "created_at": v.created_at.isoformat() if v.created_at else None
                }
                for v in variants
            ]
        }

        return VariantComparison(
            variants=variants,
            accomplishment_diffs=accomplishment_diffs,
            skill_diffs=skill_diffs,
            metadata=metadata
        )

    def clone_variant(
        self,
        source_id: int,
        new_name: str,
        notes: Optional[str] = None
    ) -> TailoredResumeModel:
        """
        Clone an existing variant with a new name.

        Args:
            source_id: ID of the variant to clone
            new_name: Name for the cloned variant
            notes: Optional notes for the new variant

        Returns:
            The newly cloned variant
        """
        return self.create_variant(
            base_resume_id=source_id,
            variant_name=new_name,
            notes=notes
        )

    def mark_as_primary(self, variant_id: int) -> None:
        """
        Mark a variant as the primary variant for its job posting.
        Unmarks any other primary variant for the same job.

        Args:
            variant_id: ID of the variant to mark as primary

        Raises:
            ValueError: If variant not found
        """
        variant = self.session.query(TailoredResumeModel).filter_by(
            id=variant_id
        ).first()

        if not variant:
            raise ValueError(f"Variant with ID {variant_id} not found")

        # Unmark all other variants for this job as primary
        self.session.query(TailoredResumeModel).filter_by(
            job_posting_id=variant.job_posting_id
        ).update({"is_primary": False})

        # Mark this variant as primary
        variant.is_primary = True
        self.session.commit()

    def track_performance(
        self,
        variant_id: int,
        metrics: Dict[str, Any]
    ) -> None:
        """
        Update performance metrics for a variant.

        Args:
            variant_id: ID of the variant
            metrics: Dictionary of metrics (e.g., {"interview_rate": 0.5, ...})

        Raises:
            ValueError: If variant not found
        """
        variant = self.session.query(TailoredResumeModel).filter_by(
            id=variant_id
        ).first()

        if not variant:
            raise ValueError(f"Variant with ID {variant_id} not found")

        # Merge with existing metrics if present
        existing_metrics = {}
        if variant.performance_metrics:
            try:
                existing_metrics = json.loads(variant.performance_metrics)
            except json.JSONDecodeError:
                pass

        existing_metrics.update(metrics)
        variant.performance_metrics = json.dumps(existing_metrics)

        self.session.commit()

    def delete_variant(self, variant_id: int) -> None:
        """
        Delete a variant.

        Args:
            variant_id: ID of the variant to delete

        Raises:
            ValueError: If variant not found or is the only variant
        """
        variant = self.session.query(TailoredResumeModel).filter_by(
            id=variant_id
        ).first()

        if not variant:
            raise ValueError(f"Variant with ID {variant_id} not found")

        # Check if this is the only variant for the job posting
        variant_count = self.session.query(TailoredResumeModel).filter_by(
            job_posting_id=variant.job_posting_id
        ).count()

        if variant_count <= 1:
            raise ValueError("Cannot delete the only variant for a job posting")

        # If deleting the primary variant, mark the first remaining variant as primary
        if variant.is_primary:
            remaining_variant = self.session.query(TailoredResumeModel).filter_by(
                job_posting_id=variant.job_posting_id
            ).filter(TailoredResumeModel.id != variant_id).first()

            if remaining_variant:
                remaining_variant.is_primary = True

        self.session.delete(variant)
        self.session.commit()

    def update_variant(
        self,
        variant_id: int,
        **kwargs
    ) -> TailoredResumeModel:
        """
        Update variant fields.

        Args:
            variant_id: ID of the variant to update
            **kwargs: Fields to update

        Returns:
            Updated variant

        Raises:
            ValueError: If variant not found
        """
        variant = self.session.query(TailoredResumeModel).filter_by(
            id=variant_id
        ).first()

        if not variant:
            raise ValueError(f"Variant with ID {variant_id} not found")

        # Update allowed fields
        allowed_fields = {
            'variant_name', 'notes', 'selected_accomplishment_ids',
            'skill_coverage_json', 'coverage_percentage', 'gaps_json',
            'recommendations_json', 'match_score'
        }

        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(variant, key, value)

        self.session.commit()
        self.session.refresh(variant)

        return variant

    # Private helper methods

    def _get_next_variant_number(self, job_posting_id: int) -> int:
        """Get the next variant number for a job posting."""
        max_number = self.session.query(
            func.max(TailoredResumeModel.variant_number)
        ).filter_by(job_posting_id=job_posting_id).scalar()

        return (max_number or 0) + 1

    def _compare_accomplishments(
        self,
        variants: List[TailoredResumeModel]
    ) -> Dict[str, Any]:
        """Compare accomplishments across variants."""
        # Parse accomplishment IDs for each variant
        accomplishment_sets = []
        for variant in variants:
            try:
                ids = json.loads(variant.selected_accomplishment_ids)
                accomplishment_sets.append(set(ids))
            except (json.JSONDecodeError, TypeError):
                accomplishment_sets.append(set())

        # Find common and unique accomplishments
        common = set.intersection(*accomplishment_sets) if accomplishment_sets else set()
        all_accomplishments = set.union(*accomplishment_sets) if accomplishment_sets else set()

        # Build diff structure
        diffs = {
            "common_accomplishments": list(common),
            "total_unique_accomplishments": len(all_accomplishments),
            "by_variant": []
        }

        for i, variant in enumerate(variants):
            variant_ids = accomplishment_sets[i]
            unique_to_variant = variant_ids - common

            diffs["by_variant"].append({
                "variant_id": variant.id,
                "variant_name": variant.variant_name or f"Variant {variant.variant_number}",
                "total_accomplishments": len(variant_ids),
                "unique_accomplishments": list(unique_to_variant),
                "unique_count": len(unique_to_variant)
            })

        return diffs

    def _compare_skill_coverage(
        self,
        variants: List[TailoredResumeModel]
    ) -> Dict[str, Any]:
        """Compare skill coverage across variants."""
        diffs = {
            "by_variant": []
        }

        for variant in variants:
            coverage_data = {}
            if variant.skill_coverage_json:
                try:
                    coverage_data = json.loads(variant.skill_coverage_json)
                except json.JSONDecodeError:
                    pass

            diffs["by_variant"].append({
                "variant_id": variant.id,
                "variant_name": variant.variant_name or f"Variant {variant.variant_number}",
                "coverage_percentage": variant.coverage_percentage,
                "covered_skills": [
                    skill for skill, covered in coverage_data.items() if covered
                ],
                "missing_skills": [
                    skill for skill, covered in coverage_data.items() if not covered
                ]
            })

        return diffs
