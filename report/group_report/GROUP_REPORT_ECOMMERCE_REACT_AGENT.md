# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: E-commerce ReAct Agent Team
- **Team Members**: Nguyễn Anh Chức, Trần Văn Quang, Nguyễn Thành Lam
- **Deployment Date**: 2026-06-01

---

## 1. Executive Summary

This project implements an e-commerce assistant to compare a direct chatbot baseline with a ReAct-style agent. The chatbot answers directly from the LLM, while the agent can call tools to verify product data, stock, discount codes, shipping fees, and final order totals.

- **Agent Goal**: Answer shopping questions with grounded tool data instead of guessing.
- **Key Outcome**: The ReAct Agent is expected to outperform the chatbot on multi-step tasks because it can use structured observations from real Python tools.
- **Evaluation Method**: Run the same test cases on `chatbot.py`, `agent_demo.py` for v1, and `agent_demo_v2.py` for v2, then compare final answers and JSON traces in `logs/`.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation

The agent follows this loop:

```text
User Question
  -> LLM Thought
  -> LLM Action: tool_name(arguments)
  -> Python tool execution
  -> Observation JSON
  -> LLM continues reasoning
  -> Final Answer
```

Implementation locations:

| File | Purpose |
| :--- | :--- |
| `src/agent/agent.py` | Agent v1: ReAct loop, parser, tool execution, final answer detection. |
| `src/agent/agent_v2.py` | Agent v2: improved prompt rules for failed observations and ambiguous requests. |
| `src/tools/ecommerce_tools.py` | Product catalog, coupon, shipping, and total calculation tools. |
| `chatbot.py` | Baseline chatbot without tools. |
| `agent_demo.py` | Runner for agent v1. |
| `agent_demo_v2.py` | Runner for agent v2. |

### 2.2 Tool Definitions

| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `get_product_info` | `item_name: str` | Get product price, stock, and weight. |
| `check_stock` | `item_name: str, quantity: int` | Check whether requested quantity is available. |
| `get_discount` | `coupon_code: str` | Validate coupon and return discount percentage. |
| `calculate_shipping` | `item_name: str, quantity: int, destination: str` | Calculate shipping fee based on product weight and city. |
| `calculate_order_total` | `item_name: str, quantity: int, coupon_code: str, destination: str` | Calculate final total after stock, coupon, and shipping validation. |

### 2.3 LLM Providers Used

- **Primary**: Gemini or OpenAI through `.env`.
- **Supported Providers**: `openai`, `google`, `local`.
- **Provider Switching**: Controlled by `DEFAULT_PROVIDER` and `DEFAULT_MODEL`.

Example:

```env
DEFAULT_PROVIDER=google
DEFAULT_MODEL=gemini-2.5-flash
```

---

## 3. Telemetry & Performance Dashboard

Telemetry is written as JSON events in the `logs/` directory.

| Event | Meaning |
| :--- | :--- |
| `AGENT_START` | New user request received by the agent. |
| `AGENT_STEP` | LLM produced a Thought/Action or Final Answer. |
| `TOOL_CALL` | Agent executed a Python tool and captured its Observation. |
| `LLM_METRIC` | Token, latency, and estimated cost metadata. |
| `AGENT_END` | Agent finished with final answer or max-step status. |
| `AGENT_PARSE_ERROR` | Model output did not contain a valid Action or Final Answer. |
| `AGENT_RUNTIME_ERROR` | Runner caught an unexpected error without exposing traceback to the user. |

Sample live trace from v1:

```text
Input: "toi muon mua iphone shop ban con bao nhieu cai"
Model: gemini-2.5-flash
Step 1 Action: get_product_info('iphone')
Observation: {"ok": true, "item_name": "iphone", "stock": 5, ...}
Step 2 Final Answer: Shop con 5 cai iphone.
```

After running the final test suite, fill this table with values from `LLM_METRIC`:

| Metric | v1 | v2 |
| :--- | :--- | :--- |
| Average Latency | TBD from logs | TBD from logs |
| Max Latency | TBD from logs | TBD from logs |
| Average Tokens per Task | TBD from logs | TBD from logs |
| Total Estimated Cost | TBD from logs | TBD from logs |

---

## 4. Root Cause Analysis - Failure Traces

### Case Study: Invalid Coupon Handling

- **Input**: `I want to buy 1 iphone with coupon SAIROI and ship to hanoi. What is the total?`
- **Expected**: The agent should not calculate a final price because coupon `SAIROI` does not exist.
- **Important Trace Lines**:

```text
Action: calculate_order_total('iphone', 1, 'SAIROI', 'hanoi')
Observation: {"ok": false, "coupon_code": "SAIROI", "discount_percent": 0, "error": "Invalid coupon code."}
```

- **Root Cause Risk in v1**: The v1 prompt does not explicitly instruct the LLM what to do when a tool returns `"ok": false`. Depending on the model response, it may ignore the failed observation or invent a fallback answer.
- **Fix in v2**: `src/agent/agent_v2.py` adds explicit rules requiring the model to respect failed observations and avoid inventing missing data.

