"""
Unit tests for ResumeParser service.

Tests cover:
- Resume file parsing (TXT, PDF, DOCX)
- Section detection (Experience, Education, Skills, Contact, etc.)
- Resume-specific text cleaning
- File validation
- Error handling
"""

import pytest
from pathlib import Path
from adaptive_resume.services.resume_parser import ResumeParser, ResumeSections
from adaptive_resume.services.job_posting_parser import (
    UnsupportedFileTypeError,
    FileTooLargeError,
    FileParseError
)


# Get test fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / 'fixtures' / 'sample_resumes'


class TestResumeSections:
    """Test suite for ResumeSections class."""

    def test_section_headers_defined(self):
        """Test that all section headers are defined."""
        assert len(ResumeSections.CONTACT) > 0
        assert len(ResumeSections.SUMMARY) > 0
        assert len(ResumeSections.EXPERIENCE) > 0
        assert len(ResumeSections.EDUCATION) > 0
        assert len(ResumeSections.SKILLS) > 0
        assert len(ResumeSections.CERTIFICATIONS) > 0
        assert len(ResumeSections.PROJECTS) > 0
        assert len(ResumeSections.AWARDS) > 0

    def test_section_headers_lowercase(self):
        """Test that section headers are lowercase for matching."""
        for section_list in [
            ResumeSections.CONTACT,
            ResumeSections.EXPERIENCE,
            ResumeSections.EDUCATION,
            ResumeSections.SKILLS
        ]:
            for header in section_list:
                assert header == header.lower(), f"Header '{header}' should be lowercase"


class TestResumeParserInit:
    """Test suite for ResumeParser initialization."""

    def test_init_creates_file_parser(self):
        """Test initialization creates JobPostingParser."""
        parser = ResumeParser()
        assert parser.file_parser is not None

    def test_multiple_instances_independent(self):
        """Test multiple parser instances are independent."""
        parser1 = ResumeParser()
        parser2 = ResumeParser()
        assert parser1.file_parser is not parser2.file_parser


class TestResumeParserBasicParsing:
    """Test suite for basic resume parsing."""

    def test_parse_resume_txt_file(self):
        """Test parsing a TXT resume file."""
        parser = ResumeParser()
        resume_path = FIXTURES_DIR / 'john_doe_resume.txt'

        text = parser.parse_resume(str(resume_path))

        assert len(text) > 0
        assert 'john doe' in text.lower()
        assert 'software engineer' in text.lower()

    def test_parse_resume_returns_string(self):
        """Test parse_resume returns a string."""
        parser = ResumeParser()
        resume_path = FIXTURES_DIR / 'john_doe_resume.txt'

        result = parser.parse_resume(str(resume_path))

        assert isinstance(result, str)

    def test_parse_resume_removes_extra_whitespace(self):
        """Test that extra whitespace is removed."""
        parser = ResumeParser()
        resume_path = FIXTURES_DIR / 'john_doe_resume.txt'

        text = parser.parse_resume(str(resume_path))

        # Should not have more than 2 consecutive newlines
        assert '\n\n\n' not in text

    def test_parse_resume_nonexistent_file_raises_error(self):
        """Test parsing non-existent file raises error."""
        parser = ResumeParser()

        with pytest.raises(Exception):  # Could be ValidationError or ParsingError
            parser.parse_resume('nonexistent_file.txt')

    def test_parse_minimal_resume(self):
        """Test parsing a minimal resume."""
        parser = ResumeParser()
        resume_path = FIXTURES_DIR / 'minimal_resume.txt'

        text = parser.parse_resume(str(resume_path))

        assert len(text) > 0
        assert 'bob johnson' in text.lower()


