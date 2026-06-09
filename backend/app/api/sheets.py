from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.api import deps
from app.models.application import SheetsSyncConfig
from app.models.user import User
from app.workers.tasks import sync_user_sheets_task

router = APIRouter()

class SheetsConfigRequest(BaseModel):
    spreadsheet_id: str
    sheet_name: Optional[str] = "Applications"
    is_enabled: Optional[bool] = True

@router.get("")
def get_sheets_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Retrieves Google Sheets synchronization settings for the user."""
    config = db.query(SheetsSyncConfig).filter(SheetsSyncConfig.user_id == current_user.id).first()
    if not config:
        return {"spreadsheet_id": "", "sheet_name": "Applications", "is_enabled": False, "configured": False}
    return {
        "spreadsheet_id": config.spreadsheet_id,
        "sheet_name": config.sheet_name,
        "is_enabled": config.is_enabled,
        "last_synced_at": config.last_synced_at.isoformat() if config.last_synced_at else None,
        "configured": True
    }

@router.post("")
def save_sheets_config(
    payload: SheetsConfigRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Creates or updates Google Sheets synchronization configurations."""
    config = db.query(SheetsSyncConfig).filter(SheetsSyncConfig.user_id == current_user.id).first()
    
    if not config:
        config = SheetsSyncConfig(
            user_id=current_user.id,
            spreadsheet_id=payload.spreadsheet_id,
            sheet_name=payload.sheet_name or "Applications",
            is_enabled=payload.is_enabled
        )
        db.add(config)
    else:
        config.spreadsheet_id = payload.spreadsheet_id
        config.sheet_name = payload.sheet_name or "Applications"
        config.is_enabled = payload.is_enabled
        
    db.commit()
    
    # Trigger an initial mirroring sync in the background
    if config.is_enabled:
        sync_user_sheets_task.delay(str(current_user.id))
        
    return {"status": "success", "message": "Sheets configuration saved."}

@router.post("/trigger")
def trigger_sheets_sync(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Manually triggers a full synchronization override to the Google sheet."""
    config = db.query(SheetsSyncConfig).filter(SheetsSyncConfig.user_id == current_user.id).first()
    if not config or not config.is_enabled:
        raise HTTPException(status_code=400, detail="Google Sheets Sync is disabled or not configured.")
        
    # Queue task
    task = sync_user_sheets_task.delay(str(current_user.id))
    return {"status": "success", "message": "Synchronization triggered in background.", "task_id": task.id}
