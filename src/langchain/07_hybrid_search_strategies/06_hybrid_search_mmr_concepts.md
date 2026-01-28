# Maximal Marginal Relevance (MMR) in RAG

Maximal Marginal Relevance (MMR) is a retrieval strategy used in **Retrieval-Augmented Generation (RAG)** to solve the **"redundancy problem."** While standard similarity search (Top-K) only looks for documents most similar to the query, MMR balances relevance to the query with diversity among the results.

---

## 1. Why do we need MMR?
In a standard vector search, the system retrieves the top 3$k$ chunks that are mathematically closest to your question.4 However, if your vector database contains three very similar paragraphs about the same fact, a standard search will likely return all three.

* **The Problem:** This "echo chamber" effect wastes the LLM's limited context window on redundant information and might miss other relevant but slightly less similar perspectives.
* **The Solution:** MMR "penalizes" documents that are too similar to those already selected for the final context, ensuring the LLM sees a broader range of information.6

---

## The Core Problem: Redundancy
In standard **Top-K Similarity Search**, the retriever pulls the chunks most mathematically similar to the query. If your database contains three nearly identical paragraphs about the same topic, the retriever will return all three.

* **Result:** The LLM receives repetitive information.
* **Consequence:** It wastes the context window and might miss a different, slightly less "similar" chunk that contains a vital alternative perspective.

---

## 2. The MMR Solution
MMR balances two competing goals:
1.  **Relevance:** How well the chunk answers the user's query.
2.  **Diversity:** How different the chunk is from the information already selected.

**It selects documents that are both highly relevant to the query and sufficiently different from already selected documents, reducing redundancy in retrieved context.**

### The Scoring Formula
MMR selects documents iteratively by maximizing the following score:

$$\text{MMR}(D_i) = \text{argmax}_{D_i \in R \setminus S} \left[ \lambda \cdot \text{Sim}(D_i, Q) - (1-\lambda) \cdot \max_{D_j \in S} \text{Sim}(D_i, D_j) \right]$$

* **$\text{Sim}(D_i, Q)$**: Similarity of candidate document to the query.
* **$\text{Sim}(D_i, D_j)$**: Similarity of the candidate to documents already in the selected set.
* **$\lambda$ (Lambda)**: The "diversity knob."


**Breakdown of terms:**
* **$\text{Sim}(D_i, Q)$:** How relevant the candidate is to your query.
* $\max_{D_j \in S} \text{Sim}(D_i, D_j)$: How similar the candidate is to the documents you have already picked.
* $\lambda$ (Lambda): The trade-off parameter (typically 0.5).

    * $\lambda = 1$: Pure similarity search (ignores diversity).

    * $\lambda = 0$: Pure diversity search (ignores relevance after the first pick)
---

## 3. How the Algorithm Works

MMR doesn't just rank everything once; it builds the final list iteratively:
1. Fetch Candidates: Retrieve a larger pool of documents (e.g., top 20) using standard similarity. This is often called fetch_k.
2.  First Pick: Select the document with the absolute highest similarity to the query.
3. Iterative Re-ranking: To pick the next document, calculate the MMR score for all remaining candidates.
4. Repeat: Pick the candidate with the highest MMR score, add it to the "selected" set, and repeat until you have 15$k$ documents.


# 4. MMR vs. Standard Retrieval: A Concrete Example

This example demonstrates how **Maximal Marginal Relevance (MMR)** improves the quality of a RAG system by preventing redundant information from crowding out useful context.

---

## 1. The Scenario
**User Query:** *"What are the best vacation spots in Europe?"*

Imagine your vector database contains the following four chunks, ranked by their mathematical similarity to the query:

| Chunk | Content | Similarity Score |
| :--- | :--- | :--- |
| **Chunk A** | "Paris is a top destination known for the Eiffel Tower and cafes." | 0.95 |
| **Chunk B** | "The Eiffel Tower in Paris is a must-see landmark for tourists." | 0.92 |
| **Chunk C** | "The Swiss Alps offer world-class skiing and hiking trails." | 0.85 |
| **Chunk D** | "Rome features historic sites like the Colosseum and great food." | 0.80 |

---

