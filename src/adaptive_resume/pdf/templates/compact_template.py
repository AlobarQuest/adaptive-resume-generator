"""Compact resume template - dense, space-efficient single-column layout."""

from typing import Dict, List, Any, Optional
from reportlab.pdfgen import canvas
from ..base_template import BaseResumeTemplate, TemplateSpec
from ..template_registry import TemplateRegistry
from .. import pdf_utils

COMPACT_SPEC = TemplateSpec(
    name="compact",
    font_family="Helvetica",
    font_size_name=14,
    font_size_heading=10,
    font_size_subheading=9,
    font_size_body=8,
    font_size_small=7,
    margin_top=0.5,
    margin_bottom=0.5,
    margin_left=0.6,
    margin_right=0.6,
    line_spacing=1.1,
    section_spacing=0.10,
    subsection_spacing=0.08,
    primary_color="#000000",
    accent_color="#000000",
    header_line=True,
    section_lines=False,
    bullet_style="•",
)

@TemplateRegistry.register("compact", spec=COMPACT_SPEC)
class CompactTemplate(BaseResumeTemplate):
    """Compact resume template for maximum content density."""

    def __init__(self, spec: Optional[TemplateSpec] = None):
        super().__init__(spec or COMPACT_SPEC)

    def build_resume(self, canvas_obj: canvas.Canvas, profile: Dict[str, Any],
                     accomplishments: List[Dict[str, Any]], education: List[Dict[str, Any]],
                     skills: List[str], certifications: List[Dict[str, Any]],
                     options: Optional[Dict[str, Any]] = None) -> None:
        options = options or {}
        x = self._get_x_start()
        y = self._get_y_start()
        w = self.spec.get_content_width()

        # Header
        y = self._compact_header(canvas_obj, profile, x, y, w)
        if options.get('summary'):
            y = self._compact_section(canvas_obj, "SUMMARY", options['summary'], x, y, w)
        if skills:
            y = self._compact_skills(canvas_obj, skills, x, y, w)
        if accomplishments:
            y = self._compact_experience(canvas_obj, accomplishments, x, y, w)
        if education:
            y = self._compact_education(canvas_obj, education, x, y)
        if certifications:
            y = self._compact_certifications(canvas_obj, certifications, x, y)

    def _compact_header(self, c, profile, x, y, w):
        name = profile.get('name', 'Name')
        c.setFont(self._get_font_variant('bold'), self.spec.font_size_name)
        c.drawString(x, y, name)
        y -= self.spec.font_size_name + 3
        
        contact = []
        for k in ['email', 'phone']:
            if profile.get(k): contact.append(profile[k])
        if contact:
            c.setFont(self.spec.font_family, self.spec.font_size_small)
            c.drawString(x, y, " | ".join(contact))
            y -= self.spec.font_size_small + 2
        
        self._draw_horizontal_line(c, x, y, w, thickness=0.5)
        return y - 8

    def _compact_section(self, c, title, text, x, y, w):
        c.setFont(self._get_font_variant('bold'), self.spec.font_size_heading)
        c.drawString(x, y, title)
        y -= self.spec.font_size_heading + 4
        
        c.setFont(self.spec.font_family, self.spec.font_size_body)
        for line in pdf_utils.wrap_text(pdf_utils.clean_text(text), 110):
            c.drawString(x, y, line)
            y -= self.spec.font_size_body + 2
        return y - 6

    def _compact_skills(self, c, skills, x, y, w):
        c.setFont(self._get_font_variant('bold'), self.spec.font_size_heading)
        c.drawString(x, y, "SKILLS")
        y -= self.spec.font_size_heading + 4
        
        c.setFont(self.spec.font_family, self.spec.font_size_body)
        skills_text = ", ".join(skills)
        for line in pdf_utils.wrap_text(skills_text, 110):
            c.drawString(x, y, line)
            y -= self.spec.font_size_body + 2
        return y - 6

    def _compact_experience(self, c, accomplishments, x, y, w):
        c.setFont(self._get_font_variant('bold'), self.spec.font_size_heading)
        c.drawString(x, y, "EXPERIENCE")
        y -= self.spec.font_size_heading + 4
        
        grouped = pdf_utils.group_by_company(accomplishments)
        for company in sorted(grouped.keys()):
            items = grouped[company]
            first = items[0]
            
            c.setFont(self._get_font_variant('bold'), self.spec.font_size_subheading)
            title = f"{first.get('job_title', 'Position')} - {first.get('company_name', company)}"
            c.drawString(x, y, title)
            y -= self.spec.font_size_subheading + 2
            
            c.setFont(self.spec.font_family, self.spec.font_size_body)
            for item in items:
                if item.get('text'):
                    c.drawString(x, y, f"• {pdf_utils.clean_text(item['text'])[:90]}...")
                    y -= self.spec.font_size_body + 1
            y -= 4
        return y

    def _compact_education(self, c, education, x, y):
        c.setFont(self._get_font_variant('bold'), self.spec.font_size_heading)
        c.drawString(x, y, "EDUCATION")
        y -= self.spec.font_size_heading + 4
        
        for edu in pdf_utils.sort_by_date(education, 'graduation_date', True):
            c.setFont(self._get_font_variant('bold'), self.spec.font_size_body)
            c.drawString(x, y, f"{edu.get('degree', '')} - {edu.get('institution', '')}")
            y -= self.spec.font_size_body + 2
        return y - 6

    def _compact_certifications(self, c, certifications, x, y):
        c.setFont(self._get_font_variant('bold'), self.spec.font_size_heading)
        c.drawString(x, y, "CERTIFICATIONS")
        y -= self.spec.font_size_heading + 4
        
        for cert in pdf_utils.sort_by_date(certifications, 'date_obtained', True):
            c.setFont(self.spec.font_family, self.spec.font_size_body)
            c.drawString(x, y, cert.get('name', ''))
            y -= self.spec.font_size_body + 2
        return y
