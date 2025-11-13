"""Test script to compare Custom RAG vs Claude Skills modes."""

import os
from dotenv import load_dotenv
from orchestrator import CorporateSafetyAgent
from orchestrator.claude_skills_provider import ClaudeSkillsProvider

# Load environment variables
load_dotenv()

# Test questions covering different hazard types
test_questions = [
    "What safety equipment is needed for working at heights?",
    "What is lockout/tagout and when should it be used?",
    "How can I prevent being hit by falling objects?",
]


def test_mode(mode_name: str, agent, questions: list):
    """Test a mode with sample questions."""
    print(f"\n{'='*70}")
    print(f"{mode_name}")
    print(f"{'='*70}\n")

    for i, question in enumerate(questions, 1):
        print(f"\n{i}. Question: {question}")
        print("-" * 70)

        try:
            result = agent.ask(question)

            print(f"Mode: {result.get('mode', 'unknown')}")
            print(f"Skill: {result['skill']}")
            print(f"Routed to: {result['routed_to']}")
            print(f"\nAnswer:\n{result['answer'][:300]}...")
            print(f"\nSources: {', '.join(result['sources'][:3])}")

        except Exception as e:
            print(f"❌ Error: {str(e)}")

        print()


def main():
    """Main test function."""
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY not found in environment variables")
        return

    print("🛡️  Corporate Safety Agent - Mode Comparison Test")
    print("Testing Custom RAG vs Claude Skills modes\n")

    # Test Custom RAG mode
    try:
        print("Initializing Custom RAG mode...")
        custom_agent = CorporateSafetyAgent(
            api_key=api_key,
            model="claude-3-haiku-20240307",  # Use Haiku for speed
            provider="anthropic"
        )
        test_mode("🏗️  CUSTOM RAG MODE", custom_agent, test_questions)
    except Exception as e:
        print(f"❌ Failed to initialize Custom RAG: {str(e)}")

    # Test Claude Skills mode
    try:
        print("\nInitializing Claude Skills mode...")
        claude_skills = ClaudeSkillsProvider(api_key=api_key)
        test_mode("🔬 CLAUDE SKILLS MODE", claude_skills, test_questions)
    except Exception as e:
        print(f"❌ Failed to initialize Claude Skills: {str(e)}")

    print(f"\n{'='*70}")
    print("✅ Test complete!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
