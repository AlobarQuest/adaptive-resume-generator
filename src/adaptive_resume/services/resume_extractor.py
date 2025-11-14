"""Resume extractor service for extracting structured data from resume text.

This service uses a hybrid approach combining spaCy NLP and Claude AI
to extract contact information, work experience, education, skills, and
certifications from resume text.
"""

from __future__ import annotations

import re
import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import date, datetime

import spacy

from ..config.settings import Settings

logger = logging.getLogger(__name__)


@dataclass
class ExtractedJob:
    """Extracted job/work experience data."""

    company_name: str
    job_title: str
    location: Optional[str] = None
    start_date: Optional[str] = None  # "Jan 2020" or "2020-01"
    end_date: Optional[str] = None    # "Present" or "Dec 2023"
    is_current: bool = False
    bullet_points: List[str] = field(default_factory=list)
    confidence_score: float = 0.0


@dataclass
class ExtractedEducation:
    """Extracted education data."""

    school_name: str
    degree_type: Optional[str] = None  # "Bachelor's", "Master's", "PhD"
    major: Optional[str] = None
    graduation_date: Optional[str] = None
    gpa: Optional[str] = None
    confidence_score: float = 0.0


@dataclass
class ExtractedCertification:
    """Extracted certification data."""

    name: str
    issuing_organization: Optional[str] = None
    issue_date: Optional[str] = None
    expiration_date: Optional[str] = None
    confidence_score: float = 0.0


@dataclass
class ExtractedResume:
    """Complete extracted resume data."""

    # Contact Information
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    website_url: Optional[str] = None

    # Work Experience
    jobs: List[ExtractedJob] = field(default_factory=list)

    # Education
    education: List[ExtractedEducation] = field(default_factory=list)

    # Skills
    skills: List[str] = field(default_factory=list)

    # Certifications
    certifications: List[ExtractedCertification] = field(default_factory=list)

    # Metadata
    confidence_score: float = 0.0
    extraction_method: str = "unknown"  # "spacy", "ai", "hybrid"


