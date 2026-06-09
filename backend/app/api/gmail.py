from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.api import deps
from app.models.user import OAuthToken, User
from app.models.application import FollowUp, Application
from app.workers.tasks import sync_user_gmail_task

router = APIRouter()

@router.get("/sync/status")
def get_gmail_sync_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Checks if the user's Gmail OAuth connection is set up and active."""
    token = db.query(OAuthToken).filter(
        OAuthToken.user_id == current_user.id,
        OAuthToken.provider == "google"
    ).first()
    
    if not token:
        return {"linked": False, "email": None}
        
    return {
        "linked": True,
        "expires_at": token.expires_at.isoformat() if token.expires_at else None,
        "updated_at": token.updated_at.isoformat() if token.updated_at else None
    }

@router.post("/sync")
def trigger_gmail_sync(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Manually triggers Gmail inbox scanning background task immediately."""
    token = db.query(OAuthToken).filter(
        OAuthToken.user_id == current_user.id,
        OAuthToken.provider == "google"
    ).first()
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account not linked. Connect Google OAuth first."
        )
        
    task = sync_user_gmail_task.delay(str(current_user.id))
    return {"status": "success", "message": "Gmail sync triggered in background.", "task_id": task.id}

@router.get("/followups")
def list_followups(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Lists outstanding follow-up suggestion cards for the user."""
    followups = db.query(FollowUp).join(Application).filter(
        Application.user_id == current_user.id,
        FollowUp.is_completed == False
    ).all()
    
    result = []
    for f in followups:
        result.append({
            "id": str(f.id),
            "application_id": str(f.application_id),
            "company_name": f.application.company_name,
            "job_title": f.application.job_title,
            "suggested_date": f.suggested_date.isoformat(),
            "suggested_body": f.suggested_body
        })
    return result

@router.put("/followups/{followup_id}/complete")
def mark_followup_complete(
    followup_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Marks a follow-up action item suggestion as completed/resolved."""
    f = db.query(FollowUp).join(Application).filter(
        FollowUp.id == followup_id,
        Application.user_id == current_user.id
    ).first()
    
    if not f:
        raise HTTPException(status_code=404, detail="Follow-up task not found.")
        
    f.is_completed = True
    db.commit()
    return {"status": "success", "message": "Follow-up marked as completed."}
