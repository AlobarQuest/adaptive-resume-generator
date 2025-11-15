"""Resume PDF Generator Service.

Main service for generating professional PDF resumes from TailoredResume data.
Transforms database models into template format and generates PDFs using ReportLab.
"""

import json
from io import BytesIO
from pathlib import Path
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from adaptive_resume.models.tailored_resume import TailoredResumeModel
from adaptive_resume.models.profile import Profile
from adaptive_resume.models.bullet_point import BulletPoint
from adaptive_resume.models.education import Education
from adaptive_resume.models.skill import Skill
from adaptive_resume.models.certification import Certification
from adaptive_resume.pdf.template_registry import TemplateRegistry, TemplateRegistryError


class ResumePDFGeneratorError(Exception):
    """Base exception for PDF generation errors."""
    pass


class ResumePDFGenerator:
    """Service for generating resume PDFs from TailoredResume data.

    This service handles:
    - Loading related data (profile, accomplishments, education, skills, certifications)
    - Transforming database models to template-compatible format
    - PDF generation using selected templates
    - Preview and file output options
    """

    def __init__(self, session: Session):
        """Initialize PDF generator service.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def generate_pdf(
        self,
        tailored_resume_id: int,
        template_name: str = "classic",
        output_path: Optional[str] = None,
        include_summary: bool = True,
        summary_text: Optional[str] = None
    ) -> bytes:
        """Generate PDF resume from TailoredResume.

        Args:
            tailored_resume_id: ID of TailoredResumeModel to generate
            template_name: Name of template to use (default: "classic")
            output_path: Optional file path to save PDF
            include_summary: Whether to include professional summary section
            summary_text: Custom summary text (uses profile summary if None)

        Returns:
            PDF content as bytes

        Raises:
            ResumePDFGeneratorError: If generation fails
            TemplateRegistryError: If template not found
        """
        # Load tailored resume with relationships
        tailored_resume = self._load_tailored_resume(tailored_resume_id)

        # Load all related data
        profile_data = self._transform_profile(tailored_resume.profile)
        accomplishments_data = self._transform_accomplishments(tailored_resume)
        education_data = self._transform_education(tailored_resume.profile)
        skills_data = self._transform_skills(tailored_resume.profile)
        certifications_data = self._transform_certifications(tailored_resume.profile)

        # Prepare options
        options = {}
        if include_summary:
            options['summary'] = summary_text or tailored_resume.profile.professional_summary

        # Generate PDF
        pdf_bytes = self._generate_pdf_with_template(
            template_name=template_name,
            profile=profile_data,
            accomplishments=accomplishments_data,
            education=education_data,
            skills=skills_data,
            certifications=certifications_data,
            options=options
        )

        # Save to file if path provided
        if output_path:
            self._save_to_file(pdf_bytes, output_path)

        return pdf_bytes

    def preview_pdf(
        self,
        tailored_resume_id: int,
        template_name: str = "classic",
        include_summary: bool = True,
        summary_text: Optional[str] = None
    ) -> BytesIO:
        """Generate PDF preview as BytesIO buffer.

        Same as generate_pdf but returns BytesIO for preview purposes.

        Args:
            tailored_resume_id: ID of TailoredResumeModel
            template_name: Template to use
            include_summary: Include summary section
            summary_text: Custom summary text

        Returns:
            BytesIO buffer containing PDF

        Raises:
            ResumePDFGeneratorError: If generation fails
        """
        pdf_bytes = self.generate_pdf(
            tailored_resume_id=tailored_resume_id,
            template_name=template_name,
            output_path=None,
            include_summary=include_summary,
            summary_text=summary_text
        )

        buffer = BytesIO(pdf_bytes)
        buffer.seek(0)
        return buffer

    def save_pdf(
        self,
        tailored_resume_id: int,
        output_path: str,
        template_name: str = "classic",
        include_summary: bool = True,
        summary_text: Optional[str] = None
    ) -> Path:
        """Generate and save PDF to file.

        Args:
            tailored_resume_id: ID of TailoredResumeModel
            output_path: File path to save PDF
            template_name: Template to use
            include_summary: Include summary section
            summary_text: Custom summary text

        Returns:
            Path object of saved file

        Raises:
            ResumePDFGeneratorError: If generation or save fails
        """
        pdf_bytes = self.generate_pdf(
            tailored_resume_id=tailored_resume_id,
            template_name=template_name,
            output_path=output_path,
            include_summary=include_summary,
            summary_text=summary_text
        )

        return Path(output_path)

    def list_available_templates(self) -> List[str]:
        """List all available resume templates.

        Returns:
            List of template names
        """
        return TemplateRegistry.list_templates()

    # Private helper methods

    def _load_tailored_resume(self, tailored_resume_id: int) -> TailoredResumeModel:
        """Load TailoredResume with all relationships.

        Args:
            tailored_resume_id: TailoredResume ID

        Returns:
            TailoredResumeModel with loaded relationships

        Raises:
            ResumePDFGeneratorError: If not found
        """
        tailored_resume = self.session.query(TailoredResumeModel).filter_by(
            id=tailored_resume_id
        ).first()

        if not tailored_resume:
            raise ResumePDFGeneratorError(
                f"TailoredResume with ID {tailored_resume_id} not found"
            )

        # Ensure relationships are loaded
        _ = tailored_resume.profile
        _ = tailored_resume.job_posting

        return tailored_resume

    def _transform_profile(self, profile: Profile) -> Dict[str, Any]:
        """Transform Profile model to template format.

        Args:
            profile: Profile model

        Returns:
            Dictionary with profile data
        """
        return {
            'name': profile.full_name,
            'email': profile.email,
            'phone': profile.phone,
            'city': profile.city,
            'state': profile.state,
            'linkedin_url': profile.linkedin_url,
            'github_url': None,  # Not in Profile model yet
            'website_url': profile.portfolio_url,
        }

    def _transform_accomplishments(
        self,
        tailored_resume: TailoredResumeModel
    ) -> List[Dict[str, Any]]:
        """Transform selected accomplishments to template format.

        Args:
            tailored_resume: TailoredResume with selected accomplishment IDs

        Returns:
            List of accomplishment dictionaries
        """
        # Parse selected accomplishment IDs
        try:
            selected_ids = json.loads(tailored_resume.selected_accomplishment_ids)
        except (json.JSONDecodeError, TypeError):
            selected_ids = []

        if not selected_ids:
            return []

        # Load selected bullet points
        bullet_points = self.session.query(BulletPoint).filter(
            BulletPoint.id.in_(selected_ids)
        ).all()

        # Transform to template format
        accomplishments = []
        for bullet in bullet_points:
            # Load job relationship
            job = bullet.job

            # Parse location (may be "City, ST" format)
            city = None
            state = None
            if job and job.location:
                parts = job.location.split(',')
                if len(parts) == 2:
                    city = parts[0].strip()
                    state = parts[1].strip()
                else:
                    city = job.location.strip()

            accomplishments.append({
                'id': bullet.id,
                'text': bullet.content,  # BulletPoint uses 'content' field
                'company_name': job.company_name if job else 'Unknown',
                'job_title': job.job_title if job else 'Position',
                'start_date': str(job.start_date) if job and job.start_date else None,
                'end_date': str(job.end_date) if job and job.end_date else None,
                'is_current': job.is_current if job else False,
                'city': city,
                'state': state,
            })

        return accomplishments

    def _transform_education(self, profile: Profile) -> List[Dict[str, Any]]:
        """Transform Education models to template format.

        Args:
            profile: Profile with education relationship

        Returns:
            List of education dictionaries
        """
        education_list = []

        for edu in profile.education:
            education_list.append({
                'id': edu.id,
                'degree': edu.degree,
                'field_of_study': edu.field_of_study,
                'institution': edu.institution,
                'graduation_date': str(edu.end_date) if edu.end_date else None,
                'gpa': float(edu.gpa) if edu.gpa else None,
                'city': None,  # Education model doesn't have location fields
                'state': None,
            })

        return education_list

    def _transform_skills(self, profile: Profile) -> List[str]:
        """Transform Skill models to template format.

        Args:
            profile: Profile with skills relationship

        Returns:
            List of skill names
        """
        return [skill.skill_name for skill in profile.skills]

    def _transform_certifications(self, profile: Profile) -> List[Dict[str, Any]]:
        """Transform Certification models to template format.

        Args:
            profile: Profile with certifications relationship

        Returns:
            List of certification dictionaries
        """
        certifications = []

        for cert in profile.certifications:
            certifications.append({
                'id': cert.id,
                'name': cert.name,
                'issuing_organization': cert.issuing_organization,
                'date_obtained': str(cert.issue_date) if cert.issue_date else None,
                'expiration_date': str(cert.expiration_date) if cert.expiration_date else None,
                'credential_id': cert.credential_id,
                'credential_url': cert.credential_url,
            })

        return certifications

    def _generate_pdf_with_template(
        self,
        template_name: str,
        profile: Dict[str, Any],
        accomplishments: List[Dict[str, Any]],
        education: List[Dict[str, Any]],
        skills: List[str],
        certifications: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Generate PDF using specified template.

        Args:
            template_name: Name of registered template
            profile: Profile data
            accomplishments: Accomplishments data
            education: Education data
            skills: Skills list
            certifications: Certifications data
            options: Template options

        Returns:
            PDF bytes

        Raises:
            TemplateRegistryError: If template not found
            ResumePDFGeneratorError: If generation fails
        """
        try:
            # Get template class
            template_class = TemplateRegistry.get_template(template_name)

            # Get template spec (if registered)
            spec = TemplateRegistry.get_spec(template_name)

            # Instantiate template
            if spec:
                template = template_class(spec)
            else:
                template = template_class()

            # Create PDF in memory
            buffer = BytesIO()
            pdf_canvas = canvas.Canvas(buffer, pagesize=letter)

            # Build resume using template
            template.build_resume(
                canvas_obj=pdf_canvas,
                profile=profile,
                accomplishments=accomplishments,
                education=education,
                skills=skills,
                certifications=certifications,
                options=options
            )

            # Finalize PDF
            pdf_canvas.save()

            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()

            return pdf_bytes

        except TemplateRegistryError:
            raise  # Re-raise template errors
        except Exception as e:
            raise ResumePDFGeneratorError(
                f"Failed to generate PDF with template '{template_name}': {str(e)}"
            ) from e

    def _save_to_file(self, pdf_bytes: bytes, output_path: str) -> None:
        """Save PDF bytes to file.

        Args:
            pdf_bytes: PDF content
            output_path: File path

        Raises:
            ResumePDFGeneratorError: If save fails
        """
        try:
            path = Path(output_path)

            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write PDF to file
            with open(path, 'wb') as f:
                f.write(pdf_bytes)

        except Exception as e:
            raise ResumePDFGeneratorError(
                f"Failed to save PDF to '{output_path}': {str(e)}"
            ) from e
