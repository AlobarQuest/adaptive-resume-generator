"""Modern resume template.

A contemporary, two-column resume template with:
- Sans-serif fonts (Helvetica)
- Two-column layout (sidebar + main content)
- Accent colors for visual interest
- Modern, clean aesthetic
- Sidebar: Contact, Skills, Education, Certifications
- Main: Summary, Experience
"""

from typing import Dict, List, Any, Optional
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor

from ..base_template import BaseResumeTemplate, TemplateSpec, ResumeSection
from ..template_registry import TemplateRegistry
from .. import pdf_utils


# Define the modern template specification
MODERN_SPEC = TemplateSpec(
    name="modern",

    # Sans-serif font for modern look
    font_family="Helvetica",

    # Font sizes
    font_size_name=20,
    font_size_heading=14,
    font_size_subheading=11,
    font_size_body=10,
    font_size_small=9,

    # Margins (inches) - wider left margin for sidebar
    margin_top=0.5,
    margin_bottom=0.5,
    margin_left=0.5,
    margin_right=0.5,

    # Spacing
    line_spacing=1.2,
    section_spacing=0.15,
    subsection_spacing=0.10,

    # Colors (modern accent color)
    primary_color="#2C3E50",  # Dark blue-gray
    accent_color="#3498DB",   # Bright blue

    # Visual elements
    header_line=False,
    section_lines=True,
    bullet_style="■",  # Square bullet for modern look
)


