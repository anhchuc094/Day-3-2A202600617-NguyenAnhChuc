# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn Anh Chức
- **Student ID**: 2A202600617
- **Date**: 2026-06-01

---

## I. Technical Contribution

My main responsibility was implementing the ReAct Agent logic and improving it from v1 to v2.

Although the team divided responsibilities by primary role, all members still participated in all three major parts of the project: tool design, agent implementation, and evaluation/reporting. This helped the group review each other's work and understand the full system end to end.

- **Modules Implemented / Updated**:
  - `src/agent/agent.py`
  - `src/agent/agent_v2.py`
  - `agent_demo.py`
  - `agent_demo_v2.py`

### Agent v1

`src/agent/agent.py` implements the core ReAct loop:

```text
Question -> Thought -> Action -> Observation -> Final Answer
```

The main logic includes:

- generating model output with `llm.generate`
- parsing `Final Answer`
- parsing `Action: tool_name(arguments)`
- executing Python tools dynamically
- appending `Observation` back into the prompt
- logging each step for trace analysis

### Agent v2

`src/agent/agent_v2.py` keeps the same execution logic but improves the system prompt. The v2 prompt adds stricter rules for:

- failed observations with `"ok": false`
- ambiguous user input
- avoiding invented prices, products, coupon codes, or destinations
- showing available options when tools return them

---

## II. Debugging Case Study

### Problem Description

The main risk in v1 was that the model might receive a failed observation but still continue answering as if the tool succeeded.

Example input:

```text
I want to buy 1 iphone with coupon SAIROI and ship to hanoi. What is the total?
```

Expected trace:

```text
Action: calculate_order_total('iphone', 1, 'SAIROI', 'hanoi')
Observation: {"ok": false, "coupon_code": "SAIROI", "discount_percent": 0, "error": "Invalid coupon code."}
```

### Diagnosis

The tool correctly detected the invalid coupon. The remaining risk was in the LLM reasoning layer: the v1 prompt did not explicitly say what to do when `ok` is false.

### Solution

In v2, I added prompt rules:

```text
If an Observation contains "ok": false, do not ignore it or invent missing data.
Explain the problem to the user, or ask for the missing/correct information.
```

This makes the model more likely to stop and report the real tool error instead of generating a hallucinated total.

---

## III. Personal Insights: Chatbot vs ReAct

The ReAct loop makes the model less like a pure text generator and more like a controller. The model decides which action to take, but Python tools provide the actual facts.

The `Thought` part helps the model plan the next step. The `Action` part connects the model to tools. The `Observation` part grounds the next decision in real output.

The agent is stronger than the chatbot for multi-step tasks, but it depends heavily on prompt format. If the model does not follow `Action:` or `Final Answer:`, the parser can fail. This is why structured prompting and logging are essential.

---

## IV. Future Improvements

- Support JSON-only tool calls to reduce parsing errors.
- Add retry logic when the model output does not contain a valid action.
- Add conversation memory for multi-turn chat.
- Add stricter validation for tool names and argument schemas.
- Move toward a graph-based agent framework for complex workflows.
