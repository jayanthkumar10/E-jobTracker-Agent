# Documentation: `backend/app/services/ai_engine.py`

## Overview
The `AIEngineService` class encapsulates the interactions with the **Google Gemini API** (using the Gemma 4-31b-it model and the Gemini Embedding models). It handles structured JSON data extractions from emails and generates vector representations for semantic search.

---

## Detailed Code Walkthrough

### 1. Model Initialization (`get_model`)
*   Instantiates `genai.GenerativeModel` using the configured model name `models/gemma-4-31b-it`.
*   Accepts optional `system_instruction` parameters to inject instructions isolated from user contents.

### 2. Structured Extraction (`extract_job_details`)
This method takes an email's body text, subject, and sender and returns a structured Pydantic schema object (`JobExtractionSchema`).
*   **The Schema Constraint**: The model is prompted with a strict JSON format structure representing keys like `company_name`, `job_title`, `status`, and `is_actual_submission_confirmation`.
*   **API Execution**: It runs `generate_content()` on the Gemma model with `response_mime_type="application/json"` and low temperature (`0.1`) to ensure deterministic outputs.
*   **Fallback JSON Decoders**: It uses a robust fallback sequence:
    1.  Attempts standard JSON parsing.
    2.  If preambles or headers are present, it locates the first `{` bracket and uses `json.JSONDecoder().raw_decode` to grab the inner JSON.
*   **Source Heuristics**: If the model fails to extract the application source, the backend runs secondary regex checks on the sender email, subject, or body text to identify major portals (e.g. `LinkedIn`, `Indeed`, `Naukri`, `Glassdoor`).

### 3. Vector Embeddings (`generate_embedding`)
*   Calls `genai.embed_content()` with `model="models/gemini-embedding-001"`.
*   Specifies `task_type="retrieval_document"`.
*   Returns a 768-dimensional float list representing the semantic meaning of the text, stored directly in PostgreSQL for RAG matching.