### Case Study: Unknown Product

- **Input**: `I want to buy 1 ipad with coupon WINNER and ship to hanoi. What is the total?`
- **Expected Observation**:

```json
{"ok": false, "error": "Product 'ipad' was not found.", "available_products": ["iphone", "laptop", "headphone"]}
```

- **Correct Behavior**: The agent should tell the user that `ipad` is unavailable and mention available products.
- **v2 Improvement**: Rule 8 asks the model to include available options when the tool returns them.

### Case Study: Not Enough Stock

- **Input**: `I want to buy 10 iphone with coupon WINNER and ship to hanoi. What is the total?`
- **Expected Observation**:

```json
{"ok": false, "item_name": "iphone", "requested_quantity": 10, "available_stock": 5, "message": "Not enough stock."}
```

- **Correct Behavior**: The agent should not calculate a total for unavailable stock.
- **v2 Improvement**: The model is instructed to stop and explain the failed observation.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Prompt v1 vs Prompt v2

Agent v1 is kept in:

```text
src/agent/agent.py
```

Agent v2 is implemented separately in:

```text
src/agent/agent_v2.py
```

The v2 prompt adds these rules:

```text
If an Observation contains "ok": false, do not ignore it or invent missing data.
Explain the problem to the user, or ask for the missing/correct information.

If the user's request is ambiguous, ask a clarifying question instead of guessing
product names, coupon codes, destinations, prices, or stock quantities.

If a tool returns available options, include those options in the final answer
when they help the user correct the request.
```

Expected impact:

| Test Case | v1 Risk | v2 Expected Behavior |
| :--- | :--- | :--- |
| Invalid coupon | May still calculate with guessed discount | Stop and report invalid coupon |
| Unknown product | May invent product price | Report product not found and show available products |
| Unsupported destination | May invent shipping fee | Report unsupported destination |
| Ambiguous product | May assume product name | Ask a clarifying question |

### Experiment 2: Test Suite

Run each test case on chatbot, v1, and v2:

```bash
python chatbot.py "I want to buy 2 iphone with coupon WINNER and ship to hanoi. What is the total?"
python agent_demo.py "I want to buy 2 iphone with coupon WINNER and ship to hanoi. What is the total?"
python agent_demo_v2.py "I want to buy 2 iphone with coupon WINNER and ship to hanoi. What is the total?"
```

Recommended cases:

| Case | Input Summary | Expected Agent Behavior |
| :--- | :--- | :--- |
| Success order | 2 iPhone, WINNER, Hanoi | Return `36,030,000 VND`. |
| Unknown product | 1 iPad, WINNER, Hanoi | Report product not found. |
| Invalid coupon | 1 iPhone, SAIROI, Hanoi | Report invalid coupon. |
| Not enough stock | 10 iPhone, WINNER, Hanoi | Report insufficient stock. |
| Unsupported destination | 1 Laptop, STUDENT, Hue | Report unsupported destination. |
| Ambiguous product | "I want to buy a phone" | Ask which product the user means. |
| Direct stock query | "How many headphones are available?" | Call `get_product_info` and report stock = 10. |
| Valid zero-discount coupon | 1 Headphone, FREESHIP, Ho Chi Minh | Return total using 0% discount and shipping fee. |
| Case-insensitive coupon | 1 Laptop, student, Danang | Treat `student` as `STUDENT` and apply 15% discount. |
| Missing coupon | 1 iPhone shipped to Hanoi, no coupon provided | Ask for coupon code or continue only if user confirms no coupon. |

### Experiment 3: Chatbot vs Agent

| Case | Chatbot Result | Agent Result | Winner |
| :--- | :--- | :--- | :--- |
| Ask stock of iPhone | May answer from general knowledge or guess | Calls `get_product_info` and returns stock = 5 | Agent |
| Multi-step order total | May guess price, coupon, or shipping | Calls tool and returns exact total | Agent |
| Unknown product | May invent iPad details | Reports product not found | Agent |
| General explanation question | Can answer directly | Agent may be slower due to ReAct format | Chatbot |

---

## 6. Production Readiness Review

- **Observability**: Structured JSON logs allow tracing each LLM step, tool call, observation, metric, and runtime error.
- **Guardrails**: `max_steps` prevents infinite loops. The runner hides Python tracebacks from end users and logs detailed errors for debugging.
- **Reliability**: Tools return structured `ok: true/false` observations, which makes failure handling explicit.
- **Security**: Tool arguments are parsed with `ast.literal_eval` or JSON parsing instead of raw `eval`.
- **Scalability**: Future versions could replace the simple loop with LangGraph, add async tool calls, persist conversations, and add a retrieval layer for larger product catalogs.

---

## 7. Conclusion

The completed system demonstrates the core difference between a chatbot and an agent. The chatbot is simple and useful for direct answers, but it cannot verify operational facts. The ReAct Agent is more reliable for multi-step shopping tasks because it calls tools, reads observations, handles failures, and produces answers grounded in deterministic system data.
