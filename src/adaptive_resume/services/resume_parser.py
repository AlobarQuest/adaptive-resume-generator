"""Resume parser service for extracting text and detecting sections from resume files.

This service extends the JobPostingParser to handle resume-specific parsing,
including section detection and resume-specific text cleaning.
"""

from __future__ import annotations

import re
import logging
from typing import Dict, Optional, Tuple
from pathlib import Path

from .job_posting_parser import (
    JobPostingParser,
    JobPostingParserError,
    UnsupportedFileTypeError,
    FileTooLargeError,
    FileParseError
)

logger = logging.getLogger(__name__)


class ResumeSections:
    """Common resume section headers and their variations."""

    CONTACT = [
        "contact", "contact information", "personal information",
        "personal details", "contact details"
    ]

    SUMMARY = [
        "summary", "professional summary", "executive summary",
        "profile", "professional profile", "objective", "career objective"
    ]

    EXPERIENCE = [
        "experience", "work experience", "professional experience",
        "employment", "employment history", "work history",
        "career history", "relevant experience"
    ]

    EDUCATION = [
        "education", "educational background", "academic background",
        "academic qualifications", "degrees"
    ]

    SKILLS = [
        "skills", "technical skills", "core competencies", "competencies",
        "areas of expertise", "expertise", "proficiencies",
        "technical proficiencies", "key skills"
    ]

    CERTIFICATIONS = [
        "certifications", "certificates", "professional certifications",
        "licenses", "credentials", "accreditations"
    ]

    PROJECTS = [
        "projects", "key projects", "notable projects",
        "academic projects", "personal projects"
    ]

    AWARDS = [
        "awards", "honors", "achievements", "recognition",
        "honors and awards", "accomplishments"
    ]


