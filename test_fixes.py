"""Test script to verify routing and question filtering fixes."""

import asyncio
import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

# Load environment variables
load_dotenv()

# Import the modules
from orchestrator.router import SafetyRouter
from orchestrator.question_filter import SafetyQuestionFilter

async def test_routing():
    """Test that questions route to correct skills."""
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        temperature=0
    )

    router = SafetyRouter(llm)

    test_cases = [
        ("a brick drop on my head, i feel dizzy", "struckby"),
        ("i saw a group of suspicious men inside the construction site", "general"),
        ("What is the primary hazard associated with working in trenches and excavations?", "general"),
    ]

    print("=" * 80)
    print("ROUTING TESTS")
    print("=" * 80)

    for query, expected_skill in test_cases:
        result = await router.route(query)
        status = "✅ PASS" if result == expected_skill else "❌ FAIL"
        print(f"\n{status}")
        print(f"Query: {query}")
        print(f"Expected: {expected_skill}")
        print(f"Got: {result}")

def test_question_filter():
    """Test that questions are correctly classified as safety-related."""
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        temperature=0
    )

    filter = SafetyQuestionFilter(llm)

    test_cases = [
        ("what is the emergency contact", True),
        ("i saw a group of suspicious men inside the construction site", True),
        ("a brick drop on my head", True),
        ("What is the primary hazard associated with working in trenches?", True),
    ]

    print("\n" + "=" * 80)
    print("QUESTION FILTER TESTS")
    print("=" * 80)

    for query, expected_is_safety in test_cases:
        is_safety, category = filter.is_safety_related(query)
        status = "✅ PASS" if is_safety == expected_is_safety else "❌ FAIL"
        print(f"\n{status}")
        print(f"Query: {query}")
        print(f"Expected safety: {expected_is_safety}")
        print(f"Got safety: {is_safety}, category: {category}")

if __name__ == "__main__":
    print("\n🔧 Testing Routing and Question Filter Fixes\n")

    # Test routing
    asyncio.run(test_routing())

    # Test question filter
    test_question_filter()

    print("\n" + "=" * 80)
    print("✅ Tests completed!")
    print("=" * 80)
