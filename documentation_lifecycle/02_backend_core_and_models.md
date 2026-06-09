# SDLC Phase 4: Core Backend Configuration & Database Models

This document breaks down the core setup and data layers of CareerOS, explaining key lines of code and how they connect across modules.

---

## 1. Configurations: `backend/app/core/config.py`

### Why this code was written:
*   Standardizes environmental variable parsing via `pydantic-settings`.
*   Connects database URLs, JWT encryption secrets, and API credentials dynamically.

### Core Line-by-Line Breakdown & Connections:
*   `class Settings(BaseSettings):`
    *   *Why*: Loads environment keys safely with automatic type validation.
*   `DATABASE_URL: str = "postgresql://..."`
    *   *Why*: Defines where SQLAlchemy hooks its DB connection engine pool.
    *   *Connection*: Used directly in [database.py](file:///c:/E-jobTracker%20Agent/backend/app/core/database.py) to set up the session connection pool.
*   `GEMINI_API_KEY: Optional[str] = None`
    *   *Why*: Stores the API studio credentials.
    *   *Connection*: Loaded by [ai_engine.py](file:///c:/E-jobTracker%20Agent/backend/app/services/ai_engine.py) to initialize GenerativeModel targets.

---

## 2. Database Connection Engine: `backend/app/core/database.py`

### Why this code was written:
*   Creates PostgreSQL session connections and registers the `pgvector` extension to allow vector distance math query compilation.

### Core Line-by-Line Breakdown & Connections:
*   `engine = create_engine(settings.DATABASE_URL)`
    *   *Why*: Initializes connection streams to Postgres.
*   `SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)`
    *   *Why*: Spawns thread-safe, transactional database session handlers.
    *   *Connection*: Imported by [deps.py](file:///c:/E-jobTracker%20Agent/backend/app/api/deps.py) to yield database sessions to API endpoints, and by Celery tasks to commit data logs.
*   `def init_db():`
    *   *Why*: Executes migrations and registers vector column extensions on application startup.
    *   *Connection*: Called inside the async startup lifecycle handler in [main.py](file:///c:/E-jobTracker%20Agent/backend/app/main.py).

---

## 3. Database Schema Models: `backend/app/models/`

### 1. User Model (`models/user.py`)
*   `google_access_token` and `google_refresh_token`:
    *   *Why*: Stores Google Auth details required to query Gmail and write to Sheets.
    *   *Connection*: Read by Celery workers in [tasks.py](file:///c:/E-jobTracker%20Agent/backend/app/workers/tasks.py) when refreshing tokens via `GoogleAuthService`.

### 2. Application Model (`models/application.py`)
*   `status = Column(String, default="APPLIED")`:
    *   *Why*: Stores the status tracking value.
    *   *Connection*: Read by `app.js` to assign colors to badge styles, and checked by `chat_rag.py` to evaluate KPIs.
*   `class Interview(Base):`:
    *   *Why*: Maps interview entries (meeting link, schedule dates) to parent applications.
    *   *Connection*: Queried by `get_analytics_summary()` endpoint inside `applications.py` to report interview counts.

### 3. Email Model (`models/email.py`)
*   `from pgvector.sqlalchemy import Vector`
*   `embedding = Column(Vector(768))`
    *   *Why*: Defines a 768-dimensional database vector column to hold semantic embeddings of email transcripts.
    *   *Connection*: Read by `chat_rag.py` to compile semantic matches via cosine distance math operators.
