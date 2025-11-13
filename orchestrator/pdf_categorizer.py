"""PDF content categorizer using LLM analysis."""

from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate


class PDFCategorizer:
    """Categorize PDF content into safety skill categories using LLM."""

    CATEGORIES = {
        "fall": "Fall hazards, working at heights, ladders, scaffolding, fall protection",
        "electrical": "Electrical safety, lockout/tagout, power lines, arc flash, wiring",
        "struckby": "Struck-by hazards, vehicles, falling objects, flying debris, rigging",
        "general": "General workplace safety, multiple hazards, or other safety topics"
    }

    def __init__(self, llm):
        """Initialize the PDF categorizer.

        Args:
            llm: LLM instance for categorization
        """
        self.llm = llm

    def categorize_content(self, content: str) -> str:
        """Analyze PDF content and determine the best category.

        Args:
            content: Extracted and cleaned text from PDF

        Returns:
            Category name (fall, electrical, struckby, or general)
        """
        # Take a sample of the content (first 2000 chars for analysis)
        sample = content[:2000]

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a workplace safety expert. Analyze the following safety document content
and determine which category it belongs to:

**Categories:**
- **fall**: Fall hazards, working at heights, ladders, scaffolding, fall protection, elevated work
- **electrical**: Electrical safety, lockout/tagout, power lines, arc flash, wiring, electrical equipment
- **struckby**: Struck-by hazards, vehicles, mobile equipment, falling objects, flying debris, rigging, load handling
- **general**: General workplace safety, multiple hazards, or other safety topics

**Instructions:**
- Analyze the main topic and keywords in the document
- Choose the MOST SPECIFIC category that best fits the content
- If the document covers multiple hazard types equally, choose "general"
- If the primary focus is on one specific hazard type, choose that category
- Respond with ONLY the category name: fall, electrical, struckby, or general

**Document Content:**
{content}"""),
            ("human", "Based on this content, which category does this document belong to? Respond with only the category name.")
        ])

        try:
            chain = prompt | self.llm
            response = chain.invoke({"content": sample})

            # Extract category from response
            category = response.content.strip().lower()

            # Validate category
            if category in self.CATEGORIES:
                print(f"✅ Categorized as: {category}")
                return category
            else:
                print(f"⚠️ Unknown category '{category}', defaulting to 'general'")
                return "general"

        except Exception as e:
            print(f"⚠️ Categorization error: {e}, defaulting to 'general'")
            return "general"

    def categorize_chunks(self, chunks: List[Dict[str, Any]], llm) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze chunks individually and group by category.

        Args:
            chunks: List of document chunks from PDF processor
            llm: LLM instance for categorization

        Returns:
            Dictionary mapping categories to lists of chunks
            Format: {"fall": [...], "electrical": [...], "struckby": [...], "general": [...]}
        """
        if not chunks:
            return {"fall": [], "electrical": [], "struckby": [], "general": []}

        categorized = {"fall": [], "electrical": [], "struckby": [], "general": []}

        print(f"\n🔍 Analyzing {len(chunks)} chunks individually...")

        for i, chunk in enumerate(chunks, 1):
            # Categorize each chunk based on its content
            content = chunk["content"]
            category = self.categorize_content(content)

            # Update chunk category
            chunk["category"] = category

            # Add to appropriate category list
            categorized[category].append(chunk)

            print(f"   Chunk {i}/{len(chunks)}: {category}")

        # Summary
        print(f"\n📊 Categorization summary:")
        for cat, items in categorized.items():
            if items:
                print(f"   {cat}: {len(items)} chunks")

        return categorized
