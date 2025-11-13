"""Main application for the Corporate Safety Agent."""

import os
import sys
from typing import Optional
from dotenv import load_dotenv

from .graph import SafetyAgentGraph
from .llm_provider import ProviderType, get_provider_info


class CorporateSafetyAgent:
    """Corporate Safety Agent powered by RAG and multiple AI providers."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        provider: ProviderType = "anthropic"
    ):
        """Initialize the Corporate Safety Agent.

        Args:
            api_key: API key for the provider (defaults to env var)
            model: Model name (provider-specific, optional)
            provider: AI provider ("anthropic" or "openai")
        """
        # Load environment variables
        load_dotenv()

        # Get provider info
        provider_info = get_provider_info(provider)
        env_var = provider_info.get("env_var", "API_KEY")

        # Get API key
        self.api_key = api_key or os.getenv(env_var)
        if not self.api_key:
            raise ValueError(
                f"{provider_info['name']} API key is required. "
                f"Set {env_var} environment variable or pass api_key parameter."
            )

        # Initialize the graph
        self.provider = provider
        self.model = model
        self.graph = SafetyAgentGraph(
            api_key=self.api_key,
            model=model,
            provider=provider
        )

        print(f"🛡️  Corporate Safety Agent initialized")
        print(f"   Provider: {provider_info.get('icon', '🤖')} {provider_info.get('name', provider)}")
        print(f"   Model: {model or 'default'}")
        print(f"   Skills: Fall Hazards, Electrical Hazards, Struck-By Hazards\n")

    def ask(self, question: str) -> dict:
        """Ask the safety agent a question.

        Args:
            question: User's safety question

        Returns:
            Dictionary containing answer and metadata
        """
        if not question or not question.strip():
            return {
                "query": question,
                "answer": "Please provide a question.",
                "skill": "None",
                "sources": [],
                "routed_to": "none"
            }

        # Process the query
        result = self.graph.process_query_sync(question)
        return result

    def interactive_mode(self):
        """Run the agent in interactive mode."""
        print("=" * 70)
        print("🛡️  CORPORATE SAFETY AGENT - Interactive Mode")
        print("=" * 70)
        print("\nAsk me about workplace safety!")
        print("Topics: Fall hazards, Electrical safety, Struck-by hazards")
        print("\nCommands:")
        print("  - Type your question and press Enter")
        print("  - Type 'quit' or 'exit' to end the session")
        print("  - Type 'help' for example questions\n")
        print("=" * 70 + "\n")

        while True:
            try:
                # Get user input
                question = input("You: ").strip()

                # Check for exit commands
                if question.lower() in ["quit", "exit", "q"]:
                    print("\n👋 Thank you for using Corporate Safety Agent. Stay safe!\n")
                    break

                # Check for help command
                if question.lower() == "help":
                    self._show_examples()
                    continue

                # Skip empty questions
                if not question:
                    continue

                # Process the question
                print("\n🤔 Processing...\n")
                result = self.ask(question)

                # Display the result
                self._display_result(result)

            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Stay safe!\n")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")

    def _display_result(self, result: dict):
        """Display the result in a formatted way.

        Args:
            result: Query result dictionary
        """
        print(f"🤖 {result['skill']}:")
        print("-" * 70)
        print(result['answer'])
        print("-" * 70)

        if result.get('sources'):
            print(f"\n📚 Sources: {', '.join(result['sources'])}")

        print(f"🎯 Routed to: {result['routed_to']}")
        print()

    def _show_examples(self):
        """Show example questions."""
        print("\n" + "=" * 70)
        print("📋 EXAMPLE QUESTIONS")
        print("=" * 70)
        print("\n🪜 Fall Hazards:")
        print("  - What safety equipment is needed for working at heights?")
        print("  - How do I properly set up a ladder?")
        print("  - What are the requirements for scaffolding?")
        print("\n⚡ Electrical Hazards:")
        print("  - What is lockout/tagout and when should it be used?")
        print("  - How far should I stay from power lines?")
        print("  - What PPE is required for electrical work?")
        print("\n🚧 Struck-By Hazards:")
        print("  - How can I prevent being hit by falling objects?")
        print("  - What safety measures are needed around forklifts?")
        print("  - How should materials be stacked safely?")
        print("\n" + "=" * 70 + "\n")


def main():
    """Main entry point for the application."""
    # Check for command line arguments
    if len(sys.argv) > 1:
        # Single question mode
        question = " ".join(sys.argv[1:])

        try:
            agent = CorporateSafetyAgent()
            result = agent.ask(question)

            print(f"\n🤖 {result['skill']}:\n")
            print(result['answer'])

            if result.get('sources'):
                print(f"\n📚 Sources: {', '.join(result['sources'])}")

            print()

        except ValueError as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

    else:
        # Interactive mode
        try:
            agent = CorporateSafetyAgent()
            agent.interactive_mode()
        except ValueError as e:
            print(f"❌ Error: {e}")
            print("\nPlease set your ANTHROPIC_API_KEY environment variable:")
            print("  export ANTHROPIC_API_KEY='your-api-key-here'")
            sys.exit(1)


if __name__ == "__main__":
    main()
