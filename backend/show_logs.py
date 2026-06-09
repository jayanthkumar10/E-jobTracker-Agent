import sys
sys.path.append("/app")

from app.core.database import SessionLocal
from app.models.email import Email
from app.models.application import Application

db = SessionLocal()
try:
    emails = db.query(Email).all()
    print(f"{'Email ID':<40} | {'Linked App':<12} | Subject")
    print("-" * 100)
    for email in emails:
        linked = str(email.application_id) if email.application_id else "None"
        print(f"{str(email.id):<40} | {linked:<12} | {email.subject[:50]}")
finally:
    db.close()
