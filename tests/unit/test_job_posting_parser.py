"""
Unit tests for JobPostingParser service.

Tests cover:
- File parsing (TXT, PDF, DOCX)
- File validation
- Text cleaning and normalization
- Encoding detection
- Error handling
- Edge cases
"""

import pytest
import tempfile
from pathlib import Path
from adaptive_resume.services.job_posting_parser import (
    JobPostingParser,
    JobPostingParserError,
    UnsupportedFileTypeError,
    FileTooLargeError,
    FileParseError,
)


class TestJobPostingParserInit:
    """Test suite for parser initialization."""

    def test_init_default(self):
        """Test parser initialization with default settings."""
        parser = JobPostingParser()
        assert parser.max_file_size == 10 * 1024 * 1024  # 10MB
        assert '.pdf' in parser.supported_formats
        assert '.docx' in parser.supported_formats
        assert '.txt' in parser.supported_formats

    def test_init_custom_size(self):
        """Test parser initialization with custom max file size."""
        custom_size = 5 * 1024 * 1024  # 5MB
        parser = JobPostingParser(max_file_size=custom_size)
        assert parser.max_file_size == custom_size


class TestJobPostingParserTextCleaning:
    """Test suite for text cleaning functionality."""

    def test_clean_text_basic(self):
        """Test basic text cleaning."""
        parser = JobPostingParser()
        text = "Job  Title:   Software    Engineer\n\n\n\nCompany: TechCorp"
        cleaned = parser.clean_text(text)

        assert "Software Engineer" in cleaned
        assert "   " not in cleaned  # No triple spaces
        assert "\n\n\n" not in cleaned  # No triple newlines

    def test_clean_text_encoding_issues(self):
        """Test cleaning text with encoding issues."""
        parser = JobPostingParser()
        text = "We\u2019re looking for developers\u2014someone great!"
        cleaned = parser.clean_text(text)

        assert "We're" in cleaned
        assert "developers--someone" in cleaned
        assert "\u2019" not in cleaned
        assert "\u2014" not in cleaned

    def test_clean_text_boilerplate_removal(self):
        """Test removal of boilerplate text."""
        parser = JobPostingParser()
        text = """
        Software Engineer position.

        Requirements: Python, SQL

        We are an equal opportunity employer. All qualified applicants
        will receive consideration.

        EOE M/F/D/V

        Click here to apply now!
        """
        cleaned = parser.clean_text(text)

        assert "Software Engineer" in cleaned
        assert "Python" in cleaned
        # Boilerplate should be reduced or removed
        assert cleaned.count("equal opportunity") <= 1

    def test_clean_text_empty(self):
        """Test cleaning empty text."""
        parser = JobPostingParser()
        assert parser.clean_text("") == ""
        assert parser.clean_text("   \n\n  ") == ""

    def test_clean_text_line_break_normalization(self):
        """Test normalization of different line break types."""
        parser = JobPostingParser()
        text = "Line 1\r\nLine 2\rLine 3\nLine 4"
        cleaned = parser.clean_text(text)

        # Should normalize to \n only
        assert "\r\n" not in cleaned
        assert "\r" not in cleaned
        assert "Line 1\nLine 2\nLine 3\nLine 4" in cleaned


class TestJobPostingParserTextParsing:
    """Test suite for text file parsing."""

    def test_parse_text_direct(self):
        """Test parsing text directly without file."""
        parser = JobPostingParser()
        text = "Job Title: Software Engineer\nRequirements: Python, SQL"
        result = parser.parse_text(text)

        assert "Software Engineer" in result
        assert "Python" in result

    def test_parse_text_file_sample(self):
        """Test parsing the sample job posting file."""
        parser = JobPostingParser()
        test_file = Path(__file__).parent.parent / "fixtures" / "sample_job_postings" / "sample_job_posting.txt"

        if not test_file.exists():
            pytest.skip("Sample job posting file not found")

        result = parser.parse_file(str(test_file))

        assert "Software Engineer" in result
        assert "Python" in result
        assert "Django" in result
        assert "5+ years" in result

    def test_parse_text_file_simple(self):
        """Test parsing a simple job posting."""
        parser = JobPostingParser()
        test_file = Path(__file__).parent.parent / "fixtures" / "sample_job_postings" / "simple_posting.txt"

        if not test_file.exists():
            pytest.skip("Simple posting file not found")

        result = parser.parse_file(str(test_file))

        assert "Data Scientist" in result
        assert "Python" in result
        assert "Machine Learning" in result

    def test_parse_text_file_whitespace(self):
        """Test parsing file with excessive whitespace."""
        parser = JobPostingParser()
        test_file = Path(__file__).parent.parent / "fixtures" / "sample_job_postings" / "whitespace_test.txt"

        if not test_file.exists():
            pytest.skip("Whitespace test file not found")

        result = parser.parse_file(str(test_file))

        assert "Software Engineer" in result
        assert "Python programming" in result
        # Should not have excessive spaces
        assert "    " not in result
        # Boilerplate should be removed
        assert result.count("equal opportunity") <= 1