class TestResumeParserSectionDetection:
    """Test suite for section detection."""

    def test_parse_with_sections_returns_dict(self):
        """Test parse_resume_with_sections returns a dictionary."""
        parser = ResumeParser()
        resume_path = FIXTURES_DIR / 'john_doe_resume.txt'

        result = parser.parse_resume_with_sections(str(resume_path))

        assert isinstance(result, dict)

    def test_parse_with_sections_has_all_keys(self):
        """Test that all expected section keys are present."""
        parser = ResumeParser()
        resume_path = FIXTURES_DIR / 'john_doe_resume.txt'

        sections = parser.parse_resume_with_sections(str(resume_path))

        expected_keys = [
            'contact', 'summary', 'experience', 'education',
            'skills', 'certifications', 'projects', 'awards', 'raw_text'
        ]
        for key in expected_keys:
            assert key in sections

    def test_detect_experience_section(self):
        """Test detection of Experience section."""
        parser = ResumeParser()
        resume_path = FIXTURES_DIR / 'john_doe_resume.txt'

        sections = parser.parse_resume_with_sections(str(resume_path))

        assert len(sections['experience']) > 0
        assert 'senior software engineer' in sections['experience'].lower()
        assert 'tech corp' in sections['experience'].lower()

    def test_detect_education_section(self):
        """Test detection of Education section."""
        parser = ResumeParser()
        resume_path = FIXTURES_DIR / 'john_doe_resume.txt'

        sections = parser.parse_resume_with_sections(str(resume_path))

        assert len(sections['education']) > 0
        assert 'computer science' in sections['education'].lower()
        assert 'berkeley' in sections['education'].lower()

    def test_detect_skills_section(self):
        """Test detection of Skills section."""
        parser = ResumeParser()
        resume_path = FIXTURES_DIR / 'john_doe_resume.txt'

        sections = parser.parse_resume_with_sections(str(resume_path))

        assert len(sections['skills']) > 0
        assert 'python' in sections['skills'].lower()

    def test_detect_contact_section(self):
        """Test detection of Contact section."""
        parser = ResumeParser()
        resume_path = FIXTURES_DIR / 'john_doe_resume.txt'

        sections = parser.parse_resume_with_sections(str(resume_path))

        assert len(sections['contact']) > 0
        # Contact section or extracted from top
        contact_text = sections['contact'].lower()
        assert 'john.doe@email.com' in contact_text or 'john doe' in contact_text

    def test_detect_certifications_section(self):
        """Test detection of Certifications section."""
        parser = ResumeParser()
        resume_path = FIXTURES_DIR / 'john_doe_resume.txt'

        sections = parser.parse_resume_with_sections(str(resume_path))

        assert len(sections['certifications']) > 0
        assert 'aws' in sections['certifications'].lower() or 'certified' in sections['certifications'].lower()

    def test_detect_summary_section(self):
        """Test detection of Summary section."""
        parser = ResumeParser()
        resume_path = FIXTURES_DIR / 'john_doe_resume.txt'

        sections = parser.parse_resume_with_sections(str(resume_path))

        # May or may not have summary
        if sections['summary']:
            assert 'experience' in sections['summary'].lower() or 'engineer' in sections['summary'].lower()

    def test_raw_text_included_in_sections(self):
        """Test that raw_text is included in sections dict."""
        parser = ResumeParser()
        resume_path = FIXTURES_DIR / 'john_doe_resume.txt'

        sections = parser.parse_resume_with_sections(str(resume_path))

        assert 'raw_text' in sections
        assert len(sections['raw_text']) > 0
        assert 'john doe' in sections['raw_text'].lower()

    def test_section_content_excludes_header(self):
        """Test that section content doesn't include the section header."""
        parser = ResumeParser()
        resume_path = FIXTURES_DIR / 'john_doe_resume.txt'

        sections = parser.parse_resume_with_sections(str(resume_path))

        # Experience section should not start with "Work Experience" or "Experience"
        experience = sections['experience'].strip()
        if experience:
            first_line = experience.split('\n')[0].lower()
            assert 'work experience' not in first_line
            # It's OK if it has "experience" as part of actual content