class ResumeParser:
    """Parser for extracting text and sections from resume files.

    This parser extends JobPostingParser functionality to add resume-specific
    features like section detection and resume-appropriate text cleaning.
    """

    def __init__(self):
        """Initialize the resume parser."""
        self.file_parser = JobPostingParser()

    def parse_resume(self, file_path: str) -> str:
        """Parse a resume file and extract text.

        Args:
            file_path: Path to the resume file (PDF, DOCX, or TXT)

        Returns:
            Cleaned text extracted from the resume

        Raises:
            UnsupportedFileTypeError: If file type is not supported
            FileTooLargeError: If file exceeds size limit
            FileParseError: If parsing fails
        """
        logger.info(f"Parsing resume from {file_path}")

        # Reuse file parsing from JobPostingParser
        raw_text = self.file_parser.parse_file(file_path)

        # Apply resume-specific cleaning
        cleaned_text = self._clean_resume_text(raw_text)

        logger.info(f"Successfully parsed resume ({len(cleaned_text)} characters)")
        return cleaned_text

    def parse_resume_with_sections(self, file_path: str) -> Dict[str, str]:
        """Parse a resume file and extract text organized by sections.

        Args:
            file_path: Path to the resume file

        Returns:
            Dictionary mapping section names to their content.
            Keys: 'contact', 'summary', 'experience', 'education', 'skills',
                  'certifications', 'projects', 'awards', 'raw_text'

        Raises:
            UnsupportedFileTypeError: If file type is not supported
            FileTooLargeError: If file exceeds size limit
            FileParseError: If parsing fails
        """
        logger.info(f"Parsing resume with section detection from {file_path}")

        # Parse the resume
        full_text = self.parse_resume(file_path)

        # Detect sections
        sections = self._detect_sections(full_text)
        sections['raw_text'] = full_text

        logger.info(f"Detected {len([k for k, v in sections.items() if v and k != 'raw_text'])} sections")
        return sections

    def validate_resume_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate that a file appears to be a resume.

        This performs basic validation like file size and format, plus
        some heuristics to check if the content looks like a resume.

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (is_valid, error_message)
        """
        # First use JobPostingParser validation
        is_valid, error = self.file_parser.validate_file(file_path)
        if not is_valid:
            return is_valid, error

        # Add resume-specific validation
        try:
            text = self.parse_resume(file_path)

            # Heuristic: Resume should have some common resume indicators
            text_lower = text.lower()

            # Check for at least one section header
            has_section = any(
                self._find_section_header(text, section_names)
                for section_names in [
                    ResumeSections.EXPERIENCE,
                    ResumeSections.EDUCATION,
                    ResumeSections.SKILLS,
                    ResumeSections.CONTACT
                ]
            )

            if not has_section:
                return False, "File does not appear to be a resume (no standard sections found)"

            # Check minimum length (resumes should have substantial content)
            if len(text.strip()) < 200:
                return False, "File appears too short to be a resume"

            return True, None

        except Exception as e:
            logger.error(f"Resume validation error: {e}", exc_info=True)
            return False, f"Failed to validate resume: {str(e)}"

    def _clean_resume_text(self, text: str) -> str:
        """Clean resume text.

        Args:
            text: Raw resume text

        Returns:
            Cleaned text
        """
        # Start with basic cleaning from JobPostingParser
        cleaned = self.file_parser.clean_text(text)

        # Remove common resume artifacts
        # Remove page numbers (e.g., "Page 1 of 2")
        cleaned = re.sub(r'Page\s+\d+\s+of\s+\d+', '', cleaned, flags=re.IGNORECASE)

        # Remove common footer text
        footer_patterns = [
            r'Confidential\s*-\s*Do\s+Not\s+Distribute',
            r'References\s+available\s+upon\s+request',
            r'Available\s+upon\s+request',
        ]
        for pattern in footer_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        # Remove extra whitespace
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        cleaned = cleaned.strip()

        return cleaned

    def _detect_sections(self, text: str) -> Dict[str, str]:
        """Detect and extract sections from resume text.

        Args:
            text: Resume text

        Returns:
            Dictionary mapping section names to their content
        """
        sections = {
            'contact': '',
            'summary': '',
            'experience': '',
            'education': '',
            'skills': '',
            'certifications': '',
            'projects': '',
            'awards': ''
        }

        # Find all section headers and their positions
        section_positions = []

        for section_key, section_names in [
            ('contact', ResumeSections.CONTACT),
            ('summary', ResumeSections.SUMMARY),
            ('experience', ResumeSections.EXPERIENCE),
            ('education', ResumeSections.EDUCATION),
            ('skills', ResumeSections.SKILLS),
            ('certifications', ResumeSections.CERTIFICATIONS),
            ('projects', ResumeSections.PROJECTS),
            ('awards', ResumeSections.AWARDS),
        ]:
            position = self._find_section_header(text, section_names)
            if position is not None:
                section_positions.append((position, section_key))

        # Sort by position
        section_positions.sort()

        # Extract content between sections
        for i, (start_pos, section_key) in enumerate(section_positions):
            # Find end position (start of next section or end of text)
            if i + 1 < len(section_positions):
                end_pos = section_positions[i + 1][0]
            else:
                end_pos = len(text)

            # Extract section content
            section_content = text[start_pos:end_pos].strip()

            # Remove the section header line from content
            lines = section_content.split('\n')
            if lines:
                # First line is likely the header, remove it
                section_content = '\n'.join(lines[1:]).strip()

            sections[section_key] = section_content

        # If no sections detected, try to extract contact from top
        if not any(sections.values()):
            # First 500 characters likely contain contact info
            sections['contact'] = text[:500]
            sections['experience'] = text[500:]

        return sections

    def _find_section_header(self, text: str, section_names: list) -> Optional[int]:
        """Find the position of a section header in text.

        Args:
            text: Resume text
            section_names: List of possible section header names

        Returns:
            Position of section header, or None if not found
        """
        text_lower = text.lower()

        for section_name in section_names:
            # Look for section name as a standalone line or with colon
            # Pattern: start of line, optional whitespace, section name, optional colon, optional whitespace, newline
            pattern = r'^[\s\-_]*' + re.escape(section_name) + r'[\s:_\-]*$'

            match = re.search(pattern, text_lower, re.MULTILINE | re.IGNORECASE)
            if match:
                return match.start()

        return None


__all__ = ['ResumeParser', 'ResumeSections']
