"""Fall Hazard Detection and Prevention Skill."""

import sys
import os
from typing import Dict, Any, List
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

# Add parent directory to path for knowledge_base import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from knowledge_base import load_knowledge_base


class FallHazardSkill:
    """Skill for handling fall hazard queries."""

    def __init__(self, llm: ChatAnthropic):
        """Initialize the fall hazard skill.

        Args:
            llm: ChatAnthropic instance for generating responses
        """
        self.llm = llm
        self.name = "Fall Hazard"
        self.description = "Handles questions about fall hazards, working at heights, ladders, scaffolding, and fall protection"

        # Load knowledge base from centralized knowledge_base folder
        full_kb = load_knowledge_base("fall")

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

            # Check for relevant keywords
            keywords = ["fall", "fell", "fallen", "height", "ladder", "scaffold", "protection", "harness",
                       "guardrail", "edge", "roof", "elevated", "injury", "injur", "emergency",
                       "first aid", "response", "incident", "victim", "medical", "911", "call",
                       "help", "hospital", "immediate", "urgent"]

            for keyword in keywords:
                if keyword in query_lower:
                    if keyword in content_lower:
                        score += 2
                    if keyword in title_lower:
                        score += 3

            # Special boost for emergency/injury phrases
            emergency_phrases = ["what should i do", "what do i do", "fell from", "injured",
                               "emergency response", "first aid"]
            for phrase in emergency_phrases:
                if phrase in query_lower and phrase in content_lower:
                    score += 4

            # Boost score for word matches (individual words)
            query_words = [w for w in query_lower.split() if len(w) > 3]  # Skip short words
            for word in query_words:
                if word in content_lower:
                    score += 1

            scored_docs.append((score, doc))

        # Sort by score and return top_k
        scored_docs.sort(reverse=True, key=lambda x: x[0])

        # Calculate confidence based on top score
        max_score = scored_docs[0][0] if scored_docs else 0
        confidence = min(max_score / 8.0, 1.0)  # Normalize to 0-1 (more lenient: 2.4 = 0.3 threshold)

        relevant_docs = [doc for score, doc in scored_docs[:top_k] if score > 0]
        if not relevant_docs:
            relevant_docs = self.documents[:top_k]
            confidence = 0.15  # Low confidence for fallback

        return relevant_docs, confidence

    async def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a fall hazard query.

        Args:
            query: User question
            context: Additional context

        Returns:
            Dictionary with answer and metadata
        """
        import urllib.parse

        # Retrieve relevant documents with confidence score
        relevant_docs, confidence = self._retrieve_relevant_docs(query)

        # If confidence is too low, return Google search link
        if confidence < 0.15:  # Lower threshold for emergency questions
            google_query = urllib.parse.quote(f"OSHA {query}")
            google_link = f"https://www.google.com/search?q={google_query}"

            return {
                "answer": f"I don't have enough information in my knowledge base to answer this question confidently.\n\nFor more information, try searching:\n{google_link}",
                "skill": self.name,
                "sources": ["External Search Required"],
                "category": "fall_hazard",
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
            ("system", """You are a corporate safety expert specializing in fall hazards and prevention.
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
            "category": "fall_hazard",
            "confidence": confidence
        }
