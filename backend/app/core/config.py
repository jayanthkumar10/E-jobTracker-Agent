import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "CareerOS"
    API_V1_STR: str = "/api/v1"
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://careeros_user:careeros_password@localhost:5432/careeros"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT Security settings
    JWT_SECRET: str = "supersecretjwttokenkey1234567890"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # Google OAuth credentials
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/oauth/google/callback"
    
    # Gemini API Key
    GEMINI_API_KEY: str = ""
    
    # Apify API Token (for LinkedIn Scraper)
    APIFY_API_TOKEN: str = ""

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
