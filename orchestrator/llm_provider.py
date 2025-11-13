"""LLM Provider abstraction for supporting multiple AI providers."""

from typing import Optional, Literal
from langchain_anthropic import ChatAnthropic


ProviderType = Literal["anthropic", "openai"]


def get_llm(
    provider: ProviderType = "anthropic",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0
):
    """Get LLM instance based on provider.

    Args:
        provider: AI provider ("anthropic" or "openai")
        model: Model name (provider-specific)
        api_key: API key for the provider
        temperature: Temperature for generation (0-1)

    Returns:
        LangChain LLM instance

    Raises:
        ValueError: If provider is not supported or API key is missing
    """
    if provider == "anthropic":
        if not api_key:
            raise ValueError("Anthropic API key is required")

        # Default to Claude 3 Haiku if no model specified (fastest, cheapest)
        if not model:
            model = "claude-3-haiku-20240307"

        return ChatAnthropic(
            api_key=api_key,
            model=model,
            temperature=temperature
        )

    elif provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError(
                "OpenAI support requires langchain-openai. "
                "Install it with: pip install langchain-openai"
            )

        if not api_key:
            raise ValueError("OpenAI API key is required")

        # Default to GPT-4o-mini if no model specified (cheapest)
        if not model:
            model = "gpt-4o-mini"

        return ChatOpenAI(
            api_key=api_key,
            model=model,
            temperature=temperature
        )

    else:
        raise ValueError(f"Unsupported provider: {provider}. Choose 'anthropic' or 'openai'")


def get_available_models(provider: ProviderType) -> list[str]:
    """Get list of available models for a provider.

    Args:
        provider: AI provider

    Returns:
        List of model names
    """
    if provider == "anthropic":
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]
    elif provider == "openai":
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo"
        ]
    else:
        return []


def get_provider_info(provider: ProviderType) -> dict:
    """Get information about a provider.

    Args:
        provider: AI provider

    Returns:
        Dictionary with provider information
    """
    providers = {
        "anthropic": {
            "name": "Anthropic Claude",
            "description": "Advanced AI assistant with strong reasoning capabilities",
            "models": get_available_models("anthropic"),
            "env_var": "ANTHROPIC_API_KEY",
            "icon": "🤖"
        },
        "openai": {
            "name": "OpenAI GPT",
            "description": "Powerful language models from OpenAI",
            "models": get_available_models("openai"),
            "env_var": "OPENAI_API_KEY",
            "icon": "🔮"
        }
    }

    return providers.get(provider, {})
