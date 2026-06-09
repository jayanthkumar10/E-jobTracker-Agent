# Documentation: `backend/app/workers/tasks.py`

## Overview
This file defines the background Celery worker tasks that handle asynchronous flows. This keeps the FastAPI API threads responsive by offloading heavy integrations (Gmail fetching, AI extractions, Google Sheets synchronization, and daily follow-up scans).

---

## Core Background Tasks

### 1. `poll_gmail_inboxes`
*   **Trigger**: Periodic task run every 15 minutes by Celery Beat, or triggered manually by a user click.
*   **Logic**:
    1.  Fetches all active users with Gmail accounts connected.
    2.  Obtains and refreshes the Google Access Token via `GoogleAuthService`.
    3.  Queries Gmail API for unread messages.
    4.  Cleans each message text and passes it to the AI Extraction Engine.
    5.  Runs the deduplicator engine to save application entries or log timeline changes.
    6.  Marks emails as read to prevent reprocessing.

### 2. `sync_user_sheets_task`
*   **Trigger**: Triggered automatically on database additions/modifications or manually by the user.
*   **Logic**:
    1.  Fetches sheets configurations (spreadsheet ID, active sheet name) for the user.
    2.  Gathers all active user applications from PostgreSQL.
    3.  Formats records into 2D row lists.
    4.  Establishes OAuth connection to the Google Sheets API and executes a batch update overwrite of the target spreadsheet.

### 3. `generate_followup_suggestions`
*   **Trigger**: Daily scheduler cron job.
*   **Logic**:
    1.  Identifies applications that have remained in the `APPLIED` or `SCREENING` stages for 14+ days.
    2.  Triggers Gemini to write custom email templates based on the company, role, recruiter name, and timeline date.
    3.  Caches the generated suggestions in the database to display on the frontend follow-up grid.
