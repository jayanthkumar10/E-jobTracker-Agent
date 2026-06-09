import sys
sys.path.append("/app")

from app.core.database import SessionLocal
from app.models.application import Application
from app.models.email import Email
from app.workers.tasks import process_email_job

db = SessionLocal()
try:
    # 1. Delete all Applications
    deleted_count = db.query(Application).delete()
    print(f"Deleted {deleted_count} applications from database.")
    
    # 2. Reset application references on emails
    emails = db.query(Email).all()
    for email in emails:
        email.application_id = None
    db.commit()
    print(f"Reset linkage on {len(emails)} emails.")
    
    # 3. Queue emails for reprocessing
    for email in emails:
        print(f"Queuing email {email.id} (Subject: {email.subject})")
        process_email_job.delay(str(email.id))
        
    print("All tasks queued.")
finally:
    db.close()
