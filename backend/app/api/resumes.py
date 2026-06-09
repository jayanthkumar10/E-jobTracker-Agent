from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

from app.core.database import get_db
from app.api import deps
from app.models.user import User
from app.models.application import ResumeTailoring, Application
from app.services.resume_tailor import ResumeTailorService, DEFAULT_BASE_RESUME

router = APIRouter()

class SingleTailorRequest(BaseModel):
    job_title: str
    company_name: str
    job_description: str
    job_url: Optional[str] = None

class BulkTailorRequest(BaseModel):
    search_url: str
    count: Optional[int] = 1

class BaseResumeUpdateRequest(BaseModel):
    base_resume: str

@router.post("/tailor-single")
def tailor_single_resume(
    payload: SingleTailorRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Instantly tailors a resume for a single job description.
    Runs synchronously and returns the tailored application.
    """
    if not payload.job_title.strip() or not payload.company_name.strip() or not payload.job_description.strip():
        raise HTTPException(status_code=400, detail="Job title, Company, and Job Description are required.")
        
    try:
        app = ResumeTailorService.tailor_application(
            db=db,
            user_id=str(current_user.id),
            job_title=payload.job_title,
            company_name=payload.company_name,
            job_description=payload.job_description,
            job_url=payload.job_url
        )
        return {
            "status": "success",
            "application_id": str(app.id),
            "company_name": app.company_name,
            "job_title": app.job_title,
            "tailored_resume_url": app.tailored_resume_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to tailor resume: {str(e)}")

@router.post("/tailor-bulk")
def tailor_bulk_resumes(
    payload: BulkTailorRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Launches a background Celery task to scrape LinkedIn jobs and bulk-tailor resumes.
    Logs a ResumeTailoring history record.
    """
    if not payload.search_url.strip():
        raise HTTPException(status_code=400, detail="LinkedIn search URL is required.")
        
    # Check if Apify token is set
    from app.core.config import settings
    if not settings.APIFY_API_TOKEN:
        raise HTTPException(status_code=400, detail="Apify API Token is not configured in backend .env settings.")
        
    try:
        # Create history record
        run = ResumeTailoring(
            user_id=current_user.id,
            job_url=payload.search_url,
            count=payload.count or 1,
            status="PROCESSING"
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        
        # Trigger Celery background task
        from app.workers.tasks import bulk_tailor_linkedin_jobs_task
        bulk_tailor_linkedin_jobs_task.delay(
            user_id=str(current_user.id),
            search_url=payload.search_url,
            count=payload.count or 1,
            run_id=str(run.id)
        )
        
        return {
            "status": "success",
            "run_id": str(run.id),
            "message": "Bulk tailoring triggered successfully in the background."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue bulk tailoring: {str(e)}")

@router.get("/history", response_model=List[dict])
def get_tailoring_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Retrieves list of past tailoring runs for the authenticated user."""
    runs = db.query(ResumeTailoring).filter(ResumeTailoring.user_id == current_user.id).order_by(ResumeTailoring.created_at.desc()).all()
    result = []
    for run in runs:
        result.append({
            "id": str(run.id),
            "job_url": run.job_url or "Single JD Optimization",
            "count": run.count,
            "status": run.status,
            "results_count": run.results_count,
            "created_at": run.created_at.isoformat() if run.created_at else None
        })
    return result

@router.get("/base")
def get_base_resume(
    current_user: User = Depends(deps.get_current_user)
):
    """Retrieves the user's base HTML resume template."""
    return {
        "base_resume": current_user.base_resume if current_user.base_resume else DEFAULT_BASE_RESUME
    }

@router.put("/base")
def update_base_resume(
    payload: BaseResumeUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Updates the user's base HTML resume template."""
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.base_resume = payload.base_resume
    db.commit()
    return {"status": "success", "message": "Base resume template updated."}
