import ast
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker

class ReActAgent:
    """
    A ReAct-style Agent that follows the Thought-Action-Observation loop.

    The LLM decides what to do next, the agent executes real Python tools, and
    the tool result is fed back as an Observation for the next reasoning step.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        """
        Build the instruction prompt that teaches the LLM how to behave.

        Important idea:
        - The LLM only knows tools through their text descriptions.
        - Strong formatting rules make parsing easier and reduce agent failures.
        """
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        return f"""
You are a careful ReAct agent. You can answer by reasoning step by step and by
calling tools when you need reliable information or calculation.

Available tools:
{tool_descriptions}

Rules:
1. Use exactly one Action per step when you need a tool.
2. Do not invent tool names. Only use the tools listed above.
3. Do not write Observation yourself. The program will add it after executing the tool.
4. When you have enough information, stop using tools and write Final Answer.
5. Keep arguments simple: strings in quotes, numbers without quotes.

Use this format:
Thought: explain what you need to do next.
Action: tool_name("string argument", 123)

After the program gives you an Observation, continue:
Thought: use the observation to decide the next step.
Action: another_tool("argument")

When done:
Final Answer: clear answer for the user.
""".strip()

    def run(self, user_input: str) -> str:
        """
        Run the ReAct loop.

        1. Generate Thought + Action.
        2. Parse Action and execute Tool.
        3. Append Observation to prompt and repeat until Final Answer.
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        self.history = []

        scratchpad = f"Question: {user_input}"

        for step in range(1, self.max_steps + 1):
            result = self.llm.generate(scratchpad, system_prompt=self.get_system_prompt())
            content = result.get("content", "").strip()

            tracker.track_request(
                provider=result.get("provider", "unknown"),
                model=self.llm.model_name,
                usage=result.get("usage", {}),
                latency_ms=result.get("latency_ms", 0),
            )
            logger.log_event("AGENT_STEP", {"step": step, "llm_output": content})

            final_answer = self._parse_final_answer(content)
            if final_answer:
                logger.log_event("AGENT_END", {"steps": step, "status": "final_answer"})
                return final_answer

            action = self._parse_action(content)
            if action is None:
                logger.log_event(
                    "AGENT_PARSE_ERROR",
                    {"step": step, "reason": "No Final Answer or Action found", "output": content},
                )
                return (
                    "I could not find a valid Action or Final Answer in the model output. "
                    "Please check the agent logs for the failed trace."
                )

            tool_name, raw_args = action
            observation = self._execute_tool(tool_name, raw_args)

            self.history.append(
                {
                    "step": step,
                    "llm_output": content,
                    "tool_name": tool_name,
                    "tool_args": raw_args,
                    "observation": observation,
                }
            )
            logger.log_event(
                "TOOL_CALL",
                {
                    "step": step,
                    "tool_name": tool_name,
                    "tool_args": raw_args,
                    "observation": observation,
                },
            )

            scratchpad = f"{scratchpad}\n\n{content}\nObservation: {observation}"

        logger.log_event("AGENT_END", {"steps": self.max_steps, "status": "max_steps_exceeded"})
        return "I reached the maximum number of reasoning steps before producing a final answer."

    def _parse_final_answer(self, text: str) -> Optional[str]:
        """
        Extract the final answer from an LLM response.
        """
        match = re.search(r"Final Answer\s*:\s*(.+)", text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def _parse_action(self, text: str) -> Optional[Tuple[str, str]]:
        """
        Extract an action in the form:
            Action: tool_name("arg", 123)
        """
        match = re.search(
            r"Action\s*:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not match:
            return None

        tool_name = match.group(1).strip()
        raw_args = match.group(2).strip()
        return tool_name, raw_args

    def _execute_tool(self, tool_name: str, args: str) -> str:
        """
        Execute a registered Python tool and return a JSON observation string.

        Tool dictionaries are expected to look like:
            {
                "name": "check_stock",
                "description": "...",
                "function": check_stock
            }
        """
        for tool in self.tools:
            if tool["name"] == tool_name:
                tool_function = tool.get("function")
                if tool_function is None:
                    return self._format_observation(
                        {
                            "ok": False,
                            "error": f"Tool '{tool_name}' has no callable function.",
                        }
                    )

                try:
                    positional_args, keyword_args = self._parse_tool_arguments(args)
                    result = tool_function(*positional_args, **keyword_args)
                    return self._format_observation(result)
                except Exception as exc:
                    logger.log_event(
                        "TOOL_ERROR",
                        {"tool_name": tool_name, "args": args, "error": str(exc)},
                    )
                    return self._format_observation(
                        {
                            "ok": False,
                            "error": f"Tool '{tool_name}' failed: {exc}",
                        }
                    )

        return self._format_observation(
            {
                "ok": False,
                "error": f"Tool '{tool_name}' not found.",
                "available_tools": [tool["name"] for tool in self.tools],
            }
        )

    def _parse_tool_arguments(self, args: str) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Convert the raw text inside Action parentheses into Python arguments.

        Examples:
            '"iphone", 2' becomes positional args ["iphone", 2]
            'item_name="iphone", quantity=2' becomes keyword args
            '{"item_name": "iphone", "quantity": 2}' becomes keyword args
        """
        if not args:
            return [], {}

        stripped_args = args.strip()
        if stripped_args.startswith("{") and stripped_args.endswith("}"):
            parsed_json = json.loads(stripped_args)
            if not isinstance(parsed_json, dict):
                raise ValueError("JSON tool arguments must be an object.")
            return [], parsed_json

        parsed_call = ast.parse(f"tool({stripped_args})", mode="eval")
        if not isinstance(parsed_call.body, ast.Call):
            raise ValueError("Tool arguments must look like a function call.")

        positional_args = [ast.literal_eval(arg) for arg in parsed_call.body.args]
        keyword_args = {
            keyword.arg: ast.literal_eval(keyword.value)
            for keyword in parsed_call.body.keywords
            if keyword.arg is not None
        }
        return positional_args, keyword_args

    def _format_observation(self, value: Any) -> str:
        """
        Return observations as compact JSON so the LLM can read them consistently.
        """
        return json.dumps(value, ensure_ascii=False)
