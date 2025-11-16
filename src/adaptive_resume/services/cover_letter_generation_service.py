"""AI-powered cover letter generation service using Claude API.

This module provides AI-powered generation of professional cover letters
tailored to specific job postings and candidate profiles.
"""

from typing import List, Optional, Dict, Any
import json
from pathlib import Path
from datetime import datetime
from anthropic import Anthropic
from sqlalchemy.orm import Session

from adaptive_resume.config.settings import Settings
from adaptive_resume.models.cover_letter import CoverLetter
from adaptive_resume.models.profile import Profile
from adaptive_resume.models.job_posting import JobPosting
from adaptive_resume.models.tailored_resume import TailoredResumeModel


class CoverLetterGenerationService:
    """Service for AI-powered cover letter generation using Claude.

    This service uses the Anthropic Claude API to generate professional,
    tailored cover letters based on templates, job postings, and candidate profiles.

    Attributes:
        session: SQLAlchemy database session
        api_key: Anthropic API key (from settings or provided)
        enabled: Whether AI generation is available
        client: Anthropic API client instance
        templates: Loaded cover letter templates
    """

    TEMPLATES_FILE = Path(__file__).parent.parent / "data" / "cover_letter_templates.json"
    AI_MODEL = "claude-sonnet-4-20250514"

    def __init__(self, session: Session, api_key: Optional[str] = None):
        """Initialize cover letter generation service.

        Args:
            session: SQLAlchemy database session
            api_key: Optional Anthropic API key. If not provided, will try to load from settings.
        """
        self.session = session
        self.settings = Settings()
        self.api_key = api_key or self.settings.get_api_key()
        self.enabled = bool(self.api_key)

        if self.enabled:
            self.client = Anthropic(api_key=self.api_key)
        else:
            self.client = None

        self.templates = self.load_templates()

    def load_templates(self) -> Dict[str, Any]:
        """Load cover letter templates from JSON file.

        Returns:
            Dictionary containing templates and guidelines

        Raises:
            FileNotFoundError: If templates file doesn't exist
            json.JSONDecodeError: If templates file is malformed
        """
        if not self.TEMPLATES_FILE.exists():
            raise FileNotFoundError(f"Templates file not found: {self.TEMPLATES_FILE}")

        with open(self.TEMPLATES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific template by ID.

        Args:
            template_id: Template identifier (e.g., "professional", "enthusiastic")

        Returns:
            Template dictionary or None if not found
        """
        for template in self.templates.get('templates', []):
            if template['id'] == template_id:
                return template
        return None

    def generate_cover_letter(
        self,
        profile: Profile,
        job_posting: Optional[JobPosting] = None,
        tailored_resume: Optional[TailoredResumeModel] = None,
        template_id: str = "professional",
        tone: Optional[str] = None,
        length: str = "medium",
        focus_areas: Optional[List[str]] = None,
        custom_context: Optional[Dict[str, Any]] = None
    ) -> CoverLetter:
        """Generate a complete cover letter using AI.

        Args:
            profile: Candidate profile
            job_posting: Optional job posting to tailor to
            tailored_resume: Optional tailored resume for consistency
            template_id: Template to use (default: "professional")
            tone: Override template's default tone
            length: Desired length ("short", "medium", "long")
            focus_areas: List of areas to emphasize (e.g., ["leadership", "technical"])
            custom_context: Additional context for generation

        Returns:
            Generated CoverLetter model instance (not yet committed to DB)

        Raises:
            ValueError: If AI is not enabled or template not found
            Exception: If generation fails
        """
        if not self.enabled or not self.client:
            raise ValueError("AI generation is not enabled. Please configure an Anthropic API key.")

        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        # Use template's default tone if not overridden
        if tone is None:
            tone = template.get('tone', 'professional')

        # Build context for AI generation
        context = self._build_context(
            profile=profile,
            job_posting=job_posting,
            tailored_resume=tailored_resume,
            template=template,
            tone=tone,
            length=length,
            focus_areas=focus_areas or [],
            custom_context=custom_context or {}
        )

        # Generate sections
        opening = self.generate_opening(template, context)
        body_paragraphs = self.generate_body_paragraphs(template, context)
        closing = self.generate_closing(template, context)

        # Assemble complete cover letter
        content = self._assemble_cover_letter(opening, body_paragraphs, closing)

        # Create CoverLetter model
        cover_letter = CoverLetter(
            profile_id=profile.id,
            job_posting_id=job_posting.id if job_posting else None,
            tailored_resume_id=tailored_resume.id if tailored_resume else None,
            content=content,
            opening_paragraph=opening,
            body_paragraphs=body_paragraphs,
            closing_paragraph=closing,
            template_id=template_id,
            tone=tone,
            length=length,
            focus_areas=focus_areas,
            ai_generated=True,
            ai_prompt_used=json.dumps(context, indent=2),  # Store for reference
            ai_model=self.AI_MODEL,
            user_edited=False,
            edit_history=[],
            company_name=job_posting.company_name if job_posting else None,
            job_title=job_posting.job_title if job_posting else None,
            word_count=self.calculate_word_count(content)
        )

        return cover_letter

    def generate_opening(self, template: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Generate opening paragraph using AI.

        Args:
            template: Cover letter template
            context: Generation context

        Returns:
            Generated opening paragraph text
        """
        prompt = self._build_opening_prompt(template, context)
        return self._call_ai(prompt, section="opening")

    def generate_body_paragraphs(
        self,
        template: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[str]:
        """Generate body paragraphs using AI.

        Args:
            template: Cover letter template
            context: Generation context

        Returns:
            List of generated body paragraph texts
        """
        num_paragraphs = template.get('body_structure', {}).get('paragraphs', 2)
        prompt = self._build_body_prompt(template, context, num_paragraphs)

        # AI returns JSON with array of paragraphs
        response = self._call_ai(prompt, section="body", expect_json=True)

        if isinstance(response, dict) and 'paragraphs' in response:
            return response['paragraphs']
        elif isinstance(response, list):
            return response
        else:
            # Fallback: treat as single paragraph
            return [str(response)]

    def generate_closing(self, template: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Generate closing paragraph using AI.

        Args:
            template: Cover letter template
            context: Generation context

        Returns:
            Generated closing paragraph text
        """
        prompt = self._build_closing_prompt(template, context)
        return self._call_ai(prompt, section="closing")

    def enhance_section(
        self,
        text: str,
        instructions: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Enhance an existing cover letter section.

        Args:
            text: Original section text
            instructions: Enhancement instructions (e.g., "make more enthusiastic")
            context: Optional context for enhancement

        Returns:
            Enhanced section text
        """
        if not self.enabled or not self.client:
            return text  # Return original if AI not available

        prompt = f"""Enhance the following cover letter section according to these instructions:

Instructions: {instructions}

Original text:
{text}

{self._format_context(context) if context else ""}

Return ONLY the enhanced text, without any explanation or metadata."""

        try:
            return self._call_ai(prompt, section="enhancement")
        except Exception as e:
            print(f"Enhancement error: {e}")
            return text  # Return original on error

    def regenerate_section(
        self,
        cover_letter: CoverLetter,
        section: str,
        custom_instructions: Optional[str] = None
    ) -> str:
        """Regenerate a specific section of an existing cover letter.

        Args:
            cover_letter: Existing cover letter
            section: Section to regenerate ("opening", "body", "closing")
            custom_instructions: Optional custom instructions

        Returns:
            Newly generated section text

        Raises:
            ValueError: If section is invalid
        """
        if section not in ["opening", "body", "closing"]:
            raise ValueError(f"Invalid section: {section}. Must be 'opening', 'body', or 'closing'")

        template = self.get_template(cover_letter.template_id)
        if not template:
            raise ValueError(f"Template not found: {cover_letter.template_id}")

        # Reconstruct context (simplified - may not have all original context)
        profile = self.session.get(Profile, cover_letter.profile_id)
        job_posting = None
        tailored_resume = None

        if cover_letter.job_posting_id:
            job_posting = self.session.get(JobPosting, cover_letter.job_posting_id)
        if cover_letter.tailored_resume_id:
            tailored_resume = self.session.get(TailoredResumeModel, cover_letter.tailored_resume_id)

        context = self._build_context(
            profile=profile,
            job_posting=job_posting,
            tailored_resume=tailored_resume,
            template=template,
            tone=cover_letter.tone,
            length=cover_letter.length,
            focus_areas=cover_letter.focus_areas or [],
            custom_context={'custom_instructions': custom_instructions} if custom_instructions else {}
        )

        if section == "opening":
            return self.generate_opening(template, context)
        elif section == "closing":
            return self.generate_closing(template, context)
        else:  # body
            paragraphs = self.generate_body_paragraphs(template, context)
            return "\n\n".join(paragraphs)

    def _build_context(
        self,
        profile: Profile,
        job_posting: Optional[JobPosting],
        tailored_resume: Optional[TailoredResumeModel],
        template: Dict[str, Any],
        tone: str,
        length: str,
        focus_areas: List[str],
        custom_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build comprehensive context for AI generation.

        Args:
            profile: Candidate profile
            job_posting: Optional job posting
            tailored_resume: Optional tailored resume
            template: Selected template
            tone: Desired tone
            length: Desired length
            focus_areas: Areas to emphasize
            custom_context: Additional custom context

        Returns:
            Context dictionary for AI prompts
        """
        context = {
            'template': template,
            'tone': tone,
            'length': length,
            'focus_areas': focus_areas,
            'candidate': {
                'name': profile.full_name,
                'email': profile.email,
                'phone': profile.phone,
                'summary': profile.professional_summary,
            }
        }

        # Add job posting info
        if job_posting:
            # Parse requirements from JSON if available
            required_skills = []
            preferred_skills = []
            if job_posting.requirements_json:
                try:
                    requirements = json.loads(job_posting.requirements_json)
                    required_skills = requirements.get('required_skills', [])
                    preferred_skills = requirements.get('preferred_skills', [])
                except (json.JSONDecodeError, TypeError):
                    pass

            context['job'] = {
                'title': job_posting.job_title,
                'company': job_posting.company_name,
                'description': job_posting.raw_text[:1000] if job_posting.raw_text else None,  # Limit size
                'required_skills': required_skills,
                'preferred_skills': preferred_skills,
            }

        # Add work history from profile
        if profile.jobs:
            recent_jobs = sorted(profile.jobs, key=lambda j: j.start_date or datetime.min, reverse=True)[:3]
            context['work_history'] = [
                {
                    'title': job.job_title,
                    'company': job.company_name,
                    'duration': f"{job.start_date} to {job.end_date or 'Present'}",
                    'accomplishments': [bp.content for bp in job.bullet_points[:5]] if job.bullet_points else []
                }
                for job in recent_jobs
            ]

        # Add skills from profile
        if profile.skills:
            context['skills'] = [skill.skill_name for skill in profile.skills[:20]]  # Top 20 skills

        # Add tailored resume info for consistency
        if tailored_resume:
            context['tailored_resume'] = {
                'match_score': tailored_resume.match_score,
                'coverage_percentage': tailored_resume.coverage_percentage,
            }

        # Merge custom context
        context.update(custom_context)

        return context

    def _build_opening_prompt(self, template: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Build AI prompt for opening paragraph generation.

        Args:
            template: Cover letter template
            context: Generation context

        Returns:
            Formatted prompt string
        """
        opening_strategy = template.get('opening_strategy', {})
        tone_guidelines = self.templates.get('tone_guidelines', {}).get(context['tone'], {})
        length_guidelines = self.templates.get('length_guidelines', {}).get(context['length'], {})

        prompt = f"""You are an expert cover letter writer. Generate the opening paragraph for a professional cover letter.

TEMPLATE STRATEGY:
- Type: {opening_strategy.get('type', 'direct')}
- Description: {opening_strategy.get('description', '')}
- Example: {opening_strategy.get('example', '')}

TONE: {context['tone']}
- Characteristics: {', '.join(tone_guidelines.get('characteristics', []))}
- Avoid: {', '.join(tone_guidelines.get('avoid', []))}

LENGTH GUIDELINE: {context['length']} ({length_guidelines.get('word_count', '250-400')} words total for full letter)

CANDIDATE:
- Name: {context['candidate']['name']}
{f"- Summary: {context['candidate']['summary']}" if context['candidate'].get('summary') else ""}

{self._format_job_context(context) if 'job' in context else ""}
{self._format_work_history(context, limit=1) if 'work_history' in context else ""}

FOCUS AREAS: {', '.join(context['focus_areas']) if context['focus_areas'] else 'General fit and interest'}

Generate ONLY the opening paragraph (2-4 sentences). Do not include a greeting/salutation. Start directly with the content."""

        return prompt

    def _build_body_prompt(
        self,
        template: Dict[str, Any],
        context: Dict[str, Any],
        num_paragraphs: int
    ) -> str:
        """Build AI prompt for body paragraphs generation.

        Args:
            template: Cover letter template
            context: Generation context
            num_paragraphs: Number of paragraphs to generate

        Returns:
            Formatted prompt string
        """
        body_structure = template.get('body_structure', {})
        tone_guidelines = self.templates.get('tone_guidelines', {}).get(context['tone'], {})
        focus_definitions = self.templates.get('focus_area_definitions', {})

        prompt = f"""You are an expert cover letter writer. Generate the body paragraphs for a professional cover letter.

TEMPLATE STRATEGY:
- Type: {body_structure.get('type', 'achievements')}
- Number of paragraphs: {num_paragraphs}
- Description: {body_structure.get('description', '')}
- Focus: {', '.join(body_structure.get('focus', []))}

TONE: {context['tone']}
- Characteristics: {', '.join(tone_guidelines.get('characteristics', []))}
- Avoid: {', '.join(tone_guidelines.get('avoid', []))}

{self._format_job_context(context) if 'job' in context else ""}
{self._format_work_history(context) if 'work_history' in context else ""}
{self._format_skills(context) if 'skills' in context else ""}

FOCUS AREAS TO EMPHASIZE:
{self._format_focus_areas(context['focus_areas'], focus_definitions)}

Generate exactly {num_paragraphs} body paragraph(s). Each paragraph should be 3-5 sentences.
Focus on connecting the candidate's experience to the job requirements.
Include specific examples and accomplishments where possible.

Return ONLY a JSON object with this structure:
{{
  "paragraphs": [
    "First body paragraph text...",
    "Second body paragraph text..."
  ]
}}

Do not include any other text or markdown formatting - ONLY the JSON object."""

        return prompt

    def _build_closing_prompt(self, template: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Build AI prompt for closing paragraph generation.

        Args:
            template: Cover letter template
            context: Generation context

        Returns:
            Formatted prompt string
        """
        closing_strategy = template.get('closing_strategy', {})
        tone_guidelines = self.templates.get('tone_guidelines', {}).get(context['tone'], {})

        prompt = f"""You are an expert cover letter writer. Generate the closing paragraph for a professional cover letter.

TEMPLATE STRATEGY:
- Type: {closing_strategy.get('type', 'formal_call_to_action')}
- Description: {closing_strategy.get('description', '')}
- Example: {closing_strategy.get('example', '')}

TONE: {context['tone']}
- Characteristics: {', '.join(tone_guidelines.get('characteristics', []))}
- Avoid: {', '.join(tone_guidelines.get('avoid', []))}

{f"COMPANY: {context['job']['company']}" if 'job' in context else ""}

Generate ONLY the closing paragraph (2-3 sentences). Include a call to action and professional sign-off.
Do not include "Sincerely" or signature - just the closing paragraph content."""

        return prompt

    def _format_job_context(self, context: Dict[str, Any]) -> str:
        """Format job context for prompts."""
        if 'job' not in context:
            return ""

        job = context['job']
        return f"""JOB POSTING:
- Title: {job.get('title', 'N/A')}
- Company: {job.get('company', 'N/A')}
{f"- Description: {job.get('description', '')[:500]}..." if job.get('description') else ""}
{f"- Required Skills: {', '.join(job.get('required_skills', [])[:10])}" if job.get('required_skills') else ""}"""

    def _format_work_history(self, context: Dict[str, Any], limit: Optional[int] = None) -> str:
        """Format work history for prompts."""
        if 'work_history' not in context or not context['work_history']:
            return ""

        history = context['work_history'][:limit] if limit else context['work_history']
        formatted = ["RELEVANT WORK EXPERIENCE:"]

        for job in history:
            formatted.append(f"- {job['title']} at {job['company']} ({job['duration']})")
            if job.get('accomplishments'):
                for acc in job['accomplishments'][:3]:  # Top 3 accomplishments
                    formatted.append(f"  • {acc}")

        return "\n".join(formatted)

    def _format_skills(self, context: Dict[str, Any]) -> str:
        """Format skills for prompts."""
        if 'skills' not in context or not context['skills']:
            return ""

        return f"KEY SKILLS: {', '.join(context['skills'])}"

    def _format_focus_areas(self, focus_areas: List[str], definitions: Dict[str, str]) -> str:
        """Format focus areas with definitions."""
        if not focus_areas:
            return "General fit and enthusiasm for the role"

        formatted = []
        for area in focus_areas:
            definition = definitions.get(area, "")
            formatted.append(f"- {area.title()}: {definition}")

        return "\n".join(formatted)

    def _format_context(self, context: Optional[Dict[str, Any]]) -> str:
        """Format additional context for prompts."""
        if not context:
            return ""

        formatted = ["ADDITIONAL CONTEXT:"]
        for key, value in context.items():
            formatted.append(f"- {key}: {value}")

        return "\n".join(formatted)

    def _call_ai(
        self,
        prompt: str,
        section: str,
        expect_json: bool = False
    ) -> Any:
        """Call Claude API with prompt.

        Args:
            prompt: Formatted prompt
            section: Section being generated (for error messages)
            expect_json: Whether to expect JSON response

        Returns:
            Generated text or parsed JSON

        Raises:
            Exception: If API call fails
        """
        if not self.enabled or not self.client:
            raise ValueError("AI is not enabled")

        try:
            response = self.client.messages.create(
                model=self.AI_MODEL,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text.strip()

            if expect_json:
                # Strip markdown if present
                content = content.replace('```json', '').replace('```', '').strip()
                return json.loads(content)

            return content

        except json.JSONDecodeError as e:
            print(f"JSON parsing error in {section}: {e}")
            print(f"Response: {content if 'content' in locals() else 'N/A'}")
            raise
        except Exception as e:
            print(f"AI generation error in {section}: {e}")
            raise

    def _assemble_cover_letter(
        self,
        opening: str,
        body_paragraphs: List[str],
        closing: str
    ) -> str:
        """Assemble complete cover letter from sections.

        Args:
            opening: Opening paragraph
            body_paragraphs: List of body paragraphs
            closing: Closing paragraph

        Returns:
            Complete cover letter text
        """
        sections = [opening] + body_paragraphs + [closing]
        return "\n\n".join(sections)

    def calculate_word_count(self, text: str) -> int:
        """Calculate word count of text.

        Args:
            text: Text to count words in

        Returns:
            Number of words
        """
        return len(text.split())

    def validate_content(self, content: str, min_words: int = 100, max_words: int = 600) -> bool:
        """Validate cover letter content.

        Args:
            content: Cover letter text
            min_words: Minimum acceptable word count
            max_words: Maximum acceptable word count

        Returns:
            True if content is valid
        """
        if not content or not content.strip():
            return False

        word_count = self.calculate_word_count(content)
        return min_words <= word_count <= max_words

    @property
    def is_available(self) -> bool:
        """Check if AI generation is available.

        Returns:
            True if API key is configured, False otherwise
        """
        return self.enabled
