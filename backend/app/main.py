from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.core.database import init_db
from app.api.auth import router as auth_router
from app.api.oauth import router as oauth_router
from app.api.applications import router as applications_router
from app.api.gmail import router as gmail_router
from app.api.chat import router as chat_router
from app.api.sheets import router as sheets_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database schemas and extensions on start
    init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for dev/local self-hosting
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API endpoints
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(oauth_router, prefix=f"{settings.API_V1_STR}/oauth", tags=["oauth"])
app.include_router(applications_router, prefix=f"{settings.API_V1_STR}/applications", tags=["applications"])
app.include_router(gmail_router, prefix=f"{settings.API_V1_STR}/gmail", tags=["gmail"])
app.include_router(chat_router, prefix=f"{settings.API_V1_STR}/chat", tags=["chat"])
app.include_router(sheets_router, prefix=f"{settings.API_V1_STR}/sync/sheets", tags=["sheets"])

# Root and health-check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.PROJECT_NAME}

# Mount static frontend files if directory exists
container_frontend_path = "/frontend/src"
local_frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/src"))
frontend_path = container_frontend_path if os.path.exists(container_frontend_path) else local_frontend_path

if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    # Fallback if path doesn't exist yet (during early initialization or building container)
    @app.get("/")
    def index_fallback():
        return {"message": "CareerOS backend running. Frontend static directory not initialized."}
