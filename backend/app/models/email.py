from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import uuid
import datetime
from app.core.database import Base

class Email(Base):
    __tablename__ = "emails"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="SET NULL"), nullable=True)
    gmail_message_id = Column(String(100), unique=True, nullable=False, index=True)
    gmail_thread_id = Column(String(100), nullable=False, index=True)
    subject = Column(String(255), nullable=True)
    sender_email = Column(String(255), nullable=True)
    recipient_email = Column(String(255), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=False)
    body_text = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)
    
    # Embedding vector (768 dimensions for Gemini text-embedding-004)
    embedding = Column(Vector(768), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="emails")
    application = relationship("Application", back_populates="emails")
