"""
Unit tests for base template classes.

Tests cover:
- TemplateSpec configuration
- BaseResumeTemplate abstract class
- TemplateRegistry functionality
- Style creation and formatting
"""

import pytest
from io import BytesIO

from adaptive_resume.pdf.base_template import (
    ResumeSection,
    TemplateSpec,
    BaseResumeTemplate,
)
from adaptive_resume.pdf.template_registry import (
    TemplateRegistry,
    TemplateRegistryError,
)

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
except ImportError:
    pytest.skip("ReportLab not installed", allow_module_level=True)


class TestResumeSection:
    """Test suite for ResumeSection enum."""

    def test_resume_section_values(self):
        """Test that all expected sections are defined."""
        assert ResumeSection.HEADER.value == "header"
        assert ResumeSection.SUMMARY.value == "summary"
        assert ResumeSection.EXPERIENCE.value == "experience"
        assert ResumeSection.EDUCATION.value == "education"
        assert ResumeSection.SKILLS.value == "skills"
        assert ResumeSection.CERTIFICATIONS.value == "certifications"


class TestTemplateSpec:
    """Test suite for TemplateSpec."""

    def test_template_spec_defaults(self):
        """Test default TemplateSpec values."""
        spec = TemplateSpec(name="test")

        assert spec.name == "test"
        assert spec.font_family == "Helvetica"
        assert spec.font_size_name == 16
        assert spec.font_size_heading == 12
        assert spec.margin_top == 0.75
        assert spec.primary_color == "#000000"
        assert spec.bullet_style == "•"

    def test_template_spec_custom_values(self):
        """Test TemplateSpec with custom values."""
        spec = TemplateSpec(
            name="custom",
            font_family="Times-Roman",
            font_size_name=18,
            primary_color="#333333",
            margin_left=1.0
        )

        assert spec.name == "custom"
        assert spec.font_family == "Times-Roman"
        assert spec.font_size_name == 18
        assert spec.primary_color == "#333333"
        assert spec.margin_left == 1.0

    def test_template_spec_get_colors(self):
        """Test color conversion methods."""
        spec = TemplateSpec(
            name="test",
            primary_color="#FF0000",
            accent_color="#0000FF"
        )

        primary = spec.get_primary_color()
        accent = spec.get_accent_color()

        assert primary is not None
        assert accent is not None

    def test_template_spec_get_content_dimensions(self):
        """Test content dimension calculations."""
        spec = TemplateSpec(
            name="test",
            margin_left=1.0,
            margin_right=1.0,
            margin_top=0.75,
            margin_bottom=0.75
        )

        content_width = spec.get_content_width()
        content_height = spec.get_content_height()

        # letter size is 8.5 x 11 inches = 612 x 792 points
        # Content width should be page width minus margins (in points)
        expected_width = 612 - (1.0 + 1.0) * 72  # 72 points per inch
        assert abs(content_width - expected_width) < 1

        expected_height = 792 - (0.75 + 0.75) * 72
        assert abs(content_height - expected_height) < 1


class MockTemplate(BaseResumeTemplate):
    """Mock template for testing BaseResumeTemplate."""

    def build_resume(self, canvas_obj, profile, accomplishments, education, skills, certifications, options=None):
        """Mock build_resume implementation."""
        # Draw a simple line to prove it works
        canvas_obj.line(100, 100, 200, 200)


class TestBaseResumeTemplate:
    """Test suite for BaseResumeTemplate."""

    def test_base_template_initialization(self):
        """Test template initialization."""
        spec = TemplateSpec(name="test")
        template = MockTemplate(spec)

        assert template.spec == spec
        assert template.styles is not None
        assert isinstance(template.styles, dict)

    def test_base_template_create_styles(self):
        """Test style creation."""
        spec = TemplateSpec(name="test")
        template = MockTemplate(spec)

        # Check that expected styles are created
        assert 'name' in template.styles
        assert 'contact' in template.styles
        assert 'heading' in template.styles
        assert 'subheading' in template.styles
        assert 'body' in template.styles
        assert 'small' in template.styles
        assert 'bullet' in template.styles

    def test_base_template_format_date_range(self):
        """Test date range formatting."""
        spec = TemplateSpec(name="test")
        template = MockTemplate(spec)

        result = template._format_date_range("2020-01", "2022-12", False)
        assert "2020" in result
        assert "2022" in result

    def test_base_template_get_coordinates(self):
        """Test coordinate getter methods."""
        spec = TemplateSpec(name="test", margin_left=1.0, margin_top=1.0)
        template = MockTemplate(spec)

        x_start = template._get_x_start()
        y_start = template._get_y_start()

        # X should be left margin in points
        assert x_start == 1.0 * 72

        # Y should be page height minus top margin
        assert y_start == 792 - (1.0 * 72)

    def test_base_template_check_page_break(self):
        """Test page break checking."""
        spec = TemplateSpec(name="test")
        template = MockTemplate(spec)

        # Create a mock canvas
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)

        # Test when page break is not needed
        current_y = 400
        needed_space = 100
        new_y = template._check_page_break(c, current_y, needed_space)

        assert new_y == current_y  # No page break

        # Test when page break is needed
        current_y = 100  # Near bottom
        needed_space = 200
        new_y = template._check_page_break(c, current_y, needed_space)

        # Should be at top of new page
        assert new_y == template._get_y_start()


