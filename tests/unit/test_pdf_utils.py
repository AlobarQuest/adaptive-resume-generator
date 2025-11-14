"""
Unit tests for PDF utility functions.

Tests cover:
- Date range formatting
- Text wrapping and cleaning
- Text truncation
- GPA formatting
- Location formatting
- Grouping and sorting
"""

import pytest
from datetime import datetime

from adaptive_resume.pdf.pdf_utils import (
    format_date_range,
    wrap_text,
    clean_text,
    truncate_text,
    format_gpa,
    format_location,
    group_by_company,
    sort_by_date,
)


class TestDateRangeFormatting:
    """Test suite for date range formatting."""

    def test_format_date_range_full_dates(self):
        """Test formatting with full ISO dates."""
        result = format_date_range("2020-01-15", "2022-12-31", False)
        assert result == "Jan 2020 - Dec 2022"

    def test_format_date_range_month_dates(self):
        """Test formatting with year-month dates."""
        result = format_date_range("2020-01", "2022-12", False)
        assert result == "Jan 2020 - Dec 2022"

    def test_format_date_range_year_only(self):
        """Test formatting with year-only dates."""
        result = format_date_range("2018", "2020", False)
        # Year-only dates still show month (defaults to Jan)
        assert result == "Jan 2018 - Jan 2020"

    def test_format_date_range_current_position(self):
        """Test formatting for current position."""
        result = format_date_range("2020-01", None, True)
        assert result == "Jan 2020 - Present"

    def test_format_date_range_no_end_date(self):
        """Test formatting with no end date."""
        result = format_date_range("2020-01", None, False)
        assert result == "Jan 2020"

    def test_format_date_range_no_start_date(self):
        """Test formatting with no start date."""
        result = format_date_range(None, "2022-12", False)
        assert result == "Dec 2022"

    def test_format_date_range_no_dates(self):
        """Test formatting with no dates."""
        result = format_date_range(None, None, False)
        assert result == ""


class TestTextWrapping:
    """Test suite for text wrapping."""

    def test_wrap_text_basic(self):
        """Test basic text wrapping."""
        text = "This is a long line that needs wrapping"
        lines = wrap_text(text, 20)

        assert len(lines) > 1
        for line in lines:
            assert len(line) <= 25  # Allow some flexibility for word boundaries

    def test_wrap_text_short_text(self):
        """Test wrapping text shorter than max length."""
        text = "Short text"
        lines = wrap_text(text, 50)

        assert len(lines) == 1
        assert lines[0] == text

    def test_wrap_text_empty(self):
        """Test wrapping empty text."""
        lines = wrap_text("", 50)
        assert lines == []

    def test_wrap_text_single_long_word(self):
        """Test wrapping with a single word longer than max length."""
        text = "Supercalifragilisticexpialidocious"
        lines = wrap_text(text, 20)

        assert len(lines) == 1
        assert lines[0] == text


class TestTextCleaning:
    """Test suite for text cleaning."""

    def test_clean_text_whitespace(self):
        """Test cleaning extra whitespace."""
        text = "This   has    extra     spaces"
        result = clean_text(text)

        assert result == "This has extra spaces"

    def test_clean_text_special_quotes(self):
        """Test replacing special quote characters."""
        text = "\u2018single quotes\u2019 and \u201cdouble quotes\u201d"
        result = clean_text(text)

        assert "'" in result
        assert '"' in result
        assert '\u2018' not in result
        assert '\u201c' not in result

    def test_clean_text_dashes(self):
        """Test replacing en/em dashes."""
        text = "Range: 2020–2022"
        result = clean_text(text)

        assert '-' in result
        assert '\u2013' not in result

    def test_clean_text_empty(self):
        """Test cleaning empty text."""
        result = clean_text("")
        assert result == ""

    def test_clean_text_none(self):
        """Test cleaning None."""
        result = clean_text(None)
        assert result == ""


