"""Utility functions for PDF resume generation.

This module provides common utility functions used across all resume templates,
including date formatting, text wrapping, and drawing helpers.
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Optional, List
import logging
import re

logger = logging.getLogger(__name__)


def format_date_range(
    start_date: Optional[str],
    end_date: Optional[str],
    is_current: bool = False
) -> str:
    """Format a date range for resume display.

    Converts various date formats to a consistent display format.
    Handles current positions and missing dates gracefully.

    Args:
        start_date: Start date (YYYY-MM-DD, YYYY-MM, or YYYY format)
        end_date: End date (same formats) or None
        is_current: Whether this is a current position

    Returns:
        Formatted date range (e.g., "Jan 2020 - Present", "2018 - 2020")

    Examples:
        >>> format_date_range("2020-01-15", "2022-12-31", False)
        'Jan 2020 - Dec 2022'
        >>> format_date_range("2020-01", None, True)
        'Jan 2020 - Present'
        >>> format_date_range("2018", "2020", False)
        '2018 - 2020'
    """
    def parse_date(date_str: Optional[str]) -> Optional[date]:
        """Parse date string into date object."""
        if not date_str:
            return None

        # Try different formats
        formats = ['%Y-%m-%d', '%Y-%m', '%Y']
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        return None

    def format_date(dt: Optional[date], show_month: bool = True) -> str:
        """Format date for display."""
        if not dt:
            return ""

        if show_month:
            return dt.strftime('%b %Y')  # Jan 2020
        else:
            return dt.strftime('%Y')  # 2020

    # Parse dates
    start = parse_date(start_date)
    end = parse_date(end_date) if not is_current else None

    # Format start date
    start_str = format_date(start) if start else ""

    # Format end date
    if is_current:
        end_str = "Present"
    elif end:
        end_str = format_date(end)
    else:
        end_str = ""

    # Combine
    if start_str and end_str:
        return f"{start_str} - {end_str}"
    elif start_str:
        return start_str
    elif end_str:
        return end_str
    else:
        return ""


def wrap_text(text: str, max_length: int = 80) -> List[str]:
    """Wrap text to fit within a maximum line length.

    Args:
        text: Text to wrap
        max_length: Maximum characters per line

    Returns:
        List of wrapped lines

    Example:
        >>> wrap_text("This is a long line that needs wrapping", 20)
        ['This is a long line', 'that needs wrapping']
    """
    if not text:
        return []

    words = text.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        word_length = len(word)

        # Check if adding this word would exceed max length
        if current_length + word_length + len(current_line) > max_length:
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_length = word_length
            else:
                # Word itself is longer than max_length
                lines.append(word)
        else:
            current_line.append(word)
            current_length += word_length

    # Add remaining words
    if current_line:
        lines.append(' '.join(current_line))

    return lines


def clean_text(text: str) -> str:
    """Clean text for PDF display.

    Removes extra whitespace, normalizes line breaks, and sanitizes
    special characters that might cause issues in PDFs.

    Args:
        text: Text to clean

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove leading/trailing whitespace
    text = text.strip()

    # Replace problematic characters
    replacements = {
        '\u2018': "'",  # Left single quote
        '\u2019': "'",  # Right single quote
        '\u201c': '"',  # Left double quote
        '\u201d': '"',  # Right double quote
        '\u2013': '-',  # En dash
        '\u2014': '-',  # Em dash
        '\u2026': '...',  # Ellipsis
    }

    for old_char, new_char in replacements.items():
        text = text.replace(old_char, new_char)

    return text


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to a maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length (including suffix)
        suffix: Suffix to add if truncated (default: "...")

    Returns:
        Truncated text

    Example:
        >>> truncate_text("This is a long text", 10)
        'This is...'
    """
    if not text or len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def format_gpa(gpa: Optional[float]) -> str:
    """Format GPA for display.

    Args:
        gpa: GPA value (0.0-4.0)

    Returns:
        Formatted GPA string (e.g., "3.75")
    """
    if gpa is None:
        return ""

    return f"{float(gpa):.2f}"


def format_location(city: Optional[str], state: Optional[str]) -> str:
    """Format city and state for display.

    Args:
        city: City name
        state: State name or abbreviation

    Returns:
        Formatted location (e.g., "San Francisco, CA")

    Examples:
        >>> format_location("San Francisco", "CA")
        'San Francisco, CA'
        >>> format_location("Seattle", None)
        'Seattle'
        >>> format_location(None, "NY")
        'NY'
    """
    if city and state:
        return f"{city}, {state}"
    elif city:
        return city
    elif state:
        return state
    else:
        return ""


def group_by_company(accomplishments: List[dict]) -> dict:
    """Group accomplishments by company.

    Args:
        accomplishments: List of accomplishment dictionaries with 'company_name' key

    Returns:
        Dictionary mapping company names to lists of accomplishments

    Example:
        >>> accomplishments = [
        ...     {'company_name': 'CompanyA', 'text': 'Did thing 1'},
        ...     {'company_name': 'CompanyB', 'text': 'Did thing 2'},
        ...     {'company_name': 'CompanyA', 'text': 'Did thing 3'},
        ... ]
        >>> grouped = group_by_company(accomplishments)
        >>> len(grouped['CompanyA'])
        2
    """
    grouped = {}

    for acc in accomplishments:
        company = acc.get('company_name', 'Unknown')
        if company not in grouped:
            grouped[company] = []
        grouped[company].append(acc)

    return grouped


def sort_by_date(items: List[dict], date_key: str = 'start_date', descending: bool = True) -> List[dict]:
    """Sort items by date.

    Args:
        items: List of dictionaries with date fields
        date_key: Key to sort by (e.g., 'start_date', 'end_date')
        descending: Sort descending (newest first) if True

    Returns:
        Sorted list of items

    Example:
        >>> jobs = [
        ...     {'start_date': '2018-01-01'},
        ...     {'start_date': '2020-01-01'},
        ...     {'start_date': '2019-01-01'},
        ... ]
        >>> sorted_jobs = sort_by_date(jobs)
        >>> sorted_jobs[0]['start_date']
        '2020-01-01'
    """
    def get_sort_key(item: dict) -> tuple:
        """Get sort key for an item."""
        date_str = item.get(date_key, '')

        # Parse date
        if not date_str:
            # Items without dates go to the end
            return (datetime.min if descending else datetime.max,)

        # Try to parse date
        formats = ['%Y-%m-%d', '%Y-%m', '%Y']
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return (dt,)
            except ValueError:
                continue

        # If parsing fails, treat as minimum date
        return (datetime.min if descending else datetime.max,)

    return sorted(items, key=get_sort_key, reverse=descending)


__all__ = [
    'format_date_range',
    'wrap_text',
    'clean_text',
    'truncate_text',
    'format_gpa',
    'format_location',
    'group_by_company',
    'sort_by_date',
]
