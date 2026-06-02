import os
import sys
from typing import Optional

from dotenv import load_dotenv

from src.core.gemini_provider import GeminiProvider
from src.core.openai_provider import OpenAIProvider
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


def build_provider(provider_name: Optional[str] = None) -> LLMProvider:
    """
    Create an LLM provider from .env settings.

    Supported providers:
        - openai
        - google
        - local
    """
    load_dotenv()

    provider = (provider_name or os.getenv("DEFAULT_PROVIDER", "openai")).lower()
    default_model = os.getenv("DEFAULT_MODEL")

    if provider == "openai":
        return OpenAIProvider(
            model_name=default_model or "gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    if provider == "google":
        return GeminiProvider(
            model_name=default_model or "gemini-1.5-flash",
            api_key=os.getenv("GEMINI_API_KEY"),
        )

    if provider == "local":
        from src.core.local_provider import LocalProvider

        return LocalProvider(
            model_path=os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf"),
        )

    raise ValueError(f"Unsupported provider: {provider}")


class SimpleChatbot:
    """
    Baseline chatbot for Phase 2.

    This class intentionally does not use tools. It sends the user's question
    directly to the LLM and returns the model's answer.
    """

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def answer(self, user_input: str) -> str:
        system_prompt = (
            "You are a helpful assistant. Answer the user directly. "
            "Do not call tools. If you are unsure, explain your assumption."
        )

        logger.log_event(
            "CHATBOT_START",
            {"input": user_input, "model": self.llm.model_name},
        )
        result = self.llm.generate(user_input, system_prompt=system_prompt)

        tracker.track_request(
            provider=result.get("provider", "unknown"),
            model=self.llm.model_name,
            usage=result.get("usage", {}),
            latency_ms=result.get("latency_ms", 0),
        )

        content = result.get("content", "").strip()
        logger.log_event(
            "CHATBOT_END",
            {"output": content, "latency_ms": result.get("latency_ms", 0)},
        )
        return content


def main() -> None:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        question = input("User: ").strip()

    chatbot = SimpleChatbot(build_provider())
    print(chatbot.answer(question))


if __name__ == "__main__":
    main()
