from agent_demo import build_provider, safe_agent_run
from src.agent.agent_v2 import ReActAgentV2
from src.tools import ECOMMERCE_TOOLS


def main() -> None:
    import sys

    question = " ".join(sys.argv[1:]).strip()
    agent = ReActAgentV2(
        llm=build_provider(),
        tools=ECOMMERCE_TOOLS,
        max_steps=5,
    )

    if question:
        print(safe_agent_run(agent, question))
        return

    print("Agent v2 chat started. Type 'exit' or 'quit' to stop.")
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

        print(f"Agent v2: {safe_agent_run(agent, question)}")


if __name__ == "__main__":
    main()
