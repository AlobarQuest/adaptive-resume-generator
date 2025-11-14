"""Resume templates for PDF generation.

This package contains all available resume templates. Each template
inherits from BaseResumeTemplate and is registered with the TemplateRegistry.

Available templates:
- classic: Traditional professional resume with serif fonts
"""

from .classic_template import ClassicTemplate, CLASSIC_SPEC

__all__ = [
    'ClassicTemplate',
    'CLASSIC_SPEC',
]