class ResumeExtractor:
    """Extractor for converting resume text into structured data.

    Uses a hybrid approach combining spaCy NLP and Claude AI for
    high accuracy extraction.
    """

    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the resume extractor.

        Args:
            settings: Application settings (for AI configuration)
        """
        self.settings = settings or Settings()

        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_md")
            logger.info("Loaded spaCy model: en_core_web_md")
        except OSError:
            logger.error("spaCy model not found. Run: python -m spacy download en_core_web_md")
            raise

        # Check AI availability
        self.ai_enabled = self.settings.get("ai_enhancement_enabled", False)
        if self.ai_enabled:
            from .ai_enhancement_service import AIEnhancementService
            self.ai_service = AIEnhancementService(self.settings)
            logger.info("AI extraction enabled")
        else:
            self.ai_service = None
            logger.info("AI extraction disabled")

    def extract(
        self,
        resume_sections: Dict[str, str],
        use_ai: bool = True
    ) -> ExtractedResume:
        """Extract structured data from resume sections.

        Args:
            resume_sections: Dictionary of resume sections from ResumeParser
            use_ai: Whether to use AI extraction (requires API key)

        Returns:
            ExtractedResume with all extracted data
        """
        logger.info("Starting resume extraction")

        # Always extract with spaCy
        spacy_result = self._extract_with_spacy(resume_sections)

        # Try AI extraction if enabled and requested
        if use_ai and self.ai_enabled and self.ai_service:
            try:
                logger.info("Attempting AI extraction")
                ai_result = self._extract_with_ai(resume_sections)

                # Merge results
                merged_result = self._merge_results(spacy_result, ai_result)
                merged_result.extraction_method = "hybrid"

                logger.info("Successfully extracted with hybrid approach")
                return merged_result

            except Exception as e:
                logger.warning(f"AI extraction failed, using spaCy only: {e}")
                spacy_result.extraction_method = "spacy"
                return spacy_result
        else:
            spacy_result.extraction_method = "spacy"
            logger.info("Extracted with spaCy only")
            return spacy_result

    def _extract_with_spacy(self, sections: Dict[str, str]) -> ExtractedResume:
        """Extract data using spaCy NLP.

        Args:
            sections: Resume sections from parser

        Returns:
            ExtractedResume with spaCy-extracted data
        """
        result = ExtractedResume()

        # Extract contact information
        contact_text = sections.get('contact', '') + '\n' + sections.get('raw_text', '')[:500]
        result.first_name, result.last_name = self._extract_name(contact_text)
        result.email = self._extract_email(contact_text)
        result.phone = self._extract_phone(contact_text)
        result.location = self._extract_location(contact_text)
        result.linkedin_url = self._extract_linkedin(contact_text)
        result.github_url = self._extract_github(contact_text)
        result.website_url = self._extract_website(contact_text)

        # Extract work experience
        experience_text = sections.get('experience', '')
        if experience_text:
            result.jobs = self._extract_jobs_spacy(experience_text)

        # Extract education
        education_text = sections.get('education', '')
        if education_text:
            result.education = self._extract_education_spacy(education_text)

        # Extract skills
        skills_text = sections.get('skills', '')
        if skills_text:
            result.skills = self._extract_skills_spacy(skills_text)

        # Extract certifications
        cert_text = sections.get('certifications', '')
        if cert_text:
            result.certifications = self._extract_certifications_spacy(cert_text)

        # Calculate confidence
        result.confidence_score = self._calculate_confidence(result)

        return result

    def _extract_name(self, text: str) -> tuple[Optional[str], Optional[str]]:
        """Extract first and last name from text."""
        doc = self.nlp(text[:500])  # Process first 500 chars

        # Look for PERSON entities
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                parts = ent.text.strip().split()
                if len(parts) >= 2:
                    return parts[0], ' '.join(parts[1:])
                elif len(parts) == 1:
                    return parts[0], None

        # Fallback: First line might be name
        first_line = text.split('\n')[0].strip()
        if first_line and len(first_line.split()) <= 4:  # Names are typically 1-4 words
            parts = first_line.split()
            if len(parts) >= 2:
                return parts[0], ' '.join(parts[1:])

        return None, None

    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address from text."""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(pattern, text)
        return match.group(0) if match else None

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from text."""
        # Various phone patterns
        patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (555) 123-4567
            r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',        # 555-123-4567
            r'\+\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'  # +1-555-123-4567
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)

        return None

    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location (city, state) from text."""
        doc = self.nlp(text[:500])

        # Look for GPE (geopolitical entity) like cities, states
        locations = []
        for ent in doc.ents:
            if ent.label_ in ["GPE", "LOC"]:
                locations.append(ent.text)

        if locations:
            return ', '.join(locations[:2])  # Take first 2 (typically city, state)

        return None

    def _extract_linkedin(self, text: str) -> Optional[str]:
        """Extract LinkedIn URL from text."""
        pattern = r'linkedin\.com/in/[\w-]+'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            url = match.group(0)
            if not url.startswith('http'):
                url = 'https://' + url
            return url
        return None

    def _extract_github(self, text: str) -> Optional[str]:
        """Extract GitHub URL from text."""
        pattern = r'github\.com/[\w-]+'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            url = match.group(0)
            if not url.startswith('http'):
                url = 'https://' + url
            return url
        return None

    def _extract_website(self, text: str) -> Optional[str]:
        """Extract personal website URL from text."""
        # Look for http/https URLs that aren't LinkedIn or GitHub
        pattern = r'https?://(?!linkedin|github)[^\s]+'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(0) if match else None

    def _extract_jobs_spacy(self, text: str) -> List[ExtractedJob]:
        """Extract job experiences using spaCy."""
        jobs = []

        # Split by company/job pattern
        # Look for patterns like "Company Name | Location" or "Job Title\nCompany Name"
        lines = text.split('\n')

        current_job = None
        current_bullets = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if this is a company/title line (usually has dates or bullet doesn't start with •)
            if not line.startswith('•') and not line.startswith('-'):
                # Save previous job if exists
                if current_job:
                    current_job.bullet_points = current_bullets
                    jobs.append(current_job)
                    current_bullets = []

                # Try to extract company, title, dates
                company, title, location, start, end, is_current = self._parse_job_header(line, lines)

                if company or title:
                    current_job = ExtractedJob(
                        company_name=company or "Unknown Company",
                        job_title=title or "Unknown Title",
                        location=location,
                        start_date=start,
                        end_date=end,
                        is_current=is_current,
                        confidence_score=0.7
                    )
            else:
                # This is a bullet point
                bullet = line.lstrip('•-').strip()
                if bullet:
                    current_bullets.append(bullet)

        # Add last job
        if current_job:
            current_job.bullet_points = current_bullets
            jobs.append(current_job)

        return jobs

    def _parse_job_header(
        self,
        line: str,
        context_lines: List[str]
    ) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], bool]:
        """Parse a job header line to extract company, title, location, dates."""
        # This is a heuristic approach - AI will do better
        company = None
        title = None
        location = None
        start_date = None
        end_date = None
        is_current = False

        # Look for dates in the line
        date_pattern = r'(\w+ \d{4}|\d{4})\s*[-–—]\s*(\w+ \d{4}|\d{4}|Present|Current)'
        date_match = re.search(date_pattern, line, re.IGNORECASE)

        if date_match:
            start_date = date_match.group(1)
            end_date = date_match.group(2)
            if end_date.lower() in ['present', 'current']:
                is_current = True

            # Remove dates from line to parse company/title
            line = line[:date_match.start()].strip()

        # Split by common separators
        parts = re.split(r'[|•]', line)

        if len(parts) >= 2:
            title = parts[0].strip()
            company = parts[1].strip()
        elif len(parts) == 1:
            # Could be just title or just company
            title = parts[0].strip()

        return company, title, location, start_date, end_date, is_current

    def _extract_education_spacy(self, text: str) -> List[ExtractedEducation]:
        """Extract education using spaCy."""
        education = []

        lines = text.split('\n')
        current_edu = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Look for degree patterns
            degree_patterns = [
                r"Bachelor['\u2019]?s?",
                r"Master['\u2019]?s?",
                r"PhD",
                r"Doctor of",
                r"Associate['\u2019]?s?",
                r"B\.?[AS]\.?",
                r"M\.?[AS]\.?",
                r"MBA"
            ]

            has_degree = any(re.search(pattern, line, re.IGNORECASE) for pattern in degree_patterns)

            if has_degree or (current_edu is None and education == []):
                # This looks like a school/degree line
                if current_edu:
                    education.append(current_edu)

                school, degree, major, grad_date, gpa = self._parse_education_line(line)

                current_edu = ExtractedEducation(
                    school_name=school or "Unknown School",
                    degree_type=degree,
                    major=major,
                    graduation_date=grad_date,
                    gpa=gpa,
                    confidence_score=0.7
                )

        if current_edu:
            education.append(current_edu)

        return education

    def _parse_education_line(
        self,
        line: str
    ) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
        """Parse education line."""
        school = None
        degree = None
        major = None
        grad_date = None
        gpa = None

        # Extract GPA
        gpa_pattern = r'GPA:?\s*(\d\.\d+)'
        gpa_match = re.search(gpa_pattern, line, re.IGNORECASE)
        if gpa_match:
            gpa = gpa_match.group(1)

        # Extract graduation date
        date_pattern = r'(\d{4}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})'
        date_match = re.search(date_pattern, line, re.IGNORECASE)
        if date_match:
            grad_date = date_match.group(1)

        # Extract degree and major (basic heuristic)
        if "bachelor" in line.lower():
            degree = "Bachelor's"
        elif "master" in line.lower() or "mba" in line.lower():
            degree = "Master's"
        elif "phd" in line.lower() or "doctor" in line.lower():
            degree = "PhD"

        # School name is typically the main part
        # Remove dates and GPA
        school = line
        if date_match:
            school = school.replace(date_match.group(0), '')
        if gpa_match:
            school = school.replace(gpa_match.group(0), '')

        school = school.split('|')[0].strip()  # Take first part if separated

        return school, degree, major, grad_date, gpa

    def _extract_skills_spacy(self, text: str) -> List[str]:
        """Extract skills using spaCy."""
        skills = []

        # Skills are typically listed with commas or bullets
        # Clean and split
        text = text.replace('•', ',').replace('-', ',')

        # Split by commas or newlines
        parts = re.split(r'[,\n]', text)

        for part in parts:
            skill = part.strip()
            # Skip section headers and empty
            if skill and len(skill) < 50 and not skill.lower().endswith(':'):
                skills.append(skill)

        return skills

    def _extract_certifications_spacy(self, text: str) -> List[ExtractedCertification]:
        """Extract certifications using spaCy."""
        certifications = []

        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line or line.endswith(':'):
                continue

            # Parse certification
            cert_name, issuer, issue_date = self._parse_certification_line(line)

            if cert_name:
                certifications.append(ExtractedCertification(
                    name=cert_name,
                    issuing_organization=issuer,
                    issue_date=issue_date,
                    confidence_score=0.7
                ))

        return certifications

    def _parse_certification_line(
        self,
        line: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse certification line."""
        name = None
        issuer = None
        issue_date = None

        # Extract date
        date_pattern = r'(\w+ \d{4}|\d{4})'
        date_match = re.search(date_pattern, line)
        if date_match:
            issue_date = date_match.group(1)
            line = line.replace(date_match.group(0), '')

        # Split by common separators
        parts = re.split(r'[-–—|]', line)

        if len(parts) >= 2:
            name = parts[0].strip()
            issuer = parts[1].strip()
        elif len(parts) == 1:
            name = parts[0].strip()

        return name, issuer, issue_date

    def _extract_with_ai(self, sections: Dict[str, str]) -> ExtractedResume:
        """Extract data using Claude AI.

        Args:
            sections: Resume sections

        Returns:
            ExtractedResume with AI-extracted data
        """
        # Combine relevant sections
        resume_text = ""
        for section_name in ['contact', 'summary', 'experience', 'education', 'skills', 'certifications']:
            if sections.get(section_name):
                resume_text += f"\n\n{section_name.upper()}:\n{sections[section_name]}"

        # Create AI prompt
        prompt = self._create_extraction_prompt(resume_text)

        # Call AI service
        response = self.ai_service.client.messages.create(
            model=self.ai_service.model,
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Parse JSON response
        response_text = response.content[0].text
        data = json.loads(response_text)

        # Convert to ExtractedResume
        return self._parse_ai_response(data)

    def _create_extraction_prompt(self, resume_text: str) -> str:
        """Create AI prompt for resume extraction."""
        return f"""Extract structured information from this resume and return as JSON.

Resume:
{resume_text}

Extract the following information:

1. Contact Information:
   - first_name, last_name
   - email, phone
   - location (city, state)
   - linkedin_url, github_url, website_url

2. Work Experience (array of jobs):
   - company_name
   - job_title
   - location
   - start_date (format: "Jan 2020" or "2020-01")
   - end_date ("Present" or "Dec 2023")
   - is_current (boolean)
   - bullet_points (array of strings)

3. Education (array):
   - school_name
   - degree_type (Bachelor's, Master's, PhD)
   - major
   - graduation_date
   - gpa

4. Skills (array of strings)

5. Certifications (array):
   - name
   - issuing_organization
   - issue_date

Return ONLY valid JSON in this exact format:
{{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone": "(555) 123-4567",
  "location": "San Francisco, CA",
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "github_url": "https://github.com/johndoe",
  "website_url": "https://johndoe.com",
  "jobs": [
    {{
      "company_name": "Tech Corp",
      "job_title": "Software Engineer",
      "location": "SF, CA",
      "start_date": "Jan 2020",
      "end_date": "Present",
      "is_current": true,
      "bullet_points": ["Developed features", "Led team"]
    }}
  ],
  "education": [
    {{
      "school_name": "UC Berkeley",
      "degree_type": "Bachelor's",
      "major": "Computer Science",
      "graduation_date": "2019",
      "gpa": "3.8"
    }}
  ],
  "skills": ["Python", "JavaScript", "SQL"],
  "certifications": [
    {{
      "name": "AWS Certified",
      "issuing_organization": "Amazon",
      "issue_date": "March 2021"
    }}
  ]
}}

Return ONLY the JSON, no other text."""

    def _parse_ai_response(self, data: Dict[str, Any]) -> ExtractedResume:
        """Parse AI response into ExtractedResume."""
        result = ExtractedResume()

        # Contact info
        result.first_name = data.get('first_name')
        result.last_name = data.get('last_name')
        result.email = data.get('email')
        result.phone = data.get('phone')
        result.location = data.get('location')
        result.linkedin_url = data.get('linkedin_url')
        result.github_url = data.get('github_url')
        result.website_url = data.get('website_url')

        # Jobs
        for job_data in data.get('jobs', []):
            job = ExtractedJob(
                company_name=job_data.get('company_name', 'Unknown'),
                job_title=job_data.get('job_title', 'Unknown'),
                location=job_data.get('location'),
                start_date=job_data.get('start_date'),
                end_date=job_data.get('end_date'),
                is_current=job_data.get('is_current', False),
                bullet_points=job_data.get('bullet_points', []),
                confidence_score=0.9
            )
            result.jobs.append(job)

        # Education
        for edu_data in data.get('education', []):
            edu = ExtractedEducation(
                school_name=edu_data.get('school_name', 'Unknown'),
                degree_type=edu_data.get('degree_type'),
                major=edu_data.get('major'),
                graduation_date=edu_data.get('graduation_date'),
                gpa=edu_data.get('gpa'),
                confidence_score=0.9
            )
            result.education.append(edu)

        # Skills
        result.skills = data.get('skills', [])

        # Certifications
        for cert_data in data.get('certifications', []):
            cert = ExtractedCertification(
                name=cert_data.get('name', 'Unknown'),
                issuing_organization=cert_data.get('issuing_organization'),
                issue_date=cert_data.get('issue_date'),
                confidence_score=0.9
            )
            result.certifications.append(cert)

        result.confidence_score = 0.9
        return result

    def _merge_results(
        self,
        spacy_result: ExtractedResume,
        ai_result: ExtractedResume
    ) -> ExtractedResume:
        """Merge spaCy and AI results, preferring AI for most fields."""
        merged = ExtractedResume()

        # Contact info: prefer AI, fallback to spaCy
        merged.first_name = ai_result.first_name or spacy_result.first_name
        merged.last_name = ai_result.last_name or spacy_result.last_name
        merged.email = ai_result.email or spacy_result.email
        merged.phone = ai_result.phone or spacy_result.phone
        merged.location = ai_result.location or spacy_result.location
        merged.linkedin_url = ai_result.linkedin_url or spacy_result.linkedin_url
        merged.github_url = ai_result.github_url or spacy_result.github_url
        merged.website_url = ai_result.website_url or spacy_result.website_url

        # Jobs: prefer AI but combine if needed
        merged.jobs = ai_result.jobs if ai_result.jobs else spacy_result.jobs

        # Education: prefer AI
        merged.education = ai_result.education if ai_result.education else spacy_result.education

        # Skills: combine and deduplicate
        all_skills = set(ai_result.skills + spacy_result.skills)
        merged.skills = sorted(list(all_skills))

        # Certifications: combine
        merged.certifications = ai_result.certifications + spacy_result.certifications

        # Confidence: average
        merged.confidence_score = (ai_result.confidence_score + spacy_result.confidence_score) / 2

        return merged

    def _calculate_confidence(self, result: ExtractedResume) -> float:
        """Calculate confidence score for extracted data."""
        scores = []

        # Contact info completeness
        contact_fields = [
            result.first_name, result.last_name, result.email,
            result.phone, result.location
        ]
        contact_score = sum(1 for f in contact_fields if f) / len(contact_fields)
        scores.append(contact_score)

        # Has work experience
        if result.jobs:
            scores.append(1.0)
        else:
            scores.append(0.3)

        # Has education
        if result.education:
            scores.append(1.0)
        else:
            scores.append(0.5)

        # Has skills
        if result.skills:
            scores.append(1.0)
        else:
            scores.append(0.3)

        return sum(scores) / len(scores)


__all__ = [
    'ResumeExtractor',
    'ExtractedResume',
    'ExtractedJob',
    'ExtractedEducation',
    'ExtractedCertification'
]
