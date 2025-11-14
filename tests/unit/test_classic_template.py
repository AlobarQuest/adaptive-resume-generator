"""Unit tests for Classic Resume Template.

Tests cover:
- Template registration
- Template initialization
- All section rendering (header, summary, experience, education, skills, certifications)
- Complete resume building
- Page break handling
- Text wrapping and formatting
"""

import pytest
from io import BytesIO
from datetime import datetime

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
except ImportError:
    pytest.skip("ReportLab not installed", allow_module_level=True)

from adaptive_resume.pdf.templates.classic_template import (
    ClassicTemplate,
    CLASSIC_SPEC,
)
from adaptive_resume.pdf.template_registry import TemplateRegistry
from adaptive_resume.pdf.base_template import TemplateSpec


class TestClassicTemplateRegistration:
    """Test suite for template registration."""

    def setup_method(self):
        """Ensure ClassicTemplate is registered before each test."""
        # Re-register if not present (may have been cleared by other tests)
        if not TemplateRegistry.is_registered("classic"):
            TemplateRegistry.register("classic", ClassicTemplate, spec=CLASSIC_SPEC)

    def test_template_is_registered(self):
        """Test that ClassicTemplate is auto-registered."""
        assert TemplateRegistry.is_registered("classic")

    def test_registered_template_class(self):
        """Test that registered template is ClassicTemplate."""
        template_class = TemplateRegistry.get_template("classic")
        assert template_class == ClassicTemplate

    def test_registered_spec(self):
        """Test that spec is registered with template."""
        spec = TemplateRegistry.get_spec("classic")
        assert spec is not None
        assert spec.name == "classic"
        assert spec.font_family == "Times-Roman"


class TestClassicTemplateInitialization:
    """Test suite for template initialization."""

    def test_init_with_default_spec(self):
        """Test initialization with default spec."""
        template = ClassicTemplate()

        assert template.spec == CLASSIC_SPEC
        assert template.spec.name == "classic"
        assert template.spec.font_family == "Times-Roman"

    def test_init_with_custom_spec(self):
        """Test initialization with custom spec."""
        custom_spec = TemplateSpec(
            name="custom-classic",
            font_family="Times-Roman",
            primary_color="#333333"
        )

        template = ClassicTemplate(custom_spec)

        assert template.spec == custom_spec
        assert template.spec.name == "custom-classic"
        assert template.spec.primary_color == "#333333"

    def test_styles_created(self):
        """Test that paragraph styles are created."""
        template = ClassicTemplate()

        assert template.styles is not None
        assert 'name' in template.styles
        assert 'contact' in template.styles
        assert 'heading' in template.styles
        assert 'body' in template.styles


class TestClassicTemplateHeader:
    """Test suite for header section rendering."""

    def setup_method(self):
        """Set up test canvas and template."""
        self.buffer = BytesIO()
        self.canvas = canvas.Canvas(self.buffer, pagesize=letter)
        self.template = ClassicTemplate()

    def test_build_header_with_full_profile(self):
        """Test header with complete profile data."""
        profile = {
            'name': 'John Doe',
            'email': 'john.doe@email.com',
            'phone': '(555) 123-4567',
            'city': 'San Francisco',
            'state': 'CA',
            'linkedin_url': 'linkedin.com/in/johndoe',
            'github_url': 'github.com/johndoe',
            'website_url': 'johndoe.com'
        }

        initial_y = self.template._get_y_start()
        new_y = self.template._build_header(self.canvas, profile, initial_y)

        # Y position should have moved down
        assert new_y < initial_y

        # No errors during rendering
        assert True

    def test_build_header_with_minimal_profile(self):
        """Test header with minimal profile data."""
        profile = {
            'name': 'Jane Smith',
            'email': 'jane@email.com'
        }

        initial_y = self.template._get_y_start()
        new_y = self.template._build_header(self.canvas, profile, initial_y)

        assert new_y < initial_y

    def test_build_header_with_no_contact_info(self):
        """Test header with name only."""
        profile = {
            'name': 'Test User'
        }

        initial_y = self.template._get_y_start()
        new_y = self.template._build_header(self.canvas, profile, initial_y)

        assert new_y < initial_y


