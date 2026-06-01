import os
import sys
import traceback
from typing import Optional

from dotenv import load_dotenv

from src.agent.agent import ReActAgent
from src.core.gemini_provider import GeminiProvider
from src.core.llm_provider import LLMProvider
from src.core.openai_provider import OpenAIProvider
from src.telemetry.logger import logger
from src.tools import ECOMMERCE_TOOLS


def build_provider(provider_name: Optional[str] = None) -> LLMProvider:
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


def main() -> None:
    question = " ".join(sys.argv[1:]).strip()
    agent = ReActAgent(
        llm=build_provider(),
        tools=ECOMMERCE_TOOLS,
        max_steps=5,
    )

    if question:
        print(safe_agent_run(agent, question))
        return

    print("Agent chat started. Type 'exit' or 'quit' to stop.")
    while True:
        try:
            question = input("User: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return

        if question.lower() in {"exit", "quit"}:
            print("Goodbye.")
            return

        if not question:
            continue

        print(f"Agent: {safe_agent_run(agent, question)}")


def safe_agent_run(agent: ReActAgent, question: str) -> str:
    """
    Run the agent without exposing Python tracebacks to the user.

    Full exception details are still written to logs for debugging.
    """
    try:
        return agent.run(question)
    except Exception as exc:
        logger.log_event(
            "AGENT_RUNTIME_ERROR",
            {
                "input": question,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
        )
        return (
            "Xin lỗi, agent gặp lỗi khi xử lý câu hỏi này. "
            "Bạn hãy kiểm tra file logs để xem chi tiết kỹ thuật."
        )


if __name__ == "__main__":
    main()