@TemplateRegistry.register("modern", spec=MODERN_SPEC)
class ModernTemplate(BaseResumeTemplate):
    """Modern two-column resume template.

    Features:
    - Contemporary sans-serif typography
    - Two-column layout (sidebar + main content)
    - Accent colors for headers
    - Compact, efficient use of space
    - Sidebar: Contact, Skills, Education, Certifications
    - Main column: Name, Summary, Experience
    """

    # Layout constants
    SIDEBAR_WIDTH = 2.25 * inch  # Width of left sidebar
    SIDEBAR_PADDING = 0.15 * inch
    MAIN_COLUMN_PADDING = 0.2 * inch

    def __init__(self, spec: Optional[TemplateSpec] = None):
        """Initialize modern template.

        Args:
            spec: Template specification. Defaults to MODERN_SPEC if not provided.
        """
        super().__init__(spec or MODERN_SPEC)

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
        """Build the complete resume PDF with two-column layout.

        Args:
            canvas_obj: ReportLab canvas object
            profile: Profile data
            accomplishments: List of accomplishments
            education: List of education entries
            skills: List of skill names
            certifications: List of certifications
            options: Optional rendering options
        """
        options = options or {}

        # Start at top of page
        current_y = self._get_y_start()

        # Draw sidebar background
        self._draw_sidebar_background(canvas_obj)

        # Build main column (name, summary, experience)
        main_x = self._get_x_start() + self.SIDEBAR_WIDTH + self.MAIN_COLUMN_PADDING
        current_y = self._build_main_column(
            canvas_obj,
            profile,
            accomplishments,
            options.get('summary'),
            main_x,
            current_y
        )

        # Build sidebar (contact, skills, education, certifications)
        sidebar_x = self._get_x_start() + self.SIDEBAR_PADDING
        self._build_sidebar(
            canvas_obj,
            profile,
            skills,
            education,
            certifications,
            sidebar_x
        )

    def _draw_sidebar_background(self, canvas_obj: canvas.Canvas) -> None:
        """Draw light gray background for sidebar.

        Args:
            canvas_obj: ReportLab canvas
        """
        canvas_obj.setFillColor(HexColor("#F8F9FA"))  # Light gray
        canvas_obj.rect(
            self._get_x_start(),
            0,
            self.SIDEBAR_WIDTH,
            self.spec.page_height,
            fill=1,
            stroke=0
        )
        canvas_obj.setFillColor(HexColor("#000000"))  # Reset to black

    def _build_main_column(
        self,
        canvas_obj: canvas.Canvas,
        profile: Dict[str, Any],
        accomplishments: List[Dict[str, Any]],
        summary_text: Optional[str],
        x_start: float,
        current_y: float
    ) -> float:
        """Build main column with name, summary, and experience.

        Args:
            canvas_obj: ReportLab canvas
            profile: Profile data
            accomplishments: Accomplishments list
            summary_text: Optional summary
            x_start: X position for main column
            current_y: Starting Y position

        Returns:
            Final Y position
        """
        # Name (large, bold, accent color)
        name = profile.get('name', 'Your Name')
        font_bold = self._get_font_variant('bold')
        canvas_obj.setFillColor(self.spec.get_primary_color())
        canvas_obj.setFont(font_bold, self.spec.font_size_name)
        canvas_obj.drawString(x_start, current_y, name)
        current_y -= self.spec.font_size_name + 10
        canvas_obj.setFillColor(HexColor("#000000"))  # Reset color

        # Summary section
        if summary_text:
            current_y = self._build_summary_section(
                canvas_obj,
                summary_text,
                x_start,
                current_y
            )

        # Experience section
        if accomplishments:
            current_y = self._build_experience_section(
                canvas_obj,
                accomplishments,
                x_start,
                current_y
            )

        return current_y

    def _build_sidebar(
        self,
        canvas_obj: canvas.Canvas,
        profile: Dict[str, Any],
        skills: List[str],
        education: List[Dict[str, Any]],
        certifications: List[Dict[str, Any]],
        x_start: float
    ) -> None:
        """Build sidebar with contact, skills, education, certifications.

        Args:
            canvas_obj: ReportLab canvas
            profile: Profile data
            skills: Skills list
            education: Education list
            certifications: Certifications list
            x_start: X position for sidebar
        """
        sidebar_width = self.SIDEBAR_WIDTH - (2 * self.SIDEBAR_PADDING)
        current_y = self._get_y_start()

        # Contact section
        current_y = self._build_contact_section(
            canvas_obj,
            profile,
            x_start,
            sidebar_width,
            current_y
        )

        # Skills section
        if skills:
            current_y = self._build_skills_sidebar(
                canvas_obj,
                skills,
                x_start,
                sidebar_width,
                current_y
            )

        # Education section
        if education:
            current_y = self._build_education_sidebar(
                canvas_obj,
                education,
                x_start,
                sidebar_width,
                current_y
            )

        # Certifications section
        if certifications:
            current_y = self._build_certifications_sidebar(
                canvas_obj,
                certifications,
                x_start,
                sidebar_width,
                current_y
            )

    def _build_contact_section(
        self,
        canvas_obj: canvas.Canvas,
        profile: Dict[str, Any],
        x_start: float,
        max_width: float,
        current_y: float
    ) -> float:
        """Build contact information in sidebar.

        Args:
            canvas_obj: ReportLab canvas
            profile: Profile data
            x_start: X position
            max_width: Maximum width
            current_y: Current Y position

        Returns:
            New Y position
        """
        # Section header
        current_y -= 20  # Space from top
        font_bold = self._get_font_variant('bold')
        canvas_obj.setFillColor(self.spec.get_accent_color())
        canvas_obj.setFont(font_bold, self.spec.font_size_heading)
        canvas_obj.drawString(x_start, current_y, "CONTACT")
        current_y -= self.spec.font_size_heading + 8
        canvas_obj.setFillColor(HexColor("#000000"))

        # Contact details
        canvas_obj.setFont(self.spec.font_family, self.spec.font_size_small)

        contact_items = []
        if profile.get('email'):
            contact_items.append(profile['email'])
        if profile.get('phone'):
            contact_items.append(profile['phone'])

        location = pdf_utils.format_location(profile.get('city'), profile.get('state'))
        if location:
            contact_items.append(location)

        if profile.get('linkedin_url'):
            contact_items.append(profile['linkedin_url'])
        if profile.get('github_url'):
            contact_items.append(profile['github_url'])
        if profile.get('website_url'):
            contact_items.append(profile['website_url'])

        # Draw each contact item
        for item in contact_items:
            # Wrap if too long
            if len(item) > 30:
                lines = pdf_utils.wrap_text(item, max_length=30)
                for line in lines:
                    canvas_obj.drawString(x_start, current_y, line)
                    current_y -= self.spec.font_size_small + 3
            else:
                canvas_obj.drawString(x_start, current_y, item)
                current_y -= self.spec.font_size_small + 3

        current_y -= self.spec.section_spacing * 72

        return current_y

    def _build_skills_sidebar(
        self,
        canvas_obj: canvas.Canvas,
        skills: List[str],
        x_start: float,
        max_width: float,
        current_y: float
    ) -> float:
        """Build skills section in sidebar.

        Args:
            canvas_obj: ReportLab canvas
            skills: Skills list
            x_start: X position
            max_width: Maximum width
            current_y: Current Y position

        Returns:
            New Y position
        """
        # Section header
        font_bold = self._get_font_variant('bold')
        canvas_obj.setFillColor(self.spec.get_accent_color())
        canvas_obj.setFont(font_bold, self.spec.font_size_heading)
        canvas_obj.drawString(x_start, current_y, "SKILLS")
        current_y -= self.spec.font_size_heading + 8
        canvas_obj.setFillColor(HexColor("#000000"))

        # Skills list (each on own line for sidebar)
        canvas_obj.setFont(self.spec.font_family, self.spec.font_size_small)
        for skill in skills:
            canvas_obj.drawString(x_start, current_y, f"• {skill}")
            current_y -= self.spec.font_size_small + 3

        current_y -= self.spec.section_spacing * 72

        return current_y

    def _build_education_sidebar(
        self,
        canvas_obj: canvas.Canvas,
        education: List[Dict[str, Any]],
        x_start: float,
        max_width: float,
        current_y: float
    ) -> float:
        """Build education section in sidebar.

        Args:
            canvas_obj: ReportLab canvas
            education: Education list
            x_start: X position
            max_width: Maximum width
            current_y: Current Y position

        Returns:
            New Y position
        """
        # Section header
        font_bold = self._get_font_variant('bold')
        canvas_obj.setFillColor(self.spec.get_accent_color())
        canvas_obj.setFont(font_bold, self.spec.font_size_heading)
        canvas_obj.drawString(x_start, current_y, "EDUCATION")
        current_y -= self.spec.font_size_heading + 8
        canvas_obj.setFillColor(HexColor("#000000"))

        # Sort by graduation date
        sorted_education = pdf_utils.sort_by_date(education, date_key='graduation_date', descending=True)

        for edu in sorted_education:
            # Degree (bold)
            degree = edu.get('degree', 'Degree')
            canvas_obj.setFont(font_bold, self.spec.font_size_small)
            # Wrap degree if too long
            degree_lines = pdf_utils.wrap_text(degree, max_length=25)
            for line in degree_lines:
                canvas_obj.drawString(x_start, current_y, line)
                current_y -= self.spec.font_size_small + 2

            # Institution
            institution = edu.get('institution', 'Institution')
            canvas_obj.setFont(self.spec.font_family, self.spec.font_size_small)
            inst_lines = pdf_utils.wrap_text(institution, max_length=25)
            for line in inst_lines:
                canvas_obj.drawString(x_start, current_y, line)
                current_y -= self.spec.font_size_small + 2

            # Year
            if edu.get('graduation_date'):
                date_str = self._format_date_range(edu['graduation_date'], None, False)
                canvas_obj.drawString(x_start, current_y, date_str)
                current_y -= self.spec.font_size_small + 2

            # GPA if present
            gpa = pdf_utils.format_gpa(edu.get('gpa'))
            if gpa:
                canvas_obj.drawString(x_start, current_y, f"GPA: {gpa}")
                current_y -= self.spec.font_size_small + 2

            current_y -= self.spec.subsection_spacing * 72

        current_y -= self.spec.section_spacing * 72

        return current_y

    def _build_certifications_sidebar(
        self,
        canvas_obj: canvas.Canvas,
        certifications: List[Dict[str, Any]],
        x_start: float,
        max_width: float,
        current_y: float
    ) -> float:
        """Build certifications section in sidebar.

        Args:
            canvas_obj: ReportLab canvas
            certifications: Certifications list
            x_start: X position
            max_width: Maximum width
            current_y: Current Y position

        Returns:
            New Y position
        """
        # Section header
        font_bold = self._get_font_variant('bold')
        canvas_obj.setFillColor(self.spec.get_accent_color())
        canvas_obj.setFont(font_bold, self.spec.font_size_heading)
        canvas_obj.drawString(x_start, current_y, "CERTIFICATIONS")
        current_y -= self.spec.font_size_heading + 8
        canvas_obj.setFillColor(HexColor("#000000"))

        # Sort by date
        sorted_certs = pdf_utils.sort_by_date(certifications, date_key='date_obtained', descending=True)

        for cert in sorted_certs:
            # Cert name (bold)
            cert_name = cert.get('name', 'Certification')
            canvas_obj.setFont(font_bold, self.spec.font_size_small)
            name_lines = pdf_utils.wrap_text(cert_name, max_length=25)
            for line in name_lines:
                canvas_obj.drawString(x_start, current_y, line)
                current_y -= self.spec.font_size_small + 2

            # Organization
            org = cert.get('issuing_organization', '')
            if org:
                canvas_obj.setFont(self.spec.font_family, self.spec.font_size_small)
                org_lines = pdf_utils.wrap_text(org, max_length=25)
                for line in org_lines:
                    canvas_obj.drawString(x_start, current_y, line)
                    current_y -= self.spec.font_size_small + 2

            # Year
            if cert.get('date_obtained'):
                date_str = self._format_date_range(cert['date_obtained'], None, False)
                canvas_obj.drawString(x_start, current_y, date_str)
                current_y -= self.spec.font_size_small + 2

            current_y -= self.spec.subsection_spacing * 72

        current_y -= self.spec.section_spacing * 72

        return current_y

    def _build_summary_section(
        self,
        canvas_obj: canvas.Canvas,
        summary_text: str,
        x_start: float,
        current_y: float
    ) -> float:
        """Build summary section in main column.

        Args:
            canvas_obj: ReportLab canvas
            summary_text: Summary text
            x_start: X position
            current_y: Current Y position

        Returns:
            New Y position
        """
        # Section header
        font_bold = self._get_font_variant('bold')
        canvas_obj.setFillColor(self.spec.get_accent_color())
        canvas_obj.setFont(font_bold, self.spec.font_size_heading)
        canvas_obj.drawString(x_start, current_y, "SUMMARY")
        current_y -= self.spec.font_size_heading + 8
        canvas_obj.setFillColor(HexColor("#000000"))

        # Summary text
        cleaned_text = pdf_utils.clean_text(summary_text)
        canvas_obj.setFont(self.spec.font_family, self.spec.font_size_body)

        # Calculate main column width
        main_width = self.spec.get_content_width() - self.SIDEBAR_WIDTH - self.MAIN_COLUMN_PADDING
        chars_per_line = int(main_width / (self.spec.font_size_body * 0.5))
        lines = pdf_utils.wrap_text(cleaned_text, max_length=chars_per_line)

        for line in lines:
            canvas_obj.drawString(x_start, current_y, line)
            current_y -= self.spec.font_size_body + 4

        current_y -= self.spec.section_spacing * 72

        return current_y

    def _build_experience_section(
        self,
        canvas_obj: canvas.Canvas,
        accomplishments: List[Dict[str, Any]],
        x_start: float,
        current_y: float
    ) -> float:
        """Build experience section in main column.

        Args:
            canvas_obj: ReportLab canvas
            accomplishments: Accomplishments list
            x_start: X position
            current_y: Current Y position

        Returns:
            New Y position
        """
        # Section header
        font_bold = self._get_font_variant('bold')
        canvas_obj.setFillColor(self.spec.get_accent_color())
        canvas_obj.setFont(font_bold, self.spec.font_size_heading)
        canvas_obj.drawString(x_start, current_y, "EXPERIENCE")
        current_y -= self.spec.font_size_heading + 8
        canvas_obj.setFillColor(HexColor("#000000"))

        # Group by company
        grouped = pdf_utils.group_by_company(accomplishments)

        # Sort companies by date
        company_dates = {}
        for company, items in grouped.items():
            sorted_items = pdf_utils.sort_by_date(items, date_key='start_date', descending=True)
            if sorted_items and sorted_items[0].get('start_date'):
                company_dates[company] = sorted_items[0]['start_date']
            else:
                company_dates[company] = ''

        sorted_companies = sorted(
            grouped.keys(),
            key=lambda c: company_dates.get(c, ''),
            reverse=True
        )

        # Calculate main column width
        main_width = self.spec.get_content_width() - self.SIDEBAR_WIDTH - self.MAIN_COLUMN_PADDING
        bullet_indent = 0.2 * inch

        for company in sorted_companies:
            items = grouped[company]
            first_item = items[0]

            # Job title (bold)
            job_title = first_item.get('job_title', 'Position')
            canvas_obj.setFont(font_bold, self.spec.font_size_subheading)
            canvas_obj.drawString(x_start, current_y, job_title)
            current_y -= self.spec.font_size_subheading + 3

            # Company and date
            company_name = first_item.get('company_name', company)
            date_range = self._format_date_range(
                first_item.get('start_date'),
                first_item.get('end_date'),
                first_item.get('is_current', False)
            )

            company_date = f"{company_name}"
            if date_range:
                company_date += f" | {date_range}"

            canvas_obj.setFont(self.spec.font_family, self.spec.font_size_small)
            canvas_obj.drawString(x_start, current_y, company_date)
            current_y -= self.spec.font_size_small + 6

            # Accomplishments
            canvas_obj.setFont(self.spec.font_family, self.spec.font_size_body)

            for item in items:
                text = item.get('text', '')
                if not text:
                    continue

                # Draw bullet
                canvas_obj.drawString(x_start, current_y, self.spec.bullet_style)

                # Wrap text
                cleaned_text = pdf_utils.clean_text(text)
                bullet_width = canvas_obj.stringWidth(self.spec.bullet_style, self.spec.font_family, self.spec.font_size_body)
                available_width = main_width - bullet_indent - bullet_width - 5
                chars_per_line = int(available_width / (self.spec.font_size_body * 0.5))
                lines = pdf_utils.wrap_text(cleaned_text, max_length=chars_per_line)

                # First line
                if lines:
                    canvas_obj.drawString(x_start + bullet_indent, current_y, lines[0])
                    current_y -= self.spec.font_size_body + 2

                    # Subsequent lines
                    for line in lines[1:]:
                        canvas_obj.drawString(x_start + bullet_indent, current_y, line)
                        current_y -= self.spec.font_size_body + 2

            current_y -= self.spec.subsection_spacing * 72

        current_y -= self.spec.section_spacing * 72

        return current_y
