"""PDF generation package for Adaptive Resume Generator.

This package provides functionality for generating professional PDF resumes
using ReportLab. It includes a template system for different resume styles,
utilities for formatting and layout, and integration with the resume generation
service.
"""

from .base_template import ResumeSection, TemplateSpec, BaseResumeTemplate
from .template_registry import TemplateRegistry, TemplateRegistryError
from . import pdf_utils

# Import templates to register them with TemplateRegistry
from . import templates  # noqa: F401 - imported for side effects (template registration)

__version__ = '0.1.0'

__all__ = [
    'ResumeSection',
    'TemplateSpec',
    'BaseResumeTemplate',
    'TemplateRegistry',
    'TemplateRegistryError',
    'pdf_utils',
]
