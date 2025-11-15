"""Classic resume template.

A traditional, professional resume template with:
- Serif font (Times-Roman)
- Bold, uppercase section headers
- Clean formatting with bullet points
- Single column layout
- Professional spacing
"""

from typing import Dict, List, Any, Optional
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_LEFT, TA_CENTER

from ..base_template import BaseResumeTemplate, TemplateSpec, ResumeSection
from ..template_registry import TemplateRegistry
from .. import pdf_utils


# Define the classic template specification
CLASSIC_SPEC = TemplateSpec(
    name="classic",

    # Serif font for professional look
    font_family="Times-Roman",

    # Font sizes
    font_size_name=18,
    font_size_heading=12,
    font_size_subheading=11,
    font_size_body=10,
    font_size_small=9,

    # Margins (inches)
    margin_top=0.75,
    margin_bottom=0.75,
    margin_left=0.75,
    margin_right=0.75,

    # Spacing
    line_spacing=1.15,
    section_spacing=0.20,
    subsection_spacing=0.12,

    # Colors (black and white for traditional look)
    primary_color="#000000",
    accent_color="#000000",

    # Visual elements
    header_line=True,
    section_lines=False,
    bullet_style="•",
)


@TemplateRegistry.register("classic", spec=CLASSIC_SPEC)
class ClassicTemplate(BaseResumeTemplate):
    """Classic professional resume template.

    Features:
    - Traditional serif typography
    - Clean single-column layout
    - Bold section headers
    - Bullet point accomplishments
    - Emphasis on readability and professionalism
    """

    def __init__(self, spec: Optional[TemplateSpec] = None):
        """Initialize classic template.

        Args:
            spec: Template specification. Defaults to CLASSIC_SPEC if not provided.
        """
        super().__init__(spec or CLASSIC_SPEC)

    def build_resume(
        self,
        canvas_obj: canvas.Canvas,
        profile: Dict[str, Any],
        accomplishments: List[Dict[str, Any]],
        education: List[Dict[str, Any]],
        skills: List[str],
        certifications: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None
    ) -> None:
        """Build the complete resume PDF.

        Args:
            canvas_obj: ReportLab canvas object
            profile: Profile data (name, email, phone, location, etc.)
            accomplishments: List of accomplishment/bullet point dicts
            education: List of education dicts
            skills: List of skill names
            certifications: List of certification dicts
            options: Optional rendering options (e.g., section order, summary text)
        """
        options = options or {}

        # Start at top of page
        current_y = self._get_y_start()

        # Build each section
        current_y = self._build_header(canvas_obj, profile, current_y)

        # Optional summary section
        if options.get('summary'):
            current_y = self._build_summary(canvas_obj, options['summary'], current_y)

        # Experience section (accomplishments grouped by company)
        if accomplishments:
            current_y = self._build_experience(canvas_obj, accomplishments, current_y)

        # Education section
        if education:
            current_y = self._build_education(canvas_obj, education, current_y)

        # Skills section
        if skills:
            current_y = self._build_skills(canvas_obj, skills, current_y)

        # Certifications section
        if certifications:
            current_y = self._build_certifications(canvas_obj, certifications, current_y)

    def _build_header(
        self,
        canvas_obj: canvas.Canvas,
        profile: Dict[str, Any],
        current_y: float
    ) -> float:
        """Build the header section with name and contact info.

        Args:
            canvas_obj: ReportLab canvas
            profile: Profile data
            current_y: Current Y position

        Returns:
            New Y position after header
        """
        x_start = self._get_x_start()
        content_width = self.spec.get_content_width()

        # Name (centered, large, bold)
        name = profile.get('name', 'Your Name')
        font_bold = self._get_font_variant('bold')
        canvas_obj.setFont(font_bold, self.spec.font_size_name)
        name_width = canvas_obj.stringWidth(name, font_bold, self.spec.font_size_name)
        name_x = x_start + (content_width - name_width) / 2
        canvas_obj.drawString(name_x, current_y, name)
        current_y -= self.spec.font_size_name + 6

        # Contact info (centered, smaller)
        contact_parts = []

        if profile.get('email'):
            contact_parts.append(profile['email'])

        if profile.get('phone'):
            contact_parts.append(profile['phone'])

        # Location
        location = pdf_utils.format_location(
            profile.get('city'),
            profile.get('state')
        )
        if location:
            contact_parts.append(location)

        # LinkedIn
        if profile.get('linkedin_url'):
            contact_parts.append(profile['linkedin_url'])

        # GitHub
        if profile.get('github_url'):
            contact_parts.append(profile['github_url'])

        # Website
        if profile.get('website_url'):
            contact_parts.append(profile['website_url'])

        # Draw contact info line
        if contact_parts:
            contact_line = " | ".join(contact_parts)
            canvas_obj.setFont(self.spec.font_family, self.spec.font_size_small)
            contact_width = canvas_obj.stringWidth(contact_line, self.spec.font_family, self.spec.font_size_small)
            contact_x = x_start + (content_width - contact_width) / 2
            canvas_obj.drawString(contact_x, current_y, contact_line)
            current_y -= self.spec.font_size_small + 4

        # Optional horizontal line under header
        if self.spec.header_line:
            current_y -= 4
            self._draw_horizontal_line(
                canvas_obj,
                x_start,
                current_y,
                content_width,
                thickness=1
            )
            current_y -= 6

        # Add section spacing
        current_y -= self.spec.section_spacing * 72

        return current_y

    def _build_summary(
        self,
        canvas_obj: canvas.Canvas,
        summary_text: str,
        current_y: float
    ) -> float:
        """Build the professional summary section.

        Args:
            canvas_obj: ReportLab canvas
            summary_text: Summary text
            current_y: Current Y position

        Returns:
            New Y position after summary
        """
        x_start = self._get_x_start()
        content_width = self.spec.get_content_width()

        # Check page break
        current_y = self._check_page_break(canvas_obj, current_y, 100)

        # Section header
        font_bold = self._get_font_variant('bold')
        canvas_obj.setFont(font_bold, self.spec.font_size_heading)
        canvas_obj.drawString(x_start, current_y, "PROFESSIONAL SUMMARY")
        current_y -= self.spec.font_size_heading + 8

        # Summary text
        cleaned_text = pdf_utils.clean_text(summary_text)
        canvas_obj.setFont(self.spec.font_family, self.spec.font_size_body)

        # Wrap text to fit width
        lines = pdf_utils.wrap_text(cleaned_text, max_length=100)
        for line in lines:
            current_y = self._check_page_break(canvas_obj, current_y, self.spec.font_size_body + 4)
            canvas_obj.drawString(x_start, current_y, line)
            current_y -= self.spec.font_size_body + 4

        # Add section spacing
        current_y -= self.spec.section_spacing * 72

        return current_y

    def _build_experience(
        self,
        canvas_obj: canvas.Canvas,
        accomplishments: List[Dict[str, Any]],
        current_y: float
    ) -> float:
        """Build the work experience section.

        Args:
            canvas_obj: ReportLab canvas
            accomplishments: List of accomplishments
            current_y: Current Y position

        Returns:
            New Y position after experience
        """
        x_start = self._get_x_start()
        content_width = self.spec.get_content_width()
        bullet_indent = 0.25 * 72  # 0.25 inch indent for bullets

        # Check page break
        current_y = self._check_page_break(canvas_obj, current_y, 100)

        # Section header
        font_bold = self._get_font_variant('bold')
        canvas_obj.setFont(font_bold, self.spec.font_size_heading)
        canvas_obj.drawString(x_start, current_y, "WORK EXPERIENCE")
        current_y -= self.spec.font_size_heading + 8

        # Group accomplishments by company
        grouped = pdf_utils.group_by_company(accomplishments)

        # Sort companies by most recent start date
        company_dates = {}
        for company, items in grouped.items():
            # Get most recent start date for this company
            sorted_items = pdf_utils.sort_by_date(items, date_key='start_date', descending=True)
            if sorted_items and sorted_items[0].get('start_date'):
                company_dates[company] = sorted_items[0]['start_date']
            else:
                company_dates[company] = ''

        # Sort companies by date
        sorted_companies = sorted(
            grouped.keys(),
            key=lambda c: company_dates.get(c, ''),
            reverse=True
        )

        # Render each company's experience
        for company in sorted_companies:
            items = grouped[company]

            # Check page break for company section
            current_y = self._check_page_break(canvas_obj, current_y, 80)

            # Get job title and dates from first accomplishment
            first_item = items[0]
            job_title = first_item.get('job_title', 'Position')
            company_name = first_item.get('company_name', company)

            # Company and title line (bold)
            font_bold = self._get_font_variant('bold')
            font_italic = self._get_font_variant('italic')
            canvas_obj.setFont(font_bold, self.spec.font_size_subheading)

            # Job title
            canvas_obj.drawString(x_start, current_y, job_title)

            # Company name on same line
            title_width = canvas_obj.stringWidth(job_title, font_bold, self.spec.font_size_subheading)
            canvas_obj.setFont(font_italic, self.spec.font_size_subheading)
            canvas_obj.drawString(x_start + title_width + 10, current_y, f"- {company_name}")
            current_y -= self.spec.font_size_subheading + 4

            # Date range and location
            date_range = self._format_date_range(
                first_item.get('start_date'),
                first_item.get('end_date'),
                first_item.get('is_current', False)
            )

            location = pdf_utils.format_location(
                first_item.get('city'),
                first_item.get('state')
            )

            location_date_parts = []
            if location:
                location_date_parts.append(location)
            if date_range:
                location_date_parts.append(date_range)

            if location_date_parts:
                location_date_line = " | ".join(location_date_parts)
                canvas_obj.setFont(self.spec.font_family, self.spec.font_size_small)
                canvas_obj.drawString(x_start, current_y, location_date_line)
                current_y -= self.spec.font_size_small + 6

            # Accomplishment bullets
            canvas_obj.setFont(self.spec.font_family, self.spec.font_size_body)

            for item in items:
                text = item.get('text', '')
                if not text:
                    continue

                # Check page break
                current_y = self._check_page_break(canvas_obj, current_y, 30)

                # Draw bullet
                canvas_obj.drawString(x_start, current_y, self.spec.bullet_style)

                # Wrap and draw text
                cleaned_text = pdf_utils.clean_text(text)
                # Calculate available width for bullet text
                bullet_width = canvas_obj.stringWidth(self.spec.bullet_style, self.spec.font_family, self.spec.font_size_body)
                available_width = content_width - bullet_indent - bullet_width - 5
                chars_per_line = int(available_width / (self.spec.font_size_body * 0.5))

                lines = pdf_utils.wrap_text(cleaned_text, max_length=chars_per_line)

                # First line (on same line as bullet)
                if lines:
                    canvas_obj.drawString(x_start + bullet_indent, current_y, lines[0])
                    current_y -= self.spec.font_size_body + 3

                    # Subsequent lines (indented further)
                    for line in lines[1:]:
                        current_y = self._check_page_break(canvas_obj, current_y, self.spec.font_size_body + 3)
                        canvas_obj.drawString(x_start + bullet_indent, current_y, line)
                        current_y -= self.spec.font_size_body + 3

            # Space between companies
            current_y -= self.spec.subsection_spacing * 72

        # Add section spacing
        current_y -= self.spec.section_spacing * 72

        return current_y

    def _build_education(
        self,
        canvas_obj: canvas.Canvas,
        education: List[Dict[str, Any]],
        current_y: float
    ) -> float:
        """Build the education section.

        Args:
            canvas_obj: ReportLab canvas
            education: List of education entries
            current_y: Current Y position

        Returns:
            New Y position after education
        """
        x_start = self._get_x_start()

        # Check page break
        current_y = self._check_page_break(canvas_obj, current_y, 100)

        # Section header
        font_bold = self._get_font_variant('bold')
        canvas_obj.setFont(font_bold, self.spec.font_size_heading)
        canvas_obj.drawString(x_start, current_y, "EDUCATION")
        current_y -= self.spec.font_size_heading + 8

        # Sort by graduation date (most recent first)
        sorted_education = pdf_utils.sort_by_date(education, date_key='graduation_date', descending=True)

        for edu in sorted_education:
            # Check page break
            current_y = self._check_page_break(canvas_obj, current_y, 60)

            # Degree and institution (bold)
            degree = edu.get('degree', 'Degree')
            institution = edu.get('institution', 'Institution')

            font_bold = self._get_font_variant('bold')
            font_italic = self._get_font_variant('italic')
            canvas_obj.setFont(font_bold, self.spec.font_size_subheading)
            canvas_obj.drawString(x_start, current_y, degree)

            # Institution on same line
            degree_width = canvas_obj.stringWidth(degree, font_bold, self.spec.font_size_subheading)
            canvas_obj.setFont(font_italic, self.spec.font_size_subheading)
            canvas_obj.drawString(x_start + degree_width + 10, current_y, f"- {institution}")
            current_y -= self.spec.font_size_subheading + 4

            # Graduation date, GPA, location
            info_parts = []

            location = pdf_utils.format_location(
                edu.get('city'),
                edu.get('state')
            )
            if location:
                info_parts.append(location)

            if edu.get('graduation_date'):
                # Format as "Month Year"
                grad_date = self._format_date_range(edu['graduation_date'], None, False)
                if grad_date:
                    info_parts.append(f"Graduated: {grad_date}")

            gpa = pdf_utils.format_gpa(edu.get('gpa'))
            if gpa:
                info_parts.append(f"GPA: {gpa}")

            if info_parts:
                info_line = " | ".join(info_parts)
                canvas_obj.setFont(self.spec.font_family, self.spec.font_size_small)
                canvas_obj.drawString(x_start, current_y, info_line)
                current_y -= self.spec.font_size_small + 4

            # Field of study (if different from degree)
            if edu.get('field_of_study') and edu['field_of_study'] not in degree:
                canvas_obj.setFont(self.spec.font_family, self.spec.font_size_body)
                canvas_obj.drawString(x_start, current_y, f"Field of Study: {edu['field_of_study']}")
                current_y -= self.spec.font_size_body + 4

            # Space between entries
            current_y -= self.spec.subsection_spacing * 72

        # Add section spacing
        current_y -= self.spec.section_spacing * 72

        return current_y

    def _build_skills(
        self,
        canvas_obj: canvas.Canvas,
        skills: List[str],
        current_y: float
    ) -> float:
        """Build the skills section.

        Args:
            canvas_obj: ReportLab canvas
            skills: List of skill names
            current_y: Current Y position

        Returns:
            New Y position after skills
        """
        x_start = self._get_x_start()
        content_width = self.spec.get_content_width()

        # Check page break
        current_y = self._check_page_break(canvas_obj, current_y, 100)

        # Section header
        font_bold = self._get_font_variant('bold')
        canvas_obj.setFont(font_bold, self.spec.font_size_heading)
        canvas_obj.drawString(x_start, current_y, "SKILLS")
        current_y -= self.spec.font_size_heading + 8

        # Format skills as comma-separated list
        skills_text = ", ".join(skills)
        cleaned_text = pdf_utils.clean_text(skills_text)

        # Wrap to fit width
        canvas_obj.setFont(self.spec.font_family, self.spec.font_size_body)
        chars_per_line = int(content_width / (self.spec.font_size_body * 0.5))
        lines = pdf_utils.wrap_text(cleaned_text, max_length=chars_per_line)

        for line in lines:
            current_y = self._check_page_break(canvas_obj, current_y, self.spec.font_size_body + 4)
            canvas_obj.drawString(x_start, current_y, line)
            current_y -= self.spec.font_size_body + 4

        # Add section spacing
        current_y -= self.spec.section_spacing * 72

        return current_y

    def _build_certifications(
        self,
        canvas_obj: canvas.Canvas,
        certifications: List[Dict[str, Any]],
        current_y: float
    ) -> float:
        """Build the certifications section.

        Args:
            canvas_obj: ReportLab canvas
            certifications: List of certification dicts
            current_y: Current Y position

        Returns:
            New Y position after certifications
        """
        x_start = self._get_x_start()

        # Check page break
        current_y = self._check_page_break(canvas_obj, current_y, 100)

        # Section header
        font_bold = self._get_font_variant('bold')
        canvas_obj.setFont(font_bold, self.spec.font_size_heading)
        canvas_obj.drawString(x_start, current_y, "CERTIFICATIONS")
        current_y -= self.spec.font_size_heading + 8

        # Sort by date (most recent first)
        sorted_certs = pdf_utils.sort_by_date(certifications, date_key='date_obtained', descending=True)

        for cert in sorted_certs:
            # Check page break
            current_y = self._check_page_break(canvas_obj, current_y, 40)

            # Certification name (bold)
            cert_name = cert.get('name', 'Certification')
            font_bold = self._get_font_variant('bold')
            canvas_obj.setFont(font_bold, self.spec.font_size_body)
            canvas_obj.drawString(x_start, current_y, cert_name)
            current_y -= self.spec.font_size_body + 4

            # Issuing organization and date
            info_parts = []

            if cert.get('issuing_organization'):
                info_parts.append(cert['issuing_organization'])

            if cert.get('date_obtained'):
                date_str = self._format_date_range(cert['date_obtained'], None, False)
                if date_str:
                    info_parts.append(f"Obtained: {date_str}")

            if cert.get('expiration_date'):
                exp_date = self._format_date_range(cert['expiration_date'], None, False)
                if exp_date:
                    info_parts.append(f"Expires: {exp_date}")

            if info_parts:
                info_line = " | ".join(info_parts)
                canvas_obj.setFont(self.spec.font_family, self.spec.font_size_small)
                canvas_obj.drawString(x_start, current_y, info_line)
                current_y -= self.spec.font_size_small + 4

            # Credential ID if available
            if cert.get('credential_id'):
                canvas_obj.setFont(self.spec.font_family, self.spec.font_size_small)
                canvas_obj.drawString(x_start, current_y, f"Credential ID: {cert['credential_id']}")
                current_y -= self.spec.font_size_small + 4

            # Space between entries
            current_y -= self.spec.subsection_spacing * 72

        # Add section spacing (smaller since it's last section typically)
        current_y -= (self.spec.section_spacing * 72) / 2

        return current_y
