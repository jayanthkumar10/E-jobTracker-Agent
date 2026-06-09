# Documentation: `backend/app/api/applications.py`

## Overview
This file handles the API controllers for all Job Application interactions. It defines endpoints for listing applications, retrieving details, manually updating application details, and generating analytical KPIs.

---

## Detailed Endpoints Walkthrough

### 1. `list_applications` (`GET /api/v1/applications`)
*   Fetches all applications matching the user ID.
*   **Ordering**: Enforces `.order_by(Application.created_at.desc())` to return applications in **latest to oldest** order.
*   Serializes records to JSON.

### 2. `get_analytics_summary` (`GET /api/v1/applications/analytics/summary`)
Calculates values for the overview panel metrics:
*   Counts total applications, active interviews, offers, and rejections.
*   **Response Rate**: Computes `(non-applied applications / total applications) * 100`.
*   **Journey Tracking**: Calculates `journey_days_count` relative to a set start date threshold (`June 10, 2025`).
*   **Streak Calculation**: Computes the daily consecutive applied streak by querying dates from applications and traversing backward.
*   **Average Interview Response Days**: Measures average duration between application creation and first scheduled interview.

### 3. `get_funnel_analytics` (`GET /api/v1/applications/analytics/funnel`)
*   Counts numbers matching each phase state: `Applied`, `Screening`, `Interviewing`, and `Offered` to compile conversion statistics for Chart.js.

### 4. `update_application` (`PUT /api/v1/applications/{app_id}`)
*   Processes manual updates from the user (notes editing, status changes, contact detail modifications).
*   **Timeline Logs**: If the status is altered manually, the endpoint inserts a new `ApplicationEvent` log, preserving history.
*   **Sheets Mirroring**: Automatically triggers the background celery task to sync updates to Google Sheets.
