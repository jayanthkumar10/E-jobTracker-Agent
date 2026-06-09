# Documentation: `backend/app/services/chat_rag.py`

## Overview
The `ChatRAGService` is the conversational intelligence layer of CareerOS. It implements a **Hybrid Retrieval-Augmented Generation (RAG)** pipeline that allows users to ask open-ended questions about their application stats and email transcripts.

---

## Detailed Code Walkthrough

### 1. Context Assembly
The service fetches context from two distinct database sources to answer queries:
*   **Relational Data (SQL)**:
    *   Queries all applications linked to the `user_id` to build a list of companies, roles, current statuses, salaries, locations, and recruiters.
    *   Queries the `Interview` table to extract upcoming interview schedules.
*   **Vector Data (pgvector)**:
    *   Generates a query vector embedding for the user's question via the `AIEngineService.generate_embedding()` method.
    *   Executes a semantic search against the `Email` table, sorting by `cosine_distance` to retrieve the top 5 most relevant emails.

### 2. LLM Prompt Configuration
It defines a system prompt with instructions for the Gemma 4 LLM:
*   Sets the persona of CareerOS AI (precise, conversational).
*   Enforces wrapping the final conversational answer inside `<reply>...</reply>` XML tags to facilitate programmatic extraction.
*   Isolates the instruction set from the raw user query context.

### 3. Response Extraction & Sanitization
Once Gemma 4 responds, the service:
1.  Performs XML block extraction. Since thinking traces or prompt descriptions may also mention `<reply>`, it uses `rsplit("<reply>", 1)` to fetch the last occurrence of the tag, which wraps the actual final reply.
2.  If the tag is closed, it splits by `</reply>` to isolate the string.
3.  Cleans leftover artifacts like `tags.`, `tags:`, or raw backticks (`` ` ``) using string replacements.
4.  Removes any leading bullet notes about guidelines to ensure a clean conversational output.
5.  Returns the sanitized response and a list of email IDs referenced in the vector search.
