"""Unit tests for additional resume templates (Modern, Compact, ATS-Friendly).

Tests cover template registration, initialization, and basic PDF generation.
"""

import pytest
from io import BytesIO

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
except ImportError:
    pytest.skip("ReportLab not installed", allow_module_level=True)

from adaptive_resume.pdf.template_registry import TemplateRegistry


class TestModernTemplate:
    """Test suite for Modern template."""

    def setup_method(self):
        """Ensure Modern template is registered."""
        if not TemplateRegistry.is_registered("modern"):
            from adaptive_resume.pdf.templates.modern_template import ModernTemplate, MODERN_SPEC
            TemplateRegistry.register("modern", ModernTemplate, spec=MODERN_SPEC)

    def test_template_registered(self):
        """Test that Modern template is registered."""
        assert TemplateRegistry.is_registered("modern")

    def test_template_initialization(self):
        """Test Modern template initialization."""
        from adaptive_resume.pdf.templates.modern_template import ModernTemplate

        template = ModernTemplate()
        assert template.spec.name == "modern"
        assert template.spec.font_family == "Helvetica"

    def test_build_resume_basic(self):
        """Test basic PDF generation with Modern template."""
        from adaptive_resume.pdf.templates.modern_template import ModernTemplate

        template = ModernTemplate()
        buffer = BytesIO()
        pdf_canvas = canvas.Canvas(buffer, pagesize=letter)

        profile = {'name': 'Test User', 'email': 'test@example.com'}
        template.build_resume(
            pdf_canvas,
            profile=profile,
            accomplishments=[],
            education=[],
            skills=[],
            certifications=[]
        )

        pdf_canvas.save()
        pdf_bytes = buffer.getvalue()

        assert len(pdf_bytes) > 0
        assert b'PDF' in pdf_bytes


class TestCompactTemplate:
    """Test suite for Compact template."""

    def setup_method(self):
        """Ensure Compact template is registered."""
        if not TemplateRegistry.is_registered("compact"):
            from adaptive_resume.pdf.templates.compact_template import CompactTemplate, COMPACT_SPEC
            TemplateRegistry.register("compact", CompactTemplate, spec=COMPACT_SPEC)

    def test_template_registered(self):
        """Test that Compact template is registered."""
        assert TemplateRegistry.is_registered("compact")

    def test_template_initialization(self):
        """Test Compact template initialization."""
        from adaptive_resume.pdf.templates.compact_template import CompactTemplate

        template = CompactTemplate()
        assert template.spec.name == "compact"

    def test_build_resume_basic(self):
        """Test basic PDF generation with Compact template."""
        from adaptive_resume.pdf.templates.compact_template import CompactTemplate

        template = CompactTemplate()
        buffer = BytesIO()
        pdf_canvas = canvas.Canvas(buffer, pagesize=letter)

        profile = {'name': 'Test User', 'email': 'test@example.com'}
        template.build_resume(
            pdf_canvas,
            profile=profile,
            accomplishments=[],
            education=[],
            skills=[],
            certifications=[]
        )

        pdf_canvas.save()
        pdf_bytes = buffer.getvalue()

        assert len(pdf_bytes) > 0
        assert b'PDF' in pdf_bytes


class TestATSFriendlyTemplate:
    """Test suite for ATS-Friendly template."""

    def setup_method(self):
        """Ensure ATS-Friendly template is registered."""
        if not TemplateRegistry.is_registered("ats-friendly"):
            from adaptive_resume.pdf.templates.ats_friendly_template import ATSFriendlyTemplate, ATS_FRIENDLY_SPEC
            TemplateRegistry.register("ats-friendly", ATSFriendlyTemplate, spec=ATS_FRIENDLY_SPEC)

    def test_template_registered(self):
        """Test that ATS-Friendly template is registered."""
        assert TemplateRegistry.is_registered("ats-friendly")

    def test_template_initialization(self):
        """Test ATS-Friendly template initialization."""
        from adaptive_resume.pdf.templates.ats_friendly_template import ATSFriendlyTemplate

        template = ATSFriendlyTemplate()
        assert template.spec.name == "ats-friendly"

    def test_build_resume_basic(self):
        """Test basic PDF generation with ATS-Friendly template."""
        from adaptive_resume.pdf.templates.ats_friendly_template import ATSFriendlyTemplate

        template = ATSFriendlyTemplate()
        buffer = BytesIO()
        pdf_canvas = canvas.Canvas(buffer, pagesize=letter)

        profile = {'name': 'Test User', 'email': 'test@example.com'}
        template.build_resume(
            pdf_canvas,
            profile=profile,
            accomplishments=[],
            education=[],
            skills=[],
            certifications=[]
        )

        pdf_canvas.save()
        pdf_bytes = buffer.getvalue()

        assert len(pdf_bytes) > 0
        assert b'PDF' in pdf_bytes
