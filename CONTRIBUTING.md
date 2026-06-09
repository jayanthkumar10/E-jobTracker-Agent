# Contributing to CareerOS

Thank you for your interest in contributing to CareerOS! We welcome contributions from developers, recruiters, job seekers, and career coaches.

## Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local, non-container development)
- A Google Cloud Developer Account (to enable Gmail/Sheets OAuth APIs)

### Local Setup with Docker (Recommended)
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/career-os.git
   cd career-os
   ```
2. Copy the environment template and fill in your keys (Gemini API key, Google OAuth Client credentials):
   ```bash
   cp .env.example .env
   ```
3. Run the development docker compose:
   ```bash
   docker-compose -f docker/docker-compose.yml up --build
   ```
4. Access the API Swagger documentation at `http://localhost:8000/docs` and the main UI at `http://localhost:8000/index.html`.

## Development Guidelines

### Folder Structure
*   `/backend`: FastAPI routing, SQLAlchemy schemas, Celery polling synchronizers, RAG engine calculations.
*   `/frontend`: Tailwind CSS designs, vanilla JavaScript SPA controllers, and HTML views.
*   `/docker`: Container profiles.

### Making Changes
1. Fork the repository and create your feature branch:
   ```bash
   git checkout -b feature/amazing-new-feature
   ```
2. Make your code modifications. Preserve inline documentation and respect PEP-8 formatting.
3. Write simple unit tests in `backend/tests/` to verify your changes.
4. Commit your changes:
   ```bash
   git commit -m "feat: add amazing new feature support"
   ```
5. Push to the branch and open a Pull Request!
