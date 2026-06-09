import sys
import os

# Add /app to python path
sys.path.append("/app")

from app.core.database import SessionLocal
from app.models.email import Email
from app.workers.tasks import process_email_job

def reprocess():
    db = SessionLocal()
    try:
        emails = db.query(Email).all()
        print(f"Found {len(emails)} emails in database.")
        for email in emails:
            print(f"Re-triggering processing for email {email.id} (Subject: {email.subject})")
            process_email_job.delay(str(email.id))
        print("All reprocess tasks queued.")
    finally:
        db.close()

if __name__ == "__main__":
    reprocess()
