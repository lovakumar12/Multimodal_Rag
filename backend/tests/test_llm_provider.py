from unittest.mock import Mock, patch

from backend.app.core.config import settings
from backend.app.generation.llm_provider import (
    GroqLLMProvider,
    OpenAILLMProvider,
    get_llm_provider,
)


def test_groq_provider_uses_configured_model_and_compatible_endpoint():
    client = Mock()
    mock_choice = Mock()
    mock_choice.message.content = " answer "
    client.chat.completions.create.return_value.choices = [mock_choice]
    with (
        patch.object(settings, "LLM_PROVIDER", "groq"),
        patch.object(settings, "LLM_MODEL", "llama-test"),
        patch.object(settings, "GROQ_API_KEY", "test-groq-key"),
        patch("openai.OpenAI", return_value=client) as openai_client,
    ):
        provider = get_llm_provider()
        answer = provider.generate("question", "system rules")

    assert isinstance(provider, GroqLLMProvider)
    openai_client.assert_called_once_with(
        api_key="test-groq-key",
        base_url="https://api.groq.com/openai/v1",
    )
    client.chat.completions.create.assert_called_once_with(
        model="llama-test",
        messages=[
            {"role": "system", "content": "system rules"},
            {"role": "user", "content": "question"},
        ],
        temperature=0.2,
    )
    assert answer == "answer"


def test_openai_provider_uses_configured_gpt_model():
    client = Mock()
    with (
        patch.object(settings, "LLM_PROVIDER", "openai"),
        patch.object(settings, "LLM_MODEL", "gpt-test"),
        patch.object(settings, "OPENAI_API_KEY", "test-openai-key"),
        patch("openai.OpenAI", return_value=client) as openai_client,
    ):
        provider = get_llm_provider()

    assert isinstance(provider, OpenAILLMProvider)
    assert provider.model_name == "gpt-test"
    openai_client.assert_called_once_with(api_key="test-openai-key")
