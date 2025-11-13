"""Knowledge Base Module - Loads JSON knowledge bases for skills."""

import json
import os
from typing import List, Dict, Any

# Path to knowledge base directory
KB_DIR = os.path.dirname(os.path.abspath(__file__))


def load_knowledge_base(category: str) -> List[Dict[str, Any]]:
    """Load knowledge base entries for a specific category.

    Args:
        category: Category name ('fall', 'electrical', 'struckby', 'general')

    Returns:
        List of knowledge base entries as dictionaries

    Raises:
        FileNotFoundError: If the knowledge base file doesn't exist
        JSONDecodeError: If the JSON file is malformed
    """
    # Map category to JSON file
    category_files = {
        'fall': 'fall_base.json',
        'electrical': 'electrical_base.json',
        'struckby': 'struckby_base.json',
        'general': 'general_base.json'
    }

    if category not in category_files:
        raise ValueError(f"Unknown category: {category}. Valid categories: {list(category_files.keys())}")

    file_path = os.path.join(KB_DIR, category_files[category])

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Knowledge base file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_all_categories() -> List[str]:
    """Get list of all available knowledge base categories.

    Returns:
        List of category names
    """
    return ['fall', 'electrical', 'struckby', 'general']


def get_kb_stats() -> Dict[str, int]:
    """Get statistics about knowledge base entries.

    Returns:
        Dictionary mapping category names to entry counts
    """
    stats = {}
    for category in get_all_categories():
        try:
            kb = load_knowledge_base(category)
            stats[category] = len(kb)
        except (FileNotFoundError, json.JSONDecodeError):
            stats[category] = 0
    return stats


__all__ = [
    'load_knowledge_base',
    'get_all_categories',
    'get_kb_stats'
]
