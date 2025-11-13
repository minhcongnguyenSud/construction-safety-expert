"""LangGraph orchestration for the corporate safety agent."""

from typing import TypedDict, Optional
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from .router import SafetyRouter
from .skills import FallHazardSkill, ElectricalHazardSkill, StruckByHazardSkill, GeneralSafetySkill
from .llm_provider import get_llm, ProviderType
from .question_filter import SafetyQuestionFilter


class AgentState(TypedDict):
    """State for the safety agent."""

    query: str
    """The user's query"""

    routed_skill: str
    """The skill that should handle the query"""

    answer: str
    """The generated answer"""

    sources: list[str]
    """Sources used to generate the answer"""

    skill_name: str
    """Name of the skill that handled the query"""

    error: str | None
    """Any error that occurred"""


class SafetyAgentGraph:
    """LangGraph-based orchestration for the corporate safety agent."""

    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,
        provider: ProviderType = "anthropic"
    ):
        """Initialize the safety agent graph.

        Args:
            api_key: API key for the provider
            model: Model name (provider-specific, optional)
            provider: AI provider ("anthropic" or "openai")
        """
        # Initialize LLM with provider
        self.provider = provider
        self.llm = get_llm(
            provider=provider,
            model=model,
            api_key=api_key,
            temperature=0
        )

        # Initialize components
        self.question_filter = SafetyQuestionFilter(self.llm)
        self.router = SafetyRouter(self.llm)
        self.fall_skill = FallHazardSkill(self.llm)
        self.electrical_skill = ElectricalHazardSkill(self.llm)
        self.struckby_skill = StruckByHazardSkill(self.llm)
        self.general_skill = GeneralSafetySkill(self.llm)

        # Build the graph
        self.graph = self._build_graph()

    def _route_query(self, state: AgentState) -> AgentState:
        """Route the query to the appropriate skill.

        Args:
            state: Current agent state

        Returns:
            Updated state with routed_skill
        """
        import asyncio

        query = state["query"]

        # First, filter the question to ensure it's safety-related
        is_safety, category = self.question_filter.is_safety_related(query)

        if not is_safety:
            # Non-safety question, mark for rejection
            return {
                **state,
                "routed_skill": f"rejected_{category}",
                "error": f"Non-safety question: {category}"
            }

        # Get routing decision for safety questions
        routed_skill = asyncio.run(self.router.route(query))

        return {
            **state,
            "routed_skill": routed_skill
        }

    def _process_with_skill(self, state: AgentState) -> AgentState:
        """Process the query with the appropriate skill.

        Args:
            state: Current agent state

        Returns:
            Updated state with answer and metadata
        """
        import asyncio

        query = state["query"]
        routed_skill = state["routed_skill"]

        # Check if question was rejected
        if routed_skill.startswith("rejected_"):
            category = routed_skill.replace("rejected_", "")
            redirect_message = self.question_filter.get_redirect_message(category)
            return {
                **state,
                "answer": redirect_message,
                "sources": [],
                "skill_name": "Question Filter",
                "error": None
            }

        try:
            # Select the appropriate skill
            if routed_skill == "fall":
                skill = self.fall_skill
            elif routed_skill == "electrical":
                skill = self.electrical_skill
            elif routed_skill == "struckby":
                skill = self.struckby_skill
            elif routed_skill == "general":
                skill = self.general_skill
            else:
                # Fallback to general skill for unrecognized routes
                skill = self.general_skill

            # Process with the skill
            result = asyncio.run(skill.process(query))

            return {
                **state,
                "answer": result["answer"],
                "sources": result["sources"],
                "skill_name": result["skill"],
                "error": None
            }

        except Exception as e:
            return {
                **state,
                "answer": f"I encountered an error processing your question: {str(e)}",
                "sources": [],
                "skill_name": "error",
                "error": str(e)
            }

    def _handle_general_query(self, state: AgentState) -> AgentState:
        """Handle general queries that don't fit a specific skill.

        Args:
            state: Current agent state

        Returns:
            Updated state with answer
        """
        import asyncio

        query = state["query"]

        # Create a general safety prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a corporate safety assistant. You help answer workplace safety questions.

If the question is about a specific hazard type (falls, electrical, struck-by), provide general guidance
and suggest the user ask more specific questions.

If the question is general or covers multiple hazard types, provide comprehensive safety advice.

Always prioritize worker safety and OSHA compliance in your responses."""),
            ("human", "{query}")
        ])

        chain = prompt | self.llm

        try:
            response = asyncio.run(chain.ainvoke({"query": query}))

            return {
                **state,
                "answer": response.content,
                "sources": ["General Safety Knowledge"],
                "skill_name": "General Safety",
                "error": None
            }
        except Exception as e:
            return {
                **state,
                "answer": f"I encountered an error: {str(e)}",
                "sources": [],
                "skill_name": "error",
                "error": str(e)
            }

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow.

        Returns:
            Compiled StateGraph
        """
        # Create the graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("route", self._route_query)
        workflow.add_node("process", self._process_with_skill)

        # Define the flow
        workflow.set_entry_point("route")
        workflow.add_edge("route", "process")
        workflow.add_edge("process", END)

        # Compile the graph
        return workflow.compile()

    async def process_query(self, query: str) -> dict:
        """Process a user query through the graph.

        Args:
            query: User question

        Returns:
            Dictionary with answer and metadata
        """
        # Initialize state
        initial_state: AgentState = {
            "query": query,
            "routed_skill": "",
            "answer": "",
            "sources": [],
            "skill_name": "",
            "error": None
        }

        # Run the graph
        result = await self.graph.ainvoke(initial_state)

        return {
            "query": result["query"],
            "answer": result["answer"],
            "skill": result["skill_name"],
            "sources": result["sources"],
            "routed_to": result["routed_skill"],
            "mode": "custom-rag"
        }

    def process_query_sync(self, query: str) -> dict:
        """Synchronous wrapper for process_query.

        Args:
            query: User question

        Returns:
            Dictionary with answer and metadata
        """
        import asyncio
        return asyncio.run(self.process_query(query))
