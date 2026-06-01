# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Trần Văn Quang
- **Student ID**: 2A202600798
- **Date**: 2026-06-01

---

## I. Technical Contribution

My main responsibility was designing and implementing the e-commerce tool layer used by the ReAct Agent.

Although the team divided responsibilities by primary role, all members still participated in all three major parts of the project: tool design, agent implementation, and evaluation/reporting. This ensured that every member understood the full ReAct workflow instead of only knowing one isolated module.

- **Modules Implemented**:
  - `src/tools/ecommerce_tools.py`
  - `src/tools/__init__.py`

- **Main Contributions**:
  - Created a deterministic product catalog with `iphone`, `laptop`, and `headphone`.
  - Implemented coupon data for `WINNER`, `STUDENT`, and `FREESHIP`.
  - Implemented supported shipping destinations: `hanoi`, `ho chi minh`, and `danang`.
  - Built five tools:
    - `get_product_info`
    - `check_stock`
    - `get_discount`
    - `calculate_shipping`
    - `calculate_order_total`

These tools return structured dictionaries with an `ok` field. This makes the agent easier to debug because each tool result clearly states whether the operation succeeded or failed.

Example:

```python
calculate_order_total("iphone", 2, "WINNER", "hanoi")
```

Expected result:

```json
{
  "ok": true,
  "subtotal_vnd": 40000000,
  "discount_percent": 10,
  "discount_amount_vnd": 4000000,
  "shipping_fee_vnd": 30000,
  "final_total_vnd": 36030000
}
```

---

## II. Debugging Case Study

### Problem Description

One important failure case was when the user asked for a product that does not exist:

```text
I want to buy 1 ipad with coupon WINNER and ship to hanoi. What is the total?
```

### Log Source

Expected trace:

```text
Action: get_product_info('ipad')
Observation: {"ok": false, "error": "Product 'ipad' was not found.", "available_products": ["iphone", "laptop", "headphone"]}
```

### Diagnosis

The tool layer correctly rejected the unknown product. This is important because a normal chatbot may hallucinate an iPad price, while the agent should be grounded in the product catalog.

### Solution

The tool returns:

- `ok: false`
- a clear error message
- a list of available products

This gives the agent enough information to tell the user that `ipad` is unavailable and suggest valid products.

---

## III. Personal Insights: Chatbot vs ReAct

The biggest difference I observed is that a chatbot answers from language knowledge, while a ReAct Agent can verify facts through tools. For e-commerce tasks, this matters because product price, stock, coupon validity, and shipping fee must come from system data, not from model guesses.

The `Observation` step is the most important part of the loop. Once the tool returns structured data, the model can produce an answer based on actual state. This makes the answer more reliable than a direct chatbot response.

However, the agent can perform worse than a chatbot on simple open-ended questions because the ReAct format adds extra steps and latency.

---

## IV. Future Improvements

- Move product data from hard-coded dictionaries to a database.
- Add product search for partial names such as `phone` or `earphones`.
- Add inventory reservation to prevent selling unavailable stock.
- Add richer shipping rules by city, distance, and delivery provider.
- Add unit tests for each tool and edge case.