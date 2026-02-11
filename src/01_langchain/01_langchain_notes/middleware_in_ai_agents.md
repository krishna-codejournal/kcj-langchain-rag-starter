# Middleware in AI Agents (Detailed Notes)

Middleware is a **control layer** that sits *around* an agent and its model/tool calls.  
Think of it as the **security + observability + reliability belt** that wraps the agent’s core loop.

In a plain agent, the flow is roughly:

```
request → model → (optional tool calls ↔ observations) → result
```

With middleware, you add **hooks** that run *before/after* key steps, and **wrappers** that intercept model/tool calls:

```
request
  → before_agent
  → before_model
      ↘ wrap_tool_call(tools)
      ↘ wrap_model_call(model)
  → after_model
  → after_agent
  → result
```

---

## Why middleware exists

Agents are powerful because they can:
- decide *what* to do next,
- call tools,
- iterate,
- and produce final answers.

But that flexibility can also create problems:
- hard-to-debug behavior,
- inconsistent prompts/output formats,
- wasted cost due to retries or loops,
- unsafe or non-compliant outputs (PII leakage),
- rate-limit or quota explosions.

**Middleware gives you structured control** without rewriting the agent itself.

---

## What middleware is responsible for (core use cases)

### 1) Tracking agent behavior (Logging, Analytics, Debugging)

Middleware can record:
- request metadata (user id, session id, timestamp),
- model inputs/outputs (with redaction),
- tool usage (tool name, arguments, latency, failures),
- number of steps/iterations,
- token usage and cost,
- final decision path (what tools were called and why).

**Benefits**
- Faster debugging (“why did it choose this tool?”)
- Auditing for compliance
- Analytics dashboards (top tools used, failure hotspots)
- Cost monitoring (token + tool spend per feature)

---

### 2) Transforming prompts, tool selection, and output formatting

Middleware can:
- inject system policies (style, safety rules, “always cite sources”, etc.)
- add project context (tenant settings, user role, environment)
- rewrite the prompt (e.g., add missing constraints)
- enforce tool schemas (validate arguments before tool execution)
- standardize final output (JSON contract, table layout, markdown format)

**Examples**
- Prompt templating: add `customer_id`, `region`, `report_name`
- Tool gating: allow only a specific set of tools in production
- Output contract enforcement: always return `{status, reason, evidence}`

---

### 3) Retries, fallbacks, and early termination logic

Agents can get stuck:
- tool failures,
- timeouts,
- partial answers,
- hallucinated tool arguments,
- infinite loops.

Middleware can implement:
- **retry policies** (retry tool call up to N times with backoff)
- **fallbacks** (if tool A fails, try tool B)
- **timeouts** (stop after X seconds)
- **max-steps** (stop after N agent iterations)
- **circuit breakers** (disable a failing tool temporarily)

**Outcome**
- More reliable production behavior
- Lower operational incidents

---

### 4) Rate limits, guardrails, and PII detection

Middleware is often the right place for **safety and governance**:
- rate limiting per user / API key
- throttling expensive tools
- allow/deny lists for tool usage
- policy checks before executing actions
- PII detection + redaction (emails, SSNs, phone numbers, addresses, etc.)
- content moderation checks
- “human-in-the-loop” approval gates for risky actions

**Why middleware is ideal here**
It centralizes policy enforcement so you don’t have to bake safety checks into every agent prompt.

---

## Middleware lifecycle: hooks and wrappers

Middleware is usually built with **hooks** and **wrappers**.

### A) Hooks (before/after stages)

#### `before_agent(request)`
Runs once at the start.
Typical actions:
- create trace id / correlation id
- attach user/session metadata
- apply rate limiting
- validate request shape

#### `before_model(context)`
Runs before each model call (agents can call model many times).
Typical actions:
- rewrite/augment prompt
- enforce system policy
- inject retrieved context
- ensure tool permissions for this user

#### `after_model(model_output)`
Runs immediately after model returns.
Typical actions:
- parse model output (tool call vs final answer)
- validate output format
- detect policy violations
- run redaction/PII masking on logs

#### `after_agent(result)`
Runs once at the end.
Typical actions:
- finalize logs + metrics
- compute cost summary
- format final response
- store trace in an observability system

