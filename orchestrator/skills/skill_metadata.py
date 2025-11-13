"""Skill metadata following SkillKit-inspired patterns."""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class SkillMetadata:
    """Metadata for a safety skill."""

    name: str
    """Skill name (e.g., 'Fall Hazard')"""

    category: str
    """Category identifier (e.g., 'fall', 'electrical')"""

    description: str
    """What this skill handles"""

    keywords: List[str]
    """Keywords for routing queries to this skill"""

    kb_category: str
    """Knowledge base category in knowledge_base/ folder"""

    confidence_threshold: float = 0.3
    """Minimum confidence to answer (below triggers fallback)"""


# Skill Registry - Progressive disclosure pattern
SKILL_REGISTRY: Dict[str, SkillMetadata] = {
    "fall": SkillMetadata(
        name="Fall Hazard",
        category="fall",
        description="Handles questions about fall hazards, working at heights, ladders, scaffolding, and fall protection",
        keywords=[
            "fall", "height", "ladder", "scaffold", "protection",
            "harness", "guardrail", "edge", "roof", "elevated",
            "scaffolding", "lanyard", "anchor", "climbing"
        ],
        kb_category="fall",
        confidence_threshold=0.15  # Lower threshold for emergency questions
    ),
    "electrical": SkillMetadata(
        name="Electrical Hazard",
        category="electrical",
        description="Handles questions about electrical safety, lockout/tagout, power lines, arc flash, and electrical equipment",
        keywords=[
            "electrical", "electric", "lockout", "tagout", "LOTO",
            "power line", "arc flash", "voltage", "wire", "shock",
            "energized", "grounding", "circuit", "outlet", "panel"
        ],
        kb_category="electrical"
    ),
    "struckby": SkillMetadata(
        name="Struck-By Hazard",
        category="struckby",
        description="Handles questions about struck-by hazards, vehicle safety, falling objects, flying debris, and load handling",
        keywords=[
            "struck", "vehicle", "forklift", "falling object", "flying",
            "debris", "load", "rigging", "material handling", "crane",
            "equipment", "moving", "swing", "suspended"
        ],
        kb_category="struckby"
    ),
    "general": SkillMetadata(
        name="General Safety",
        category="general",
        description="Handles general workplace safety questions including PPE, fire safety, hazard communication, ergonomics, and other safety topics",
        keywords=[
            "ppe", "safety", "equipment", "protection", "hazard", "emergency",
            "fire", "chemical", "ergonomic", "confined space", "heat", "cold",
            "violence", "respiratory", "machine", "guard", "slip", "trip",
            "safety glasses", "hard hat", "gloves", "boots", "hearing protection"
        ],
        kb_category="general"
    )
}


def get_skill_metadata(category: str) -> SkillMetadata:
    """Get metadata for a skill category.

    Args:
        category: Skill category (fall, electrical, struckby)

    Returns:
        SkillMetadata object

    Raises:
        KeyError: If category not found
    """
    return SKILL_REGISTRY[category]


def list_all_skills() -> List[SkillMetadata]:
    """Get list of all available skills.

    Returns:
        List of skill metadata
    """
    return list(SKILL_REGISTRY.values())
