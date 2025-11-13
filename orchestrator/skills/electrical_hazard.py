"""Electrical Hazard Detection and Prevention Skill."""

import sys
import os
from typing import Dict, Any, List
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

# Add parent directory to path for knowledge_base import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from knowledge_base import load_knowledge_base


class ElectricalHazardSkill:
    """Skill for handling electrical hazard queries."""

    def __init__(self, llm: ChatAnthropic):
        """Initialize the electrical hazard skill.

        Args:
            llm: ChatAnthropic instance for generating responses
        """
        self.llm = llm
        self.name = "Electrical Hazard"
        self.description = "Handles questions about electrical safety, lockout/tagout, power lines, arc flash, and electrical equipment"

        # Load knowledge base from centralized knowledge_base folder
        full_kb = load_knowledge_base("electrical")

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
            keywords = ["electric", "electrical", "shock", "power", "voltage", "wire",
                       "loto", "lockout", "tagout", "arc", "flash", "ground", "gfci",
                       "circuit", "energize", "de-energize"]

            for keyword in keywords:
                if keyword in query_lower:
                    if keyword in content_lower:
                        score += 2
                    if keyword in title_lower:
                        score += 3

            # Boost score for exact phrase matches
            if any(word in content_lower for word in query_lower.split()):
                score += 1

            scored_docs.append((score, doc))

        # Sort by score and return top_k
        scored_docs.sort(reverse=True, key=lambda x: x[0])

        # Calculate confidence based on top score
        max_score = scored_docs[0][0] if scored_docs else 0
        confidence = min(max_score / 10.0, 1.0)  # Normalize to 0-1

        relevant_docs = [doc for score, doc in scored_docs[:top_k] if score > 0]
        if not relevant_docs:
            relevant_docs = self.documents[:top_k]
            confidence = 0.1  # Low confidence for fallback

        return relevant_docs, confidence

    async def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process an electrical hazard query.

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
        if confidence < 0.15:  # Lowered threshold
            google_query = urllib.parse.quote(f"OSHA {query}")
            google_link = f"https://www.google.com/search?q={google_query}"

            return {
                "answer": f"I don't have enough information in my knowledge base to answer this question confidently.\n\nFor more information, try searching:\n{google_link}",
                "skill": self.name,
                "sources": ["External Search Required"],
                "category": "electrical_hazard",
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
            ("system", """You are a corporate safety expert specializing in electrical hazards and safety.
Your role is to provide accurate, practical safety advice based on OSHA standards and NFPA 70E guidelines.

Use the following knowledge base to answer questions:

{context}

CRITICAL CONSTRAINTS:
- Keep response under 1500 characters (SMS-ready)
- Be clear, direct, and concise
- Use bullet points for readability
- Only answer based on the knowledge base provided
- If the knowledge base doesn't cover the question, say "I don't have specific information on this"
- Reference specific regulations when applicable (OSHA 1910.333, NFPA 70E)
- Emphasize lockout/tagout and de-energization
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
            "category": "electrical_hazard",
            "confidence": confidence
        }