---

### B) Wrappers (intercept calls)

#### `wrap_model_call(model)`
This wrapper intercepts every model invocation.
It can:
- measure latency and tokens
- retry model call on transient failures
- switch models as fallback (e.g., “fast model” → “smart model”)
- enforce max context length and truncation rules

#### `wrap_tool_call(tool_fn)`
This wrapper intercepts tool calls.
It can:
- validate tool arguments (schema check)
- apply tool-specific rate limits
- redact sensitive fields in logs
- retries/backoff if tool fails
- add caching for deterministic tools
- block dangerous tools in certain environments

---

## A concrete example: “Report Issue Analyzer” agent

You (Harry) build an agent that:
1. reads a user question,
2. picks a tool to query Oracle/MongoDB,
3. returns a root-cause explanation.

Middleware can add:
- logging every query + latency
- deny-list for `DELETE/UPDATE` SQL in prod
- retry for temporary DB timeouts
- PII masking for customer identifiers
- max-steps to stop runaway loops
- standardized output:

```json
{
  "status": "FAIL",
  "reason": "Mismatch between report and DB",
  "evidence": ["SQL used...", "Row counts..."],
  "next_steps": ["Check filter condition...", "Verify FX rates..."]
}
```

This makes the agent **production-safe** and **debuggable**.

---

## Minimal pseudo-implementation (conceptual)

Below is a simplified pattern (framework-agnostic).  
(Real implementations vary across LangChain/LangGraph, OpenAI Agents SDK, etc.)

```python
class Middleware:
    def before_agent(self, request): ...
    def before_model(self, ctx): ...
    def after_model(self, output): ...
    def after_agent(self, result): ...
    def wrap_model_call(self, model_call): return model_call
    def wrap_tool_call(self, tool_call): return tool_call


def run_agent(request, agent, model, tools, middleware: Middleware):
    middleware.before_agent(request)

    # Wrap model and tools
    model_call = middleware.wrap_model_call(model)
    wrapped_tools = {name: middleware.wrap_tool_call(fn) for name, fn in tools.items()}

    ctx = {"request": request, "tools": wrapped_tools}

    while True:
        middleware.before_model(ctx)
        output = model_call(ctx)         # model decides: tool call or final answer
        middleware.after_model(output)

        if output["type"] == "tool_call":
            tool_name = output["tool"]["name"]
            args = output["tool"]["args"]
            obs = wrapped_tools[tool_name](**args)
            ctx["observation"] = obs
            continue

        result = output["final"]
        break

    middleware.after_agent(result)
    return result
```

---

## Design tips: where middleware fits best

### Put in middleware
- logging/tracing
- retries/backoff
- safety checks (PII, guardrails, permissions)
- output schema enforcement
- caching, rate limiting
- cost monitoring, token budgets

### Keep in the agent logic
- domain reasoning (how to diagnose a report issue)
- tool choice strategy (which tool to call and why)
- final explanation (human-readable “cause and fix”)

Middleware should be **generic**, reusable across many agents.

---

## Common middleware patterns (practical checklists)

### Observability
- [ ] Trace ID per request
- [ ] Log tool calls + latency + errors
- [ ] Token/cost tracking
- [ ] Step counter + loop detection

### Reliability
- [ ] Timeouts
- [ ] Retries with exponential backoff
- [ ] Fallback model/tool
- [ ] Circuit breaker for flaky tools

### Safety & Governance
- [ ] PII redaction in logs and outputs
- [ ] Tool allowlist/denylist
- [ ] Environment rules (dev vs prod)
- [ ] SQL safety (block DML, enforce read-only)
- [ ] Rate limits and quotas

### Output quality
- [ ] JSON/markdown formatting standard
- [ ] Validation and repair (if invalid schema)
- [ ] Consistent error messages

---

## Summary

Middleware is the **control + safety + reliability wrapper** around an agent.  
It doesn’t change what the agent *is*; it changes how the agent *behaves in production* by adding:

- **visibility** (logging/analytics),
- **consistency** (prompt/output transforms),
- **robustness** (retries/fallbacks/termination),
- **governance** (rate limits/guardrails/PII checks).

If the agent is the “brain,” middleware is the **nervous system and seatbelt** 🧠🪢
