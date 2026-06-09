# Software Development Life Cycle (SDLC) Overview: CareerOS

This document outlines the software development life cycle (SDLC) approach taken to build CareerOS (E-jobTracker Agent) from scratch, detailing the requirements, database design, architecture, and deployment stages.

---

## 1. Phase 1: Requirements Analysis & Specification
The project was initiated to solve a common user pain point: **manual overhead in tracking job applications**.

### Core Functional Requirements:
1.  **Passive Tracking**: The system must scan the user's Gmail inbox for application confirmations, interview invites, and rejections.
2.  **Entity Extraction**: It must parse unstructured email content to extract structured entities (company, role, recruiter, salary, location, work mode).
3.  **Timeline & Event Logging**: Status changes must update the parent application card and append historical timeline event logs.
4.  **Google Sheets Integration**: Updates must automatically sync to a user-configured Google Sheet to maintain external backups.
5.  **Stagnant Warnings**: Highlight applications with no activity for 14+ days and generate draft follow-up templates using Gen AI.
6.  **Conversational RAG Chat**: Allow users to query their relational dashboard stats and vector-embedded emails.

### Non-Functional Requirements:
*   **Performance**: Background polling must not block API request threads.
*   **Security**: Password hashing via bcrypt, user token validation via JWT, and secure handling of Google OAuth2 credentials.
*   **Vector Search**: Cosine distance vector math for querying email transcripts.

---

## 2. Phase 2: System Architecture Design
To satisfy performance requirements (background polling, sheets syncing, and AI parsing), a **microservice architecture** was selected:

```
                          ┌───────────────────────┐
                          │     Web Browser       │
                          │   (HTML/CSS/JS/SPA)   │
                          └───────────┬───────────┘
                                      │
                                      │ HTTP Request / JWT Token
                                      ▼
                        ┌───────────────────────────┐
                        │      FastAPI Backend      │
                        └─────────────┬─────────────┘
                                      │
           ┌──────────────────────────┴──────────────────────────┐
           ▼                                                     ▼
┌───────────────────────┐                               ┌───────────────────────┐
│  PostgreSQL Database  │                               │     Redis Broker      │
│     (pgvector)        │                               └───────────┬───────────┘
└───────────────────────┘                                           │
                                                                    ▼
                                                        ┌───────────────────────┐
                                                        │     Celery Worker     │
                                                        │   (Gmail/Sheets/AI)   │
                                                        └───────────────────────┘
```

### Key Integrations:
*   **Redis**: Acts as the broker and task queue for Celery.
*   **Celery Worker**: Performs asynchronous email scans and sheets syncs, isolating heavy network IO from FastAPIs event loop.
*   **pgvector PostgreSQL**: Extends SQL database with vector columns for storing embeddings, allowing hybrid relational-vector queries.

---

## 3. Phase 3: Database & ORM Modeling
The data schema is structured in [database.py](file:///c:/E-jobTracker%20Agent/backend/app/core/database.py) and [models/](file:///c:/E-jobTracker%20Agent/backend/app/models/):
*   A `user` can have multiple `applications`.
*   An `application` contains details (company, role) and has a one-to-many relationship with `application_events` (timeline history) and `interviews`.
*   An `email` belongs to a `user` and optional `application`, containing a `vector` embedding column.

---

## 4. Phase 4: Implementation (Coding Phase)
Refer to the following files in this directory for line-by-line coding details and component integrations:
*   [02_backend_core_and_models.md](file:///c:/E-jobTracker%20Agent/documentation_lifecycle/02_backend_core_and_models.md)
*   [03_backend_logic_and_api.md](file:///c:/E-jobTracker%20Agent/documentation_lifecycle/03_backend_logic_and_api.md)
*   [04_celery_and_tasks.md](file:///c:/E-jobTracker%20Agent/documentation_lifecycle/04_celery_and_tasks.md)
*   [05_frontend_flow.md](file:///c:/E-jobTracker%20Agent/documentation_lifecycle/05_frontend_flow.md)
