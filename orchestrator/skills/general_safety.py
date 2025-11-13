"""General Safety Skill for topics not covered by specific hazard skills."""

import sys
import os
from typing import Dict, Any, List
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

# Add parent directory to path for knowledge_base import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from knowledge_base import load_knowledge_base


class GeneralSafetySkill:
    """Skill for handling general workplace safety queries."""

    def __init__(self, llm: ChatAnthropic):
        """Initialize the general safety skill.

        Args:
            llm: ChatAnthropic instance for generating responses
        """
        self.llm = llm
        self.name = "General Safety"
        self.description = "Handles general workplace safety questions including PPE, fire safety, hazard communication, ergonomics, and other safety topics"

        # Load knowledge base from centralized knowledge_base folder
        full_kb = load_knowledge_base("general")

        # Convert knowledge base to documents
        self.documents = [
            Document(
                page_content=item["content"],
                metadata={"title": item["title"], "category": item["category"]}
            )
            for item in full_kb
        ]

    def _retrieve_relevant_docs(self, query: str, top_k: int = 3) -> tuple[List[Document], float]:
        """Simple keyword-based retrieval of relevant documents.

        Args:
            query: User query
            top_k: Number of documents to retrieve

        Returns:
            Tuple of (List of relevant documents, confidence score)
        """
        query_lower = query.lower()

        # Score documents based on keyword matching
        scored_docs = []
        for doc in self.documents:
            score = 0
            content_lower = doc.page_content.lower()
            title_lower = doc.metadata["title"].lower()

            # Check for relevant keywords - EXPANDED LIST
            keywords = [
                # PPE and Equipment
                "ppe", "safety", "equipment", "protection", "protective", "gear",
                "hard hat", "helmet", "glasses", "goggles", "gloves", "boots",
                "respirator", "mask", "vest", "harness",

                # General Safety
                "hazard", "dangerous", "risk", "unsafe", "warning", "caution",
                "safety", "safe", "secure", "emergency", "urgent",

                # Injuries and First Aid
                "injury", "injured", "hurt", "wound", "wounded", "bleeding", "blood",
                "cut", "laceration", "burn", "burned", "bruise", "sprain", "fracture",
                "broken", "pain", "ache", "sick", "ill", "medical", "doctor", "hospital",
                "first aid", "treatment", "care", "bandage", "splint",

                # Emergency Response
                "emergency", "accident", "incident", "crash", "collision", "help",
                "ambulance", "911", "call", "report", "evacuate", "evacuation",

                # Site and Entry
                "site", "enter", "entry", "arrive", "new", "first day", "orientation",
                "induction", "training", "safety briefing", "sign in",

                # Environmental Hazards
                "fire", "smoke", "flame", "burning", "chemical", "smell", "odor",
                "gas", "fumes", "vapor", "toxic", "poison", "spill", "leak",
                "suspicious", "unknown", "strange", "unusual",

                # Physical Hazards
                "fall", "trip", "slip", "stumble", "height", "edge", "hole", "opening",
                "electric", "shock", "power", "wire", "cable", "exposed",
                "struck", "hit", "crush", "caught", "pinch", "trap",

                # Specific Topics
                "ergonomic", "lifting", "manual handling", "repetitive", "strain",
                "confined space", "permit", "entry", "enclosed",
                "heat", "hot", "cold", "freeze", "temperature", "weather",
                "violence", "assault", "threat", "aggression",
                "respiratory", "breathing", "air", "oxygen", "ventilation",
                "machine", "equipment", "tool", "guard", "shield",
                "ladder", "scaffold", "platform", "roof"
            ]

            # Score based on keyword matches
            for keyword in keywords:
                if keyword in query_lower:
                    if keyword in content_lower:
                        score += 2
                    if keyword in title_lower:
                        score += 4  # Increased from 3

            # Boost score for query word matches in content
            query_words = [w for w in query_lower.split() if len(w) > 3]  # Skip short words
            for word in query_words:
                if word in content_lower:
                    score += 1
                if word in title_lower:
                    score += 2

            scored_docs.append((score, doc))

        # Sort by score and return top_k
        scored_docs.sort(reverse=True, key=lambda x: x[0])

        # Calculate confidence based on top score - MORE GENEROUS
        max_score = scored_docs[0][0] if scored_docs else 0
        confidence = min(max_score / 6.0, 1.0)  # Changed from 10.0 to 6.0 for higher confidence

        relevant_docs = [doc for score, doc in scored_docs[:top_k] if score > 0]
        if not relevant_docs:
            relevant_docs = self.documents[:top_k]
            confidence = 0.2  # Increased from 0.1 to give fallback docs a chance

        return relevant_docs, confidence

    async def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a general safety query.

        Args:
            query: User question
            context: Additional context

        Returns:
            Dictionary with answer and metadata
        """
        import urllib.parse

        # Retrieve relevant documents with confidence score
        relevant_docs, confidence = self._retrieve_relevant_docs(query, top_k=5)  # Increased from 3 to 5

        # If confidence is too low, return Google search link - LOWERED THRESHOLD
        if confidence < 0.15:  # Changed from 0.3 to 0.15
            google_query = urllib.parse.quote(f"OSHA {query}")
            google_link = f"https://www.google.com/search?q={google_query}"

            return {
                "answer": f"I don't have enough information in my knowledge base to answer this question confidently.\n\nFor more information, try searching:\n{google_link}",
                "skill": self.name,
                "sources": ["External Search Required"],
                "category": "general_safety",
                "confidence": confidence,
                "google_link": google_link
            }

        # Build context from documents
        doc_context = "\n\n".join([
            f"**{doc.metadata['title']}**\n{doc.page_content}"
            for doc in relevant_docs
        ])

        # Create prompt with SMS constraints
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a corporate safety expert specializing in general workplace safety.
Your role is to provide accurate, practical safety advice based on OSHA standards and best practices.

Use the following knowledge base to answer questions:

{context}

CRITICAL CONSTRAINTS:
- Keep response under 1500 characters (SMS-ready)
- Be clear, direct, and concise
- Use bullet points for readability
- Only answer based on the knowledge base provided
- If the knowledge base doesn't cover the question, say "I don't have specific information on this"
- Reference specific regulations when applicable
- Prioritize worker safety"""),
            ("human", "{query}")
        ])

        # Generate response
        chain = prompt | self.llm
        response = await chain.ainvoke({
            "context": doc_context,
            "query": query
        })

        answer = response.content

        # Enforce 1500 character limit
        if len(answer) > 1500:
            answer = answer[:1497] + "..."

        return {
            "answer": answer,
            "skill": self.name,
            "sources": [doc.metadata["title"] for doc in relevant_docs],
            "category": "general_safety",
            "confidence": confidence
        }