class TestTemplateRegistry:
    """Test suite for TemplateRegistry."""

    def setup_method(self):
        """Clear registry before each test."""
        TemplateRegistry.clear()

    def teardown_method(self):
        """Clear registry after each test."""
        TemplateRegistry.clear()

    def test_register_template_direct(self):
        """Test registering a template directly."""
        TemplateRegistry.register("test", MockTemplate)

        assert TemplateRegistry.is_registered("test")
        assert "test" in TemplateRegistry.list_templates()

    def test_register_template_decorator(self):
        """Test registering a template with decorator."""
        @TemplateRegistry.register("decorated")
        class DecoratedTemplate(BaseResumeTemplate):
            def build_resume(self, *args, **kwargs):
                pass

        assert TemplateRegistry.is_registered("decorated")
        assert DecoratedTemplate is not None

    def test_register_template_with_spec(self):
        """Test registering a template with default spec."""
        spec = TemplateSpec(name="test")
        TemplateRegistry.register("test", MockTemplate, spec=spec)

        retrieved_spec = TemplateRegistry.get_spec("test")
        assert retrieved_spec == spec

    def test_get_template(self):
        """Test retrieving a registered template."""
        TemplateRegistry.register("test", MockTemplate)

        template_class = TemplateRegistry.get_template("test")
        assert template_class == MockTemplate

    def test_get_template_not_found(self):
        """Test retrieving non-existent template."""
        with pytest.raises(TemplateRegistryError) as exc_info:
            TemplateRegistry.get_template("nonexistent")

        assert "not found" in str(exc_info.value)

    def test_list_templates(self):
        """Test listing all registered templates."""
        TemplateRegistry.register("test1", MockTemplate)
        TemplateRegistry.register("test2", MockTemplate)

        templates = TemplateRegistry.list_templates()

        assert len(templates) == 2
        assert "test1" in templates
        assert "test2" in templates
        # Should be sorted
        assert templates == sorted(templates)

    def test_is_registered(self):
        """Test checking if template is registered."""
        TemplateRegistry.register("test", MockTemplate)

        assert TemplateRegistry.is_registered("test")
        assert not TemplateRegistry.is_registered("nonexistent")

    def test_unregister_template(self):
        """Test unregistering a template."""
        TemplateRegistry.register("test", MockTemplate)
        assert TemplateRegistry.is_registered("test")

        TemplateRegistry.unregister("test")
        assert not TemplateRegistry.is_registered("test")

    def test_unregister_nonexistent(self):
        """Test unregistering non-existent template."""
        with pytest.raises(TemplateRegistryError):
            TemplateRegistry.unregister("nonexistent")

    def test_register_duplicate_warning(self):
        """Test registering duplicate template name."""
        TemplateRegistry.register("test", MockTemplate)

        # Registering again should work (with warning)
        TemplateRegistry.register("test", MockTemplate)

        # Should still be registered
        assert TemplateRegistry.is_registered("test")

    def test_register_invalid_class(self):
        """Test registering non-BaseResumeTemplate class."""
        class InvalidTemplate:
            pass

        with pytest.raises(ValueError):
            TemplateRegistry.register("invalid", InvalidTemplate)

    def test_get_template_info(self):
        """Test getting template information."""
        TemplateRegistry.register("test", MockTemplate)

        info = TemplateRegistry.get_template_info()

        assert "test" in info
        assert info["test"]["class_name"] == "MockTemplate"
        assert "module" in info["test"]

    def test_clear_registry(self):
        """Test clearing the registry."""
        TemplateRegistry.register("test1", MockTemplate)
        TemplateRegistry.register("test2", MockTemplate)

        TemplateRegistry.clear()

        assert len(TemplateRegistry.list_templates()) == 0
