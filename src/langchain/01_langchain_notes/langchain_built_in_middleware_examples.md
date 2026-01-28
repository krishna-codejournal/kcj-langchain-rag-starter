# Built-in “Middleware” Features in LangChain (with Examples)

LangChain doesn’t ship a single object literally called **Middleware**.  
But it *does* include several **built-in building blocks** that behave like middleware:

- **Callbacks** (observe + intercept the agent/LLM/tool lifecycle)
- **Runnable configuration** (tags/metadata, recursion limits, timeouts in integrations)
- **Retries** (`with_retry()` / `RunnableRetry`)
- **Fallbacks** (`with_fallbacks()`)
- **Message history wrappers** (session state around chains)
- **Output parsers** (enforce formats, repair invalid output)
- **Tool wrappers / Structured tools** (schema validation and safer tool calls)

This doc lists those **built-ins**, explains when to use them, and gives runnable examples.

> Note: Examples use LangChain “core” patterns (Runnables) because they are the most general and work across chains/agents.

---

## 1) Built-in Callbacks (Observability Middleware)

### What it gives you
- before/after LLM calls
- before/after tool calls
- chain start/end events
- streaming events
- errors

### Built-in callback handlers (common ones)
- `StdOutCallbackHandler` (prints events)
- `StreamingStdOutCallbackHandler` (prints tokens as they stream)

### Example: Attach `StdOutCallbackHandler` to a chain

```python
from langchain.callbacks import StdOutCallbackHandler
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o-mini")
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are concise."),
    ("human", "{q}")
])

chain = prompt | llm

resp = chain.invoke(
    {"q": "Explain middleware in one paragraph."},
    config={"callbacks": [StdOutCallbackHandler()]}
)
print(resp.content)
```

### Example: Streaming output middleware

```python
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o-mini",
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()]
)

llm.invoke("Write a 3-line poem about data pipelines.")
```

✅ Use callbacks for **logging, analytics, debugging, traces**.

---

## 2) Built-in Retry Middleware (`with_retry` / `RunnableRetry`)

### What it gives you
Automatic retries for transient failures (network, rate limits, temporary tool errors).

### Example: Retry an LLM runnable

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")

llm_retry = llm.with_retry(
    stop_after_attempt=3
)

llm_retry.invoke("Give a one-line summary of RAG.")
```

### Example: Retry a full chain

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

prompt = ChatPromptTemplate.from_template("Answer briefly: {q}")
llm = ChatOpenAI(model="gpt-4o-mini")

chain = (prompt | llm).with_retry(stop_after_attempt=3)

chain.invoke({"q": "What is semantic chunking?"})
```

✅ Use retries for **reliability**.

---

## 3) Built-in Fallback Middleware (`with_fallbacks`)

### What it gives you
If the primary runnable fails, LangChain tries a fallback runnable.

### Example: Model fallback (fast → strong)

```python
from langchain_openai import ChatOpenAI

primary = ChatOpenAI(model="gpt-4o-mini")     # cheaper/faster
fallback = ChatOpenAI(model="gpt-4.1-mini")   # stronger (example)

safe_llm = primary.with_fallbacks([fallback])

safe_llm.invoke("Explain vector database vs vector store.")
```

### Example: Fallback to a canned response
Useful when you want graceful degradation.

```python
from langchain_core.runnables import RunnableLambda

def canned(_):
    return "Sorry, I'm temporarily unable to answer. Please try again."

primary = (ChatPromptTemplate.from_template("{q}") | ChatOpenAI(model="gpt-4o-mini"))
fallback = RunnableLambda(canned)

chain = primary.with_fallbacks([fallback])
print(chain.invoke({"q": "What is HyDE in RAG?"}))
```

✅ Use fallbacks for **resilience** and **SLA friendliness**.

---

## 4) Built-in Input/Output Transformation Middleware (Runnables)

These are “middleware-like” because they sit *between* steps.

### 4.1 `RunnableLambda` (custom transform)

```python
from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

def before_model(x):
    x["q"] = "Policy: do not output PII.\n" + x["q"]
    return x

def after_model(msg):
    return {"answer": msg.content, "status": "OK"}

chain = (
    RunnableLambda(before_model)
    | ChatPromptTemplate.from_template("{q}")
    | ChatOpenAI(model="gpt-4o-mini")
    | RunnableLambda(after_model)
)

print(chain.invoke({"q": "Explain what middleware does in agents."}))
```

### 4.2 `RunnablePassthrough` + `RunnableMap` (shape control)

```python
from langchain_core.runnables import RunnablePassthrough, RunnableMap, RunnableLambda
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")

def add_meta(q):
    return {"q": q, "trace_id": "T-123"}

chain = (
    RunnableLambda(add_meta)
    | RunnableMap({"answer": (lambda x: x["q"]) | llm, "trace_id": (lambda x: x["trace_id"])})
)

out = chain.invoke("One line: what is an agent?")
print(out)
```

✅ Use runnables for **prompt injection, output contracts, routing, shaping data**.

---

## 5) Built-in “Config Middleware”: tags, metadata, recursion limits

LangChain Runnables accept config like:

- `tags` (group traces)
- `metadata` (attach trace context)
- `callbacks`
- in some contexts: `recursion_limit` (important for graphs/agents)

