# SDLC Phase 4: Celery Background Tasks & Scheduling

This document covers how asynchronous workers, messaging brokers, and background sync processes are configured and connected in CareerOS.

---

## 1. Task Queue Config: `backend/app/workers/celery_app.py`

### Why this code was written:
*   Initializes the Celery task queue, using Redis as the message broker.

### Line-by-Line Breakdown & Inter-Component Connections:
*   `celery_app = Celery("tasks", broker=settings.REDIS_URL, backend=settings.REDIS_URL)`
    *   *Why*: Links Celery to the Redis broker URL for task tracking and results storage.
*   `celery_app.conf.beat_schedule = { ... }`
    *   *Why*: Registers periodic scheduler times.
    *   *Connection*: Connects `poll_gmail_inboxes` (every 15 minutes) and `generate_followup_suggestions` (daily) tasks automatically.

---

## 2. Worker Core Tasks: `backend/app/workers/tasks.py`

### Why this code was written:
*   Contains the actual logic executed asynchronously by Celery workers to keep FastAPI API execution times low.

### Line-by-Line Breakdown & Inter-Component Connections:
*   `@celery_app.task(name="poll_gmail_inboxes")`
    *   *Why*: Scans linked user emails in the background.
    *   *Connection*: Calls `GoogleAuthService.refresh_token` to get a fresh API token, calls `email_parser.py` to strip email contents, and triggers `DeduplicatorService` to save records.
*   `@celery_app.task(name="sync_user_sheets_task")`
    *   *Why*: Syncs the database applications list with Google Sheets.
    *   *Connection*: Triggered instantly inside [applications.py](file:///c:/E-jobTracker%20Agent/backend/app/api/applications.py) endpoint whenever a user updates a card or modifies details.
*   `@celery_app.task(name="generate_followup_suggestions")`
    *   *Why*: Daily cron job that drafts follow-up templates for stagnant applications.
    *   *Connection*: Writes drafts to the `Application` record, which are fetched and displayed in the frontend follow-ups panel on the dashboard.
