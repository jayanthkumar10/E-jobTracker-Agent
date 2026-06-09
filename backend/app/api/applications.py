from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from app.core.database import get_db
from app.api import deps
from app.models.application import Application, ApplicationEvent, Interview
from app.models.user import User

router = APIRouter()

@router.get("", response_model=List[dict])
def list_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Lists all job applications for the current authenticated user."""
    apps = db.query(Application).filter(Application.user_id == current_user.id).order_by(Application.created_at.desc()).all()
    result = []
    for app in apps:
        result.append({
            "id": str(app.id),
            "company_name": app.company_name,
            "job_title": app.job_title,
            "status": app.status,
            "location": app.location,
            "salary_range": app.salary_range,
            "recruiter_name": app.recruiter_name,
            "source": app.source,
            "created_at": app.created_at.isoformat() if app.created_at else None,
            "updated_at": app.updated_at.isoformat() if app.updated_at else None
        })
    return result

@router.get("/analytics/summary")
def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Calculates summary KPIs: Applications sent, active interviews, rejections, offers, conversion rate, streak, journey start date, avg days to interview."""
    user_id = current_user.id
    
    total_apps = db.query(Application).filter(Application.user_id == user_id).count()
    rejections = db.query(Application).filter(Application.user_id == user_id, Application.status == "REJECTED").count()
    offers = db.query(Application).filter(Application.user_id == user_id, Application.status == "OFFERED").count()
    
    # Active interviews
    active_interviews = db.query(Interview).join(Application).filter(
        Application.user_id == user_id,
        Interview.scheduled_at >= datetime.utcnow()
    ).count()

    # Calculate Response Rate: (applications that advanced beyond APPLIED) / (total applications)
    non_applied_count = db.query(Application).filter(
        Application.user_id == user_id,
        Application.status != "APPLIED"
    ).count()
    
    response_rate = round((non_applied_count / total_apps * 100), 1) if total_apps > 0 else 0.0

    # 1. Journey Start Date
    journey_start_date = "2025-06-10"
    journey_start_dt = datetime.strptime(journey_start_date, "%Y-%m-%d").date()
    journey_days_count = (datetime.utcnow().date() - journey_start_dt).days + 1

    # 2. Average days to interview
    apps_with_interviews = db.query(Application).join(Interview).filter(Application.user_id == user_id).all()
    days_list = []
    for app in apps_with_interviews:
        first_iv = db.query(Interview).filter(Interview.application_id == app.id).order_by(Interview.scheduled_at.asc()).first()
        if first_iv and app.created_at:
            diff = (first_iv.scheduled_at - app.created_at).days
            days_list.append(max(0, diff))
    avg_days_to_interview = round(sum(days_list) / len(days_list), 1) if days_list else 0.0

    # 3. Daily applied streak
    app_dates = db.query(Application.created_at).filter(Application.user_id == user_id).all()
    unique_dates = sorted(list(set([d[0].date() for d in app_dates if d[0]])), reverse=True)
    
    streak = 0
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    
    if unique_dates:
        if unique_dates[0] == today or unique_dates[0] == yesterday:
            streak = 1
            current_date = unique_dates[0]
            for next_date in unique_dates[1:]:
                if (current_date - next_date).days == 1:
                    streak += 1
                    current_date = next_date
                else:
                    break
                    
    # 4. Interviews Done (Conducted)
    interviews_done = db.query(Interview).join(Application).filter(Application.user_id == user_id).count()

    return {
        "total_applications": total_apps,
        "active_interviews": active_interviews,
        "rejections": rejections,
        "offers_received": offers,
        "response_rate": response_rate,
        "journey_start_date": journey_start_date,
        "journey_days_count": journey_days_count,
        "avg_days_to_interview": avg_days_to_interview,
        "daily_applied_streak": streak,
        "interviews_done": interviews_done
    }

@router.get("/analytics/funnel")
def get_funnel_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Returns application funnel metrics."""
    user_id = current_user.id
    
    # Standard states
    applied = db.query(Application).filter(Application.user_id == user_id).count()
    screening = db.query(Application).filter(Application.user_id == user_id, Application.status.in_(["SCREENING", "INTERVIEWING", "OFFERED", "REJECTED"])).count()
    interviewing = db.query(Application).filter(Application.user_id == user_id, Application.status.in_(["INTERVIEWING", "OFFERED", "REJECTED"])).count()
    offered = db.query(Application).filter(Application.user_id == user_id, Application.status == "OFFERED").count()

    return {
        "applied": applied,
        "screening": screening,
        "interviewing": interviewing,
        "offered": offered
    }

@router.get("/{app_id}")
def get_application_details(
    app_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Retrieves detailed information about a single application, including its timeline events."""
    app = db.query(Application).filter(Application.id == app_id, Application.user_id == current_user.id).first()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        
    events = db.query(ApplicationEvent).filter(ApplicationEvent.application_id == app.id).order_by(ApplicationEvent.event_date.asc()).all()
    interviews = db.query(Interview).filter(Interview.application_id == app.id).order_by(Interview.scheduled_at.asc()).all()
    
    return {
        "id": str(app.id),
        "company_name": app.company_name,
        "job_title": app.job_title,
        "status": app.status,
        "recruiter_name": app.recruiter_name,
        "recruiter_email": app.recruiter_email,
        "salary_range": app.salary_range,
        "location": app.location,
        "work_mode": app.work_mode,
        "notes": app.notes,
        "created_at": app.created_at.isoformat() if app.created_at else None,
        "timeline": [
            {
                "id": str(ev.id),
                "stage": ev.stage,
                "event_date": ev.event_date.strftime("%Y-%m-%d"),
                "notes": ev.notes
            } for ev in events
        ],
        "interviews": [
            {
                "id": str(iv.id),
                "stage_name": iv.stage_name,
                "scheduled_at": iv.scheduled_at.isoformat(),
                "duration_minutes": iv.duration_minutes,
                "interviewer_names": iv.interviewer_names or [],
                "meeting_link": iv.meeting_link,
                "notes": iv.notes
            } for iv in interviews
        ]
    }

@router.put("/{app_id}")
def update_application(
    app_id: UUID,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """Updates manual edits to an application and logs it in the timeline if status changes."""
    app = db.query(Application).filter(Application.id == app_id, Application.user_id == current_user.id).first()
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        
    old_status = app.status
    new_status = payload.get("status")
    
    # Update fields
    if "company_name" in payload: app.company_name = payload["company_name"]
    if "job_title" in payload: app.job_title = payload["job_title"]
    if "recruiter_name" in payload: app.recruiter_name = payload["recruiter_name"]
    if "recruiter_email" in payload: app.recruiter_email = payload["recruiter_email"]
    if "salary_range" in payload: app.salary_range = payload["salary_range"]
    if "location" in payload: app.location = payload["location"]
    if "work_mode" in payload: app.work_mode = payload["work_mode"]
    if "notes" in payload: app.notes = payload["notes"]
    if new_status: app.status = new_status
    
    app.updated_at = datetime.utcnow()
    
    # Log event if status changed
    if new_status and old_status != new_status:
        event = ApplicationEvent(
            application_id=app.id,
            stage=new_status,
            event_date=datetime.utcnow(),
            notes="Status updated manually by user."
        )
        db.add(event)
        
    db.commit()
    db.refresh(app)
    
    # Sync sheets if configured
    from app.workers.tasks import sync_user_sheets_task
    sync_user_sheets_task.delay(str(current_user.id))
    
    return {"status": "success", "message": "Application updated."}