class TestJobPostingParserFileValidation:
    """Test suite for file validation."""

    def test_validate_file_not_found(self):
        """Test validation of non-existent file."""
        parser = JobPostingParser()
        is_valid, error = parser.validate_file("nonexistent_file.txt")

        assert not is_valid
        assert "not found" in error.lower()

    def test_validate_file_unsupported_type(self):
        """Test validation of unsupported file type."""
        parser = JobPostingParser()

        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            temp_path = f.name
            f.write(b"test content")

        try:
            is_valid, error = parser.validate_file(temp_path)
            assert not is_valid
            assert "unsupported" in error.lower()
        finally:
            Path(temp_path).unlink()

    def test_validate_file_too_large(self):
        """Test validation of oversized file."""
        parser = JobPostingParser(max_file_size=100)  # 100 bytes

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            temp_path = f.name
            f.write(b"x" * 200)  # 200 bytes

        try:
            is_valid, error = parser.validate_file(temp_path)
            assert not is_valid
            assert "too large" in error.lower()
        finally:
            Path(temp_path).unlink()

    def test_validate_file_valid(self):
        """Test validation of valid file."""
        parser = JobPostingParser()
        test_file = Path(__file__).parent.parent / "fixtures" / "sample_job_postings" / "simple_posting.txt"

        if not test_file.exists():
            pytest.skip("Simple posting file not found")

        is_valid, error = parser.validate_file(str(test_file))

        assert is_valid
        assert error is None


class TestJobPostingParserErrorHandling:
    """Test suite for error handling."""

    def test_parse_file_not_found(self):
        """Test parsing non-existent file raises correct error."""
        parser = JobPostingParser()

        with pytest.raises(FileNotFoundError):
            parser.parse_file("nonexistent_file.txt")

    def test_parse_file_unsupported_type(self):
        """Test parsing unsupported file type raises correct error."""
        parser = JobPostingParser()

        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            temp_path = f.name
            f.write(b"test content")

        try:
            with pytest.raises(UnsupportedFileTypeError):
                parser.parse_file(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_parse_file_too_large(self):
        """Test parsing oversized file raises correct error."""
        parser = JobPostingParser(max_file_size=100)  # 100 bytes

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            temp_path = f.name
            f.write(b"x" * 200)  # 200 bytes

        try:
            with pytest.raises(FileTooLargeError):
                parser.parse_file(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_parse_empty_file(self):
        """Test parsing empty file raises correct error."""
        parser = JobPostingParser()
        test_file = Path(__file__).parent.parent / "fixtures" / "sample_job_postings" / "empty_file.txt"

        if not test_file.exists():
            pytest.skip("Empty file not found")

        with pytest.raises(FileParseError):
            parser.parse_file(str(test_file))


class TestJobPostingParserPDFSupport:
    """Test suite for PDF parsing (if pypdf is available)."""

    def test_pdf_support_available(self):
        """Test if PDF support is properly detected."""
        parser = JobPostingParser()
        # Just check the property exists
        assert isinstance(parser.is_pdf_supported, bool)

    def test_parse_pdf_without_library(self, monkeypatch):
        """Test PDF parsing fails gracefully without pypdf."""
        parser = JobPostingParser()

        # Mock PDF_AVAILABLE to False
        import adaptive_resume.services.job_posting_parser as parser_module
        original_value = parser_module.PDF_AVAILABLE
        monkeypatch.setattr(parser_module, 'PDF_AVAILABLE', False)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            temp_path = f.name
            f.write(b"fake pdf content")

        try:
            with pytest.raises(FileParseError) as exc_info:
                parser.parse_file(temp_path)
            assert "PDF support not available" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()
            monkeypatch.setattr(parser_module, 'PDF_AVAILABLE', original_value)


class TestJobPostingParserDOCXSupport:
    """Test suite for DOCX parsing (if python-docx is available)."""

    def test_docx_support_available(self):
        """Test if DOCX support is properly detected."""
        parser = JobPostingParser()
        # Just check the property exists
        assert isinstance(parser.is_docx_supported, bool)

    def test_parse_docx_without_library(self, monkeypatch):
        """Test DOCX parsing fails gracefully without python-docx."""
        parser = JobPostingParser()

        # Mock DOCX_AVAILABLE to False
        import adaptive_resume.services.job_posting_parser as parser_module
        original_value = parser_module.DOCX_AVAILABLE
        monkeypatch.setattr(parser_module, 'DOCX_AVAILABLE', False)

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            temp_path = f.name
            f.write(b"fake docx content")

        try:
            with pytest.raises(FileParseError) as exc_info:
                parser.parse_file(temp_path)
            assert "DOCX support not available" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()
            monkeypatch.setattr(parser_module, 'DOCX_AVAILABLE', original_value)


class TestJobPostingParserIntegration:
    """Integration tests for complete workflows."""

    def test_full_workflow_text_file(self):
        """Test complete workflow: validate -> parse -> clean."""
        parser = JobPostingParser()
        test_file = Path(__file__).parent.parent / "fixtures" / "sample_job_postings" / "sample_job_posting.txt"

        if not test_file.exists():
            pytest.skip("Sample job posting file not found")

        # Validate
        is_valid, error = parser.validate_file(str(test_file))
        assert is_valid
        assert error is None

        # Parse
        result = parser.parse_file(str(test_file))

        # Verify quality
        assert len(result) > 100  # Should have substantial content
        assert "Software Engineer" in result
        assert "Python" in result
        assert "Django" in result
        assert "    " not in result  # No excessive whitespace
        assert result.count("\n\n\n") == 0  # No triple newlines

    def test_parse_text_direct_workflow(self):
        """Test parsing pasted text workflow."""
        parser = JobPostingParser()

        raw_text = """
        Senior   Backend    Engineer


        Required: Python,  PostgreSQL, Docker


        5+ years experience

        We are an equal opportunity employer EOE
        """

        result = parser.parse_text(raw_text)

        assert "Backend Engineer" in result
        assert "Python" in result
        assert "PostgreSQL" in result
        assert "    " not in result
        # Boilerplate reduced
        assert result.count("equal opportunity") <= 1
