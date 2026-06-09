# SDLC Phase 4: Business Logic Services & API Routes

This document details how CareerOS's business logic services work, how lines of code connect across APIs, and how AI responses are cleaned.

---

## 1. RAG Conversation: `backend/app/services/chat_rag.py`

### Why this code was written:
*   Implements a hybrid retrieval-augmented generation (RAG) system to answer user queries using both database statistics and raw email vectors.

### Line-by-Line Breakdown & Inter-Component Connections:
*   `apps = db.query(Application).filter(Application.user_id == user_id).all()`
    *   *Why*: Assembles structured application facts (company, status, salary).
    *   *Connection*: Creates a clean Markdown string injected into `user_content` context.
*   `query_embedding = AIEngineService.generate_embedding(question)`
    *   *Why*: Converts user questions into vectors.
    *   *Connection*: Feeds the query vector to the `cosine_distance` query to look up emails.
*   `matching_emails = db.query(Email)...order_by(Email.embedding.cosine_distance(query_embedding)).limit(5).all()`
    *   *Why*: Pulls the top 5 most similar parsed emails.
*   `text_response = text_response.rsplit("<reply>", 1)[1] ... split("</reply>", 1)[0]`
    *   *Why*: Grabs content inside the final `<reply>` XML block.
    *   *Connection*: Cleans up LLM thoughts so only clean conversational responses are returned to `chatForm.submit` event handlers in [app.js](file:///c:/E-jobTracker%20Agent/frontend/src/js/app.js).

---

## 2. Structured AI Parsing: `backend/app/services/ai_engine.py`

### Why this code was written:
*   Queries Gemini to extract structured JSON data from email strings.

### Line-by-Line Breakdown & Inter-Component Connections:
*   `model = cls.get_model()`
    *   *Why*: Instantiates the Gemma 4 LLM model.
*   `response = model.generate_content(prompt, generation_config=genai.GenerationConfig(response_mime_type="application/json", ...))`
    *   *Why*: Forces Gemma to output structured JSON matching the database schema.
    *   *Connection*: Raw text is parsed via JSON Decoders and passed directly to `deduplicator.py` to write/update records in the Database.

---

## 3. API Routing: `backend/app/api/`

### 1. OAuth Redirect Handler (`api/oauth.py`)
*   `@router.get("/google/login")`
    *   *Why*: Directs users to Google's sign-in screen to authorize email scanning scope permissions.
*   `@router.get("/google/callback")`
    *   *Why*: Catches the OAuth state codes, exchanges them for access/refresh tokens, and commits them to the `User` DB row.
    *   *Connection*: Sets `google_refresh_token` in `user.py` which Celery Beat uses for periodic email scanning.

### 2. Applications Controller (`api/applications.py`)
*   `apps = db.query(Application).filter(Application.user_id == current_user.id).order_by(Application.created_at.desc()).all()`
    *   *Why*: Fetches records sorted by creation date descending.
    *   *Connection*: Feeds sorted list to the `applications` array rendered by `app.js` table managers.
*   `avg_days_to_interview = round(sum(days_list) / len(days_list), 1) if days_list else 0.0`
    *   *Why*: Calculates metrics showing average interview feedback wait times.
    *   *Connection*: Populated in the `#stat-avg-days` analytics cards in `dashboard.html`.
