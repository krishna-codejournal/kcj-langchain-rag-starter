# Human-in-the-Loop (HITL) Middleware in LangChain

Human‑in‑the‑Loop (HITL) is a **middleware pattern** where a human can **review, approve, modify, or reject** an agent’s decision *before* it continues or completes an action.

In LangChain terms, HITL is **not business logic**.  
It is a **control layer** that intercepts the agent flow at critical points.

---

## 1. Why HITL is Middleware (Conceptually)

HITL qualifies as middleware because it:

- sits **between agent steps**
- intercepts **decisions or actions**
- pauses or reroutes execution
- enforces **governance, safety, and accountability**
- is reusable across agents

### Agent without HITL

```
Question → LLM → Tool → Answer
```

### Agent with HITL Middleware

```
Question
  ↓
LLM proposes action
  ↓
[ HUMAN REVIEW GATE ]   ← middleware
  ↓
Approved? → continue
Rejected? → stop / revise
```

The agent does not “know” *who* approved it.  
That’s exactly what middleware does.

---

## 2. When You Need HITL Middleware

Use HITL when agents can:

- execute **irreversible actions** (DB updates, emails, payments)
- expose **sensitive data** (PII, finance, health)
- generate **regulatory or audit‑relevant outputs**
- make **high‑impact decisions** (approvals, denials)
- operate in **production systems**

### Real examples
- SQL write queries
- Vendor payment triggers
- Customer credit decisions
- Compliance reports
- Incident remediation actions

---

## 3. HITL Patterns in LangChain

LangChain supports HITL using **middleware composition**, not a single class.

### Main patterns:
1. Approval middleware (yes/no)
2. Edit-and-continue middleware
3. Escalation middleware
4. Sampling-based HITL (only some cases)
5. LangGraph checkpoint + resume (best practice)

---

## 4. Simple HITL Middleware Using RunnableLambda

### Use case
Block dangerous SQL unless human approves.

```python
from langchain_core.runnables import RunnableLambda

def human_approval_middleware(action: dict):
    print("⚠️ Proposed action:")
    print(action)

    decision = input("Approve action? (yes/no): ").lower()

    if decision != "yes":
        raise ValueError("Action rejected by human")

    return action
```

### Usage in a chain

```python
chain = (
    agent_decision_runnable
    | RunnableLambda(human_approval_middleware)
    | tool_execution_runnable
)
```

✅ This is **true middleware**:
- reusable
- intercepts flow
- agent logic unchanged

---

## 5. HITL for Output Review (Before Final Answer)

### Example: Human review before sending report result

```python
def review_output(text: str):
    print("📄 Agent Output:")
    print(text)

    edit = input("Edit output (or press Enter to accept): ")

    if edit.strip():
        return edit
    return text
```

```python
final_chain = llm_chain | RunnableLambda(review_output)
```

Human becomes a **runtime editor middleware**.

---

## 6. HITL Middleware with Decision Routing

Human decides what happens next.

```python
def human_router(state):
    print("Agent suggestion:", state["proposal"])
    choice = input("approve / revise / stop: ")

    state["decision"] = choice
    return state
```

Downstream logic branches based on `decision`.

---

## 7. Production‑Grade HITL: LangGraph (Recommended)

For serious systems, **LangGraph** is the correct tool.

LangGraph makes HITL a **first‑class middleware node**.

---

## 8. LangGraph HITL Example (Checkpoint + Resume)

### Step 1: Define graph state

```python
from typing import TypedDict

class State(TypedDict):
    proposal: str
    approved: bool
```

---

### Step 2: Agent proposes an action

```python
def propose(state: State):
    state["proposal"] = "Execute SQL UPDATE on customer table"
    return state
```

---

### Step 3: Human approval node (middleware)

```python
def human_review(state: State):
    print("⚠️ Proposed:", state["proposal"])
    decision = input("Approve? (yes/no): ")

    state["approved"] = decision == "yes"
    return state
```

---

### Step 4: Conditional routing

```python
def should_continue(state: State):
    return "continue" if state["approved"] else "stop"
```

---

### Step 5: Build graph

```python
from langgraph.graph import StateGraph, END

graph = StateGraph(State)

graph.add_node("propose", propose)
graph.add_node("human_review", human_review)

graph.add_edge("propose", "human_review")
graph.add_conditional_edges(
    "human_review",
    should_continue,
    {
        "continue": END,
        "stop": END
    }
)

app = graph.compile()
app.invoke({})
```

🧠 This gives you:
- pause/resume
- deterministic checkpoints
- auditable approval paths
- enterprise‑grade HITL

---

## 9. HITL + Audit Trail (Middleware Responsibility)

HITL middleware should also log:

- who approved
- when
- what was approved
- original vs final content

```python
audit_log = {
    "action": action,
    "approved_by": "user123",
    "timestamp": "2026‑01‑25"
}
```

This is **governance middleware**, not agent logic.

---

## 10. Where HITL Fits in the Middleware Stack

```
User Request
  ↓
Token guard middleware
  ↓
Summarization middleware
  ↓
Agent reasoning
  ↓
HITL approval middleware   ← critical gate
  ↓
Tool execution
  ↓
Output formatting
  ↓
Logging & audit
```

---

## 11. HITL Best Practices

### Do
- Put HITL **before irreversible actions**
- Keep HITL logic **outside prompts**
- Log every decision
- Use LangGraph for production
- Make approval UX simple

### Avoid
- Baking HITL into prompts
- Relying on “LLM self‑approval”
- Blocking everything (use sampling)
- Skipping audit logs

---

## 12. HITL in Your Use Case (Report QA / Data Systems)

For your Report QA & Issue Analyzer:

| Step | HITL Role |
|----|----|
| SQL execution | Approve non‑SELECT |
| Report mismatch | Approve escalation |
| Vendor export | Approve send |
| Fix recommendation | Approve apply |

This keeps AI **assistive**, not autonomous.

---

## 13. Final Takeaway

**Human‑in‑the‑Loop is control middleware.**

It provides:
- safety
- trust
- compliance
- accountability

If **agents are the brain**,  
HITL middleware is the **conscience and brake pedal** 🧠🛑

---

*Recommended path for you*:
- Dev / POC → RunnableLambda HITL
- Production → LangGraph HITL with checkpoints
