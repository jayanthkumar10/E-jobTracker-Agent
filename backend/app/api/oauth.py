import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional

from app.core.config import settings
from app.core.database import get_db
from app.api import deps
from app.models.user import User, OAuthToken

router = APIRouter()

SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets" # For exporting to Google Sheets!
]

@router.get("/google/login")
def google_login(
    state: str, # Pass user jwt token as state to associate Google account with logged-in user
    db: Session = Depends(get_db)
):
    """
    Constructs and redirects to Google OAuth consent page.
    Requires user JWT token passed as state.
    """
    # Verify the state is a valid JWT before initiating
    user_id = deps.security.decode_access_token(state)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid session state token")

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",  # Crucial to obtain a refresh token for background sync
        "prompt": "consent",       # Force consent screen to guarantee refresh token is returned
        "state": state
    }
    
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return RedirectResponse(auth_url)


@router.get("/google/callback")
async def google_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    OAuth Callback handler. Exhanges Google code for access and refresh tokens.
    Saves credentials into the database linked to the authenticated user.
    """
    if error:
        raise HTTPException(status_code=400, detail=f"Google OAuth Error: {error}")
    
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing required parameters code or state")

    # Decode state token to verify and identify user
    user_id = deps.security.decode_access_token(state)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid state token parameter")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Exchange authorization code for token
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=payload)
        
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange code: {response.text}"
        )
        
    token_data = response.json()
    
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 3600)
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    
    # Store or update the token in the DB
    oauth_token = db.query(OAuthToken).filter(
        OAuthToken.user_id == user.id, 
        OAuthToken.provider == "google"
    ).first()
    
    if not oauth_token:
        oauth_token = OAuthToken(
            user_id=user.id,
            provider="google",
            access_token=access_token,
            refresh_token=refresh_token,
            token_uri=token_url,
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=SCOPES,
            expires_at=expires_at
        )
        db.add(oauth_token)
    else:
        oauth_token.access_token = access_token
        # Update refresh token only if new one is supplied
        if refresh_token:
            oauth_token.refresh_token = refresh_token
        oauth_token.expires_at = expires_at
        oauth_token.updated_at = datetime.utcnow()
        
    db.commit()
    
    # Redirect user back to UI settings or dashboard with a success parameter
    # Usually frontend is served on port 8000 (FastAPI static) or port 3000 during dev
    # We will redirect to the root index.html with a query param
    return RedirectResponse(url="/dashboard.html?auth=success")
