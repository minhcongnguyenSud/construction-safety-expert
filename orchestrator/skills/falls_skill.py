"""
Falls and Working at Heights Skill

Expert in: falls from heights, scaffolds, ladders, MEWPs, guardrails,
fall protection systems, Working at Heights (WAH) training
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


class FallsSkill:
    """
    Specialized skill for falls and working at heights hazards.

    This skill handles questions about:
    - Falls from heights (roofs, edges, openings)
    - Scaffold safety and requirements
    - Ladder selection and use
    - Mobile Elevated Work Platforms (MEWPs, boom lifts, scissor lifts)
    - Guardrail systems
    - Fall arrest, travel restraint, fall protection equipment
    - Working at Heights (WAH) training requirements
    """

    def __init__(self):
        self.name = "falls_and_working_at_heights"
        self.category = "fall"
        self.rag_engine = RAGEngine()
        self.kb_manager = KnowledgeBaseManager()

    def can_handle(self, question: str) -> float:
        """
        Determine if this skill can handle the question.
        Returns confidence score 0.0 to 1.0
        """
        keywords = [
            'fall', 'falling', 'fell', 'height', 'elevated', 'roof', 'edge',
            'scaffold', 'scaffolding', 'ladder', 'mewp', 'boom lift', 'scissor lift',
            'guardrail', 'fall arrest', 'fall protection', 'harness', 'lanyard',
            'travel restraint', 'working at heights', 'wah training', 'tie off',
            'anchor point', 'elevated work platform'
        ]

        question_lower = question.lower()
        matches = sum(1 for kw in keywords if kw in question_lower)

        # Calculate confidence score
        confidence = min(matches / 3.0, 1.0)  # 3 or more keywords = 100% confidence
        return confidence

    def handle_question(self, question: str) -> str:
        """
        Handle a falls-related safety question using RAG.
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
        response = f"""**Falls and Working at Heights Safety**

Based on Ontario construction safety regulations:

{context}

**Key Points:**
- Falls are the #1 cause of construction deaths in Ontario
- O. Reg 213/91 Section 26 requires fall protection
- Working at Heights training is mandatory for personal fall protection systems
- Use highest level of protection: guardrails > travel restraint > fall arrest

For specific situations, always consult with a competent person and follow O. Reg 213/91.
"""
        return response

    def _fallback_response(self, question: str) -> str:
        """Fallback when no knowledge base results found."""
        return """**Falls and Working at Heights Safety**

This question relates to fall protection. Key requirements under O. Reg 213/91:

- Fall protection required when exposed to fall hazards
- Guardrails are the preferred method (Section 26)
- Working at Heights (WAH) training required for personal fall protection
- Scaffolds require proper design, erection, and inspection
- Ladders must be inspected before each use
- MEWPs require operator training and fall protection

Please provide more specific details for a more detailed answer.
"""
