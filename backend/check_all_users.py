import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.application import Application

db = SessionLocal()
try:
    users = db.query(User).all()
    print(f"Total Users: {len(users)}")
    for u in users:
        apps = db.query(Application).filter(Application.user_id == u.id).all()
        print(f"User ID: {u.id}, Email: {u.email}, Apps count: {len(apps)}")
        statuses = [a.status for a in apps]
        print(f"  Statuses: {statuses}")
finally:
    db.close()