class TestTextTruncation:
    """Test suite for text truncation."""

    def test_truncate_text_long(self):
        """Test truncating long text."""
        text = "This is a very long text that needs truncation"
        result = truncate_text(text, 20)

        assert len(result) == 20
        assert result.endswith("...")

    def test_truncate_text_short(self):
        """Test truncating text shorter than max."""
        text = "Short"
        result = truncate_text(text, 20)

        assert result == text

    def test_truncate_text_custom_suffix(self):
        """Test truncating with custom suffix."""
        text = "This is long text"
        result = truncate_text(text, 10, suffix="--")

        assert len(result) == 10
        assert result.endswith("--")

    def test_truncate_text_empty(self):
        """Test truncating empty text."""
        result = truncate_text("", 20)
        assert result == ""


class TestGPAFormatting:
    """Test suite for GPA formatting."""

    def test_format_gpa_decimal(self):
        """Test formatting decimal GPA."""
        result = format_gpa(3.75)
        assert result == "3.75"

    def test_format_gpa_integer(self):
        """Test formatting integer GPA."""
        result = format_gpa(4.0)
        assert result == "4.00"

    def test_format_gpa_none(self):
        """Test formatting None GPA."""
        result = format_gpa(None)
        assert result == ""


class TestLocationFormatting:
    """Test suite for location formatting."""

    def test_format_location_city_and_state(self):
        """Test formatting with city and state."""
        result = format_location("San Francisco", "CA")
        assert result == "San Francisco, CA"

    def test_format_location_city_only(self):
        """Test formatting with city only."""
        result = format_location("Seattle", None)
        assert result == "Seattle"

    def test_format_location_state_only(self):
        """Test formatting with state only."""
        result = format_location(None, "NY")
        assert result == "NY"

    def test_format_location_none(self):
        """Test formatting with no location."""
        result = format_location(None, None)
        assert result == ""


class TestGroupByCompany:
    """Test suite for grouping accomplishments by company."""

    def test_group_by_company_basic(self):
        """Test basic grouping."""
        accomplishments = [
            {'company_name': 'CompanyA', 'text': 'Task 1'},
            {'company_name': 'CompanyB', 'text': 'Task 2'},
            {'company_name': 'CompanyA', 'text': 'Task 3'},
        ]

        grouped = group_by_company(accomplishments)

        assert len(grouped) == 2
        assert len(grouped['CompanyA']) == 2
        assert len(grouped['CompanyB']) == 1

    def test_group_by_company_empty(self):
        """Test grouping empty list."""
        grouped = group_by_company([])
        assert grouped == {}

    def test_group_by_company_missing_name(self):
        """Test grouping with missing company name."""
        accomplishments = [
            {'text': 'Task 1'},
            {'company_name': 'CompanyA', 'text': 'Task 2'},
        ]

        grouped = group_by_company(accomplishments)

        assert 'Unknown' in grouped
        assert 'CompanyA' in grouped


class TestSortByDate:
    """Test suite for sorting by date."""

    def test_sort_by_date_descending(self):
        """Test sorting in descending order (newest first)."""
        items = [
            {'start_date': '2018-01-01'},
            {'start_date': '2020-01-01'},
            {'start_date': '2019-01-01'},
        ]

        sorted_items = sort_by_date(items)

        assert sorted_items[0]['start_date'] == '2020-01-01'
        assert sorted_items[1]['start_date'] == '2019-01-01'
        assert sorted_items[2]['start_date'] == '2018-01-01'

    def test_sort_by_date_ascending(self):
        """Test sorting in ascending order (oldest first)."""
        items = [
            {'start_date': '2020-01-01'},
            {'start_date': '2018-01-01'},
            {'start_date': '2019-01-01'},
        ]

        sorted_items = sort_by_date(items, descending=False)

        assert sorted_items[0]['start_date'] == '2018-01-01'
        assert sorted_items[1]['start_date'] == '2019-01-01'
        assert sorted_items[2]['start_date'] == '2020-01-01'

    def test_sort_by_date_missing_dates(self):
        """Test sorting with missing dates."""
        items = [
            {'start_date': '2020-01-01'},
            {'start_date': ''},
            {'start_date': '2019-01-01'},
        ]

        sorted_items = sort_by_date(items)

        # Items with missing dates should be at the end
        assert sorted_items[-1]['start_date'] == ''

    def test_sort_by_date_different_key(self):
        """Test sorting by different date key."""
        items = [
            {'end_date': '2020-01-01'},
            {'end_date': '2018-01-01'},
        ]

        sorted_items = sort_by_date(items, date_key='end_date')

        assert sorted_items[0]['end_date'] == '2020-01-01'
