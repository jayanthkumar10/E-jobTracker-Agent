# Documentation: `frontend/src/js/app.js`

## Overview
`app.js` is the central JavaScript engine orchestrating all user events, animations, REST integrations, and UI state updates on the CareerOS main dashboard.

---

## Key Core Architectures

### 1. Initialization (`DOMContentLoaded`)
On DOM ready:
*   Confirms a valid JWT authorization token exists in `localStorage`. Redirects to `index.html` if missing.
*   Calls Lucide APIs to instantiate SVGs.
*   Initializes OAuth badges, updates analytic counters, and fetches initial lists.

### 2. Search & Filtering (`filterApplications`)
Implements client-side list filtering without triggering redundant database hits:
*   Listens to keystrokes in `#search-apps` (keyword queries).
*   Listens to changes in `#filter-status` select dropdown.
*   Matches company name, job role, and status values, updating the table interface dynamically.

### 3. Funnel Visualization (`renderFunnelChart`)
*   Sets up a Chart.js vertical bar plot comparing `Applied` and `Interviewing` metrics.
*   Renders with colors and smooth borders matching the slate-dark-mode aesthetic.

### 4. Interactive Chat submits (`chatForm.submit`)
*   Captures chat form inputs.
*   Appends user message bubbles instantly to the chat feed.
*   Spawns animated typing placeholders.
*   Sends queries to the FastAPI RAG backend, removes placeholders, formats response text, and renders markdown elements.
