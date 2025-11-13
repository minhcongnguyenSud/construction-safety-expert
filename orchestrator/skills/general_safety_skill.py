"""
General Construction Safety Skill

Expert in: struck-by, excavation, confined spaces, cranes, health hazards,
fire prevention, PPE, emergency response, and all other construction hazards
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


class GeneralSafetySkill:
    """
    Specialized skill for general construction safety hazards.

    This skill handles questions about:
    - Struck-by hazards (mobile equipment, traffic control)
    - Excavation and trenching (soil classification, shoring, cave-ins)
    - Confined spaces (permits, atmospheric testing, rescue)
    - Cranes and hoisting (lift planning, rigging, signals)
    - Health hazards (asbestos, silica, lead, noise, vibration)
    - Heat/cold stress and MSDs
    - Hot work, fire prevention, demolition
    - PPE requirements
    - Housekeeping and emergency response
    - OHSA legal duties
    """

    def __init__(self):
        self.name = "general_construction_safety"
        self.category = "general"
        self.rag_engine = RAGEngine()
        self.kb_manager = KnowledgeBaseManager()

    def can_handle(self, question: str) -> float:
        """
        Determine if this skill can handle the question.
        Returns confidence score 0.0 to 1.0
        """
        keywords = [
            # Struck-by
            'struck', 'hit by', 'mobile equipment', 'vehicle', 'traffic', 'backing',
            'crane', 'load', 'falling object',
            # Excavation
            'trench', 'trenching', 'excavation', 'excavating', 'cave-in', 'shoring',
            'soil', 'digging',
            # Confined spaces
            'confined space', 'entry permit', 'atmospheric', 'oxygen', 'gas',
            # Cranes/hoisting
            'crane', 'hoist', 'rigging', 'lift', 'lifting', 'sling', 'signal',
            # Health hazards
            'asbestos', 'silica', 'lead', 'noise', 'dust', 'exposure', 'respiratory',
            'vibration', 'chemical', 'whmis',
            # Heat/cold/MSD
            'heat stress', 'cold stress', 'msd', 'musculoskeletal', 'ergonomic',
            'lifting', 'strain',
            # Fire/demolition
            'fire', 'welding', 'hot work', 'demolition', 'extinguisher',
            # PPE/General
            'ppe', 'hard hat', 'safety glasses', 'gloves', 'respirator',
            'housekeeping', 'emergency', 'first aid', 'incident',
            # Legal
            'ohsa', 'regulation', 'duty', 'employer', 'supervisor', 'worker'
        ]

        question_lower = question.lower()
        matches = sum(1 for kw in keywords if kw in question_lower)

        # Calculate confidence score
        confidence = min(matches / 3.0, 1.0)
        return confidence

    def handle_question(self, question: str) -> str:
        """
        Handle a general construction safety question using RAG.
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

        # Determine subcategory for tailored response
        subcategory = self._identify_subcategory(question.lower())

        # Generate response
        response = f"""**{subcategory} - Construction Safety**

Based on Ontario construction safety regulations:

{context}

**Important Reminders:**
- Follow O. Reg 213/91 requirements
- Conduct hazard assessments before work
- Ensure workers are trained and competent
- Use appropriate PPE and controls
- Report all incidents immediately

For specific situations, consult with a competent person or safety professional.
"""
        return response

    def _identify_subcategory(self, question_lower: str) -> str:
        """Identify the specific subcategory of safety concern."""
        if any(kw in question_lower for kw in ['struck', 'vehicle', 'equipment', 'traffic']):
            return "Struck-By Hazards"
        elif any(kw in question_lower for kw in ['trench', 'excavation', 'cave-in', 'shoring']):
            return "Excavation and Trenching Safety"
        elif any(kw in question_lower for kw in ['confined space', 'permit', 'atmospheric']):
            return "Confined Space Entry"
        elif any(kw in question_lower for kw in ['crane', 'hoist', 'rigging', 'lift']):
            return "Cranes and Hoisting Safety"
        elif any(kw in question_lower for kw in ['asbestos', 'silica', 'lead', 'dust', 'noise']):
            return "Health Hazard Exposure"
        elif any(kw in question_lower for kw in ['heat', 'cold', 'msd', 'ergonomic']):
            return "Heat/Cold Stress and Ergonomics"
        elif any(kw in question_lower for kw in ['fire', 'welding', 'hot work', 'demolition']):
            return "Fire Prevention and Hot Work"
        elif any(kw in question_lower for kw in ['ppe', 'hard hat', 'respirator']):
            return "Personal Protective Equipment"
        else:
            return "General Construction Safety"

    def _fallback_response(self, question: str) -> str:
        """Fallback when no knowledge base results found."""
        return """**General Construction Safety**

Key construction safety principles under O. Reg 213/91:

- Conduct hazard assessments before starting work
- Ensure all workers are trained and competent
- Use engineering controls before PPE
- Maintain good housekeeping practices
- Follow manufacturer instructions for equipment
- Report all hazards and incidents immediately

For specific safety requirements, please provide more details or consult O. Reg 213/91.
"""
