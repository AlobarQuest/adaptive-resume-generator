"""ATS-Friendly resume template - simple structure optimized for parsing."""

from typing import Dict, List, Any, Optional
from reportlab.pdfgen import canvas
from ..base_template import BaseResumeTemplate, TemplateSpec
from ..template_registry import TemplateRegistry
from .. import pdf_utils

ATS_FRIENDLY_SPEC = TemplateSpec(
    name="ats-friendly",
    font_family="Times-Roman",
    font_size_name=16,
    font_size_heading=12,
    font_size_subheading=11,
    font_size_body=11,
    font_size_small=10,
    margin_top=1.0,
    margin_bottom=1.0,
    margin_left=1.0,
    margin_right=1.0,
    line_spacing=1.3,
    section_spacing=0.20,
    subsection_spacing=0.15,
    primary_color="#000000",
    accent_color="#000000",
    header_line=False,
    section_lines=False,
    bullet_style="-",
)

@TemplateRegistry.register("ats-friendly", spec=ATS_FRIENDLY_SPEC)
class ATSFriendlyTemplate(BaseResumeTemplate):
    """ATS-Friendly template with simple, parseable structure."""

    def __init__(self, spec: Optional[TemplateSpec] = None):
        super().__init__(spec or ATS_FRIENDLY_SPEC)

    def build_resume(self, canvas_obj: canvas.Canvas, profile: Dict[str, Any],
                     accomplishments: List[Dict[str, Any]], education: List[Dict[str, Any]],
                     skills: List[str], certifications: List[Dict[str, Any]],
                     options: Optional[Dict[str, Any]] = None) -> None:
        options = options or {}
        x = self._get_x_start()
        y = self._get_y_start()

        # Simple header
        y = self._ats_header(canvas_obj, profile, x, y)
        
        # Sections in standard order
        if options.get('summary'):
            y = self._ats_section_text(canvas_obj, "PROFESSIONAL SUMMARY", options['summary'], x, y)
        if skills:
            y = self._ats_section_skills(canvas_obj, skills, x, y)
        if accomplishments:
            y = self._ats_section_experience(canvas_obj, accomplishments, x, y)
        if education:
            y = self._ats_section_education(canvas_obj, education, x, y)
        if certifications:
            y = self._ats_section_certifications(canvas_obj, certifications, x, y)

    def _ats_header(self, c, profile, x, y):
        # Name (bold, large)
        c.setFont(self._get_font_variant('bold'), self.spec.font_size_name)
        c.drawString(x, y, profile.get('name', 'NAME'))
        y -= self.spec.font_size_name + 6
        
        # Contact (each on own line for clarity)
        c.setFont(self.spec.font_family, self.spec.font_size_body)
        if profile.get('email'):
            c.drawString(x, y, f"Email: {profile['email']}")
            y -= self.spec.font_size_body + 3
        if profile.get('phone'):
            c.drawString(x, y, f"Phone: {profile['phone']}")
            y -= self.spec.font_size_body + 3
        
        loc = pdf_utils.format_location(profile.get('city'), profile.get('state'))
        if loc:
            c.drawString(x, y, f"Location: {loc}")
            y -= self.spec.font_size_body + 3
        
        if profile.get('linkedin_url'):
            c.drawString(x, y, f"LinkedIn: {profile['linkedin_url']}")
            y -= self.spec.font_size_body + 3
        
        return y - 10

    def _ats_section_text(self, c, title, text, x, y):
        c.setFont(self._get_font_variant('bold'), self.spec.font_size_heading)
        c.drawString(x, y, title)
        y -= self.spec.font_size_heading + 6
        
        c.setFont(self.spec.font_family, self.spec.font_size_body)
        for line in pdf_utils.wrap_text(pdf_utils.clean_text(text), 80):
            c.drawString(x, y, line)
            y -= self.spec.font_size_body + 3
        return y - 10

    def _ats_section_skills(self, c, skills, x, y):
        c.setFont(self._get_font_variant('bold'), self.spec.font_size_heading)
        c.drawString(x, y, "SKILLS")
        y -= self.spec.font_size_heading + 6
        
        c.setFont(self.spec.font_family, self.spec.font_size_body)
        c.drawString(x, y, ", ".join(skills))
        y -= self.spec.font_size_body + 3
        return y - 10

    def _ats_section_experience(self, c, accomplishments, x, y):
        c.setFont(self._get_font_variant('bold'), self.spec.font_size_heading)
        c.drawString(x, y, "WORK EXPERIENCE")
        y -= self.spec.font_size_heading + 6
        
        grouped = pdf_utils.group_by_company(accomplishments)
        for company in sorted(grouped.keys()):
            items = grouped[company]
            first = items[0]
            
            # Job title
            c.setFont(self._get_font_variant('bold'), self.spec.font_size_subheading)
            c.drawString(x, y, first.get('job_title', 'Position'))
            y -= self.spec.font_size_subheading + 3
            
            # Company and dates
            c.setFont(self.spec.font_family, self.spec.font_size_body)
            company_line = first.get('company_name', company)
            date_range = self._format_date_range(
                first.get('start_date'), first.get('end_date'), first.get('is_current', False)
            )
            if date_range:
                company_line += f" | {date_range}"
            c.drawString(x, y, company_line)
            y -= self.spec.font_size_body + 4
            
            # Bullets
            for item in items:
                if item.get('text'):
                    c.drawString(x, y, f"- {pdf_utils.clean_text(item['text'])}")
                    y -= self.spec.font_size_body + 3
            y -= 6
        return y

    def _ats_section_education(self, c, education, x, y):
        c.setFont(self._get_font_variant('bold'), self.spec.font_size_heading)
        c.drawString(x, y, "EDUCATION")
        y -= self.spec.font_size_heading + 6
        
        for edu in pdf_utils.sort_by_date(education, 'graduation_date', True):
            c.setFont(self._get_font_variant('bold'), self.spec.font_size_subheading)
            c.drawString(x, y, edu.get('degree', 'Degree'))
            y -= self.spec.font_size_subheading + 3
            
            c.setFont(self.spec.font_family, self.spec.font_size_body)
            inst_line = edu.get('institution', 'Institution')
            if edu.get('graduation_date'):
                date_str = self._format_date_range(edu['graduation_date'], None, False)
                inst_line += f" | {date_str}"
            if edu.get('gpa'):
                inst_line += f" | GPA: {pdf_utils.format_gpa(edu['gpa'])}"
            c.drawString(x, y, inst_line)
            y -= self.spec.font_size_body + 6
        return y

    def _ats_section_certifications(self, c, certifications, x, y):
        c.setFont(self._get_font_variant('bold'), self.spec.font_size_heading)
        c.drawString(x, y, "CERTIFICATIONS")
        y -= self.spec.font_size_heading + 6
        
        for cert in pdf_utils.sort_by_date(certifications, 'date_obtained', True):
            c.setFont(self.spec.font_family, self.spec.font_size_body)
            cert_line = cert.get('name', 'Certification')
            if cert.get('issuing_organization'):
                cert_line += f" - {cert['issuing_organization']}"
            if cert.get('date_obtained'):
                date_str = self._format_date_range(cert['date_obtained'], None, False)
                cert_line += f" ({date_str})"
            c.drawString(x, y, cert_line)
            y -= self.spec.font_size_body + 3
        return y
