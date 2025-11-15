"""Resume templates for PDF generation.

This package contains all available resume templates. Each template
inherits from BaseResumeTemplate and is registered with the TemplateRegistry.

Available templates:
- classic: Traditional professional resume with serif fonts
- modern: Contemporary two-column layout with sidebar
- compact: Dense, space-efficient single-column layout
- ats-friendly: Simple structure optimized for ATS parsing
"""

from .classic_template import ClassicTemplate, CLASSIC_SPEC
from .modern_template import ModernTemplate, MODERN_SPEC
from .compact_template import CompactTemplate, COMPACT_SPEC
from .ats_friendly_template import ATSFriendlyTemplate, ATS_FRIENDLY_SPEC

__all__ = [
    'ClassicTemplate',
    'CLASSIC_SPEC',
    'ModernTemplate',
    'MODERN_SPEC',
    'CompactTemplate',
    'COMPACT_SPEC',
    'ATSFriendlyTemplate',
    'ATS_FRIENDLY_SPEC',
]
