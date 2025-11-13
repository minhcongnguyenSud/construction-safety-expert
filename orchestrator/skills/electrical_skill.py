"""
Electrical Safety Skill

Expert in: electrical hazards, LOTO, overhead lines, temporary power,
arc flash, GFCI, underground utilities
"""

from typing import List, Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from knowledge_base_manager import KnowledgeBaseManager
    from rag_engine import RAGEngine
except ImportError:
    from orchestrator.knowledge_base_manager import KnowledgeBaseManager
    from orchestrator.rag_engine import RAGEngine


class ElectricalSkill:
    """
    Specialized skill for electrical safety hazards.

    This skill handles questions about:
    - Electrical shock and electrocution hazards
    - Lock Out Tag Out (LOTO) procedures
    - Overhead power lines and clearance requirements
    - Temporary power installations and GFCI
    - Arc flash hazards
    - Underground utility location
    - Electrical equipment inspection
    """

    def __init__(self):
        self.name = "electrical_safety"
        self.category = "electrical"
        self.rag_engine = RAGEngine()
        self.kb_manager = KnowledgeBaseManager()

    def can_handle(self, question: str) -> float:
        """
        Determine if this skill can handle the question.
        Returns confidence score 0.0 to 1.0
        """
        keywords = [
            'electric', 'electrical', 'electrocution', 'shock', 'power',
            'loto', 'lock out', 'tag out', 'lockout', 'tagout',
            'overhead line', 'power line', 'conductor', 'voltage',
            'gfci', 'ground fault', 'grounding', 'bonding',
            'arc flash', 'energized', 'de-energize', 'temporary power',
            'generator', 'panel', 'circuit', 'underground utility'
        ]

        question_lower = question.lower()
        matches = sum(1 for kw in keywords if kw in question_lower)

        # Calculate confidence score
        confidence = min(matches / 3.0, 1.0)
        return confidence

    def handle_question(self, question: str) -> str:
        """
        Handle an electrical safety question using RAG.
        """
        # Search knowledge base
        results = self.rag_engine.search(question, category=self.category, top_k=5)

        if not results:
            return self._fallback_response(question)

        # Build context from results
        context = "\n\n".join([
            f"**{r['title']}**\n{r['content']}"
            for r in results
        ])

        # Generate response
        response = f"""**Electrical Safety**

Based on Ontario construction safety regulations:

{context}

**Critical Safety Points:**
- Sections 181-183 of O. Reg 213/91 cover electrical safety
- Maintain clearances from overhead power lines (3m minimum for up to 750V)
- LOTO procedures required before working on equipment
- All temporary power must have GFCI protection
- Only qualified electrical workers may work on energized equipment

For electrical work, always follow O. Reg 213/91 and consult qualified personnel.
"""
        return response

    def _fallback_response(self, question: str) -> str:
        """Fallback when no knowledge base results found."""
        return """**Electrical Safety**

Key electrical safety requirements under O. Reg 213/91:

- Work on de-energized equipment whenever possible (Sections 181-183)
- Lock Out Tag Out (LOTO) required before maintenance
- Maintain minimum clearances from overhead power lines
- GFCI protection required for all temporary power
- Only qualified workers may perform electrical work
- Underground utilities must be located before excavation

Contact a qualified electrical professional for specific electrical hazards.
"""
