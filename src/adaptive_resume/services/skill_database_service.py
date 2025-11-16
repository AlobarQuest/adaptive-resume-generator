"""
Skill Database Service - Autocomplete and skill search functionality.

Provides fuzzy search, autocomplete, and skill recommendations from
a comprehensive skill database.
"""

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Dict, Any
from difflib import SequenceMatcher


@dataclass
class SkillSuggestion:
    """A skill suggestion returned from search."""

    id: int
    name: str
    canonical_name: str
    category: str
    subcategory: str
    description: str
    difficulty_level: str
    popularity_rank: int
    trending: bool
    match_score: float  # 0.0 to 1.0, higher is better
    match_type: str  # "exact", "alias", "prefix", "fuzzy", "category"


@dataclass
class SkillDetails:
    """Complete details for a skill."""

    id: int
    name: str
    canonical_name: str
    aliases: List[str]
    category: str
    subcategory: str
    related_skills: List[int]
    difficulty_level: str
    common_in_roles: List[str]
    description: str
    popularity_rank: int
    trending: bool


@dataclass
class SkillMatch:
    """Result of validating a skill name."""

    matched: bool
    skill_id: Optional[int]
    canonical_name: Optional[str]
    match_type: str  # "exact", "alias", "fuzzy", "none"


class SkillDatabaseServiceError(Exception):
    """Base exception for skill database service errors."""
    pass


