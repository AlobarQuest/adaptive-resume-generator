"""AI-powered bullet point enhancement service using Claude API.

This module provides AI-powered enhancement for resume bullet points using
the Anthropic Claude API. It's an optional enhancement that complements the
rule-based BulletEnhancer service.
"""

from typing import List, Optional, Dict
import json
from anthropic import Anthropic
from adaptive_resume.config.settings import Settings


class AIEnhancementService:
    """Service for AI-powered bullet point enhancement using Claude.
    
    This service uses the Anthropic Claude API to generate improved versions
    of resume bullet points following professional best practices.
    
    Attributes:
        api_key: Anthropic API key (from settings or provided)
        enabled: Whether AI enhancement is available
        client: Anthropic API client instance
    """
    
    ENHANCEMENT_PROMPT = """You are an expert resume writer and career coach. Your task is to improve a resume bullet point using best practices.

Original bullet: "{original}"

Please provide 3 improved versions of this bullet point. Each should:
1. Start with a strong action verb (Developed, Led, Implemented, etc.)
2. Include specific details about what was done
3. Show measurable impact with numbers, percentages, or concrete outcomes
4. Use professional, active voice
5. Be concise (1-2 lines, under 150 characters if possible)
6. Follow the pattern: [Action Verb] + [What] + [How/Tool] + [Impact]

If the original is missing important information (like metrics, technologies, or outcomes), use [PLACEHOLDER] to indicate where the user should fill in details.

Return ONLY a JSON object with this structure:
{{
  "suggestions": [
    {{
      "text": "First improved version",
      "focus": "brief description of what this version emphasizes",
      "placeholders": ["list", "of", "placeholders", "to", "fill"]
    }},
    {{
      "text": "Second improved version",
      "focus": "brief description",
      "placeholders": []
    }},
    {{
      "text": "Third improved version",
      "focus": "brief description",
      "placeholders": []
    }}
  ]
}}

Do not include any other text, explanation, or markdown formatting - ONLY the JSON object."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize AI service with API key.
        
        Args:
            api_key: Optional Anthropic API key. If not provided, will try to load from settings.
        """
        self.settings = Settings()
        self.api_key = api_key or self.settings.get_api_key()
        self.enabled = bool(self.api_key)
        
        if self.enabled:
            self.client = Anthropic(api_key=self.api_key)
        else:
            self.client = None
    
    def test_connection(self) -> bool:
        """Test if API key is valid by making a minimal API call.
        
        Returns:
            True if connection successful, False otherwise
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            # Make a minimal API call to test
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=50,
                messages=[{"role": "user", "content": "Say 'ok'"}]
            )
            return bool(response.content)
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def enhance_bullet(self, original_text: str) -> List[Dict[str, any]]:
        """Get AI-enhanced suggestions for a bullet point.
        
        Args:
            original_text: The original bullet point text
            
        Returns:
            List of suggestion dicts with 'text', 'focus', and 'placeholders' keys.
            Returns empty list if AI is not enabled or if enhancement fails.
            
        Example:
            >>> service = AIEnhancementService(api_key="sk-...")
            >>> suggestions = service.enhance_bullet("worked on database")
            >>> print(suggestions[0]['text'])
            'Optimized database queries using SQL indexing, reducing load time by 40%'
        """
        if not self.enabled or not self.client:
            return []
        
        try:
            prompt = self.ENHANCEMENT_PROMPT.format(original=original_text)
            
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse JSON response
            content = response.content[0].text
            
            # Strip markdown if present
            content = content.replace('```json', '').replace('```', '').strip()
            
            result = json.loads(content)
            return result.get('suggestions', [])
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Response content: {content if 'content' in locals() else 'N/A'}")
            return []
        except Exception as e:
            print(f"AI Enhancement error: {e}")
            return []
    
    def enhance_bullets_batch(
        self, 
        bullet_texts: List[str],
        progress_callback: Optional[callable] = None
    ) -> Dict[str, List[Dict[str, any]]]:
        """Enhance multiple bullets in batch.
        
        Args:
            bullet_texts: List of original bullet point texts
            progress_callback: Optional callback function(current, total) for progress updates
            
        Returns:
            Dict mapping original text to list of suggestions
        """
        results = {}
        total = len(bullet_texts)
        
        for idx, text in enumerate(bullet_texts):
            if progress_callback:
                progress_callback(idx + 1, total)
            
            results[text] = self.enhance_bullet(text)
        
        return results
    
    @property
    def is_available(self) -> bool:
        """Check if AI enhancement is available.
        
        Returns:
            True if API key is configured, False otherwise
        """
        return self.enabled
