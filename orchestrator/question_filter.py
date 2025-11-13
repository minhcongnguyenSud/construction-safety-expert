"""Question filter to ensure only safety-related queries are processed."""

from langchain_core.prompts import ChatPromptTemplate


class SafetyQuestionFilter:
    """Filter to validate if questions are safety-related."""

    def __init__(self, llm):
        """Initialize the question filter.

        Args:
            llm: LLM instance for question analysis
        """
        self.llm = llm

    def is_safety_related(self, question: str) -> tuple[bool, str]:
        """Check if a question is related to workplace safety.

        Args:
            question: User's question

        Returns:
            Tuple of (is_safety_related: bool, category: str)
            category is one of: 'safety', 'hr', 'general', 'personal'
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a workplace safety expert. Analyze the following question and determine if it's related to workplace safety.

**Safety topics include (answer "safety" for these):**
- Fall hazards, working at heights, ladders, scaffolding
- Fall injuries, emergency response, first aid for falls
- Electrical safety, lockout/tagout, power lines, electrical injuries
- Struck-by hazards, vehicles, falling objects, crush injuries, head injuries
- Personal protective equipment (PPE)
- OSHA regulations and standards
- Workplace hazard identification
- Safety procedures and protocols
- Emergency response and injury management
- Safety training and certifications
- Risk assessment
- Accident prevention
- Injury response and first aid
- Equipment safety
- Excavation, trenching, confined spaces
- Workplace security, suspicious persons, unauthorized access
- Workplace violence, threats, aggressive behavior
- Emergency contacts and first aid procedures
- Site entry procedures and safety orientation
- Any question about "what should I do" related to workplace hazards

**IMPORTANT**: If someone mentions falling, being struck, electrical shock, or any workplace injury/hazard,
it's a SAFETY question even if phrased personally (e.g., "I fell", "what should I do").

**Non-safety topics (answer with appropriate category):**
- "hr" - HR policies (vacation, sick leave, benefits, compensation, hiring)
- "general" - General company information, operations not related to safety
- "personal" - Personal relationships, career advice unrelated to safety

**Instructions:**
Analyze the question and respond with ONLY ONE WORD:
- "safety" - if it's about workplace safety, hazards, injuries, or emergency response
- "hr" - if it's about HR, benefits, or employment policies
- "general" - if it's general workplace questions
- "personal" - if it's personal advice unrelated to safety

**Question:** {question}"""),
            ("human", "Is this a workplace safety question? Answer with one word only: safety, hr, general, or personal")
        ])

        try:
            chain = prompt | self.llm
            response = chain.invoke({"question": question})

            category = response.content.strip().lower()

            # Validate response
            valid_categories = ['safety', 'hr', 'general', 'personal']
            if category not in valid_categories:
                # Default to safety if unclear
                category = 'safety'

            is_safety = (category == 'safety')
            return is_safety, category

        except Exception as e:
            print(f"⚠️ Question filter error: {e}, allowing question")
            # Default to allowing the question if error
            return True, 'safety'

    def get_redirect_message(self, category: str) -> str:
        """Get appropriate redirect message for non-safety questions.

        Args:
            category: Question category (hr, general, personal)

        Returns:
            Redirect message
        """
        messages = {
            'hr': """I'm a workplace safety assistant and can only answer questions about workplace safety hazards, OSHA regulations, and safety procedures.

For questions about HR policies, benefits, compensation, or employment matters, please contact:
- Your HR department
- Your direct supervisor
- Your company's employee handbook

Is there a workplace safety question I can help you with?""",
            'general': """I'm a workplace safety assistant focused specifically on safety hazards and OSHA compliance.

For general workplace questions unrelated to safety, please contact:
- Your supervisor or manager
- Your HR department
- The appropriate department for your question

Do you have a workplace safety question I can assist with?""",
            'personal': """I'm a workplace safety assistant and can only help with workplace safety questions.

For personal matters or non-work-related questions, please consult:
- Your supervisor for work-related guidance
- Your HR department for employee support resources
- Appropriate professional services for personal advice

Is there a workplace safety topic I can help you with?"""
        }

        return messages.get(category, messages['general'])