class TestClassicTemplateSummary:
    """Test suite for summary section rendering."""

    def setup_method(self):
        """Set up test canvas and template."""
        self.buffer = BytesIO()
        self.canvas = canvas.Canvas(self.buffer, pagesize=letter)
        self.template = ClassicTemplate()

    def test_build_summary_short(self):
        """Test summary with short text."""
        summary = "Experienced software engineer with 5 years in web development."

        initial_y = 600
        new_y = self.template._build_summary(self.canvas, summary, initial_y)

        assert new_y < initial_y

    def test_build_summary_long(self):
        """Test summary with long text that wraps."""
        summary = (
            "Highly motivated software engineer with extensive experience in full-stack "
            "development, cloud architecture, and agile methodologies. Proven track record "
            "of delivering scalable solutions and leading cross-functional teams. Strong "
            "expertise in Python, JavaScript, and modern web frameworks."
        )

        initial_y = 600
        new_y = self.template._build_summary(self.canvas, summary, initial_y)

        assert new_y < initial_y


class TestClassicTemplateExperience:
    """Test suite for experience section rendering."""

    def setup_method(self):
        """Set up test canvas and template."""
        self.buffer = BytesIO()
        self.canvas = canvas.Canvas(self.buffer, pagesize=letter)
        self.template = ClassicTemplate()

    def test_build_experience_single_company(self):
        """Test experience with single company."""
        accomplishments = [
            {
                'company_name': 'Tech Corp',
                'job_title': 'Software Engineer',
                'start_date': '2020-01',
                'end_date': '2023-12',
                'is_current': False,
                'city': 'San Francisco',
                'state': 'CA',
                'text': 'Developed scalable web applications using Python and React'
            },
            {
                'company_name': 'Tech Corp',
                'job_title': 'Software Engineer',
                'start_date': '2020-01',
                'end_date': '2023-12',
                'is_current': False,
                'city': 'San Francisco',
                'state': 'CA',
                'text': 'Implemented CI/CD pipelines reducing deployment time by 50%'
            }
        ]

        initial_y = 600
        new_y = self.template._build_experience(self.canvas, accomplishments, initial_y)

        assert new_y < initial_y

    def test_build_experience_multiple_companies(self):
        """Test experience with multiple companies."""
        accomplishments = [
            {
                'company_name': 'Current Corp',
                'job_title': 'Senior Engineer',
                'start_date': '2022-01',
                'end_date': None,
                'is_current': True,
                'city': 'Seattle',
                'state': 'WA',
                'text': 'Leading backend development team'
            },
            {
                'company_name': 'Previous Corp',
                'job_title': 'Engineer',
                'start_date': '2019-01',
                'end_date': '2021-12',
                'is_current': False,
                'city': 'Austin',
                'state': 'TX',
                'text': 'Built microservices architecture'
            }
        ]

        initial_y = 600
        new_y = self.template._build_experience(self.canvas, accomplishments, initial_y)

        assert new_y < initial_y

    def test_build_experience_long_bullet(self):
        """Test experience with long bullet text that wraps."""
        accomplishments = [
            {
                'company_name': 'Test Corp',
                'job_title': 'Developer',
                'start_date': '2020-01',
                'end_date': '2023-12',
                'is_current': False,
                'text': (
                    'Led the development of a comprehensive enterprise resource planning '
                    'system that integrated with multiple legacy systems, improved '
                    'operational efficiency by 40%, and reduced manual data entry by 90% '
                    'through intelligent automation and machine learning algorithms'
                )
            }
        ]

        initial_y = 600
        new_y = self.template._build_experience(self.canvas, accomplishments, initial_y)

        assert new_y < initial_y

    def test_build_experience_current_position(self):
        """Test experience with current position (no end date)."""
        accomplishments = [
            {
                'company_name': 'Current Corp',
                'job_title': 'Lead Developer',
                'start_date': '2022-06',
                'end_date': None,
                'is_current': True,
                'city': 'Remote',
                'state': None,
                'text': 'Managing development team'
            }
        ]

        initial_y = 600
        new_y = self.template._build_experience(self.canvas, accomplishments, initial_y)

        assert new_y < initial_y


