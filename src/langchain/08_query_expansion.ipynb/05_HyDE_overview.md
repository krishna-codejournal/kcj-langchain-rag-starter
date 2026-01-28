# HyDE (Hypothetical Document Embeddings)

HyDE (Hypothetical Document Embeddings) is a retrieval technique for RAG that follows this idea:

> **Instead of embedding the user’s question, first ask the LLM to write a hypothetical answer document, then embed that document and retrieve using it.**

### Why this works

User questions are often:
- Short
- Vague
- Missing important keywords

A hypothetical answer is richer and more **document-like**, which means its embedding lands closer (in vector space) to the real supporting documents you want to retrieve.

🧠 **In one line:**  
HyDE turns a query into a mini fake document so semantic search has more surface area to grab onto.

---

## The Problem HyDE Solves

### Plain Semantic Retrieval

Traditional semantic retrieval embeds the query directly:

- **Query:** “Why is my report balance wrong?”
- The embedding is based on a short sentence with little context
- Vector search returns loosely related or overly broad documents

### How HyDE Improves This

HyDE adds context *before* retrieval by generating a hypothetical explanation that includes likely concepts such as:

- Cutoff dates  
- Late postings  
- FX conversion  
- Join logic  
- Filters  
- Reconciliation  

The resulting embedding now contains these concepts, making retrieval significantly sharper and more relevant.

---

## HyDE Architecture

```text
User Query
   |
   v
(1) HyDE Generator (LLM)
    -> produces a hypothetical document (fake but plausible)
   |
   v
(2) Embed hypothetical document
   |
   v
(3) Vector search using that embedding
   |
   v
(4) Retrieve top-k real documents (ground truth context)
   |
   v
(5) Final Answerer (LLM)
    -> answers using retrieved docs (not the hypothetical doc)


Key safety rule: The hypothetical document is used for retrieval only.
The final answer must be grounded in retrieved sources (or DB/tool outputs).

What the “hypothetical document” looks like

If the user asks:

“How does LangChain use memory and agents compared to CrewAI?”

HyDE might generate something like:

a short structured comparison

mentions of agent executors, tools, memory types, planning loops, role-based agents

terms like “ConversationBufferMemory”, “RunnableWithMessageHistory”, “AgentExecutor”, “tools”, “Crew”, “tasks”, etc.

That text is much closer to what real docs contain than the raw question.

Why HyDE works (intuition)

Embeddings work best when the query “resembles” the documents.

User query = question-shaped

Your knowledge base = answer/document-shaped

HyDE converts the query into document-shaped text, reducing the mismatch.

It’s especially helpful when:

the user uses different wording than your docs

synonyms/abbreviations are common (e.g., “balance mismatch” vs “recon variance”)

your docs are long and structured, while queries are tiny

Variants of HyDE
1) Classic HyDE (single hypothetical doc)

Generate 1 hypothetical doc

Embed it

Retrieve with it

Fast and usually good.

2) Multi-HyDE (multiple hypothetical docs)

Generate N different hypothetical docs (different angles)

Embed each

Retrieve and merge results

Great for ambiguous queries, but costs more.

3) Structured HyDE

Generate a hypothetical doc with a fixed schema:

Definitions

Symptoms

Common causes

Checks

Fixes

This improves consistency and retrieval quality for enterprise use cases (like your report issue analyzer).

4) Hybrid HyDE (BM25 + HyDE)

Retrieve using:

BM25 on original query (keyword exactness)

Vector search on HyDE doc (semantic richness)

Merge + rerank

This is often the sweet spot.

Where HyDE shines (use cases)
Enterprise reporting / RCA (your world)

“Why is customer balance wrong?”

“ORA-00942 in report”

“Mongo vs Oracle mismatch”

HyDE tends to “speak the language” of your functional docs and known-issues pages.

Helpdesk / troubleshooting knowledge bases

Users describe symptoms poorly; HyDE expands them into likely technical phrasing.

Legal/policy/HR docs

Queries are vague, docs are formal. HyDE bridges style mismatch.

Code / API documentation search

User asks “how do I do X” but docs mention the exact class/method names.

Risks and how to guardrail
Risk 1: The hypothetical doc hallucinates

Yes, it can. But it’s okay if:

it’s only used to retrieve

final answer is grounded in retrieved docs

Guardrail: In the final prompt, explicitly say:

“Ignore the hypothetical document. Use only retrieved documents for the answer.”

Risk 2: Topic drift

If the model invents the wrong angle, retrieval can go sideways.

Guardrails:

Keep hypothetical docs short (e.g., 150–300 words)

Force it to stick to the query scope (report name, metric, region, time window)

Use multi-hyde only when needed

Risk 3: Extra cost/latency

HyDE adds an LLM call before retrieval.

Mitigations:

Use cheaper model for HyDE generation

Cache HyDE outputs for repeated queries

Turn it on only for “hard queries” (low retrieval confidence)

Practical recipe (pseudo-steps)

Generate hypothetical doc:

Prompt: “Write a concise document that would answer the question…”

Embed hypothetical doc

Retrieve top-k docs

Answer using retrieved docs (and cite them)

LangChain-style sketch (conceptual)
# 1) hyde_doc = llm.invoke(prompt.format(question=q))
# 2) hyde_vec = embedding.embed_query(hyde_doc)
# 3) docs = vectorstore.similarity_search_by_vector(hyde_vec, k=K)
# 4) final = answer_llm.invoke(answer_prompt.format(question=q, context=docs))


If you’re using a retriever abstraction, you can wrap HyDE as a “pre-retrieval” step.

HyDE vs Query Decomposition (how they relate)

They solve different problems and can be combined:

HyDE: makes one query more retrievable by turning it into a doc-like representation.

Query Decomposition: splits a complex query into multiple smaller ones.

Combo pattern (very strong):

Decompose question into sub-questions

For each sub-question, apply HyDE retrieval

Synthesize sub-answers

This is 🔥 for report RCA and verification.

When NOT to use HyDE

Simple fact lookups where keywords are exact (BM25 works)

When you already have excellent query rewriting

When latency budget is tight

When your vector store is already returning clean top-3 results consistently

