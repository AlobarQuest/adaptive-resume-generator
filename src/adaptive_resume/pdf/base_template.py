"""Base template classes for PDF resume generation.

This module provides the foundation for creating resume templates using ReportLab.
All templates inherit from BaseResumeTemplate and use TemplateSpec for configuration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import logging

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor, black
    from reportlab.pdfgen import canvas
    from reportlab.platypus import Paragraph, Frame
except ImportError as exc:  # pragma: no cover
    raise ImportError("ReportLab is required for PDF generation") from exc

logger = logging.getLogger(__name__)


class ResumeSection(Enum):
    """Resume sections that can be included in a template."""

    HEADER = "header"
    SUMMARY = "summary"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    SKILLS = "skills"
    CERTIFICATIONS = "certifications"
    PROJECTS = "projects"
    AWARDS = "awards"


@dataclass
class TemplateSpec:
    """Template specification with fonts, colors, spacing, and layout.

    This class defines all visual and layout parameters for a resume template.
    Templates can customize these values to create different visual styles.

    Attributes:
        name: Template name (e.g., "Classic", "Modern")
        font_family: Base font family (e.g., "Helvetica", "Times-Roman")
        font_size_name: Font size for name in header (points)
        font_size_heading: Font size for section headings (points)
        font_size_subheading: Font size for job titles, school names (points)
        font_size_body: Font size for body text (points)
        font_size_small: Font size for dates, locations (points)
        margin_top: Top margin (inches)
        margin_bottom: Bottom margin (inches)
        margin_left: Left margin (inches)
        margin_right: Right margin (inches)
        line_spacing: Line spacing multiplier (1.0 = single spacing)
        section_spacing: Space between sections (inches)
        subsection_spacing: Space between items within a section (inches)
        primary_color: Primary text color (hex or color name)
        accent_color: Accent color for headings, lines (hex or color name)
        header_line: Whether to include line under header
        section_lines: Whether to include lines under section headings
        bullet_style: Bullet point character (e.g., "•", "-", "▸")
    """

    name: str

    # Fonts
    font_family: str = "Helvetica"
    font_size_name: int = 16
    font_size_heading: int = 12
    font_size_subheading: int = 11
    font_size_body: int = 10
    font_size_small: int = 9

    # Margins (inches)
    margin_top: float = 0.75
    margin_bottom: float = 0.75
    margin_left: float = 0.75
    margin_right: float = 0.75

    # Spacing
    line_spacing: float = 1.2
    section_spacing: float = 0.25
    subsection_spacing: float = 0.15

    # Colors (hex strings)
    primary_color: str = "#000000"
    accent_color: str = "#0066CC"

    # Visual elements
    header_line: bool = True
    section_lines: bool = False
    bullet_style: str = "•"

    # Page size
    page_width: float = letter[0]
    page_height: float = letter[1]

    def get_primary_color(self):
        """Get primary color as ReportLab Color object."""
        return HexColor(self.primary_color) if self.primary_color.startswith('#') else black

    def get_accent_color(self):
        """Get accent color as ReportLab Color object."""
        return HexColor(self.accent_color) if self.accent_color.startswith('#') else black

    def get_content_width(self) -> float:
        """Get usable content width (page width minus margins)."""
        return self.page_width - (self.margin_left + self.margin_right) * inch

    def get_content_height(self) -> float:
        """Get usable content height (page height minus margins)."""
        return self.page_height - (self.margin_top + self.margin_bottom) * inch


class BaseResumeTemplate(ABC):
    """Abstract base class for resume templates.

    All resume templates inherit from this class and implement the build_resume
    method. The base class provides common functionality for creating styles,
    formatting dates, and drawing common elements.

    Attributes:
        spec: TemplateSpec with configuration
        styles: Dictionary of ReportLab ParagraphStyle objects
    """

    def __init__(self, spec: TemplateSpec):
        """Initialize template with specification.

        Args:
            spec: TemplateSpec with template configuration
        """
        self.spec = spec
        self.styles = self._create_styles()
        logger.debug(f"Initialized {spec.name} template")

    @abstractmethod
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

        This is the main method that templates must implement. It receives
        all resume data and is responsible for rendering it to the PDF canvas.

        Args:
            canvas_obj: ReportLab Canvas object to draw on
            profile: Profile dictionary with contact info
            accomplishments: List of accomplishment dictionaries (grouped by job)
            education: List of education dictionaries
            skills: List of skill strings
            certifications: List of certification dictionaries
            options: Optional settings (include_gaps, include_recommendations, etc.)
        """
        pass

    def _create_styles(self) -> Dict[str, ParagraphStyle]:
        """Create paragraph styles for this template.

        Returns:
            Dictionary mapping style names to ParagraphStyle objects
        """
        styles = {}

        # Name style (for header)
        styles['name'] = ParagraphStyle(
            'name',
            fontSize=self.spec.font_size_name,
            fontName=f"{self.spec.font_family}-Bold",
            textColor=self.spec.get_primary_color(),
            spaceAfter=6,
            alignment=0  # Left aligned
        )

        # Contact info style
        styles['contact'] = ParagraphStyle(
            'contact',
            fontSize=self.spec.font_size_small,
            fontName=self.spec.font_family,
            textColor=self.spec.get_primary_color(),
            spaceAfter=12
        )

        # Section heading style
        styles['heading'] = ParagraphStyle(
            'heading',
            fontSize=self.spec.font_size_heading,
            fontName=f"{self.spec.font_family}-Bold",
            textColor=self.spec.get_accent_color(),
            spaceBefore=self.spec.section_spacing * 72,  # Convert inches to points
            spaceAfter=6,
            textTransform='uppercase' if self.spec.name == 'Classic' else None
        )

        # Subheading style (job title, school name)
        styles['subheading'] = ParagraphStyle(
            'subheading',
            fontSize=self.spec.font_size_subheading,
            fontName=f"{self.spec.font_family}-Bold",
            textColor=self.spec.get_primary_color(),
            spaceBefore=self.spec.subsection_spacing * 72,
            spaceAfter=2
        )

        # Body text style
        styles['body'] = ParagraphStyle(
            'body',
            fontSize=self.spec.font_size_body,
            fontName=self.spec.font_family,
            textColor=self.spec.get_primary_color(),
            leading=self.spec.font_size_body * self.spec.line_spacing,
            spaceAfter=4
        )

        # Small text style (dates, locations)
        styles['small'] = ParagraphStyle(
            'small',
            fontSize=self.spec.font_size_small,
            fontName=self.spec.font_family,
            textColor=self.spec.get_primary_color(),
            spaceAfter=2
        )

        # Bullet point style
        styles['bullet'] = ParagraphStyle(
            'bullet',
            fontSize=self.spec.font_size_body,
            fontName=self.spec.font_family,
            textColor=self.spec.get_primary_color(),
            leftIndent=20,
            bulletIndent=10,
            leading=self.spec.font_size_body * self.spec.line_spacing,
            spaceAfter=3
        )

        return styles

    def _draw_horizontal_line(
        self,
        canvas_obj: canvas.Canvas,
        x: float,
        y: float,
        width: float,
        color=None,
        thickness: float = 1
    ) -> None:
        """Draw a horizontal line.

        Args:
            canvas_obj: ReportLab Canvas object
            x: X coordinate (left edge)
            y: Y coordinate
            width: Line width
            color: Line color (uses accent color if None)
            thickness: Line thickness in points
        """
        canvas_obj.saveState()
        canvas_obj.setStrokeColor(color or self.spec.get_accent_color())
        canvas_obj.setLineWidth(thickness)
        canvas_obj.line(x, y, x + width, y)
        canvas_obj.restoreState()

    def _format_date_range(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
        is_current: bool = False
    ) -> str:
        """Format a date range for display.

        Args:
            start_date: Start date string (e.g., "2020-01-01")
            end_date: End date string or None
            is_current: Whether this is a current position

        Returns:
            Formatted date range (e.g., "Jan 2020 - Present")
        """
        from .pdf_utils import format_date_range
        return format_date_range(start_date, end_date, is_current)

    def _get_y_start(self) -> float:
        """Get starting Y coordinate (top of content area).

        Returns:
            Y coordinate in points from bottom of page
        """
        return self.spec.page_height - (self.spec.margin_top * inch)

    def _get_x_start(self) -> float:
        """Get starting X coordinate (left edge of content area).

        Returns:
            X coordinate in points from left of page
        """
        return self.spec.margin_left * inch

    def _check_page_break(
        self,
        canvas_obj: canvas.Canvas,
        current_y: float,
        needed_space: float
    ) -> float:
        """Check if a page break is needed and create new page if necessary.

        Args:
            canvas_obj: ReportLab Canvas object
            current_y: Current Y position
            needed_space: Space needed for next content (points)

        Returns:
            New Y position (either current_y or top of new page)
        """
        min_y = self.spec.margin_bottom * inch

        if current_y - needed_space < min_y:
            # Need a new page
            canvas_obj.showPage()
            return self._get_y_start()

        return current_y

    def _get_font_variant(self, variant: str = 'regular') -> str:
        """Get the correct font name for a variant.

        ReportLab has specific font names for each variant. This method
        maps the font family to the correct variant names.

        Args:
            variant: Font variant ('regular', 'bold', 'italic', 'bold-italic')

        Returns:
            Font name for the specified variant
        """
        # Map font families to their variant names
        font_variants = {
            'Times-Roman': {
                'regular': 'Times-Roman',
                'bold': 'Times-Bold',
                'italic': 'Times-Italic',
                'bold-italic': 'Times-BoldItalic'
            },
            'Helvetica': {
                'regular': 'Helvetica',
                'bold': 'Helvetica-Bold',
                'italic': 'Helvetica-Oblique',
                'bold-italic': 'Helvetica-BoldOblique'
            },
            'Courier': {
                'regular': 'Courier',
                'bold': 'Courier-Bold',
                'italic': 'Courier-Oblique',
                'bold-italic': 'Courier-BoldOblique'
            }
        }

        # Get the variants for this font family
        variants = font_variants.get(self.spec.font_family, {})

        # Return the requested variant, or fallback to regular
        return variants.get(variant, self.spec.font_family)


__all__ = ['ResumeSection', 'TemplateSpec', 'BaseResumeTemplate']
