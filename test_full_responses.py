"""Test full end-to-end responses for previously failing questions."""

import asyncio
import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

# Load environment variables
load_dotenv()

# Import orchestrator components
from orchestrator.graph import SafetyAgentGraph
from orchestrator.router import SafetyRouter
from orchestrator.question_filter import SafetyQuestionFilter
from orchestrator.skills.general_safety import GeneralSafetySkill
from orchestrator.skills.fall_hazard import FallHazardSkill
from orchestrator.skills.electrical_hazard import ElectricalHazardSkill
from orchestrator.skills.struckby_hazard import StruckByHazardSkill

async def test_full_system():
    """Test complete system with previously failing questions."""

    # Initialize LLM
    llm = ChatAnthropic(
        model="claude-3-5-haiku-20241022",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        temperature=0
    )

    # Initialize orchestrator
    filter = SafetyQuestionFilter(llm)
    router = SafetyRouter(llm)

    # Initialize skills
    skills = {
        "general": GeneralSafetySkill(llm),
        "fall": FallHazardSkill(llm),
        "electrical": ElectricalHazardSkill(llm),
        "struckby": StruckByHazardSkill(llm)
    }

    # Test cases from user's failing questions
    test_questions = [
        "a brick drop on my head, i feel dizzy",
        "i saw a group of suspicious men inside the construction site",
        "What is the primary hazard associated with working in trenches and excavations?",
        "what is the emergency contact",
    ]

    print("=" * 100)
    print("FULL SYSTEM END-TO-END TESTS")
    print("=" * 100)

    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*100}")
        print(f"TEST {i}/4: {question}")
        print(f"{'='*100}")

        # Step 1: Question filter
        is_safety, category = filter.is_safety_related(question)
        print(f"\n1️⃣ Question Filter: {category} (is_safety: {is_safety})")

        if not is_safety:
            print("❌ FAILED: Question was filtered out as non-safety")
            continue

        # Step 2: Routing
        skill_id = await router.route(question)
        print(f"2️⃣ Router: Routed to '{skill_id}' skill")

        # Step 3: Skill processing
        skill = skills.get(skill_id)
        if not skill:
            print(f"❌ FAILED: Skill '{skill_id}' not found")
            continue

        result = await skill.process(question)

        # Step 4: Results
        print(f"3️⃣ Confidence: {result.get('confidence', 0):.2f}")
        print(f"4️⃣ Sources: {', '.join(result.get('sources', []))}")

        answer = result.get('answer', '')
        if 'I don\'t have enough information' in answer:
            print(f"\n❌ FAILED: No answer provided (low confidence)")
        else:
            print(f"\n✅ SUCCESS: Answer provided")

        print(f"\n📝 Answer Preview:")
        print(f"{answer[:300]}..." if len(answer) > 300 else answer)

if __name__ == "__main__":
    print("\n🔧 Testing Full System with Previously Failing Questions\n")
    asyncio.run(test_full_system())
    print("\n" + "=" * 100)
    print("✅ All tests completed!")
    print("=" * 100)
