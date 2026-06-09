# CareerOS 🚀 (AI-Powered Job Application CRM)

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](CONTRIBUTING.md)

**CareerOS** (formerly *E-jobTracker Agent*) is an open-source, self-hosted, AI-powered Job Application CRM. It is designed to automate your job search pipeline by scanning your Gmail inbox for career-related emails, parsing application states with Google Gemini structured schemas, syncing records to Google Sheets, and providing a natural-language hybrid RAG chat assistant to query your search history.

---

## 🌟 Key Features

1. **Automatic Gmail Syncer**: Scans your inbox incrementally using read-only Google OAuth to find applications, interview updates, offers, and rejections.
2. **AI-Driven Data Extraction**: Uses structured schemas via Google Gemini to automatically extract company, job title, contact details, status, interview stages, location, salary, next action items, and application dates.
3. **Smart deduplication**: Groups email threads and status updates under normalized company-role applications.
4. **Interactive RAG Chat**: Ask natural language questions like:
   * *"Which companies did I apply to last week?"*
   * *"What interviews do I have scheduled for next week?"*
   * *"Draft an email requesting a status update for Stripe."*
5. **Glassmorphism Analytics Dashboard**: Track conversion rates (Applied $\rightarrow$ Interview $\rightarrow$ Offer), response rates, and application velocities with visual Chart.js dashboards.
6. **Follow-Up Assistant**: Automatically flags applications that have stagnated (no activity for 14+ days) and drafts contextual templates to follow up.
7. **Google Sheets Sync**: Keeps your applications mirrored in real-time in a dedicated spreadsheet.
8. **AI Resume Tailor & Optimizer**: Automatically rewrites your base resume HTML using Google Gemini to match target job descriptions (ATS keyword injection, mirror job titles, summary hooks) without fabricating facts. Serves tailored resumes as print-ready HTML pages.
9. **Bulk LinkedIn Scraper**: Asynchronously triggers and polls an Apify crawler task to extract job listings from a LinkedIn jobs search URL, filters them for relevance (AI/workflows), and bulk-tailors customized resumes in background Celery tasks.


---

## 🏗️ System Architecture

```
                                  +------------------+
                                  |   User Browser   |
                                  +--------+---------+
                                           | HTTP / WebSockets
                                           v
+------------------+              +--------+---------+
|    Gmail API     | <----------> |   FastAPI Server |
+------------------+              +---+--------+-----+
                                      |        |
+------------------+                  |        |  +--------------------+
| Google Sheets API| <----------------+        |  | Gemini Cloud API   |
+------------------+                           |  +---------+----------+
                                               v            |
+------------------+                      +----+-----+      |
|  Redis Broker    | <------------------> | Celery   | <----+
+------------------+                      | Worker   |
                                          +----+-----+
                                               |
                                               v
                                          +----+-----+
                                          |Postgres  |
                                          |(+vector) |
                                          +----------+
```

---

## 🔑 Setup Credentials & API Keys

To run CareerOS, you need credentials for Google OAuth (to access Gmail and Sheets) and Google AI Studio (for the Gemini API).

### 1. Google Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Click **Create API Key**.
3. Save the key; this will be set as `GEMINI_API_KEY` in your environment variables.

### 2. Google OAuth 2.0 Credentials (Gmail & Sheets)
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project named `CareerOS`.
3. In the left-hand menu, navigate to **APIs & Services** > **Library**. Search for and enable the following APIs:
   * **Gmail API**
   * **Google Sheets API**
4. Navigate to **APIs & Services** > **OAuth consent screen**:
   * Choose **External** user type.
   * Add your email and app support contact details.
   * Under **Scopes**, add `.../auth/gmail.readonly` and `.../auth/spreadsheets`. (For testing, you can add them manually, or use standard user email scopes first).
   * Under **Test users**, add the Gmail account(s) you intend to log in with.
5. Navigate to **APIs & Services** > **Credentials**:
   * Click **Create Credentials** > **OAuth client ID**.
   * Select **Web application** as the Application Type.
   * Add the following under **Authorized redirect URIs**:
     ```
     http://localhost:8000/api/v1/oauth/google/callback
     ```
   * Click **Create** and copy your **Client ID** and **Client Secret**.

---

## 🚀 Deployment Option A: Containerized (Docker Compose - Recommended)

The easiest way to run CareerOS is using Docker. It builds and launches PostgreSQL (with pgvector), Redis, the FastAPI backend, the Celery background worker, and serves the frontend.

