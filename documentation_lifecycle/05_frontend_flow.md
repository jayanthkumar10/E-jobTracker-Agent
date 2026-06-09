# SDLC Phase 4: Frontend Flow & User Experience

This document details how the Glassmorphism SPA layouts, API fetch wrappers, client-side status filtering, and chat interfaces are implemented and connected.

---

## 1. Single Page Interface: `frontend/src/dashboard.html`

### Why this code was written:
*   Builds a premium, modern dashboard utilizing custom CSS themes, Chart.js funnel plots, side navigation bars, modal drawers, and chatbot feeds.

### Line-by-Line Breakdown & Inter-Component Connections:
*   `<select id="filter-status" onchange="filterApplications()">`
    *   *Why*: Dropdown menu containing statuses (`APPLIED`, `SCREENING`, `INTERVIEWING`, etc.).
    *   *Connection*: Triggers JavaScript's `filterApplications` logic in [app.js](file:///c:/E-jobTracker%20Agent/frontend/src/js/app.js) whenever the selection changes.
*   `<div id="chat-messages" ...>`
    *   *Why*: The scrollable container where RAG chat bubbles are appended.
    *   *Connection*: Controlled by DOM injectors inside the `appendChatMessage` JavaScript function.

---

## 2. Client Controller: `frontend/src/js/app.js`

### Why this code was written:
*   Binds user actions, queries backend REST endpoints, and manages frontend rendering states.

### Line-by-Line Breakdown & Inter-Component Connections:
*   `applications = await appsAPI.list();`
    *   *Why*: Loads tracked applications from the database.
    *   *Connection*: Calls `appsAPI.list()` from `api.js` to query backend REST APIs, receiving records already sorted from latest to oldest.
*   `function filterApplications() { ... }`
    *   *Why*: Filters the dashboard table client-side.
    *   *Connection*: Grabs values from `#search-apps` input and `#filter-status` dropdown, running filter loops over the memory cache before calling `renderApplicationsTable()`.
*   `chatForm.addEventListener("submit", async (e) => { ... })`
    *   *Why*: Handles conversational inquiries.
    *   *Connection*: Prevents form reloads, clears inputs, invokes `chatAPI.sendMessage()` via `api.js`, spawns animated bouncing typing states, and parses response text into user chat bubbles.
