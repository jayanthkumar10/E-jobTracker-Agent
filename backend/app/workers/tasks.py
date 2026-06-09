from app.workers.celery_app import celery_app
from sqlalchemy.orm import Session
import httpx
from datetime import datetime, timedelta
import logging

from app.core.database import SessionLocal
from app.models.user import User, OAuthToken
from app.models.email import Email
from app.services.google_auth_svc import GoogleAuthService
from app.services.email_parser import EmailParser

logger = logging.getLogger(__name__)

@celery_app.task
def trigger_all_users_sync():
    """
    Periodic orchestrator task (Celery Beat).
    Queries all users with Google OAuth credentials and spawns a sync task for each.
    """
    db = SessionLocal()
    try:
        users_with_google = db.query(User).join(OAuthToken).filter(
            OAuthToken.provider == "google"
        ).all()
        
        for user in users_with_google:
            sync_user_gmail_task.delay(str(user.id))
            
        return f"Triggered sync for {len(users_with_google)} users."
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_user_gmail_task(self, user_id: str):
    """
    Incremental Gmail sync worker for a specific user.
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return f"User {user_id} not found."
            
        token = db.query(OAuthToken).filter(
            OAuthToken.user_id == user.id,
            OAuthToken.provider == "google"
        ).first()
        
        if not token:
            return f"No Google credentials for user {user_id}."

        # Obtain a fresh valid access token
        try:
            access_token = GoogleAuthService.get_valid_token(db, token)
        except Exception as e:
            logger.error(f"OAuth refresh failed for user {user_id}: {str(e)}")
            return f"Sync aborted: Credentials expired or revoked."

        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Define search filter (emails from the last 30 days or general job application queries)
        sync_after = (datetime.utcnow() - timedelta(days=30)).strftime("%Y/%m/%d")
        search_query = f"after:{sync_after} subject:(application OR interview OR offer OR career OR resume OR applied OR status OR job OR recruiter)"
        
        list_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages"
        params = {"q": search_query, "maxResults": 100}
        
        new_emails_count = 0
        
        with httpx.Client(timeout=30.0) as client:
            # Fetch message list
            response = client.get(list_url, headers=headers, params=params)
            if response.status_code != 200:
                logger.error(f"Failed to fetch Gmail list: {response.text}")
                return f"Sync failed: {response.text}"
                
            messages = response.json().get("messages", [])
            
            for msg_summary in messages:
                msg_id = msg_summary.get("id")
                
                # Check if we already have this email synced
                exists = db.query(Email).filter(Email.gmail_message_id == msg_id).first()
                if exists:
                    continue
                    
                # Fetch full message content
                detail_url = f"{list_url}/{msg_id}"
                detail_response = client.get(detail_url, headers=headers)
                if detail_response.status_code != 200:
                    logger.warning(f"Failed to fetch message details for {msg_id}: {detail_response.text}")
                    continue
                    
                raw_message = detail_response.json()
                
                # Parse the raw email
                parsed_data = EmailParser.parse_gmail_message(raw_message)
                
                # Create Email record
                db_email = Email(
                    user_id=user.id,
                    gmail_message_id=parsed_data["gmail_message_id"],
                    gmail_thread_id=parsed_data["gmail_thread_id"],
                    subject=parsed_data["subject"],
                    sender_email=parsed_data["sender_email"],
                    recipient_email=parsed_data["recipient_email"],
                    received_at=parsed_data["received_at"],
                    body_text=parsed_data["body_text"],
                    body_html=parsed_data["body_html"]
                )
                db.add(db_email)
                db.commit()
                db.refresh(db_email)
                
                new_emails_count += 1
                
                # Enqueue the AI processing extraction task
                process_email_job.delay(str(db_email.id))
                
        return f"Synchronized successfully. Found {new_emails_count} new emails."
    except Exception as exc:
        logger.error(f"Error executing sync task: {str(exc)}")
        db.rollback()
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(rate_limit='12/m')
def process_email_job(email_id: str):
    """
    Background worker that runs Gemini AI extraction, smart deduplication,
    and pgvector embedding generation for a synced email.
    """
    from app.services.ai_engine import AIEngineService
    from app.services.deduplicator import Deduplicator
    
    db = SessionLocal()
    try:
        email = db.query(Email).filter(Email.id == email_id).first()
        if not email:
            return f"Email {email_id} not found."

        # 1. Run Gemini AI extraction
        extracted_data = AIEngineService.extract_job_details(email.body_text, email.subject, email.sender_email)
        
        if extracted_data:
            # 2. Run Deduplication & Timeline Evolve logic
            app_record = Deduplicator.match_and_update_application(
                db=db,
                user_id=email.user_id,
                extracted_data=extracted_data,
                email_date=email.received_at
            )
            
            if app_record:
                # Link email to application
                email.application_id = app_record.id
                db.commit()
                
                # 3. Schedule real-time Google Sheets Mirroring Sync
                # We trigger the sheet sync job in background
                sync_user_sheets_task.delay(str(email.user_id))
            else:
                logger.info(f"Email {email_id} parsed but skipped application creation/update (unconfirmed submission).")
        else:
            logger.warning(f"AI extraction returned null or failed for email {email_id}")

        # 4. Generate RAG Vector Embeddings for the email body text
        embedding = AIEngineService.generate_embedding(email.body_text or email.subject)
        if embedding:
            email.embedding = embedding
            db.commit()
            
        return f"Successfully processed email {email_id}."
    except Exception as e:
        logger.error(f"Error processing email job {email_id}: {str(e)}")
        db.rollback()
        return f"Failed to process email {email_id}: {str(e)}"
    finally:
        db.close()


@celery_app.task
def sync_user_sheets_task(user_id: str):
    """
    Triggers Google Sheets Mirroring Sync for a user.
    """
    from app.services.sheets_sync import SheetsSyncService
    
    db = SessionLocal()
    try:
        result = SheetsSyncService.sync_to_sheet(db, user_id)
        return result
    except Exception as e:
        logger.error(f"Error executing sheet sync task: {str(e)}")
        return f"Failed: {str(e)}"
    finally:
        db.close()


@celery_app.task
def detect_all_users_followups():
    """
    Scans all users to detect inactive applications and suggest follow-up emails.
    """
    db = SessionLocal()
    try:
        users = db.query(User).all()
        count = 0
        for user in users:
            detect_user_followups_task.delay(str(user.id))
            count += 1
        return f"Triggered follow-up scanning for {count} users."
    finally:
        db.close()


@celery_app.task
def detect_user_followups_task(user_id: str):
    """
    Detects and drafts followups for a specific user.
    """
    from app.services.follow_up import FollowUpService
    
    db = SessionLocal()
    try:
        created = FollowUpService.detect_and_create_follow_ups(db, user_id)
        return f"Suggested {created} new follow-up tasks."
    except Exception as e:
        logger.error(f"Error executing follow-up detection: {str(e)}")
        return f"Failed: {str(e)}"
    finally:
        db.close()


