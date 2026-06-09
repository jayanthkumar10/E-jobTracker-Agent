# Documentation: `backend/app/services/deduplicator.py`

## Overview
The `DeduplicatorService` class acts as the validation filter when logging job applications. It prevents duplicate entries for the same company and job title, and manages the timeline logs by creating state transition history records.

---

## Detailed Code Walkthrough

### 1. Match Checking
When a parsed email yields structured application fields, the deduplicator performs a search against the database:
*   Queries the `Application` table matching the user ID, company name (casing-insensitive), and job role title.

### 2. Processing logic (`process_application_update`)
*   **Case A: New Application**:
    *   If no matching company-role record exists, it inserts a new `Application` row with status `APPLIED` (or whatever the parsed status was).
    *   Appends an initial event in the `ApplicationEvent` timeline logging `"Application tracked automatically from email."`.
*   **Case B: Existing Application**:
    *   If a matching application exists, it compares the current status with the parsed status.
    *   *If the status matches*: It updates fields like work mode, salary, or location if the newly parsed email has more detailed data.
    *   *If the status differs* (e.g. from `APPLIED` to `INTERVIEWING` or `REJECTED`):
        *   Updates the parent application status.
        *   Inserts a new `ApplicationEvent` row logging the status transition (e.g. `"Updated: SCREENING from email."`) with notes referencing the parsed details.
*   **Google Sheets Trigger**: It initiates a background celery task to sync the updated database state with Google Sheets.
