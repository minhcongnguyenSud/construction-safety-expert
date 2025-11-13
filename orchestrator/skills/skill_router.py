"""
Skill Router - Semantic Analysis and Classification

This module analyzes safety questions using semantic analysis and routes them
to the appropriate specialized skill for handling.

Simple Workflow:
1. User asks a safety question
2. Router analyzes question semantics (keywords, context)
3. Router calculates confidence score for each skill
4. Router selects the best skill (highest confidence)
5. Selected skill handles the question using its expertise
"""

from typing import Dict, List, Tuple

# Import skills - handle both package and direct imports
try:
    from .falls_skill import FallsSkill
    from .electrical_skill import ElectricalSkill
    from .general_safety_skill import GeneralSafetySkill
except ImportError:
    from falls_skill import FallsSkill
    from electrical_skill import ElectricalSkill
    from general_safety_skill import GeneralSafetySkill


class SkillRouter:
    """
    Intelligent router that classifies safety questions and dispatches to
    the appropriate specialized skill using semantic analysis.

    Classification Method:
    - Keyword matching with domain-specific terms
    - Confidence scoring (0.0 to 1.0)
    - Highest confidence wins
    - Falls back to general skill if unclear
    """

    def __init__(self):
        """Initialize all available skills."""
        self.skills = {
            'falls': FallsSkill(),
            'electrical': ElectricalSkill(),
            'general': GeneralSafetySkill()
        }

    def classify_question(self, question: str) -> Tuple[str, float, object]:
        """
        Classify the question and select the best skill to handle it.

        Args:
            question: The safety question to classify

        Returns:
            Tuple of (skill_name, confidence_score, skill_object)

        Example:
            >>> router = SkillRouter()
            >>> skill_name, confidence, skill = router.classify_question(
            ...     "Worker fell from scaffold"
            ... )
            >>> print(skill_name)  # "falls"
            >>> print(confidence)  # 0.8
        """
        # Calculate confidence for each skill
        scores = {}
        for name, skill in self.skills.items():
            scores[name] = skill.can_handle(question)

        # Select skill with highest confidence
        best_skill_name = max(scores, key=scores.get)
        best_confidence = scores[best_skill_name]
        best_skill = self.skills[best_skill_name]

        # Log classification decision
        print(f"\n📊 Question Classification:")
        print(f"   Question: {question[:60]}...")
        print(f"   Confidence Scores:")
        for name, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            indicator = "✅" if name == best_skill_name else "  "
            print(f"      {indicator} {name}: {score:.2%}")
        print(f"   Selected: {best_skill_name} ({best_confidence:.2%} confidence)\n")

        return best_skill_name, best_confidence, best_skill

    def route_question(self, question: str) -> str:
        """
        Route a question to the appropriate skill and get the answer.

        This is the main method to use:
        1. Classifies the question
        2. Routes to the best skill
        3. Returns the expert answer

        Args:
            question: Safety question from user

        Returns:
            Expert answer from the selected skill

        Example:
            >>> router = SkillRouter()
            >>> answer = router.route_question("How do I set up a scaffold safely?")
            >>> print(answer)
            # Returns falls skill's expert answer about scaffolding
        """
        # Classify and select skill
        skill_name, confidence, skill = self.classify_question(question)

        # Get answer from selected skill
        answer = skill.handle_question(question)

        return answer

    def get_skill_info(self) -> Dict[str, Dict]:
        """
        Get information about all available skills.

        Returns:
            Dictionary with skill names and their capabilities
        """
        info = {}
        for name, skill in self.skills.items():
            info[name] = {
                'name': skill.name,
                'category': skill.category,
                'description': skill.__doc__.strip().split('\n')[0] if skill.__doc__ else "No description"
            }
        return info

    def explain_classification(self, question: str) -> Dict:
        """
        Explain how the question would be classified (for debugging/testing).

        Args:
            question: Question to analyze

        Returns:
            Dictionary with classification details
        """
        skill_name, confidence, skill = self.classify_question(question)

        # Get all scores
        all_scores = {}
        for name, s in self.skills.items():
            all_scores[name] = s.can_handle(question)

        return {
            'question': question,
            'selected_skill': skill_name,
            'confidence': confidence,
            'all_scores': all_scores,
            'explanation': f"Selected {skill_name} with {confidence:.1%} confidence"
        }


def test_router():
    """Test the router with sample questions."""
    router = SkillRouter()

    test_questions = [
        "Worker fell from scaffold while installing drywall",
        "Employee received electric shock from power cord",
        "Trench collapsed and buried worker",
        "Crane operator lost control of suspended load",
        "How do I properly set up a ladder?",
        "What are the LOTO procedures?",
        "Need information about silica dust exposure",
        "Confined space entry requirements"
    ]

    print("=" * 70)
    print("SKILL ROUTER TEST")
    print("=" * 70)

    for i, question in enumerate(test_questions, 1):
        print(f"\n{i}. {question}")
        skill_name, confidence, skill = router.classify_question(question)
        print(f"   → Routed to: {skill.name}")

    print("\n" + "=" * 70)
    print("✅ Router test complete")
    print("=" * 70)


if __name__ == "__main__":
    test_router()
