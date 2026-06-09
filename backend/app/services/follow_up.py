from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
from typing import Optional

from app.models.application import Application, FollowUp
from app.services.ai_engine import AIEngineService

logger = logging.getLogger(__name__)

class FollowUpService:
    @classmethod
    def generate_draft_body(cls, company_name: str, job_title: str, recruiter_name: Optional[str] = None) -> str:
        """Uses Gemini to generate a tailored, professional follow-up email draft."""
        recruiter = recruiter_name or "Hiring Team"
        prompt = f"""
        Write a concise, professional follow-up email from a candidate to a recruiter/hiring team.
        The candidate applied for the '{job_title}' position at '{company_name}'.
        It has been over two weeks since the application/last contact, and they want to politely express continued interest and ask about next steps.
        
        Address it to '{recruiter}'. Keep it short, confident, and polite. 
        Do not add placeholders. Make the email ready to send.
        """
        try:
            model = AIEngineService.get_model()
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Failed to generate follow-up draft body: {str(e)}")
            # Return a generic fallback template
            return f"Dear {recruiter},\n\nI hope this email finds you well.\n\nI am writing to check in on the status of my application for the {job_title} role at {company_name}. I remain very interested in the opportunity and would appreciate any updates on the timeline for next steps.\n\nThank you for your time.\n\nBest regards,\n[Your Name]"

    @classmethod
    def detect_and_create_follow_ups(cls, db: Session, user_id: str) -> int:
        """
        Scans applications and creates follow-up suggestions for applications
        with no activity in 14 days.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=14)
        
        # Query applications that are APPLIED or SCREENING or INTERVIEWING
        # and haven't been updated in 14 days, and don't already have pending follow-ups
        stagnant_apps = db.query(Application).filter(
            Application.user_id == user_id,
            Application.status.in_(["APPLIED", "SCREENING", "INTERVIEWING"]),
            Application.updated_at <= cutoff_date
        ).all()
        
        created_count = 0
        
        for app in stagnant_apps:
            # Check if there is already a pending follow-up for this application
            has_pending = db.query(FollowUp).filter(
                FollowUp.application_id == app.id,
                FollowUp.is_completed == False
            ).first()
            
            if has_pending:
                continue
                
            # Generate follow-up body
            draft_body = cls.generate_draft_body(
                company_name=app.company_name,
                job_title=app.job_title,
                recruiter_name=app.recruiter_name
            )
            
            # Create FollowUp suggestion
            follow_up = FollowUp(
                application_id=app.id,
                suggested_date=(datetime.utcnow() + timedelta(days=1)).date(),
                is_completed=False,
                suggested_body=draft_body
            )
            db.add(follow_up)
            created_count += 1
            
        if created_count > 0:
            db.commit()
            
        return created_count