## 2. Standard Top-2 Retrieval
In a standard similarity search where $k=2$, the system simply picks the two highest-scoring documents.

* **Selected:** Chunk A and Chunk B.
* **Result:** The LLM receives two different paragraphs that both discuss the Eiffel Tower and Paris.
* **The Problem:** The LLM remains "blind" to the fact that the database contains information about Switzerland or Italy. The context is redundant.

---

## 3. Retrieval with MMR ($\lambda = 0.5$)
MMR evaluates documents one by one, factoring in how much **new** information they provide compared to what has already been picked.



### Step 1: The First Pick
The algorithm starts by picking the most relevant document.
* **Selected:** **Chunk A** (Similarity 0.95).

### Step 2: Evaluating the Second Pick
The algorithm now calculates the MMR score for the remaining chunks:

* **Chunk B:** While relevance is high (0.92), it is **extremely similar** to Chunk A. The "redundancy penalty" is high, causing its MMR score to drop significantly.
* **Chunk C:** Relevance is moderate (0.85), but it is **highly diverse** compared to Chunk A (Paris vs. Swiss Alps). Because it provides new information, its MMR score remains high.

### Final Result
* **Selected:** **Chunk A** and **Chunk C**.

---

## 4. The Benefit
By using MMR, the LLM receives a much broader context:
1.  **City Tourism:** Paris and the Eiffel Tower.
2.  **Nature/Adventure:** The Swiss Alps and skiing.

**Outcome:** The generated answer will be more comprehensive and helpful to the user, rather than just repeating facts about Paris.

## 5. LangChain Implementation

In LangChain, you can convert any compatible vector store into an MMR retriever using the `search_type="mmr"` argument.

```python
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# Initialize vector store
vectorstore = Chroma(
    persist_directory="./my_db", 
    embedding_function=OpenAIEmbeddings()
)

# Create the MMR retriever
retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        'k': 4,              # Final number of chunks to return
        'fetch_k': 20,       # Initial pool to consider for diversity
        'lambda_mult': 0.5   # The balance between relevance (1.0) and diversity (0.0)
    }
)
``` 


# When to Use Maximal Marginal Relevance (MMR)

In LangChain, switching your retriever from the default `similarity` search to `mmr` is highly beneficial in specific scenarios where data variety matters more than pure mathematical proximity.

---

## 1. Key Use Cases for MMR

You should switch to **MMR** if your RAG pipeline faces the following challenges:

### A. Your Data is Repetitive
If your vector store contains multiple versions of the same document, overlapping transcripts, or many similar news articles, a standard search will fill your context window with the same facts repeated in different words.
* **Example:** You have five different support tickets all describing the same "login error." MMR will pick one and then look for other, different types of issues to give the LLM a broader perspective.

### B. The LLM is "Hallucinating" or Getting Confused
When an LLM is given three slightly different versions of the same fact (e.g., different dates for the same event in three different chunks), it often struggles to prioritize the information. This conflict can lead to hallucinations or incoherent answers.
* **MMR Solution:** By providing distinct, non-overlapping facts, you give the LLM a clearer "source of truth" to work with.

### C. You Want Maximum "Coverage"
If a user asks a broad or multi-part question, you need the retriever to explore different facets of the topic rather than digging deep into just one.
* **The "Pros and Cons" Example:** If a user asks, "What are the pros and cons of electric cars?", a standard similarity search might find five different "pro" paragraphs because they all match the "electric car" keywords. MMR forces the retriever to look for the "cons" to maintain diversity in the results.

---

## 2. Summary Comparison

| Feature | Standard Similarity | MMR (Diversity Search) |
| :--- | :--- | :--- |
| **Goal** | Find the absolute closest matches. | Find relevant but unique matches. |
| **Best For** | Fact-checking a single specific point. | Summarization and broad inquiries. |
| **Risk** | Redundancy and wasted context. | May pick a slightly less relevant chunk. |

---

## 3. Implementation Tip
In LangChain, you can quickly test if MMR improves your specific use case by adjusting the `lambda_mult` parameter. 
* Use **0.5** for a balanced approach.
* Use **0.2** if you want to force high diversity (very different chunks).