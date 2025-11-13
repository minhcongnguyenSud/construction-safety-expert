"""Router for determining which safety skill should handle a query."""

from typing import List, Dict, Any
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


class RouteDecision(BaseModel):
    """Model for routing decision."""

    skill: str = Field(description="The skill that should handle this query: 'fall', 'electrical', 'struckby', or 'general'")
    confidence: float = Field(description="Confidence score between 0 and 1")
    reasoning: str = Field(description="Brief explanation of why this skill was chosen")


class SafetyRouter:
    """Routes queries to appropriate safety skills."""

    def __init__(self, llm: ChatAnthropic):
        """Initialize the router.

        Args:
            llm: ChatAnthropic instance for routing decisions
        """
        self.llm = llm

        # Define available skills
        self.skills = {
            "fall": {
                "name": "Fall Hazard Skill",
                "keywords": ["fall", "height", "ladder", "scaffold", "roof", "edge",
                           "protection", "harness", "guardrail", "elevated", "climbing"],
                "description": "Handles fall protection, working at heights, ladders, scaffolding"
            },
            "electrical": {
                "name": "Electrical Hazard Skill",
                "keywords": ["electric", "electrical", "shock", "power", "voltage", "wire",
                           "lockout", "tagout", "loto", "arc", "flash", "circuit", "energize"],
                "description": "Handles electrical safety, lockout/tagout, power lines, arc flash"
            },
            "struckby": {
                "name": "Struck-By Hazard Skill",
                "keywords": ["struck", "hit", "vehicle", "equipment", "falling object",
                           "flying", "crane", "forklift", "load", "lifting", "rigging",
                           "brick", "debris", "drop", "dropped", "head injury", "concussion"],
                "description": "Handles struck-by hazards, vehicles, falling/flying objects, rigging, head injuries from impacts"
            },
            "general": {
                "name": "General Safety Skill",
                "keywords": ["ppe", "safety", "equipment", "protection", "fire", "chemical",
                           "emergency", "hazard", "ergonomic", "confined space", "heat", "cold",
                           "violence", "respiratory", "machine", "guard", "slip", "trip",
                           "safety glasses", "hard hat", "gloves", "boots", "hearing protection",
                           "excavation", "trench", "dig", "cave", "soil", "security", "suspicious",
                           "intruder", "trespasser", "unauthorized", "emergency contact", "first aid"],
                "description": "Handles general workplace safety including PPE, fire safety, excavation, security, workplace violence, emergency procedures, and other safety topics"
            }
        }

    def _keyword_based_routing(self, query: str) -> Dict[str, float]:
        """Simple keyword-based routing as a fallback.

        Args:
            query: User query

        Returns:
            Dictionary mapping skill names to scores
        """
        query_lower = query.lower()
        scores = {}

        for skill_id, skill_info in self.skills.items():
            score = 0
            for keyword in skill_info["keywords"]:
                if keyword in query_lower:
                    score += 1
            scores[skill_id] = score

        return scores

    async def route(self, query: str) -> str:
        """Route a query to the appropriate skill.

        Args:
            query: User question

        Returns:
            Skill identifier ('fall', 'electrical', 'struckby', or 'general')
        """
        # First try keyword-based routing for quick decisions
        keyword_scores = self._keyword_based_routing(query)
        max_keyword_score = max(keyword_scores.values()) if keyword_scores else 0

        # If we have a clear keyword match, use it
        if max_keyword_score >= 2:
            return max(keyword_scores.items(), key=lambda x: x[1])[0]

        # Otherwise, use LLM for more nuanced routing
        try:
            # Build skill descriptions
            skill_descriptions = "\n".join([
                f"- **{skill_id}**: {info['description']}"
                for skill_id, info in self.skills.items()
            ])

            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a routing assistant for a corporate safety system.
Your job is to determine which safety skill should handle a user's question.

Available skills:
{skill_descriptions}

Analyze the user's question and determine which skill is most appropriate.
- Choose 'fall' for questions about fall protection, heights, ladders, scaffolding
- Choose 'electrical' for questions about electrical safety, power, lockout/tagout
- Choose 'struckby' for questions about struck-by hazards, vehicles, falling/flying objects
- Choose 'general' if the question doesn't fit any specific skill or covers multiple skills

Respond with just the skill name: fall, electrical, struckby, or general"""),
                ("human", "{query}")
            ])

            chain = prompt | self.llm
            response = await chain.ainvoke({
                "skill_descriptions": skill_descriptions,
                "query": query
            })

            # Extract skill from response
            skill = response.content.strip().lower()

            # Validate the response
            if skill in self.skills or skill == "general":
                return skill

            # If invalid, fall back to keyword routing
            if max_keyword_score > 0:
                return max(keyword_scores.items(), key=lambda x: x[1])[0]

            return "general"

        except Exception as e:
            print(f"Error in LLM routing: {e}")
            # Fall back to keyword routing
            if max_keyword_score > 0:
                return max(keyword_scores.items(), key=lambda x: x[1])[0]
            return "general"

    def get_skill_info(self, skill_id: str) -> Dict[str, Any]:
        """Get information about a skill.

        Args:
            skill_id: Skill identifier

        Returns:
            Skill information dictionary
        """
        return self.skills.get(skill_id, {})
