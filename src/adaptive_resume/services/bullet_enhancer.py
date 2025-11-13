"""Bullet point enhancement service using template-based approach."""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re


@dataclass
class EnhancementTemplate:
    """Template for bullet point enhancement."""
    category: str
    name: str
    pattern: str
    prompts: Dict[str, str]
    action_verbs: List[str]
    example: str
    description: str


class BulletEnhancer:
    """
    Service for rule-based bullet point enhancement.
    
    Provides template-based enhancement using industry best practices
    for resume bullet points. No external dependencies required.
    """
    
    # Template definitions based on BULLET_TEMPLATES.md
    TEMPLATES = {
        'achievement': EnhancementTemplate(
            category='achievement',
            name='Achievement/Impact',
            pattern='[ACTION] [WHAT] [METHOD], [IMPACT]',
            prompts={
                'action': 'What action verb best describes what you did? (e.g., Developed, Implemented, Built)',
                'what': 'What specifically did you create, build, or accomplish?',
                'method': 'What tools, technologies, or methods did you use?',
                'impact': 'What was the measurable impact? (%, $, time saved, quality improved)'
            },
            action_verbs=[
                'Achieved', 'Accomplished', 'Delivered', 'Developed', 'Implemented',
                'Built', 'Created', 'Designed', 'Established', 'Generated',
                'Increased', 'Improved', 'Optimized', 'Reduced', 'Exceeded'
            ],
            example='Developed automated testing framework using Python and pytest, reducing bug detection time by 40%',
            description='Use for accomplishments with measurable results and business impact'
        ),
        
        'leadership': EnhancementTemplate(
            category='leadership',
            name='Leadership/Management',
            pattern='[LED] [TEAM_SIZE] [DOING_WHAT], [OUTCOME]',
            prompts={
                'led': 'What leadership verb? (Led, Managed, Directed, Coordinated)',
                'team_size': 'How many people and what roles? (e.g., "team of 8 engineers")',
                'doing_what': 'What were you leading them through? (e.g., "through agile development")',
                'outcome': 'What specific outcome was achieved? (e.g., "delivering 2 weeks early")'
            },
            action_verbs=[
                'Led', 'Managed', 'Directed', 'Coordinated', 'Supervised',
                'Mentored', 'Coached', 'Guided', 'Oversaw', 'Spearheaded',
                'Orchestrated', 'Facilitated', 'Motivated', 'Trained', 'Cultivated'
            ],
            example='Led cross-functional team of 8 engineers through agile sprints, delivering product 2 weeks ahead of schedule',
            description='Use for team leadership, management, or mentorship roles'
        ),
        
        'technical': EnhancementTemplate(
            category='technical',
            name='Technical Implementation',
            pattern='[BUILT] [WHAT_SYSTEM] [USING_TECH], [PURPOSE]',
            prompts={
                'built': 'What technical verb? (Built, Developed, Implemented, Architected)',
                'what_system': 'What specific system, feature, or component? (e.g., "microservices architecture")',
                'using_tech': 'What specific technologies or stack? (e.g., "Node.js and Docker")',
                'purpose': 'What was the business purpose or technical improvement? (e.g., "enabling 10x user growth")'
            },
            action_verbs=[
                'Built', 'Developed', 'Architected', 'Engineered', 'Implemented',
                'Designed', 'Coded', 'Deployed', 'Integrated', 'Migrated',
                'Configured', 'Automated', 'Programmed', 'Refactored', 'Optimized'
            ],
            example='Built microservices architecture using Node.js and Docker, enabling horizontal scaling to 10x user growth',
            description='Use for software development, infrastructure, or technical implementations'
        ),
        
        'problem_solving': EnhancementTemplate(
            category='problem_solving',
            name='Problem-Solving',
            pattern='[IDENTIFIED] [PROBLEM] [BY_SOLUTION], [IMPROVEMENT]',
            prompts={
                'identified': 'What problem-solving verb? (Identified, Resolved, Fixed, Debugged)',
                'problem': 'What was the specific problem or issue? (e.g., "database query bottleneck")',
                'by_solution': 'How did you solve it? (e.g., "by implementing caching")',
                'improvement': 'What metric improved? (e.g., "response time from 3s to 0.4s")'
            },
            action_verbs=[
                'Identified', 'Resolved', 'Fixed', 'Debugged', 'Diagnosed',
                'Troubleshot', 'Solved', 'Corrected', 'Remediated', 'Eliminated',
                'Mitigated', 'Addressed', 'Uncovered', 'Discovered', 'Analyzed'
            ],
            example='Identified database N+1 query issue causing slow page loads, improving response time from 3.2s to 0.4s',
            description='Use when you solved a specific problem or fixed an issue'
        ),
        
        'process_improvement': EnhancementTemplate(
            category='process_improvement',
            name='Process Improvement',
            pattern='[STREAMLINED] [PROCESS] [RESULTING_IN]',
            prompts={
                'streamlined': 'What improvement verb? (Streamlined, Optimized, Automated, Improved)',
                'process': 'What process or workflow did you improve? (e.g., "code review process")',
                'resulting_in': 'What measurable improvement? (e.g., "reducing review time by 60%")'
            },
            action_verbs=[
                'Streamlined', 'Optimized', 'Automated', 'Improved', 'Enhanced',
                'Redesigned', 'Revamped', 'Modernized', 'Simplified', 'Accelerated',
                'Refined', 'Upgraded', 'Transformed', 'Reorganized', 'Consolidated'
            ],
            example='Streamlined code review process by implementing automated linting, reducing review time by 60%',
            description='Use when you made an existing process more efficient'
        ),
        
        'research': EnhancementTemplate(
            category='research',
            name='Research/Analysis',
            pattern='[RESEARCHED] [WHAT] [USING_METHOD], [OUTCOME]',
            prompts={
                'researched': 'What research verb? (Researched, Analyzed, Evaluated, Studied)',
                'what': 'What did you research or analyze? (e.g., "12 SaaS products in CRM space")',
                'using_method': 'What methodology? (e.g., "through competitive analysis")',
                'outcome': 'What decision or action resulted? (e.g., "identifying 3 market gaps worth $4M")'
            },
            action_verbs=[
                'Researched', 'Analyzed', 'Evaluated', 'Studied', 'Assessed',
                'Examined', 'Investigated', 'Reviewed', 'Surveyed', 'Audited',
                'Compiled', 'Measured', 'Tested', 'Validated', 'Benchmarked'
            ],
            example='Conducted competitive analysis of 12 SaaS products, identifying 3 key market gaps generating $4.2M in revenue',
            description='Use for research, analysis, or evaluation work'
        ),
        
        'training': EnhancementTemplate(
            category='training',
            name='Training/Mentorship',
            pattern='[TRAINED] [WHO] [IN_WHAT], [RESULT]',
            prompts={
                'trained': 'What development verb? (Trained, Mentored, Coached, Taught)',
                'who': 'Who did you train? (e.g., "4 junior developers")',
                'in_what': 'In what skills or practices? (e.g., "in test-driven development")',
                'result': 'What was the measurable result? (e.g., "improving code quality by 35%")'
            },
            action_verbs=[
                'Trained', 'Mentored', 'Coached', 'Taught', 'Educated',
                'Developed', 'Instructed', 'Guided', 'Onboarded', 'Upskilled',
                'Facilitated', 'Tutored', 'Counseled', 'Advised', 'Empowered'
            ],
            example='Mentored 4 junior developers in test-driven development, improving their code review scores by 35%',
            description='Use when you trained, mentored, or developed others'
        ),
        
        'collaboration': EnhancementTemplate(
            category='collaboration',
            name='Collaboration/Partnership',
            pattern='[COLLABORATED] [WITH_WHOM] [TO_ACCOMPLISH], [RESULT]',
            prompts={
                'collaborated': 'What collaboration verb? (Collaborated, Partnered, Coordinated, Worked)',
                'with_whom': 'With which teams or partners? (e.g., "with Product and Design teams")',
                'to_accomplish': 'To accomplish what? (e.g., "to launch new feature set")',
                'result': 'What was achieved? (e.g., "achieving 10K signups in first week")'
            },
            action_verbs=[
                'Collaborated', 'Partnered', 'Coordinated', 'Cooperated', 'Allied',
                'Teamed', 'United', 'Liaised', 'Interfaced', 'Synchronized',
                'Integrated', 'Negotiated', 'Facilitated', 'Brokered', 'Mediated'
            ],
            example='Partnered with Product and Design teams to launch feature set, achieving 10K+ signups in first week',
            description='Use when cross-functional collaboration was key'
        ),
        
        'initiative': EnhancementTemplate(
            category='initiative',
            name='Initiative/Innovation',
            pattern='[PIONEERED] [NEW_THING] [ACHIEVING]',
            prompts={
                'pioneered': 'What innovation verb? (Pioneered, Initiated, Launched, Established)',
                'new_thing': 'What new program, process, or system? (e.g., "company\'s first intern program")',
                'achieving': 'What was the adoption or impact? (e.g., "with 75% conversion to full-time")'
            },
            action_verbs=[
                'Pioneered', 'Initiated', 'Launched', 'Established', 'Founded',
                'Created', 'Introduced', 'Originated', 'Spearheaded', 'Championed',
                'Instituted', 'Innovated', 'Conceived', 'Devised', 'Formulated'
            ],
            example='Pioneered company\'s first intern program recruiting 8 students, with 75% conversion to full-time offers',
            description='Use when you started something new or innovative'
        ),
        
        'scale': EnhancementTemplate(
            category='scale',
            name='Scale/Growth',
            pattern='[SCALED] [WHAT] [FROM_TO] [WHILE]',
            prompts={
                'scaled': 'What growth verb? (Scaled, Grew, Expanded, Increased)',
                'what': 'What did you scale? (e.g., "platform infrastructure")',
                'from_to': 'From what to what? (e.g., "from 500K to 5M users")',
                'while_maintaining': 'While maintaining what quality? (e.g., "maintaining 99.95% uptime")'
            },
            action_verbs=[
                'Scaled', 'Grew', 'Expanded', 'Increased', 'Amplified',
                'Multiplied', 'Extended', 'Broadened', 'Accelerated', 'Boosted',
                'Elevated', 'Advanced', 'Propelled', 'Maximized', 'Surged'
            ],
            example='Scaled platform to handle 10x traffic (500K to 5M users) while maintaining 99.95% uptime',
            description='Use when you managed significant growth or scaling'
        )
    }
    
    def analyze_bullet(self, text: str) -> Tuple[str, float]:
        """
        Analyze bullet point and suggest best template category.
        
        Args:
            text: Original bullet point text
            
        Returns:
            Tuple of (category_name, confidence_score)
        """
        text_lower = text.lower()
        scores = {}
        
        # Score each template based on keyword matches
        for name, template in self.TEMPLATES.items():
            score = 0.0
            
            # Check for action verbs (strong signal)
            for verb in template.action_verbs:
                if verb.lower() in text_lower:
                    score += 2.0
                    break
            
            # Category-specific keyword matching
            if name == 'leadership' and any(word in text_lower for word in 
                ['team', 'led', 'managed', 'coordinated', 'supervised', 'mentored', 'coached']):
                score += 1.5
            
            if name == 'technical' and any(word in text_lower for word in
                ['built', 'developed', 'implemented', 'code', 'system', 'api', 'software', 'app']):
                score += 1.5
            
            if name == 'problem_solving' and any(word in text_lower for word in
                ['fixed', 'resolved', 'debugged', 'issue', 'problem', 'bug', 'error']):
                score += 1.5
            
            if name == 'process_improvement' and any(word in text_lower for word in
                ['streamlined', 'optimized', 'improved', 'automated', 'efficiency', 'faster']):
                score += 1.5
            
            if name == 'research' and any(word in text_lower for word in
                ['researched', 'analyzed', 'evaluated', 'studied', 'analysis', 'data']):
                score += 1.5
            
            if name == 'training' and any(word in text_lower for word in
                ['trained', 'mentored', 'coached', 'taught', 'onboarded', 'developed']):
                score += 1.5
            
            if name == 'collaboration' and any(word in text_lower for word in
                ['collaborated', 'partnered', 'worked with', 'cross-functional', 'stakeholder']):
                score += 1.5
            
            if name == 'initiative' and any(word in text_lower for word in
                ['pioneered', 'initiated', 'launched', 'established', 'founded', 'created', 'first']):
                score += 1.5
            
            if name == 'scale' and any(word in text_lower for word in
                ['scaled', 'grew', 'expanded', 'increased', 'growth', 'from', 'to']):
                score += 1.5
            
            # Check for quantifiable metrics (suggests achievement)
            if re.search(r'\d+%|\$\d+|from \d+ to \d+|\d+x', text):
                if name == 'achievement':
                    score += 1.0
            
            scores[name] = score
        
        # Return best match or default to achievement
        if max(scores.values()) > 0:
            best_category = max(scores, key=scores.get)
            return best_category, scores[best_category]
        
        return 'achievement', 0.5  # Default fallback
    
    def get_template(self, category: str) -> EnhancementTemplate:
        """
        Get template by category name.
        
        Args:
            category: Template category identifier
            
        Returns:
            EnhancementTemplate for the category
        """
        return self.TEMPLATES.get(category, self.TEMPLATES['achievement'])
    
    def get_all_categories(self) -> List[str]:
        """
        Get list of all template categories.
        
        Returns:
            List of category identifiers
        """
        return list(self.TEMPLATES.keys())
    
    def generate_enhanced_bullet(
        self, 
        category: str,
        responses: Dict[str, str]
    ) -> str:
        """
        Generate enhanced bullet from template and user responses.
        
        Args:
            category: Template category to use
            responses: Dict mapping prompt keys to user responses
            
        Returns:
            Formatted bullet point string
        """
        template = self.get_template(category)
        
        # Build bullet based on category-specific template
        if category == 'achievement':
            return (
                f"{responses.get('action', '[ACTION]')} "
                f"{responses.get('what', '[WHAT]')} "
                f"{responses.get('method', '[USING WHAT]')}, "
                f"{responses.get('impact', '[IMPACT]')}"
            )
        
        elif category == 'leadership':
            return (
                f"{responses.get('led', '[LED]')} "
                f"{responses.get('team_size', '[TEAM]')} "
                f"{responses.get('doing_what', '[DOING WHAT]')}, "
                f"{responses.get('outcome', '[OUTCOME]')}"
            )
        
        elif category == 'technical':
            return (
                f"{responses.get('built', '[BUILT]')} "
                f"{responses.get('what_system', '[SYSTEM]')} "
                f"using {responses.get('using_tech', '[TECH]')}, "
                f"{responses.get('purpose', '[PURPOSE]')}"
            )
        
        elif category == 'problem_solving':
            return (
                f"{responses.get('identified', '[ACTION]')} "
                f"{responses.get('problem', '[PROBLEM]')} "
                f"by {responses.get('by_solution', '[SOLUTION]')}, "
                f"{responses.get('improvement', '[IMPROVEMENT]')}"
            )
        
        elif category == 'process_improvement':
            return (
                f"{responses.get('streamlined', '[ACTION]')} "
                f"{responses.get('process', '[PROCESS]')} "
                f"{responses.get('resulting_in', '[RESULT]')}"
            )
        
        elif category == 'research':
            return (
                f"{responses.get('researched', '[ACTION]')} "
                f"{responses.get('what', '[WHAT]')} "
                f"{responses.get('using_method', '[METHOD]')}, "
                f"{responses.get('outcome', '[OUTCOME]')}"
            )
        
        elif category == 'training':
            return (
                f"{responses.get('trained', '[ACTION]')} "
                f"{responses.get('who', '[WHO]')} "
                f"in {responses.get('in_what', '[WHAT]')}, "
                f"{responses.get('result', '[RESULT]')}"
            )
        
        elif category == 'collaboration':
            return (
                f"{responses.get('collaborated', '[ACTION]')} "
                f"with {responses.get('with_whom', '[WHOM]')} "
                f"to {responses.get('to_accomplish', '[ACCOMPLISH]')}, "
                f"{responses.get('result', '[RESULT]')}"
            )
        
        elif category == 'initiative':
            return (
                f"{responses.get('pioneered', '[ACTION]')} "
                f"{responses.get('new_thing', '[NEW THING]')} "
                f"{responses.get('achieving', '[ACHIEVING]')}"
            )
        
        elif category == 'scale':
            return (
                f"{responses.get('scaled', '[ACTION]')} "
                f"{responses.get('what', '[WHAT]')} "
                f"from {responses.get('from_to', '[FROM TO]')} "
                f"while {responses.get('while_maintaining', '[WHILE]')}"
            )
        
        return "[Enhanced bullet could not be generated]"
    
    def extract_existing_info(self, text: str) -> Dict[str, str]:
        """
        Extract any existing information from the bullet to pre-fill prompts.
        
        Args:
            text: Original bullet point text
            
        Returns:
            Dict with any extracted information
        """
        info = {}
        
        # Extract numbers/metrics
        metrics = re.findall(r'\d+%|\$[\d,]+|from \d+ to \d+|\d+x', text)
        if metrics:
            info['metrics'] = ', '.join(metrics)
        
        # Extract action verb (first word if capitalized)
        words = text.split()
        if words:
            first_word = words[0].rstrip('.,;:')
            if first_word and first_word[0].isupper():
                info['action_verb'] = first_word
        
        return info
