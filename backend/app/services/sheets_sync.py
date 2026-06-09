import httpx
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.models.application import Application, SheetsSyncConfig
from app.models.user import OAuthToken
from app.services.google_auth_svc import GoogleAuthService

logger = logging.getLogger(__name__)

class SheetsSyncService:
    @classmethod
    def sync_to_sheet(cls, db: Session, user_id: str) -> str:
        """
        Executes a mirroring sync.
        Fetches all applications for the user, clears the sheet, and writes the latest rows.
        """
        # Find Sheets sync config
        sync_config = db.query(SheetsSyncConfig).filter(
            SheetsSyncConfig.user_id == user_id,
            SheetsSyncConfig.is_enabled == True
        ).first()
        
        if not sync_config:
            return "Sync skipped: Google Sheets Sync is not configured or is disabled."

        # Find Google OAuth token
        token = db.query(OAuthToken).filter(
            OAuthToken.user_id == user_id,
            OAuthToken.provider == "google"
        ).first()
        
        if not token:
            return "Sync skipped: User Google OAuth credentials not found."

        try:
            # Refresh and retrieve a valid access token
            access_token = GoogleAuthService.get_valid_token(db, token)
        except Exception as e:
            logger.error(f"Failed to refresh token for sheet sync: {str(e)}")
            return f"Sync aborted: Auth refresh failed."

        # Fetch applications
        applications = db.query(Application).filter(Application.user_id == user_id).order_by(Application.updated_at.desc()).all()
        
        headers = [
            "Company Name", "Job Title", "Status", "Location", 
            "Salary Range", "Recruiter Name", "Recruiter Email", "Last Updated"
        ]
        
        rows = [headers]
        for app in applications:
            rows.append([
                app.company_name or "",
                app.job_title or "",
                app.status or "",
                app.location or "",
                app.salary_range or "",
                app.recruiter_name or "",
                app.recruiter_email or "",
                app.updated_at.strftime("%Y-%m-%d %H:%M:%S") if app.updated_at else ""
            ])

        # Prepare sheets API details
        spreadsheet_id = sync_config.spreadsheet_id
        sheet_name = sync_config.sheet_name or "Applications"
        clear_url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{sheet_name}!A1:Z:clear"
        update_url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{sheet_name}!A1?valueInputOption=USER_ENTERED"
        
        auth_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        with httpx.Client(timeout=30.0) as client:
            # 1. Clear existing sheet
            clear_res = client.post(clear_url, headers=auth_headers)
            if clear_res.status_code != 200:
                logger.error(f"Failed to clear Google Sheet: {clear_res.text}")
                return f"Sync failed on clear: {clear_res.text}"

            # 2. Update with fresh values
            body = {
                "range": f"{sheet_name}!A1",
                "majorDimension": "ROWS",
                "values": rows
            }
            update_res = client.put(update_url, headers=auth_headers, json=body)
            if update_res.status_code != 200:
                logger.error(f"Failed to update Google Sheet: {update_res.text}")
                return f"Sync failed on update: {update_res.text}"

        # Update sync timestamp
        sync_config.last_synced_at = datetime.utcnow()
        db.commit()
        
        return "Sync completed successfully."