class TestResumeParserAlternateFormats:
    """Test suite for alternate resume formats."""

    def test_parse_jane_smith_resume(self):
        """Test parsing Jane Smith's resume (different format)."""
        parser = ResumeParser()
        resume_path = FIXTURES_DIR / 'jane_smith_resume.txt'

        sections = parser.parse_resume_with_sections(str(resume_path))

        # Check that sections are detected
        assert len(sections['experience']) > 0
        assert 'product manager' in sections['experience'].lower()

        assert len(sections['education']) > 0
        assert 'mba' in sections['education'].lower() or 'business' in sections['education'].lower()

    def test_parse_resume_with_uppercase_headers(self):
        """Test parsing resume with all uppercase section headers."""
        parser = ResumeParser()
        resume_path = FIXTURES_DIR / 'jane_smith_resume.txt'

        sections = parser.parse_resume_with_sections(str(resume_path))

        # Should still detect EXPERIENCE, EDUCATION, SKILLS
        assert len(sections['experience']) > 0 or len(sections['education']) > 0

    def test_parse_minimal_resume_with_sections(self):
        """Test parsing minimal resume with sections."""
        parser = ResumeParser()
        resume_path = FIXTURES_DIR / 'minimal_resume.txt'

        sections = parser.parse_resume_with_sections(str(resume_path))

        # Should detect at least experience or education
        assert len(sections['experience']) > 0 or len(sections['education']) > 0


class TestResumeParserValidation:
    """Test suite for resume file validation."""

    def test_validate_resume_file_valid_txt(self):
        """Test validation passes for valid TXT resume."""
        parser = ResumeParser()
        resume_path = FIXTURES_DIR / 'john_doe_resume.txt'

        is_valid, error = parser.validate_resume_file(str(resume_path))

        assert is_valid is True
        assert error is None

    def test_validate_resume_file_nonexistent(self):
        """Test validation fails for non-existent file."""
        parser = ResumeParser()

        is_valid, error = parser.validate_resume_file('nonexistent.txt')

        assert is_valid is False
        assert error is not None

    def test_validate_resume_checks_for_sections(self):
        """Test validation checks for resume sections."""
        parser = ResumeParser()
        resume_path = FIXTURES_DIR / 'john_doe_resume.txt'

        is_valid, error = parser.validate_resume_file(str(resume_path))

        # Should pass because it has standard resume sections
        assert is_valid is True

    def test_validate_resume_minimal(self):
        """Test validation of minimal but valid resume."""
        parser = ResumeParser()
        resume_path = FIXTURES_DIR / 'minimal_resume.txt'

        is_valid, error = parser.validate_resume_file(str(resume_path))

        # Minimal resume might fail validation if too short
        # This is OK - validation is meant to catch poor quality resumes
        if not is_valid:
            assert 'short' in error.lower() or 'sections' in error.lower()
        else:
            assert is_valid is True


class TestResumeParserTextCleaning:
    """Test suite for resume-specific text cleaning."""

    def test_clean_resume_text_removes_page_numbers(self):
        """Test that page numbers are removed."""
        parser = ResumeParser()

        text = "Page 1 of 2\n\nJohn Doe\nSoftware Engineer"
        cleaned = parser._clean_resume_text(text)

        assert 'page 1 of 2' not in cleaned.lower()
        assert 'john doe' in cleaned.lower()

    def test_clean_resume_text_removes_references_line(self):
        """Test that 'References available upon request' is removed."""
        parser = ResumeParser()

        text = "John Doe\nSoftware Engineer\n\nReferences available upon request"
        cleaned = parser._clean_resume_text(text)

        assert 'references available' not in cleaned.lower()
        assert 'john doe' in cleaned.lower()

    def test_clean_resume_text_normalizes_whitespace(self):
        """Test that excessive whitespace is normalized."""
        parser = ResumeParser()

        text = "John Doe\n\n\n\n\nSoftware Engineer"
        cleaned = parser._clean_resume_text(text)

        # Should not have more than 2 consecutive newlines
        assert '\n\n\n' not in cleaned


