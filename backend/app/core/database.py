from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Engine configuration (uses setting environment)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Automatically check connection and reconnect if lost
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    """
    Creates tables and database extensions.
    Called on system startup.
    """
    # Import models here to register them with Base.metadata before creation
    from app.models import Base as ModelsBase
    
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.execute(text("ALTER TABLE applications ADD COLUMN IF NOT EXISTS source VARCHAR(100);"))
        conn.commit()
        
    ModelsBase.metadata.create_all(bind=engine)

def get_db():
    """
    FastAPI dependency that provides a local database session
    and ensures it's closed after the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
