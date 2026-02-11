# Middleware in LangChain (Production‑Grade Guide)

This document explains **how to implement middleware concepts in LangChain**, mapping the generic *agent middleware lifecycle* to **LangChain primitives**.

Middleware here means:
> A reusable control layer around agents, LLM calls, and tools that adds **logging, safety, retries, guardrails, and observability** without changing business logic.

---

## 1. Mental Model: Middleware vs Agent in LangChain

### Plain Agent Flow (no middleware)

```
User Query
   ↓
Agent (LLM decides next step)
   ↓
Tool Call (optional)
   ↓
Observation
   ↓
Final Answer
```

### Agent with Middleware (LangChain style)

```
User Query
   ↓
[before_agent]        ← validation, rate‑limit, tracing
   ↓
Agent Loop
   ↓
[before_model]        ← prompt transform, policies
   ↓
LLM Call
   ↓
[after_model]         ← logging, parsing, safety checks
   ↓
[wrap_tool_call]      ← retries, validation, guardrails
   ↓
Observation
   ↓
[after_agent]         ← metrics, formatting, storage
   ↓
Final Answer
```

LangChain does **not** provide one “middleware class”.  
Instead, middleware is built using **Callbacks + Runnables + Tool wrappers**.

---

## 2. Core Middleware Building Blocks in LangChain

| Middleware Need | LangChain Feature |
|-----------------|------------------|
| before/after agent | `CallbackHandler` |
| before/after model | `on_llm_start`, `on_llm_end` |
| tool interception | `on_tool_start`, `on_tool_end` |
| retries/fallbacks | `RunnableRetry`, custom wrappers |
| prompt transforms | `RunnableLambda`, `ChatPromptTemplate` |
| guardrails / PII | callbacks + validators |
| observability | callbacks + traces |
| rate limits | external limiter in callbacks |

---

## 3. Callback‑Based Middleware (Primary Pattern)

### 3.1 Custom Middleware Callback Handler

```python
from langchain.callbacks.base import BaseCallbackHandler
import time

class MiddlewareCallback(BaseCallbackHandler):

    def on_chain_start(self, serialized, inputs, **kwargs):
        # before_agent
        self.start_time = time.time()
        print("🚦 Agent started")
        print("Inputs:", inputs)

    def on_llm_start(self, serialized, prompts, **kwargs):
        # before_model
        print("🧠 LLM call starting")
        print("Prompt:", prompts)

    def on_llm_end(self, response, **kwargs):
        # after_model
        print("✅ LLM response received")
        print("Tokens used:", response.llm_output)

    def on_tool_start(self, serialized, input_str, **kwargs):
        # wrap_tool_call (before)
        print("🔧 Tool called:", serialized["name"])
        print("Arguments:", input_str)

    def on_tool_end(self, output, **kwargs):
        # wrap_tool_call (after)
        print("🔁 Tool output:", output)

    def on_chain_end(self, outputs, **kwargs):
        # after_agent
        duration = time.time() - self.start_time
        print("🏁 Agent finished in", duration, "seconds")
        print("Final output:", outputs)
```

### 3.2 Attaching Middleware to an Agent

```python
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType

llm = ChatOpenAI(model="gpt-4o-mini")

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    callbacks=[MiddlewareCallback()],
    verbose=True
)
```

This **automatically wraps**:
- all LLM calls
- all tool calls
- all agent steps

This is your **LangChain middleware spine**.

---

## 4. Prompt & Output Transformation Middleware (Runnable Layer)

Callbacks *observe*; Runnables *transform*.

### 4.1 before_model: Prompt Injection Middleware

```python
from langchain_core.runnables import RunnableLambda

def inject_policy(inputs):
    inputs["question"] = (
        "Follow security policy. Do not expose PII.\n"
        + inputs["question"]
    )
    return inputs

middleware_before_model = RunnableLambda(inject_policy)
```

### 4.2 after_model: Output Normalization Middleware

```python
def normalize_output(text):
    return {
        "status": "SUCCESS",
        "answer": text
    }

middleware_after_model = RunnableLambda(normalize_output)
```

### 4.3 Chaining with Middleware

```python
chain = (
    middleware_before_model
    | prompt
    | llm
    | middleware_after_model
)
```

This is **true functional middleware**, not just logging.

---

## 5. Tool Middleware (Retries, Validation, Guardrails)

### 5.1 Tool Wrapper Pattern

```python
def tool_middleware(tool_fn):
    def wrapped_tool(*args, **kwargs):
        # validation
        if "DROP" in str(kwargs).upper():
            raise ValueError("Dangerous SQL blocked")

        try:
            return tool_fn(*args, **kwargs)
        except Exception as e:
            # retry / fallback
            print("Retrying tool...")
            return tool_fn(*args, **kwargs)
    return wrapped_tool
```

### 5.2 Register Tool with Middleware

```python
from langchain.tools import Tool

safe_sql_tool = Tool(
    name="safe_sql_query",
    func=tool_middleware(run_sql_query),
    description="Read‑only SQL execution"
)
```

---

## 6. Retry & Fallback Middleware (RunnableRetry)

```python
from langchain_core.runnables import RunnableRetry

llm_with_retry = llm.with_retry(
    stop_after_attempt=3,
    retry_if_exception_type=Exception
)
```

You can stack this with callbacks and prompts.

---

## 7. PII & Guardrails Middleware

### 7.1 Simple PII Detection Example

```python
import re

def pii_guard(text):
    if re.search(r"\b\d{3}-\d{2}-\d{4}\b", text):
        raise ValueError("SSN detected")
    return text
```

Use it in:
- `after_model` Runnable
- `on_llm_end` callback (to block or redact)

---

## 8. Rate Limiting Middleware (Conceptual)

LangChain delegates rate limiting externally.

```python
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=10, period=60)
def rate_limited_llm_call(prompt):
    return llm.invoke(prompt)
```

Attach via:
- tool wrapper
- custom Runnable
- LLM wrapper

---

## 9. Observability Middleware (Production Setup)

Middleware callbacks can push to:
- OpenTelemetry
- LangSmith
- Prometheus
- ELK / Datadog

Example:

```python
from langsmith import traceable

@traceable
def run_agent(query):
    return agent.invoke(query)
```

LangSmith becomes your **agent flight recorder** ✈️

---

## 10. Mapping Middleware Hooks to LangChain

| Generic Middleware | LangChain Hook |
|-------------------|---------------|
| before_agent | `on_chain_start` |
| after_agent | `on_chain_end` |
| before_model | `on_llm_start` |
| after_model | `on_llm_end` |
| wrap_model_call | LLM wrapper / retry |
| wrap_tool_call | Tool wrapper + callbacks |

---

## 11. When to Use LangGraph Instead

If you need:
- hard step limits
- branching logic
- human approval gates
- deterministic state machines

👉 **LangGraph** is middleware‑first by design.

LangChain = flexible  
LangGraph = controlled & auditable

---

## 12. Final Summary

In LangChain, **middleware is not one class**, it is a **layered design**:

- **Callbacks** → observe, log, enforce policies
- **Runnables** → transform prompts & outputs
- **Tool wrappers** → retries, safety, validation
- **Retries & fallbacks** → reliability
- **External services** → rate limits, tracing

If the **agent is the brain**, LangChain middleware is the **nervous system + brakes + dashboard** 🧠🛑📊

---

*Recommended for your use case (Report QA / Issue Analyzer):*
- Callbacks for tracing & debugging
- Tool wrappers for SQL safety
- Runnable middleware for output contracts
- LangGraph when moving to production workflows