class TestClassicTemplateEducation:
    """Test suite for education section rendering."""

    def setup_method(self):
        """Set up test canvas and template."""
        self.buffer = BytesIO()
        self.canvas = canvas.Canvas(self.buffer, pagesize=letter)
        self.template = ClassicTemplate()

    def test_build_education_single_entry(self):
        """Test education with single entry."""
        education = [
            {
                'degree': 'Bachelor of Science in Computer Science',
                'institution': 'University of California',
                'graduation_date': '2020-05',
                'gpa': 3.75,
                'city': 'Berkeley',
                'state': 'CA',
                'field_of_study': 'Computer Science'
            }
        ]

        initial_y = 600
        new_y = self.template._build_education(self.canvas, education, initial_y)

        assert new_y < initial_y

    def test_build_education_multiple_entries(self):
        """Test education with multiple entries."""
        education = [
            {
                'degree': 'Master of Science',
                'institution': 'Stanford University',
                'graduation_date': '2022-06',
                'gpa': 3.9,
                'city': 'Stanford',
                'state': 'CA'
            },
            {
                'degree': 'Bachelor of Science',
                'institution': 'UC Berkeley',
                'graduation_date': '2020-05',
                'gpa': 3.75,
                'city': 'Berkeley',
                'state': 'CA'
            }
        ]

        initial_y = 600
        new_y = self.template._build_education(self.canvas, education, initial_y)

        assert new_y < initial_y

    def test_build_education_no_gpa(self):
        """Test education without GPA."""
        education = [
            {
                'degree': 'Bachelor of Arts',
                'institution': 'State University',
                'graduation_date': '2019-05',
                'city': 'Austin',
                'state': 'TX'
            }
        ]

        initial_y = 600
        new_y = self.template._build_education(self.canvas, education, initial_y)

        assert new_y < initial_y

    def test_build_education_minimal_data(self):
        """Test education with minimal data."""
        education = [
            {
                'degree': 'Bachelor of Science',
                'institution': 'Tech University'
            }
        ]

        initial_y = 600
        new_y = self.template._build_education(self.canvas, education, initial_y)

        assert new_y < initial_y


class TestClassicTemplateSkills:
    """Test suite for skills section rendering."""

    def setup_method(self):
        """Set up test canvas and template."""
        self.buffer = BytesIO()
        self.canvas = canvas.Canvas(self.buffer, pagesize=letter)
        self.template = ClassicTemplate()

    def test_build_skills_short_list(self):
        """Test skills with short list."""
        skills = ['Python', 'JavaScript', 'SQL']

        initial_y = 600
        new_y = self.template._build_skills(self.canvas, skills, initial_y)

        assert new_y < initial_y

    def test_build_skills_long_list(self):
        """Test skills with long list that wraps."""
        skills = [
            'Python', 'JavaScript', 'TypeScript', 'React', 'Node.js',
            'Django', 'Flask', 'PostgreSQL', 'MongoDB', 'Redis',
            'Docker', 'Kubernetes', 'AWS', 'Azure', 'Git',
            'CI/CD', 'Agile', 'Scrum', 'REST APIs', 'GraphQL'
        ]

        initial_y = 600
        new_y = self.template._build_skills(self.canvas, skills, initial_y)

        assert new_y < initial_y

    def test_build_skills_single_skill(self):
        """Test skills with single skill."""
        skills = ['Python']

        initial_y = 600
        new_y = self.template._build_skills(self.canvas, skills, initial_y)

        assert new_y < initial_y


class TestClassicTemplateCertifications:
    """Test suite for certifications section rendering."""

    def setup_method(self):
        """Set up test canvas and template."""
        self.buffer = BytesIO()
        self.canvas = canvas.Canvas(self.buffer, pagesize=letter)
        self.template = ClassicTemplate()

    def test_build_certifications_single(self):
        """Test certifications with single entry."""
        certifications = [
            {
                'name': 'AWS Certified Solutions Architect',
                'issuing_organization': 'Amazon Web Services',
                'date_obtained': '2022-03',
                'expiration_date': '2025-03',
                'credential_id': 'ABC123XYZ'
            }
        ]

        initial_y = 600
        new_y = self.template._build_certifications(self.canvas, certifications, initial_y)

        assert new_y < initial_y

    def test_build_certifications_multiple(self):
        """Test certifications with multiple entries."""
        certifications = [
            {
                'name': 'Google Cloud Professional',
                'issuing_organization': 'Google',
                'date_obtained': '2023-01',
                'credential_id': 'GCP456'
            },
            {
                'name': 'Certified Scrum Master',
                'issuing_organization': 'Scrum Alliance',
                'date_obtained': '2021-06',
                'credential_id': 'CSM789'
            }
        ]

        initial_y = 600
        new_y = self.template._build_certifications(self.canvas, certifications, initial_y)

        assert new_y < initial_y

    def test_build_certifications_minimal_data(self):
        """Test certifications with minimal data."""
        certifications = [
            {
                'name': 'Basic Certification',
                'issuing_organization': 'Certifying Body'
            }
        ]

        initial_y = 600
        new_y = self.template._build_certifications(self.canvas, certifications, initial_y)

        assert new_y < initial_y