class SkillDatabaseService:
    """
    Service for searching and autocompleting skills from a comprehensive database.

    Features:
    - Fuzzy search with multiple matching strategies
    - Autocomplete with ranking
    - Skill relationships and recommendations
    - Performance-optimized with caching
    """

    def __init__(self, database_path: Optional[Path] = None):
        """
        Initialize the skill database service.

        Args:
            database_path: Path to skills database JSON file.
                          If None, uses default bundled database.
        """
        if database_path is None:
            # Use bundled database
            package_dir = Path(__file__).parent.parent
            database_path = package_dir / "data" / "skills_database.json"

        self.database_path = database_path
        self._database: Dict[str, Any] = {}
        self._skills_by_id: Dict[int, Dict[str, Any]] = {}
        self._skills_by_canonical: Dict[str, Dict[str, Any]] = {}
        self._alias_map: Dict[str, int] = {}  # alias -> skill_id
        self._category_skills: Dict[str, List[int]] = {}  # category -> skill_ids

        self._load_database()

    def _load_database(self) -> None:
        """Load and index the skills database."""
        if not self.database_path.exists():
            raise SkillDatabaseServiceError(
                f"Skill database not found at {self.database_path}"
            )

        try:
            with open(self.database_path, 'r', encoding='utf-8') as f:
                self._database = json.load(f)
        except json.JSONDecodeError as e:
            raise SkillDatabaseServiceError(
                f"Failed to parse skill database: {e}"
            )

        # Index skills for fast lookup
        for skill in self._database.get('skills', []):
            skill_id = skill['id']
            canonical = skill['canonical_name'].lower()

            self._skills_by_id[skill_id] = skill
            self._skills_by_canonical[canonical] = skill

            # Index aliases
            for alias in skill.get('aliases', []):
                self._alias_map[alias.lower()] = skill_id

            # Also add the display name as an alias
            self._alias_map[skill['name'].lower()] = skill_id

            # Index by category
            category = skill['category']
            if category not in self._category_skills:
                self._category_skills[category] = []
            self._category_skills[category].append(skill_id)

    def search_skills(
        self,
        query: str,
        limit: int = 10,
        category_filter: Optional[str] = None
    ) -> List[SkillSuggestion]:
        """
        Search for skills matching the query with autocomplete-style ranking.

        Matching strategy (in priority order):
        1. Exact match on canonical name or alias
        2. Prefix match on name or alias
        3. Fuzzy match on name
        4. Contains match in description

        Args:
            query: Search query string
            limit: Maximum number of results to return
            category_filter: Optional category to filter by

        Returns:
            List of SkillSuggestion sorted by relevance
        """
        if not query or not query.strip():
            # Return popular/trending skills
            return self._get_popular_skills(limit, category_filter)

        query = query.strip().lower()
        matches: List[SkillSuggestion] = []

        # Get skills to search (filtered by category if needed)
        skills_to_search = self._get_skills_for_search(category_filter)

        for skill in skills_to_search:
            suggestion = self._match_skill(skill, query)
            if suggestion:
                matches.append(suggestion)

        # Sort by match score (descending), then popularity (ascending rank = more popular)
        matches.sort(key=lambda x: (-x.match_score, x.popularity_rank))

        return matches[:limit]

    def _get_skills_for_search(
        self,
        category_filter: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Get list of skills to search based on category filter."""
        if category_filter:
            skill_ids = self._category_skills.get(category_filter, [])
            return [self._skills_by_id[sid] for sid in skill_ids]
        return list(self._skills_by_id.values())

    def _match_skill(
        self,
        skill: Dict[str, Any],
        query: str
    ) -> Optional[SkillSuggestion]:
        """
        Attempt to match a skill against a query.

        Returns SkillSuggestion if match found, None otherwise.
        """
        canonical = skill['canonical_name'].lower()
        name = skill['name'].lower()
        aliases = [a.lower() for a in skill.get('aliases', [])]

        # 1. Exact match (highest priority)
        if query == canonical or query == name or query in aliases:
            return self._create_suggestion(skill, 1.0, "exact")

        # 2. Prefix match
        if canonical.startswith(query) or name.startswith(query):
            score = 0.9
            return self._create_suggestion(skill, score, "prefix")

        for alias in aliases:
            if alias.startswith(query):
                return self._create_suggestion(skill, 0.85, "prefix")

        # 3. Contains match
        if query in canonical or query in name:
            score = 0.7
            return self._create_suggestion(skill, score, "contains")

        for alias in aliases:
            if query in alias:
                return self._create_suggestion(skill, 0.65, "contains")

        # 4. Fuzzy match using sequence matcher
        fuzzy_score = self._fuzzy_match(query, canonical, name, aliases)
        if fuzzy_score >= 0.6:  # Minimum threshold for fuzzy match
            return self._create_suggestion(skill, fuzzy_score, "fuzzy")

        # 5. Description contains (lowest priority)
        description = skill.get('description', '').lower()
        if query in description:
            return self._create_suggestion(skill, 0.3, "description")

        return None

    def _fuzzy_match(
        self,
        query: str,
        canonical: str,
        name: str,
        aliases: List[str]
    ) -> float:
        """
        Calculate fuzzy match score using sequence similarity.

        Returns the highest similarity score found.
        """
        scores = [
            SequenceMatcher(None, query, canonical).ratio(),
            SequenceMatcher(None, query, name).ratio(),
        ]

        for alias in aliases:
            scores.append(SequenceMatcher(None, query, alias).ratio())

        return max(scores)

    def _create_suggestion(
        self,
        skill: Dict[str, Any],
        score: float,
        match_type: str
    ) -> SkillSuggestion:
        """Create a SkillSuggestion from a skill dict."""
        # Boost trending skills slightly
        if skill.get('trending', False):
            score = min(1.0, score * 1.05)

        return SkillSuggestion(
            id=skill['id'],
            name=skill['name'],
            canonical_name=skill['canonical_name'],
            category=skill['category'],
            subcategory=skill['subcategory'],
            description=skill['description'],
            difficulty_level=skill['difficulty_level'],
            popularity_rank=skill['popularity_rank'],
            trending=skill['trending'],
            match_score=score,
            match_type=match_type
        )

    def _get_popular_skills(
        self,
        limit: int,
        category_filter: Optional[str] = None
    ) -> List[SkillSuggestion]:
        """Get popular/trending skills when no query provided."""
        skills = self._get_skills_for_search(category_filter)

        # Prefer trending skills, then sort by popularity
        trending = [s for s in skills if s.get('trending', False)]
        non_trending = [s for s in skills if not s.get('trending', False)]

        trending.sort(key=lambda x: x['popularity_rank'])
        non_trending.sort(key=lambda x: x['popularity_rank'])

        combined = trending[:limit//2] + non_trending[:limit//2]

        suggestions = [
            self._create_suggestion(skill, 0.5, "popular")
            for skill in combined[:limit]
        ]

        return suggestions

    def get_skill_details(self, skill_id: int) -> Optional[SkillDetails]:
        """
        Get complete details for a skill by ID.

        Args:
            skill_id: Skill ID to look up

        Returns:
            SkillDetails if found, None otherwise
        """
        skill = self._skills_by_id.get(skill_id)
        if not skill:
            return None

        return SkillDetails(
            id=skill['id'],
            name=skill['name'],
            canonical_name=skill['canonical_name'],
            aliases=skill.get('aliases', []),
            category=skill['category'],
            subcategory=skill['subcategory'],
            related_skills=skill.get('related_skills', []),
            difficulty_level=skill['difficulty_level'],
            common_in_roles=skill.get('common_in_roles', []),
            description=skill['description'],
            popularity_rank=skill['popularity_rank'],
            trending=skill['trending']
        )

    def get_related_skills(
        self,
        skill_id: int,
        limit: int = 5
    ) -> List[SkillSuggestion]:
        """
        Get related skills for a given skill.

        Args:
            skill_id: Skill ID to find related skills for
            limit: Maximum number of related skills to return

        Returns:
            List of related SkillSuggestion objects
        """
        skill = self._skills_by_id.get(skill_id)
        if not skill:
            return []

        related_ids = skill.get('related_skills', [])[:limit]
        related_suggestions = []

        for related_id in related_ids:
            related_skill = self._skills_by_id.get(related_id)
            if related_skill:
                related_suggestions.append(
                    self._create_suggestion(related_skill, 0.8, "related")
                )

        return related_suggestions

    def suggest_skills_for_role(
        self,
        role_title: str,
        limit: int = 15
    ) -> List[SkillSuggestion]:
        """
        Suggest skills commonly used in a specific role.

        Args:
            role_title: Job role title (e.g., "Software Engineer", "Data Scientist")
            limit: Maximum number of skills to suggest

        Returns:
            List of SkillSuggestion objects
        """
        role_lower = role_title.lower()
        matching_skills = []

        for skill in self._skills_by_id.values():
            common_roles = [r.lower() for r in skill.get('common_in_roles', [])]

            # Check if role matches any common roles
            for common_role in common_roles:
                if role_lower in common_role or common_role in role_lower:
                    suggestion = self._create_suggestion(skill, 0.9, "role_match")
                    matching_skills.append(suggestion)
                    break

        # Sort by popularity
        matching_skills.sort(key=lambda x: x.popularity_rank)

        return matching_skills[:limit]

    def validate_skill(self, skill_name: str) -> SkillMatch:
        """
        Validate if a skill name exists in the database.

        Args:
            skill_name: Skill name to validate

        Returns:
            SkillMatch with validation results
        """
        if not skill_name or not skill_name.strip():
            return SkillMatch(
                matched=False,
                skill_id=None,
                canonical_name=None,
                match_type="none"
            )

        name_lower = skill_name.strip().lower()

        # Check exact canonical match
        if name_lower in self._skills_by_canonical:
            skill = self._skills_by_canonical[name_lower]
            return SkillMatch(
                matched=True,
                skill_id=skill['id'],
                canonical_name=skill['canonical_name'],
                match_type="exact"
            )

        # Check alias match
        if name_lower in self._alias_map:
            skill_id = self._alias_map[name_lower]
            skill = self._skills_by_id[skill_id]
            return SkillMatch(
                matched=True,
                skill_id=skill_id,
                canonical_name=skill['canonical_name'],
                match_type="alias"
            )

        # Try fuzzy match as last resort
        best_match = None
        best_score = 0.0

        for skill in self._skills_by_id.values():
            canonical = skill['canonical_name'].lower()
            name = skill['name'].lower()
            aliases = [a.lower() for a in skill.get('aliases', [])]

            score = self._fuzzy_match(name_lower, canonical, name, aliases)
            if score > best_score:
                best_score = score
                best_match = skill

        # Accept fuzzy match if score is high enough
        if best_score >= 0.8:
            return SkillMatch(
                matched=True,
                skill_id=best_match['id'],
                canonical_name=best_match['canonical_name'],
                match_type="fuzzy"
            )

        return SkillMatch(
            matched=False,
            skill_id=None,
            canonical_name=None,
            match_type="none"
        )

    def get_skill_by_alias(self, alias: str) -> Optional[SkillDetails]:
        """
        Get skill details by alias or name.

        Args:
            alias: Skill name or alias to look up

        Returns:
            SkillDetails if found, None otherwise
        """
        match = self.validate_skill(alias)
        if match.matched and match.skill_id:
            return self.get_skill_details(match.skill_id)
        return None

    def get_categories(self) -> List[Dict[str, Any]]:
        """
        Get all skill categories.

        Returns:
            List of category dictionaries
        """
        return self._database.get('categories', [])

    def get_skill_path(self, path_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a skill progression path by ID.

        Args:
            path_id: Skill path ID

        Returns:
            Skill path dictionary if found, None otherwise
        """
        for path in self._database.get('skill_paths', []):
            if path['id'] == path_id:
                return path
        return None

    def get_all_skill_paths(self) -> List[Dict[str, Any]]:
        """
        Get all skill progression paths.

        Returns:
            List of skill path dictionaries
        """
        return self._database.get('skill_paths', [])

    @property
    def total_skills(self) -> int:
        """Get total number of skills in database."""
        return len(self._skills_by_id)

    @property
    def version(self) -> str:
        """Get database version."""
        return self._database.get('version', 'unknown')
