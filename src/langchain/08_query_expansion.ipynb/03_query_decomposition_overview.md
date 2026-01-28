# Query Decomposition Design Document  
## Report Issue Analyzer & Report Verification System (Oracle + RAG)

---

## 1. Overview

Modern enterprise reports often fail due to complex dependencies across data sources, transformations, filters, and business rules. A single user question like:

> “Why is Customer Balance wrong in AMS 8.3 report?”

usually hides **multiple intents**:
- understanding business definitions
- validating source data
- checking filters and joins
- reconciling values
- diagnosing root causes

**Query Decomposition** is the technique of breaking such a complex query into smaller, well-scoped sub-queries, executing them using the right tools (RAG, SQL, rules), and synthesizing a reliable final answer.

This document defines a **production-grade query decomposition architecture** for a **Report Issue Analyzer / Report Verification system** using:
- Oracle (source of truth)
- RAG (report logic, metadata, known issues)
- LLMs (planning and reasoning only)

---

## 2. Goals & Non-Goals

### Goals
- High accuracy and auditability
- Deterministic numeric validation using SQL
- Clear PASS/FAIL verdicts
- Explainable root cause analysis
- Scalable to multiple reports and regions

### Non-Goals
- LLM-generated calculations
- Black-box answers without evidence
- Single-prompt “magic” reasoning

---

## 3. High-Level Architecture

```text
 ┌──────────────────────────────┐
 │        User Question         │
 └──────────────┬───────────────┘
                │
                v
 ┌──────────────────────────────┐
 │ 1) Intent & Task Classifier  │
 │  - verify / explain / RCA    │
 │  - entities, metric, scope  │
 └──────────────┬───────────────┘
                │
                v
 ┌──────────────────────────────┐
 │ 2) Query Decomposer (LLM)    │
 │  - sub-questions             │
 │  - dependency graph (DAG)    │
 └──────────────┬───────────────┘
                │
                v
 ┌────────────────────────────────────────────┐
 │ 3) Planner / Orchestrator                  │
 │  - execution order                         │
 │  - route to RAG / SQL / rules              │
 └───────┬─────────────────────┬─────────────┘
         │                     │
         v                     v
┌──────────────────┐   ┌─────────────────────┐
│ 4a) RAG Engine    │   │ 4b) SQL Generator   │
│ - definitions     │   │ - joins & filters  │
│ - mappings        │   │ - Oracle execution │
└──────────┬───────┘   └──────────┬──────────┘
           │                       │
           v                       v
 ┌────────────────────────────────────────────┐
 │ 5) Sub-Answer Generator                    │
 │  - evidence-backed answers                │
 └──────────────┬─────────────────────────────┘
                v
 ┌────────────────────────────────────────────┐
 │ 6) Synthesizer & Verdict Engine             │
 │  - PASS / FAIL                              │
 │  - explanation & root cause                 │
 └────────────────────────────────────────────┘


## 4. Query Decomposition Concept

Query decomposition splits a single user query into:

- Atomic sub-questions  
- Each mapped to the best execution tool  
- With explicit dependencies  

This approach avoids:

- Vague retrieval  
- Hallucinated joins  
- Incorrect numeric reasoning  

---

## 5. Sub-Query Schema (Core Contract)

Each decomposed step follows a strict schema:

```json
{
  "id": "SQ-3",
  "type": "rag | sql | rule | analysis",
  "question": "What filters apply to Customer Balance in AMS 8.3?",
  "depends_on": ["SQ-1", "SQ-2"],
  "inputs": {
    "report": "AMS 8.3",
    "metric": "Customer Balance",
    "region": "EMEA"
  },
  "expected_output": "List of filters and conditions",
  "confidence_required": true
}


This schema allows:

- DAG-based execution  
- Deterministic orchestration  
- Clear audit trails  

---

## 6. Decomposition Playbooks by Use Case

### 6.1 Report Verification

**User Query**

> “Verify Customer Balance for Contract 456 in AMS 8.3 report”

**Decomposition**

```text
SQ-1: Business definition of Customer Balance        (RAG)
SQ-2: Source tables and columns                     (RAG)
SQ-3: Filters (region, date, status, currency)      (RAG)
SQ-4: Generate SQL                                  (SQL generation)
SQ-5: Execute SQL in Oracle                         (SQL)
SQ-6: Compare report vs source                      (Analysis)
SQ-7: Diagnose mismatch if any                      (Rules + RAG)



## 6.2 Issue Explanation / Root Cause Analysis

**User Query**

> “Why is Customer Balance wrong in AMS 8.3?”

**Hypothesis-Driven Decomposition**

```text
SQ-1: Known failure patterns for this metric
SQ-2: Data freshness vs report cutoff
SQ-3: Join logic mismatches
SQ-4: Currency conversion or rounding issues
SQ-5: Late or backdated postings
SQ-6: Rank likely causes by confidence


6.3 Reconciliation (Mongo vs Oracle)

User Query

“Why is Mongo count higher than Oracle?”

Diagnostic Tree

SQ-1: Filter mismatch
SQ-2: Delete handling difference
SQ-3: Incremental watermark issue
SQ-4: Duplicate records
SQ-5: Late-arriving data

7. Tool Routing Rules
Sub-Query Type	Tool	Reason
Definitions & logic	RAG	Stored knowledge
Mapping & joins	RAG	Metadata driven
Numeric values	SQL	Source of truth
Comparison	Analysis	Deterministic
Root cause	Hybrid	Knowledge + rules

Rule: LLMs never compute report numbers.
They reason; databases decide.

8. Verdict & User-Facing Output Format
Result: ❌ FAIL

Metric: Customer Balance
Report Value: 1,245,000
Source Value (Oracle): 1,238,450
Difference: 6,550

Likely Root Cause:
• Late postings after report cutoff
• Missing FX revaluation for EUR contracts

Confidence: 0.82

Suggested Fix:
• Align cutoff timestamp
• Re-run FX adjustment job


This format is:

understandable by business users

actionable by engineering teams

defensible in audits

9. Design Principles

Separation of concerns

LLM = planner

RAG = memory

SQL = truth

Rules = guardrails

Explainability over cleverness

Deterministic validation

Composable and extensible

10. Future Extensions

LangGraph DAG execution

Confidence scoring per sub-query

Caching of verified SQL results

Knowledge graph for entity resolution

Automated regression validation for reports

11. Summary

Query decomposition transforms report analysis from:

“Trust the model”

into:

“Verify, explain, and prove”

This architecture enables enterprise-grade report verification, reconciliation, and issue diagnosis with accuracy, transparency, and trust.


---

If you want, next I can:
- split this into **Architecture / Execution / Prompting docs**
- add **LangGraph node mapping**
- provide **ready-to-use system + planner prompts**
- generate a **repo folder structure** around this

Just say the word and we’ll keep building 🚀