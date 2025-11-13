"""
Tag Service - CRUD operations and intelligent tag matching for bullet points.

This service provides:
1. Basic CRUD for tags
2. Tag synonym mapping
3. Category-based grouping
4. Smart tag matching for job descriptions
"""

from typing import List, Dict, Set, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from adaptive_resume.models.tag import Tag, BulletTag, PREDEFINED_TAGS


class TagServiceError(Exception):
    """Base exception for TagService errors."""
    pass


class TagNotFoundError(TagServiceError):
    """Raised when a tag is not found."""
    pass


class TagService:
    """Service for managing tags and tag-based filtering."""
    
    # Tag synonyms for intelligent matching
    TAG_SYNONYMS = {
        'programming': ['coding', 'development', 'software development', 'software engineering'],
        'database': ['sql', 'nosql', 'data storage', 'dbms'],
        'cloud': ['aws', 'azure', 'gcp', 'cloud computing', 'cloud infrastructure'],
        'security': ['cybersecurity', 'infosec', 'information security', 'secure'],
        'devops': ['ci/cd', 'continuous integration', 'deployment', 'infrastructure as code'],
        'architecture': ['system design', 'software architecture', 'solution architecture'],
        'leadership': ['management', 'leading', 'supervising', 'directing'],
        'team-management': ['people management', 'team lead', 'managing teams'],
        'mentoring': ['coaching', 'training', 'teaching', 'guiding'],
        'project-management': ['pm', 'project coordination', 'project planning'],
        'agile': ['scrum', 'kanban', 'sprint', 'agile methodologies'],
        'budgeting': ['budget management', 'financial planning', 'cost management'],
        'cost-reduction': ['cost savings', 'cost optimization', 'expense reduction'],
        'revenue-growth': ['revenue increase', 'sales growth', 'income growth'],
        'customer-service': ['customer support', 'client service', 'help desk'],
        'sales': ['selling', 'business development', 'account executive'],
        'automation': ['automated', 'scripting', 'workflow automation'],
        'optimization': ['improve', 'enhance', 'streamline', 'optimize'],
        'api': ['rest api', 'web services', 'microservices', 'api development'],
        'frontend': ['front-end', 'ui', 'user interface', 'web development'],
        'backend': ['back-end', 'server-side', 'backend development'],
        'testing': ['qa', 'quality assurance', 'test automation', 'unit testing'],
        'documentation': ['technical writing', 'docs', 'documentation'],
        'collaboration': ['teamwork', 'cross-functional', 'team collaboration'],
        'communication': ['presentations', 'stakeholder communication', 'reporting'],
    }
    
    # Category groupings for better organization
    CATEGORY_WEIGHTS = {
        'technical': 1.2,  # Technical skills often most important
        'leadership': 1.15,  # Leadership highly valued
        'financial': 1.1,  # Financial impact matters
        'customer': 1.0,  # Standard weight
        'process': 1.05,  # Process improvements valued
        'communication': 1.0,  # Standard weight
        'problem-solving': 1.1,  # Problem solving important
        'soft-skills': 1.0,  # Standard weight
    }
    
    def __init__(self, session: Session):
        """
        Initialize TagService.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self._synonym_cache = None
        self._reverse_synonym_cache = None
    
    def create_tag(self, name: str, category: Optional[str] = None) -> Tag:
        """
        Create a new tag.
        
        Args:
            name: Tag name (will be normalized to lowercase with hyphens)
            category: Optional category for grouping
            
        Returns:
            Created Tag object
            
        Raises:
            TagServiceError: If tag already exists
        """
        # Normalize tag name
        normalized_name = self._normalize_tag_name(name)
        
        # Check if tag exists
        existing = self.get_tag_by_name(normalized_name)
        if existing:
            raise TagServiceError(f"Tag '{normalized_name}' already exists")
        
        # Create tag
        tag = Tag(name=normalized_name, category=category)
        self.session.add(tag)
        self.session.commit()
        
        return tag
    
    def get_tag_by_id(self, tag_id: int) -> Tag:
        """
        Get tag by ID.
        
        Args:
            tag_id: Tag ID
            
        Returns:
            Tag object
            
        Raises:
            TagNotFoundError: If tag not found
        """
        tag = self.session.query(Tag).filter_by(id=tag_id).first()
        if not tag:
            raise TagNotFoundError(f"Tag with ID {tag_id} not found")
        return tag
    
    def get_tag_by_name(self, name: str) -> Optional[Tag]:
        """
        Get tag by name.
        
        Args:
            name: Tag name
            
        Returns:
            Tag object or None if not found
        """
        normalized_name = self._normalize_tag_name(name)
        return self.session.query(Tag).filter_by(name=normalized_name).first()
    
    def get_or_create_tag(self, name: str, category: Optional[str] = None) -> Tag:
        """
        Get existing tag or create if it doesn't exist.
        
        Args:
            name: Tag name
            category: Optional category
            
        Returns:
            Tag object (existing or newly created)
        """
        tag = self.get_tag_by_name(name)
        if tag:
            # Update category if provided and different
            if category and tag.category != category:
                tag.category = category
                self.session.commit()
            return tag
        return self.create_tag(name, category)
    
    def get_all_tags(self, category: Optional[str] = None) -> List[Tag]:
        """
        Get all tags, optionally filtered by category.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of Tag objects
        """
        query = self.session.query(Tag)
        if category:
            query = query.filter_by(category=category)
        return query.order_by(Tag.category, Tag.name).all()
    
    def get_tags_by_category(self) -> Dict[str, List[Tag]]:
        """
        Get tags grouped by category.
        
        Returns:
            Dictionary mapping category to list of tags
        """
        tags = self.get_all_tags()
        grouped = {}
        for tag in tags:
            category = tag.category or 'uncategorized'
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(tag)
        return grouped
    
    def update_tag(self, tag_id: int, name: Optional[str] = None, 
                   category: Optional[str] = None) -> Tag:
        """
        Update tag information.
        
        Args:
            tag_id: Tag ID
            name: Optional new name
            category: Optional new category
            
        Returns:
            Updated Tag object
            
        Raises:
            TagNotFoundError: If tag not found
            TagServiceError: If new name conflicts with existing tag
        """
        tag = self.get_tag_by_id(tag_id)
        
        if name:
            normalized_name = self._normalize_tag_name(name)
            # Check for conflicts
            existing = self.get_tag_by_name(normalized_name)
            if existing and existing.id != tag_id:
                raise TagServiceError(f"Tag '{normalized_name}' already exists")
            tag.name = normalized_name
        
        if category is not None:
            tag.category = category
        
        self.session.commit()
        return tag
    
    def delete_tag(self, tag_id: int, force: bool = False) -> None:
        """
        Delete a tag.
        
        Args:
            tag_id: Tag ID
            force: If True, delete even if tag is in use
            
        Raises:
            TagNotFoundError: If tag not found
            TagServiceError: If tag is in use and force=False
        """
        tag = self.get_tag_by_id(tag_id)
        
        # Check if tag is in use
        if tag.usage_count > 0 and not force:
            raise TagServiceError(
                f"Tag '{tag.name}' is used by {tag.usage_count} bullet point(s). "
                "Use force=True to delete anyway."
            )
        
        self.session.delete(tag)
        self.session.commit()
    
    def find_matching_tags(self, text: str, threshold: float = 0.5) -> List[Tuple[Tag, float]]:
        """
        Find tags that match text using synonym matching.
        
        Args:
            text: Text to match against (e.g., job description)
            threshold: Minimum confidence score (0-1) to include
            
        Returns:
            List of (Tag, confidence_score) tuples, sorted by score descending
        """
        text_lower = text.lower()
        tag_scores = {}
        
        # Build synonym cache if needed
        if self._synonym_cache is None:
            self._build_synonym_cache()
        
        # Check each tag and its synonyms
        all_tags = self.get_all_tags()
        for tag in all_tags:
            score = 0.0
            matches = []
            
            # Check exact tag name match
            if tag.name in text_lower:
                score += 1.0
                matches.append(tag.name)
            
            # Check synonyms
            if tag.name in self._synonym_cache:
                for synonym in self._synonym_cache[tag.name]:
                    if synonym in text_lower:
                        # Synonyms get slightly lower weight
                        score += 0.8
                        matches.append(synonym)
            
            # Normalize score by number of matches (prevent double-counting)
            if matches:
                # Use max score approach: if tag name matches, that's strongest signal
                final_score = min(1.0, score)
                
                # Apply category weight
                if tag.category and tag.category in self.CATEGORY_WEIGHTS:
                    final_score *= self.CATEGORY_WEIGHTS[tag.category]
                
                if final_score >= threshold:
                    tag_scores[tag] = final_score
        
        # Sort by score descending
        return sorted(tag_scores.items(), key=lambda x: x[1], reverse=True)
    
    def suggest_tags_for_text(self, text: str, max_suggestions: int = 10) -> List[Tag]:
        """
        Suggest tags for given text.
        
        Args:
            text: Text to analyze
            max_suggestions: Maximum number of tags to suggest
            
        Returns:
            List of suggested Tag objects
        """
        matching_tags = self.find_matching_tags(text, threshold=0.3)
        return [tag for tag, score in matching_tags[:max_suggestions]]
    
    def expand_tag_query(self, tag_names: List[str]) -> Set[str]:
        """
        Expand tag names to include synonyms.
        
        Args:
            tag_names: List of tag names to expand
            
        Returns:
            Set of tag names including synonyms
        """
        if self._reverse_synonym_cache is None:
            self._build_synonym_cache()
        
        expanded = set()
        for name in tag_names:
            normalized = self._normalize_tag_name(name)
            expanded.add(normalized)
            
            # Add synonyms
            if normalized in self._synonym_cache:
                expanded.update(self._synonym_cache[normalized])
            
            # Add reverse mappings (if this is a synonym, add the primary tag)
            if normalized in self._reverse_synonym_cache:
                primary_tag = self._reverse_synonym_cache[normalized]
                expanded.add(primary_tag)
                # Add other synonyms of the primary tag
                if primary_tag in self._synonym_cache:
                    expanded.update(self._synonym_cache[primary_tag])
        
        return expanded
    
    def seed_predefined_tags(self) -> int:
        """
        Seed database with predefined tags.
        
        Returns:
            Number of tags created
        """
        created_count = 0
        for category, tag_names in PREDEFINED_TAGS.items():
            for tag_name in tag_names:
                try:
                    self.get_or_create_tag(tag_name, category)
                    created_count += 1
                except TagServiceError:
                    # Tag already exists, skip
                    pass
        return created_count
    
    def _normalize_tag_name(self, name: str) -> str:
        """
        Normalize tag name to lowercase with hyphens.
        
        Args:
            name: Raw tag name
            
        Returns:
            Normalized tag name
        """
        return name.lower().strip().replace(' ', '-').replace('_', '-')
    
    def _build_synonym_cache(self):
        """Build forward and reverse synonym caches."""
        self._synonym_cache = {}
        self._reverse_synonym_cache = {}
        
        for primary_tag, synonyms in self.TAG_SYNONYMS.items():
            # Normalize everything
            primary_normalized = self._normalize_tag_name(primary_tag)
            synonyms_normalized = [self._normalize_tag_name(s) for s in synonyms]
            
            # Store forward mapping
            self._synonym_cache[primary_normalized] = synonyms_normalized
            
            # Store reverse mapping
            for synonym in synonyms_normalized:
                self._reverse_synonym_cache[synonym] = primary_normalized