### Example: Tags + metadata

```python
chain.invoke(
    {"q": "Explain retries in LangChain."},
    config={
        "tags": ["prod", "middleware", "observability"],
        "metadata": {"tenant": "cisco_capital", "feature": "report_qa"}
    }
)
```

✅ Use config for **trace correlation** and **multi-tenant context**.

---

## 6) Built-in Output Parsing Middleware (Format Enforcement)

Output parsers are “middleware” because they enforce a contract between LLM and your application.

### 6.1 String parser (`StrOutputParser`)

```python
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

chain = ChatPromptTemplate.from_template("Answer in one sentence: {q}") | ChatOpenAI(model="gpt-4o-mini") | StrOutputParser()
print(chain.invoke({"q": "What is MMR in RAG?"}))
```

### 6.2 JSON parser (structured responses)
If your prompt asks for JSON, parse it and fail fast if invalid.

```python
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

parser = JsonOutputParser()
prompt = ChatPromptTemplate.from_template(
    "Return JSON with keys: status, reason. Question: {q}"
)

chain = prompt | ChatOpenAI(model="gpt-4o-mini") | parser
print(chain.invoke({"q": "Why might ORA-00942 occur?"}))
```

✅ Use parsers for **API contracts** and **deterministic downstream processing**.

---

## 7) Built-in Tool “Middleware”: Structured tools & schema validation

LangChain supports **Structured Tools** (typed args via Pydantic).  
This gives you built-in argument validation, which is a key middleware feature.

### Example: Pydantic-based tool validation

```python
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool

class SqlArgs(BaseModel):
    query: str = Field(..., description="Read-only SELECT query")

def run_sql(query: str) -> str:
    if not query.strip().lower().startswith("select"):
        raise ValueError("Only SELECT is allowed")
    return "rows: 42 (demo)"

sql_tool = StructuredTool.from_function(
    func=run_sql,
    name="safe_sql",
    description="Executes read-only SQL",
    args_schema=SqlArgs
)
```

✅ Use structured tools for **safe tool calling** and **clean validation errors**.

---

## 8) Built-in Agent Middleware: verbose tracing

Agents have built-in debugging modes (useful during development):

```python
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True
)
```

This is “middleware-lite”: it prints intermediate steps and tool calls.

✅ Use it to quickly see **agent reasoning + tool usage** during dev.

---

## 9) “Middleware-like” Session State: Message History wrappers

For chat apps, you often want middleware that:
- loads history
- stores history
- enforces token budget

LangChain provides wrappers for history management.

### Example: RunnableWithMessageHistory (conceptual)

```python
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

store = {}

def get_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

chat = ChatPromptTemplate.from_messages([("human", "{q}")]) | ChatOpenAI(model="gpt-4o-mini")

chain = RunnableWithMessageHistory(
    chat,
    get_history,
    input_messages_key="q",
    history_messages_key="history"
)

chain.invoke(
    {"q": "Remember my name is Harry."},
    config={"configurable": {"session_id": "s1"}}
)
```

✅ Use this for **chat middleware**: memory, personalization, continuity.

---

## 10) Putting It Together: A Real Middleware Stack

Here’s a practical “stack” you can use for your **Report Issue Analyzer**:

1. **Callbacks** (logging + traces)
2. **Prompt injection runnable** (policy/context)
3. **LLM with retry** (reliability)
4. **Structured tool** (safe SQL)
5. **Output parser** (JSON contract)
6. **Fallback chain** (graceful degradation)

### End-to-end skeleton

```python
from langchain.callbacks import StdOutCallbackHandler
from langchain_core.runnables import RunnableLambda
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

def before(x):
    x["q"] = f"Follow policy: do not output PII.\nQuestion: {x['q']}"
    return x

prompt = ChatPromptTemplate.from_template("{q}")
parser = JsonOutputParser()

llm = ChatOpenAI(model="gpt-4o-mini").with_retry(stop_after_attempt=3)

chain = (
    RunnableLambda(before)
    | prompt
    | llm
    | parser
).with_fallbacks([
    RunnableLambda(lambda _: {"status": "ERROR", "reason": "Temporary failure"})
])

out = chain.invoke(
    {"q": "Why is ORA-00942 happening in my AMS report?"},
    config={"callbacks": [StdOutCallbackHandler()], "tags": ["report_qa"]}
)

print(out)
```

---

## Quick Cheat Sheet

### Use this when you need…
- **Logging/analytics/debugging** → Callbacks
- **Prompt/output shaping** → Runnables (`RunnableLambda`, `RunnableMap`)
- **Stability** → `with_retry()`
- **Graceful degradation** → `with_fallbacks()`
- **Safe tool calls** → Structured Tools (Pydantic schema)
- **Strict contracts** → Output parsers (`JsonOutputParser`)
- **Chat memory** → `RunnableWithMessageHistory`

---

## Summary

LangChain’s “built-in middleware” is not a single feature. It’s a **composition** of:

- **Callbacks** (observe + enforce)
- **Runnables** (transform + route)
- **Retries/Fallbacks** (reliability)
- **Structured tools** (safety)
- **Output parsers** (contracts)
- **Message history wrappers** (state)

This layered approach is exactly what you want for production agents: **control without chaos** 🧠🧰

