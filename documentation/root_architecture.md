# CareerOS System Architecture & Connection Diagram

This document explains how the individual components of the CareerOS (E-jobTracker Agent) codebase interact, how data flows through the system, and how the frontend, backend database, Celery workers, and AI services are connected.

---

## 1. Core Architecture Blueprint

CareerOS is split into three main layers:
1.  **Frontend Clients (SPA)**: Renders the interface, collects user actions, and communicates with the FastAPI server.
2.  **FastAPI Backend (API & Routing)**: Handles authentication, exposes database operations, and initiates background tasks.
3.  **Celery & Redis Worker Layer**: Executes long-running tasks asynchronously (polling Gmail, scanning emails, generating follow-ups, and writing to Google Sheets).

```
[ Frontend SPA (HTML/JS) ]
         │
         ▼ (HTTP API Requests / JWT Bearer Auth)
[ FastAPI Backend (main.py) ]
   ├── [ Database Session ] ────> [ PostgreSQL (pgvector) ]
   └── [ Celery Client ] ────────> [ Redis Broker ] ──> [ Celery Worker ]
                                                              │
                                                              ▼
                                                 [ Google & Gemini APIs ]
```

---

## 2. Component Directory Structure & Map

Here is the directory map of the codebase. Each file has a corresponding detailed explanation file inside this `documentation/` directory.

### Core Backend Setup
*   [config.py](file:///c:/E-jobTracker%20Agent/backend/app/core/config.py): Stores environment settings (API keys, DB URLs, secrets).
*   [database.py](file:///c:/E-jobTracker%20Agent/backend/app/core/database.py): Manages connections to PostgreSQL and registers the `pgvector` extension.
*   [security.py](file:///c:/E-jobTracker%20Agent/backend/app/core/security.py): Handles passwords hashing and JWT authentication token creation.

### Database Models (ORM)
*   [user.py](file:///c:/E-jobTracker%20Agent/backend/app/models/user.py): Defines User credentials and Google credentials.
*   [application.py](file:///c:/E-jobTracker%20Agent/backend/app/models/application.py): Defines Applications, Timeline Events, and Google Sheet config.
*   [email.py](file:///c:/E-jobTracker%20Agent/backend/app/models/email.py): Stores email records and their 768-dimensional vectors.

### Asynchronous Workers
*   [celery_app.py](file:///c:/E-jobTracker%20Agent/backend/app/workers/celery_app.py): Sets up Celery queueing.
*   [tasks.py](file:///c:/E-jobTracker%20Agent/backend/app/workers/tasks.py): Houses core background tasks (Gmail fetch, Sheets synchronization).

### Business Logic Services
*   [ai_engine.py](file:///c:/E-jobTracker%20Agent/backend/app/services/ai_engine.py): Direct wrapper for Gemma 4 structured JSON extraction and embedding generation.
*   [email_parser.py](file:///c:/E-jobTracker%20Agent/backend/app/services/email_parser.py): Cleans dirty email strings.
*   [deduplicator.py](file:///c:/E-jobTracker%20Agent/backend/app/services/deduplicator.py): Manages duplicates and logs status changes.
*   [sheets_sync.py](file:///c:/E-jobTracker%20Agent/backend/app/services/sheets_sync.py): Overwrites Google Sheets spreadsheet data.
*   [follow_up.py](file:///c:/E-jobTracker%20Agent/backend/app/services/follow_up.py): Drafts follow-up suggestions for cold applications.
*   [chat_rag.py](file:///c:/E-jobTracker%20Agent/backend/app/services/chat_rag.py): Hybrid retrieval system (SQL stats + email similarity search).

---

## 3. End-to-End Dynamic Connections

### 1. User Registration & Auth Connection
*   **Frontend**: User enters credentials in `index.html`. `api.js` submits a POST request to `/api/v1/auth/register`.
*   **Backend Routing**: `backend/app/api/auth.py` receives request, calls functions in `backend/app/core/security.py` to encrypt passwords, writes to `backend/app/models/user.py` tables, and returns a signed JWT.
*   **State**: The token is saved in `localStorage` in the browser.

### 2. The Gmail Parsing Connection
*   **Trigger**: Celery Beat launches `poll_gmail_inboxes` in `backend/app/workers/tasks.py`.
*   **Retrieval**: The task fetches the refresh token from `backend/app/models/user.py`, refreshes it using `backend/app/services/google_auth_svc.py`, and queries Gmail.
*   **AI Engine**: The email body is cleaned via `backend/app/services/email_parser.py`, and fed into `backend/app/services/ai_engine.py` which retrieves structured extraction fields.
*   **Write**: The deduplicator in `backend/app/services/deduplicator.py` inserts rows into `backend/app/models/application.py`. The embeddings service generates query vectors and saves them to `backend/app/models/email.py`.

### 3. The Chat (RAG) Connection
*   **Frontend**: User submits a message in the chat box on `dashboard.html`.
*   **Backend Controller**: `backend/app/api/chat.py` receives the query and calls `backend/app/services/chat_rag.py`.
*   **Hybrid Search**:
    1. It counts entries in the relational `applications` table.
    2. It embeds the query via `ai_engine.py` and queries the `emails` table using the `pgvector` cosine distance operator `<=>`.
    3. It feeds both contexts to Gemma 4, filters out the `<reply>` block, and responds to the frontend.
