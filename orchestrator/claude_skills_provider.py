"""Claude Skills Provider - Integration with Claude Code managed skills."""

import os
from typing import Dict, Optional
from anthropic import Anthropic


class ClaudeSkillsProvider:
    """
    Provider for Claude Code managed skills.

    Uses the same knowledge base as custom RAG but with Claude Code's
    prompt-based skill system for comparison.
    """

    # Map question types to Claude Code skills
    SKILL_MAPPING = {
        'falls': 'falls-safety',
        'electrical': 'electrical-safety',
        'struck-by': 'struck-by-hazards',
        'workplace': 'workplace-safety',
        'confined': 'confined-spaces',
        'cranes': 'cranes-hoisting',
        'excavation': 'excavation-safety',
        'health': 'health-hazards'
    }

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Claude Skills Provider.

        Args:
            api_key: Anthropic API key (uses env var if not provided)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for Claude Skills mode")

        self.client = Anthropic(api_key=self.api_key)
        self.skill_prompts = self._load_skill_prompts()

    def _load_skill_prompts(self) -> Dict[str, str]:
        """Load skill prompts from .claude/skills directory."""
        prompts = {}
        skills_dir = ".claude/skills"

        for skill_name in self.SKILL_MAPPING.values():
            skill_file = os.path.join(skills_dir, skill_name, "SKILL.md")
            if os.path.exists(skill_file):
                with open(skill_file, 'r') as f:
                    prompts[skill_name] = f.read()

        return prompts

    def _classify_question(self, question: str) -> str:
        """Classify question to determine which skill to use.

        Args:
            question: User's safety question

        Returns:
            Skill name (e.g., 'falls-safety', 'electrical-safety')
        """
        question_lower = question.lower()

        # Falls keywords
        falls_keywords = [
            'fall', 'height', 'ladder', 'scaffold', 'roof', 'edge',
            'guardrail', 'harness', 'wah', 'elevated', 'mewp', 'lift'
        ]

        # Electrical keywords
        electrical_keywords = [
            'electric', 'shock', 'power', 'voltage', 'loto', 'lockout',
            'energized', 'wire', 'cable', 'overhead line', 'arc flash', 'gfci'
        ]

        # Struck-by keywords
        struckby_keywords = [
            'struck', 'hit', 'vehicle', 'truck', 'forklift', 'crane',
            'falling object', 'dropped', 'rigging', 'traffic', 'backing'
        ]

        # Calculate scores
        falls_score = sum(1 for kw in falls_keywords if kw in question_lower)
        electrical_score = sum(1 for kw in electrical_keywords if kw in question_lower)
        struckby_score = sum(1 for kw in struckby_keywords if kw in question_lower)

        # Select highest scoring skill
        if falls_score >= electrical_score and falls_score >= struckby_score and falls_score > 0:
            return 'falls-safety'
        elif electrical_score >= struckby_score and electrical_score > 0:
            return 'electrical-safety'
        elif struckby_score > 0:
            return 'struck-by-hazards'
        else:
            return 'workplace-safety'  # Default to general workplace safety

    def ask(self, question: str) -> Dict:
        """Ask a question using Claude Skills.

        Args:
            question: User's safety question

        Returns:
            Dictionary with answer, skill used, and metadata
        """
        # Classify the question
        skill_name = self._classify_question(question)

        # Get the skill prompt
        skill_prompt = self.skill_prompts.get(skill_name)
        if not skill_prompt:
            return {
                "query": question,
                "answer": f"Skill '{skill_name}' not found.",
                "skill": skill_name,
                "mode": "claude-skills",
                "sources": [],
                "routed_to": skill_name
            }

        # Replace $ARGUMENTS with the actual question
        full_prompt = skill_prompt.replace("$ARGUMENTS", question)

        # Call Claude API with the skill prompt
        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Use Haiku for low-latency/cost
                max_tokens=2000,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": full_prompt
                }]
            )

            answer = response.content[0].text

            return {
                "query": question,
                "answer": answer,
                "skill": skill_name.replace('-', ' ').title(),
                "mode": "claude-skills",
                "sources": [f"Claude Code Skill: {skill_name}"],
                "routed_to": skill_name
            }

        except Exception as e:
            return {
                "query": question,
                "answer": f"Error calling Claude API: {str(e)}",
                "skill": skill_name,
                "mode": "claude-skills",
                "sources": [],
                "routed_to": skill_name
            }

    def get_available_skills(self) -> Dict[str, str]:
        """Get list of available Claude Code skills.

        Returns:
            Dictionary mapping skill names to descriptions
        """
        descriptions = {
            'falls-safety': 'Expert in falls from heights, scaffolds, ladders, MEWPs, guardrails, and fall protection systems',
            'electrical-safety': 'Expert in electrical hazards, LOTO procedures, overhead lines, temporary power, GFCI, and arc flash protection',
            'struck-by-hazards': 'Expert in struck-by hazards including mobile equipment, traffic control, crane loads, falling objects, and backing vehicles',
            'workplace-safety': 'Expert in general workplace safety including PPE, fire safety, hot work, demolition, housekeeping, and emergency response',
            'confined-spaces': 'Expert in confined space entry requirements including atmospheric testing, entry permits, and rescue planning',
            'cranes-hoisting': 'Expert in crane operations, hoisting safety, rigging, lift planning, and regulation updates',
            'excavation-safety': 'Expert in excavation and trenching safety including soil classification, shoring, and cave-in prevention',
            'health-hazards': 'Expert in construction health hazards including asbestos, silica, lead, noise, vibration, chemicals, and heat/cold stress'
        }

        return {k: v for k, v in descriptions.items() if k in self.skill_prompts}
