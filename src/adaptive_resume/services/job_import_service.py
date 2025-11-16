"""
Job Import Service - Import jobs from various sources.

Provides functionality for importing job postings from URLs, clipboard,
CSV files, and various job board platforms.
"""

import re
import csv
import json
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urlparse
from dataclasses import dataclass
from io import StringIO

try:
    import requests
    from bs4 import BeautifulSoup
    SCRAPING_AVAILABLE = True
except ImportError:
    SCRAPING_AVAILABLE = False


@dataclass
class ImportedJob:
    """Container for imported job data."""
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    description: str = ""
    requirements: Optional[str] = None
    application_url: Optional[str] = None
    source_platform: Optional[str] = None
    raw_html: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'company_name': self.company_name,
            'job_title': self.job_title,
            'location': self.location,
            'salary': self.salary,
            'description': self.description,
            'requirements': self.requirements,
            'application_url': self.application_url,
            'source_platform': self.source_platform
        }


class JobImportService:
    """Service for importing jobs from various sources."""

    # Platform detection patterns
    PLATFORM_PATTERNS = {
        'linkedin': r'linkedin\.com',
        'indeed': r'indeed\.com',
        'glassdoor': r'glassdoor\.com',
        'monster': r'monster\.com',
        'ziprecruiter': r'ziprecruiter\.com',
        'dice': r'dice\.com',
        'stackoverflow': r'stackoverflow\.com/jobs',
        'github': r'github\.com/careers',
    }

    def __init__(self, timeout: int = 10):
        """Initialize the service.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = None
        if SCRAPING_AVAILABLE:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

    def detect_platform(self, url: str) -> Optional[str]:
        """Detect the job board platform from URL.

        Args:
            url: Job posting URL

        Returns:
            Platform name or None if not recognized
        """
        for platform, pattern in self.PLATFORM_PATTERNS.items():
            if re.search(pattern, url, re.IGNORECASE):
                return platform
        return 'generic'

    def import_from_url(self, url: str, user_consent: bool = False) -> ImportedJob:
        """Import a job from a URL.

        Args:
            url: Job posting URL
            user_consent: Whether user consented to web scraping

        Returns:
            ImportedJob with extracted data

        Raises:
            ValueError: If scraping not available or consent not given
            requests.RequestException: If request fails
        """
        if not SCRAPING_AVAILABLE:
            raise ValueError(
                "Web scraping not available. Install requests and beautifulsoup4: "
                "pip install requests beautifulsoup4"
            )

        if not user_consent:
            raise ValueError(
                "User consent required for web scraping. Please confirm that you "
                "have permission to scrape this website and comply with its Terms of Service."
            )

        # Detect platform
        platform = self.detect_platform(url)

        # Fetch the page
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()

        html = response.text

        # Parse based on platform
        if platform == 'linkedin':
            job = self._parse_linkedin(html, url)
        elif platform == 'indeed':
            job = self._parse_indeed(html, url)
        elif platform == 'glassdoor':
            job = self._parse_glassdoor(html, url)
        else:
            job = self._parse_generic(html, url)

        job.source_platform = platform
        job.application_url = url
        job.raw_html = html

        return job

    def import_from_clipboard(self, text: str) -> ImportedJob:
        """Import a job from clipboard text.

        Args:
            text: Pasted job posting text

        Returns:
            ImportedJob with extracted data
        """
        job = ImportedJob()
        job.description = text
        job.source_platform = 'clipboard'

        # Try to extract basic info from text
        lines = text.split('\n')

        # Look for company name (often in first few lines)
        for i, line in enumerate(lines[:5]):
            line = line.strip()
            if line and len(line) < 100:  # Company names are usually short
                # Heuristic: If line contains certain keywords, might be company
                if any(word in line.lower() for word in ['inc', 'llc', 'corp', 'ltd', 'company']):
                    job.company_name = line
                    break

        # Look for job title (usually prominent early in text)
        for i, line in enumerate(lines[:10]):
            line = line.strip()
            if line and 20 < len(line) < 100:  # Job titles are medium length
                # Heuristic: Contains job-related keywords
                if any(word in line.lower() for word in [
                    'engineer', 'developer', 'manager', 'analyst', 'designer',
                    'specialist', 'coordinator', 'director', 'senior', 'junior'
                ]):
                    if not job.job_title:  # Take first match
                        job.job_title = line
                        break

        # Look for location
        location_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2})'
        location_match = re.search(location_pattern, text)
        if location_match:
            job.location = location_match.group(1)

        # Look for salary
        salary_pattern = r'\$[\d,]+(?:\s*-\s*\$[\d,]+)?(?:\s*(?:per|/)\s*(?:year|hour|yr|hr))?'
        salary_match = re.search(salary_pattern, text, re.IGNORECASE)
        if salary_match:
            job.salary = salary_match.group(0)

        return job

    def import_bulk_csv(self, csv_content: str) -> List[Tuple[ImportedJob, Optional[str]]]:
        """Import multiple jobs from CSV content.

        Expected CSV format:
        company_name,job_title,location,salary,description,application_url

        Args:
            csv_content: CSV file content as string

        Returns:
            List of (ImportedJob, error_message) tuples
        """
        results = []

        try:
            reader = csv.DictReader(StringIO(csv_content))

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
                try:
                    job = ImportedJob(
                        company_name=row.get('company_name', '').strip() or None,
                        job_title=row.get('job_title', '').strip() or None,
                        location=row.get('location', '').strip() or None,
                        salary=row.get('salary', '').strip() or None,
                        description=row.get('description', '').strip() or '',
                        application_url=row.get('application_url', '').strip() or None,
                        source_platform='csv'
                    )

                    # Validate: at least job description required
                    if not job.description:
                        results.append((job, f"Row {row_num}: Missing job description"))
                    else:
                        results.append((job, None))

                except Exception as e:
                    # Create partial job with error
                    job = ImportedJob(source_platform='csv')
                    results.append((job, f"Row {row_num}: {str(e)}"))

        except Exception as e:
            # CSV parsing error
            job = ImportedJob(source_platform='csv')
            results.append((job, f"CSV parsing error: {str(e)}"))

        return results

    # Platform-specific parsers

    def _parse_linkedin(self, html: str, url: str) -> ImportedJob:
        """Parse LinkedIn job posting.

        Note: LinkedIn actively prevents scraping. This is a basic
        implementation that may not work reliably. Users should
        consider manual paste or API integration.
        """
        soup = BeautifulSoup(html, 'html.parser')
        job = ImportedJob()

        # LinkedIn uses specific class names (subject to change)
        try:
            # Job title
            title_elem = soup.find('h1', class_=re.compile('job.*title|title'))
            if title_elem:
                job.job_title = title_elem.get_text(strip=True)

            # Company name
            company_elem = soup.find('a', class_=re.compile('company|topcard'))
            if company_elem:
                job.company_name = company_elem.get_text(strip=True)

            # Location
            location_elem = soup.find('span', class_=re.compile('location|topcard'))
            if location_elem:
                job.location = location_elem.get_text(strip=True)

            # Description
            desc_elem = soup.find('div', class_=re.compile('description|show-more'))
            if desc_elem:
                job.description = desc_elem.get_text(separator='\n', strip=True)

        except Exception:
            # Fallback to generic parsing
            return self._parse_generic(html, url)

        # If we didn't get description, use generic parser
        if not job.description:
            return self._parse_generic(html, url)

        return job

    def _parse_indeed(self, html: str, url: str) -> ImportedJob:
        """Parse Indeed job posting."""
        soup = BeautifulSoup(html, 'html.parser')
        job = ImportedJob()

        try:
            # Indeed structure (as of 2025)
            # Job title
            title_elem = soup.find('h1', class_=re.compile('jobsearch.*title'))
            if not title_elem:
                title_elem = soup.find('h1')
            if title_elem:
                job.job_title = title_elem.get_text(strip=True)

            # Company name
            company_elem = soup.find('div', class_=re.compile('company'))
            if not company_elem:
                company_elem = soup.find('span', class_=re.compile('company'))
            if company_elem:
                job.company_name = company_elem.get_text(strip=True)

            # Location
            location_elem = soup.find('div', class_=re.compile('location'))
            if not location_elem:
                location_elem = soup.find('span', class_=re.compile('location'))
            if location_elem:
                job.location = location_elem.get_text(strip=True)

            # Salary
            salary_elem = soup.find('span', class_=re.compile('salary'))
            if salary_elem:
                job.salary = salary_elem.get_text(strip=True)

            # Description
            desc_elem = soup.find('div', id=re.compile('jobDesc'))
            if not desc_elem:
                desc_elem = soup.find('div', class_=re.compile('jobDesc|description'))
            if desc_elem:
                job.description = desc_elem.get_text(separator='\n', strip=True)

        except Exception:
            # Fallback to generic
            return self._parse_generic(html, url)

        if not job.description:
            return self._parse_generic(html, url)

        return job

    def _parse_glassdoor(self, html: str, url: str) -> ImportedJob:
        """Parse Glassdoor job posting."""
        soup = BeautifulSoup(html, 'html.parser')
        job = ImportedJob()

        try:
            # Glassdoor structure
            # Job title
            title_elem = soup.find('div', class_=re.compile('job.*title')) or soup.find('h2')
            if title_elem:
                job.job_title = title_elem.get_text(strip=True)

            # Company
            company_elem = soup.find('div', class_=re.compile('employer'))
            if company_elem:
                job.company_name = company_elem.get_text(strip=True)

            # Location
            location_elem = soup.find('span', class_=re.compile('location'))
            if location_elem:
                job.location = location_elem.get_text(strip=True)

            # Salary
            salary_elem = soup.find('span', class_=re.compile('salary'))
            if salary_elem:
                job.salary = salary_elem.get_text(strip=True)

            # Description
            desc_elem = soup.find('div', class_=re.compile('desc|JobDetails'))
            if desc_elem:
                job.description = desc_elem.get_text(separator='\n', strip=True)

        except Exception:
            return self._parse_generic(html, url)

        if not job.description:
            return self._parse_generic(html, url)

        return job

    def _parse_generic(self, html: str, url: str) -> ImportedJob:
        """Generic HTML parser for unknown job boards.

        Uses heuristics to find job-related content.
        """
        soup = BeautifulSoup(html, 'html.parser')
        job = ImportedJob()

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()

        # Try to find job title (usually in h1 or h2)
        for tag in ['h1', 'h2']:
            title_elem = soup.find(tag)
            if title_elem:
                text = title_elem.get_text(strip=True)
                if text and len(text) < 200:  # Reasonable title length
                    job.job_title = text
                    break

        # Look for company name (heuristics)
        # Often near the title or has "company" in class
        for elem in soup.find_all(['div', 'span', 'a'], class_=re.compile('company', re.I)):
            text = elem.get_text(strip=True)
            if text and len(text) < 100:
                job.company_name = text
                break

        # Look for location
        for elem in soup.find_all(['div', 'span'], class_=re.compile('location', re.I)):
            text = elem.get_text(strip=True)
            if text and len(text) < 100:
                job.location = text
                break

        # Look for salary
        for elem in soup.find_all(['div', 'span'], class_=re.compile('salary|compensation', re.I)):
            text = elem.get_text(strip=True)
            if '$' in text or 'salary' in text.lower():
                job.salary = text
                break

        # Get description - use main text content
        # Look for largest text block
        description_candidates = []

        for elem in soup.find_all(['div', 'section', 'article']):
            # Skip if too many child divs (likely not content)
            if len(elem.find_all('div')) > 10:
                continue

            text = elem.get_text(separator='\n', strip=True)
            if len(text) > 200:  # Substantial text
                description_candidates.append(text)

        if description_candidates:
            # Use longest text block
            job.description = max(description_candidates, key=len)
        else:
            # Fallback: get all text
            job.description = soup.get_text(separator='\n', strip=True)

        return job


__all__ = ['JobImportService', 'ImportedJob']
