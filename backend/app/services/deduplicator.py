import re
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.models.application import Application, ApplicationEvent
from app.models.email import Email
from app.services.ai_engine import JobExtractionSchema

class Deduplicator:
    @staticmethod
    def normalize_string(text: str) -> str:
        """Normalizes company names and roles by stripping casing, whitespace, and common suffixes."""
        if not text:
            return ""
        # Convert to lowercase
        normalized = text.lower().strip()
        # Remove suffixes like corp, inc, ltd, co, corporation, incorporated
        normalized = re.sub(r'\b(corp|inc|ltd|co|llc|corporation|incorporated|limited)\b', '', normalized)
        # Remove non-alphanumeric characters
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
        # Collapse multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized.strip()

    @classmethod
    def match_and_update_application(
        cls,
        db: Session,
        user_id: str,
        extracted_data: JobExtractionSchema,
        email_date: datetime
    ) -> Optional[Application]:
        """
        Looks for an existing application matching user_id + company + role.
        If found, appends the status update to the application's timeline event list and returns it.
        Otherwise, creates a new Application.
        """
        # Only consider status "APPLIED" if there is an explicit confirmation of submission.
        if extracted_data.status == "APPLIED" and not getattr(extracted_data, "is_actual_submission_confirmation", False):
            return None

        norm_company = cls.normalize_string(extracted_data.company_name)
        norm_role = cls.normalize_string(extracted_data.job_title)
        
        # Query all active applications for the user
        all_apps = db.query(Application).filter(Application.user_id == user_id).all()
        
        matched_app: Optional[Application] = None
        
        for app in all_apps:
            # Check company match
            if cls.normalize_string(app.company_name) == norm_company:
                # Check role match (using company-role combination rule approved by user)
                if cls.normalize_string(app.job_title) == norm_role:
                    matched_app = app
                    break

        if matched_app:
            # Update the existing application metadata if values are provided
            matched_app.status = extracted_data.status
            if extracted_data.recruiter_name:
                matched_app.recruiter_name = extracted_data.recruiter_name
            if extracted_data.recruiter_email:
                matched_app.recruiter_email = extracted_data.recruiter_email
            if extracted_data.salary:
                matched_app.salary_range = extracted_data.salary
            if extracted_data.location:
                matched_app.location = extracted_data.location
            if extracted_data.work_mode:
                matched_app.work_mode = extracted_data.work_mode
            if not matched_app.source and getattr(extracted_data, "source", None):
                matched_app.source = extracted_data.source
                
            matched_app.updated_at = datetime.utcnow()
            
            # Create a timeline event
            event = ApplicationEvent(
                application_id=matched_app.id,
                stage=extracted_data.status if not extracted_data.stage else f"{extracted_data.status} ({extracted_data.stage})",
                event_date=email_date,
                notes=extracted_data.next_action or f"Status updated automatically from email sync."
            )
            db.add(event)
            db.commit()
            db.refresh(matched_app)
            return matched_app
        else:
            # Create a completely new application record
            new_app = Application(
                user_id=user_id,
                company_name=extracted_data.company_name,
                job_title=extracted_data.job_title,
                recruiter_name=extracted_data.recruiter_name,
                recruiter_email=extracted_data.recruiter_email,
                status=extracted_data.status,
                salary_range=extracted_data.salary,
                location=extracted_data.location,
                work_mode=extracted_data.work_mode,
                source=getattr(extracted_data, "source", None),
                created_at=email_date,
                updated_at=email_date
            )
            db.add(new_app)
            db.commit()
            db.refresh(new_app)
            
            # Create the initial event
            initial_event = ApplicationEvent(
                application_id=new_app.id,
                stage="APPLIED",
                event_date=email_date,
                notes=f"Application created automatically via email sync."
            )
            db.add(initial_event)
            
            # If the current parsed status is already beyond APPLIED (e.g. Interview scheduled)
            # add an additional status event to capture the current state
            if extracted_data.status != "APPLIED":
                subsequent_event = ApplicationEvent(
                    application_id=new_app.id,
                    stage=extracted_data.status if not extracted_data.stage else f"{extracted_data.status} ({extracted_data.stage})",
                    event_date=email_date,
                    notes=extracted_data.next_action or f"Initial status sync set to {extracted_data.status}."
                )
                db.add(subsequent_event)
                
            db.commit()
            db.refresh(new_app)
            return new_app