### Prerequisites
* [Docker](https://docs.docker.com/get-docker/)
* [Docker Compose](https://docs.docker.com/compose/install/)

### Steps
1. Clone your repository:
   ```bash
   git clone https://github.com/jayanthkumar10/E-jobTracker-Agent.git
   cd E-jobTracker-Agent
   ```
2. Copy the Docker environment template:
   ```bash
   cp docker/.env.example docker/.env
   ```
3. Open `docker/.env` in an editor and fill in your keys:
   ```ini
   JWT_SECRET=generatethiswith-opensslrandhex32
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   GEMINI_API_KEY=your-gemini-api-key
   ```
4. Build and run the stack:
   ```bash
   docker-compose -f docker/docker-compose.yml up --build -d
   ```
5. Check that the containers are healthy:
   ```bash
   docker ps
   ```
   You should see four containers running: `careeros_db`, `careeros_redis`, `careeros_backend`, and `careeros_worker`.
6. Open your browser and navigate to:
   * **Frontend Portal**: `http://localhost:8000/index.html`
   * **FastAPI Interactive Docs (Swagger)**: `http://localhost:8000/docs`

---

## 🛠️ Deployment Option B: Bare-Metal Setup (Development Mode)

If you prefer to run services manually for code customization, follow these instructions.

### Prerequisites
* Python 3.11+
* [PostgreSQL](https://www.postgresql.org/download/) (configured with [pgvector](https://github.com/pgvector/pgvector) installed)
* [Redis](https://redis.io/download/) (for Celery broker tasks)

### 1. Database Setup
1. Create a PostgreSQL user and database:
   ```sql
   CREATE USER careeros_user WITH PASSWORD 'careeros_password';
   CREATE DATABASE careeros OWNER careeros_user;
   ```
2. Connect to the `careeros` database and create the pgvector extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

### 2. Redis Setup
Start the Redis server locally on default port `6379`.
* On Linux/macOS: `sudo service redis-server start` or `redis-server`
* On Windows: Start the Redis service or run it in WSL.

### 3. Backend Setup
1. Navigate to the backend folder:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create your local `.env` configuration:
   ```bash
   cp ../.env.example .env
   ```
   Update `.env` with your local Postgres URL (`postgresql://careeros_user:careeros_password@localhost:5432/careeros`), Redis URL, and your Google and Gemini API keys.
5. Run database migrations / initialize tables:
   ```bash
   python -c "from app.core.database import init_db; init_db()"
   ```
6. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### 4. Background Workers (Celery)
To parse emails and perform background syncs, start the Celery worker and the Celery periodic beat scheduler. Open a new terminal with the virtual environment activated:

* **Start the Celery worker**:
  ```bash
  celery -A app.workers.celery_app worker --loglevel=info
  ```
* **Start the Celery Beat Scheduler** (for recurring checks, open another terminal):
  ```bash
  celery -A app.workers.celery_app beat --loglevel=info
  ```

### 5. Frontend Portal Mounting
By default, the FastAPI application in `backend/app/main.py` is configured to mount the static files from `frontend/src` directly, meaning running the FastAPI app serves the frontend. 
Ensure the path mappings in `backend/app/main.py` point correctly to the local `/frontend/src` directory.
You can then access the app at `http://localhost:8000/index.html`.

---

## 📡 API Routing Reference

* `POST /api/v1/auth/register` - Create user login credentials.
* `POST /api/v1/auth/token` - Authenticate user credentials and return JWT token.
* `GET /api/v1/oauth/google/login` - Initiate Google OAuth sequence (exposes login URL).
* `GET /api/v1/oauth/google/callback` - Receive Google OAuth authorization code and exchange for refresh tokens.
* `POST /api/v1/gmail/sync` - Manually trigger Gmail sync background tasks.
* `GET /api/v1/applications` - CRUD list of all parsed applications.
* `POST /api/v1/chat` - Interact with the hybrid RAG conversational AI assistant.
* `GET /api/v1/gmail/followups` - List stalled application recommendations and drafted email contents.
* `POST /api/v1/sheets/sync` - Mirror applications data manually to active Google Sheet spreads.
* `POST /api/v1/resumes/tailor-single` - Instantly tailor a resume HTML for a single job description.
* `POST /api/v1/resumes/tailor-bulk` - Launch background Celery scraper to bulk tailor resumes from a LinkedIn search URL.
* `GET /api/v1/resumes/history` - Retrieve list of past resume tailoring runs.
* `GET /api/v1/resumes/base` - Get user's base resume HTML template.
* `PUT /api/v1/resumes/base` - Update user's base resume HTML template.


---

## 📄 License

CareerOS is open-source software distributed under the [MIT License](LICENSE).
