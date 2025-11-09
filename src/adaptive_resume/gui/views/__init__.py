"""High-level views rendered inside the main GUI window."""

from .jobs_view import JobsView
from .skills_summary_view import SkillsSummaryView
from .applications_view import ApplicationsView

__all__ = ["JobsView", "SkillsSummaryView", "ApplicationsView"]
