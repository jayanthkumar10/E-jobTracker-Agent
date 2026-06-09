from datetime import datetime, timedelta
import httpx
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import OAuthToken

class GoogleAuthService:
    @staticmethod
    def get_valid_token(db: Session, token: OAuthToken) -> str:
        """
        Checks if the stored access token is expired.
        If expired, uses the refresh token to get a new one, updates the DB, and returns it.
        """
        # If token expires in less than 5 minutes, refresh it
        token_expires = token.expires_at.replace(tzinfo=None) if token.expires_at else None
        if token_expires and datetime.utcnow() < (token_expires - timedelta(minutes=5)):
            return token.access_token

        # Exchange refresh token for new access token
        token_url = token.token_uri or "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": settings.GOOGLE_CLIENT_ID or token.client_id,
            "client_secret": settings.GOOGLE_CLIENT_SECRET or token.client_secret,
            "refresh_token": token.refresh_token,
            "grant_type": "refresh_token"
        }

        with httpx.Client() as client:
            response = client.post(token_url, data=payload)
            
        if response.status_code != 200:
            # Mark token as invalid if refresh fails (e.g., user revoked permissions)
            # This will alert the UI to show reconnect warning
            token.expires_at = datetime.utcnow() - timedelta(days=1)
            db.commit()
            raise Exception(f"Failed to refresh Google OAuth token: {response.text}")
            
        token_data = response.json()
        
        token.access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 3600)
        token.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        token.updated_at = datetime.utcnow()
        
        db.commit()
        return token.access_token
