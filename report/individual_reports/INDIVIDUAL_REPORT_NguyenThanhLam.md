# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyễn THành Lam
- **Student ID**: 2A202600625
- **Date**: 2026-06-01

---

## I. Technical Contribution

My main responsibility was building the evaluation workflow, comparing chatbot vs agent behavior, and preparing the report structure.

Although the team divided responsibilities by primary role, all members still participated in all three major parts of the project: tool design, agent implementation, and evaluation/reporting. The role split was used to clarify ownership, not to separate knowledge or contribution.

- **Modules / Files Involved**:
  - `chatbot.py`
  - `agent.py`
  - `src/telemetry/logger.py`
  - `report/group_report/GROUP_REPORT.md`

### Chatbot Baseline

I helped define `chatbot.py` as the Phase 2 baseline. This chatbot sends the user question directly to the LLM and does not use tools.

This is useful for comparison because it shows the limitation of direct LLM answering on tasks that require exact product data.

### Evaluation Workflow

The same test cases should be run on:

```bash
python chatbot.py "..."
python agent.py "..."
```

Then the results are compared using:

- final answer correctness
- tool calls
- observations
- latency
- token count
- error handling quality

---

## II. Debugging Case Study

### Problem Description

At first, structured JSON logs were printed directly to the terminal during chat mode. This made the demo hard to read because user-facing answers were mixed with telemetry lines.

### Log Source

Example noisy events:

```text
AGENT_START
LLM_METRIC
AGENT_STEP
TOOL_CALL
AGENT_END
```

### Diagnosis

The logger wrote to both file and console by default. For debugging this is useful, but for an interactive demo it makes the interface confusing.

### Solution

The logger was updated so JSON telemetry is written to files in `logs/` by default. Console logging can still be enabled with:

```env
LOG_TO_CONSOLE=true
```

This keeps the user-facing chat clean while preserving full observability for analysis.

---

## III. Personal Insights: Chatbot vs ReAct

The chatbot baseline is easier to run and usually faster because it only makes one LLM call. However, it cannot verify whether a product exists, whether a coupon is valid, or whether the shop has enough stock.

The ReAct Agent is better for operational tasks because it shows its reasoning path through logs:

```text
AGENT_STEP -> TOOL_CALL -> Observation -> AGENT_STEP -> Final Answer
```

This trace makes debugging much clearer. Instead of only seeing a wrong final answer, we can identify whether the failure came from the prompt, the parser, the tool, or the model's reasoning.

---

## IV. Future Improvements

- Add a script to automatically run the full test suite and produce a comparison table.
- Parse `logs/*.log` into a CSV metrics dashboard.
- Add pass/fail labels for each test case.
- Track v1 vs v2 success rate automatically.
- Add screenshots or saved terminal outputs for final submission evidence.