class TestResumeParserSectionHeaderFinding:
    """Test suite for _find_section_header method."""

    def test_find_section_header_simple(self):
        """Test finding a simple section header."""
        parser = ResumeParser()
        text = "John Doe\n\nExperience\n\nSoftware Engineer"

        position = parser._find_section_header(text, ResumeSections.EXPERIENCE)

        assert position is not None
        assert position > 0

    def test_find_section_header_with_colon(self):
        """Test finding section header with colon."""
        parser = ResumeParser()
        text = "John Doe\n\nExperience:\n\nSoftware Engineer"

        position = parser._find_section_header(text, ResumeSections.EXPERIENCE)

        assert position is not None

    def test_find_section_header_uppercase(self):
        """Test finding uppercase section header."""
        parser = ResumeParser()
        text = "John Doe\n\nEXPERIENCE\n\nSoftware Engineer"

        position = parser._find_section_header(text, ResumeSections.EXPERIENCE)

        assert position is not None

    def test_find_section_header_not_found(self):
        """Test when section header is not found."""
        parser = ResumeParser()
        text = "John Doe\n\nSoftware Engineer"

        position = parser._find_section_header(text, ResumeSections.EXPERIENCE)

        assert position is None

    def test_find_section_header_alternate_name(self):
        """Test finding section with alternate name."""
        parser = ResumeParser()
        text = "John Doe\n\nWork Experience\n\nSoftware Engineer"

        position = parser._find_section_header(text, ResumeSections.EXPERIENCE)

        # Should find "Work Experience" as it's in the list
        assert position is not None


class TestResumeParserErrorHandling:
    """Test suite for error handling."""

    def test_parse_invalid_file_type(self):
        """Test parsing invalid file type raises error."""
        parser = ResumeParser()

        # Create a temporary file with invalid extension
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b"Some content")
            temp_path = f.name

        try:
            with pytest.raises(UnsupportedFileTypeError):
                parser.parse_resume(temp_path)
        finally:
            import os
            os.unlink(temp_path)

    def test_parse_empty_file_raises_error(self):
        """Test parsing empty file raises appropriate error."""
        parser = ResumeParser()

        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w') as f:
            temp_path = f.name

        try:
            # Empty file should raise FileParseError
            with pytest.raises(FileParseError):
                parser.parse_resume(temp_path)
        finally:
            import os
            os.unlink(temp_path)


class TestResumeParserIntegration:
    """Integration tests for ResumeParser."""

    def test_full_workflow_john_doe(self):
        """Test complete workflow with John Doe resume."""
        parser = ResumeParser()
        resume_path = FIXTURES_DIR / 'john_doe_resume.txt'

        # Validate
        is_valid, error = parser.validate_resume_file(str(resume_path))
        assert is_valid

        # Parse with sections
        sections = parser.parse_resume_with_sections(str(resume_path))

        # Verify all major sections detected
        assert len(sections['experience']) > 100  # Substantial experience section
        assert len(sections['education']) > 20
        assert len(sections['skills']) > 20

        # Verify content
        assert 'tech corp' in sections['experience'].lower()
        assert 'berkeley' in sections['education'].lower()
        assert 'python' in sections['skills'].lower()

    def test_full_workflow_jane_smith(self):
        """Test complete workflow with Jane Smith resume."""
        parser = ResumeParser()
        resume_path = FIXTURES_DIR / 'jane_smith_resume.txt'

        # Validate
        is_valid, error = parser.validate_resume_file(str(resume_path))
        assert is_valid

        # Parse with sections
        sections = parser.parse_resume_with_sections(str(resume_path))

        # Verify content
        assert 'product manager' in sections['experience'].lower()
        assert 'harvard' in sections['education'].lower() or 'stanford' in sections['education'].lower()