class TestClassicTemplateComplete:
    """Test suite for complete resume building."""

    def setup_method(self):
        """Set up test canvas and template."""
        self.buffer = BytesIO()
        self.canvas = canvas.Canvas(self.buffer, pagesize=letter)
        self.template = ClassicTemplate()

    def test_build_resume_complete(self):
        """Test building complete resume with all sections."""
        profile = {
            'name': 'John Doe',
            'email': 'john@email.com',
            'phone': '(555) 123-4567',
            'city': 'San Francisco',
            'state': 'CA'
        }

        accomplishments = [
            {
                'company_name': 'Tech Corp',
                'job_title': 'Senior Engineer',
                'start_date': '2020-01',
                'end_date': None,
                'is_current': True,
                'text': 'Led development team'
            }
        ]

        education = [
            {
                'degree': 'BS Computer Science',
                'institution': 'State University',
                'graduation_date': '2019-05',
                'gpa': 3.8
            }
        ]

        skills = ['Python', 'JavaScript', 'React']

        certifications = [
            {
                'name': 'AWS Certified',
                'issuing_organization': 'Amazon',
                'date_obtained': '2022-01'
            }
        ]

        options = {
            'summary': 'Experienced software engineer with focus on web development.'
        }

        # Should not raise any exceptions
        self.template.build_resume(
            self.canvas,
            profile,
            accomplishments,
            education,
            skills,
            certifications,
            options
        )

        # Save to verify PDF is valid
        self.canvas.save()

        # Check that some content was written
        pdf_content = self.buffer.getvalue()
        assert len(pdf_content) > 0
        assert b'PDF' in pdf_content

    def test_build_resume_minimal(self):
        """Test building resume with minimal data."""
        profile = {'name': 'Test User'}
        accomplishments = []
        education = []
        skills = []
        certifications = []

        # Should not raise any exceptions
        self.template.build_resume(
            self.canvas,
            profile,
            accomplishments,
            education,
            skills,
            certifications
        )

        self.canvas.save()
        pdf_content = self.buffer.getvalue()
        assert len(pdf_content) > 0

    def test_build_resume_no_summary(self):
        """Test building resume without summary."""
        profile = {'name': 'Jane Doe', 'email': 'jane@email.com'}
        accomplishments = []
        education = []
        skills = ['Python']
        certifications = []

        # No summary in options
        self.template.build_resume(
            self.canvas,
            profile,
            accomplishments,
            education,
            skills,
            certifications,
            options={}
        )

        self.canvas.save()
        pdf_content = self.buffer.getvalue()
        assert len(pdf_content) > 0


class TestClassicTemplatePageBreaks:
    """Test suite for page break handling."""

    def setup_method(self):
        """Set up test canvas and template."""
        self.buffer = BytesIO()
        self.canvas = canvas.Canvas(self.buffer, pagesize=letter)
        self.template = ClassicTemplate()

    def test_page_break_in_experience(self):
        """Test page break with many accomplishments."""
        # Create many accomplishments to force page break
        accomplishments = []
        for i in range(20):
            accomplishments.append({
                'company_name': f'Company {i}',
                'job_title': f'Position {i}',
                'start_date': f'20{i:02d}-01',
                'end_date': f'20{i:02d}-12',
                'is_current': False,
                'text': f'Accomplishment {i} with some detailed text about the work performed'
            })

        initial_y = 600
        new_y = self.template._build_experience(self.canvas, accomplishments, initial_y)

        # Should handle page breaks without errors
        assert new_y > 0

    def test_page_break_in_education(self):
        """Test page break with many education entries."""
        education = []
        for i in range(10):
            education.append({
                'degree': f'Degree {i}',
                'institution': f'University {i}',
                'graduation_date': f'20{i:02d}-05',
                'gpa': 3.5 + (i * 0.01)
            })

        initial_y = 200  # Start low to force page break
        new_y = self.template._build_education(self.canvas, education, initial_y)

        assert new_y > 0
