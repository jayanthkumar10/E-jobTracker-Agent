from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, ARRAY, Text, Integer, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import datetime
from app.core.database import Base

class Application(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_name = Column(String(255), nullable=False, index=True)
    job_title = Column(String(255), nullable=False, index=True)
    recruiter_name = Column(String(255), nullable=True)
    recruiter_email = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="APPLIED")  # 'APPLIED', 'SCREENING', 'INTERVIEWING', 'OFFERED', 'REJECTED', 'WITHDRAWN'
    salary_range = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    work_mode = Column(String(50), nullable=True)  # 'REMOTE', 'HYBRID', 'ONSITE'
    application_url = Column(Text, nullable=True)
    resume_version = Column(String(100), nullable=True)
    source = Column(String(100), nullable=True)  # E.g., 'LinkedIn', 'Indeed', 'Naukri', 'Direct'
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="applications")
    events = relationship("ApplicationEvent", back_populates="application", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="application", cascade="all, delete-orphan")
    follow_ups = relationship("FollowUp", back_populates="application", cascade="all, delete-orphan")
    emails = relationship("Email", back_populates="application")

    job_description = Column(Text, nullable=True)
    tailored_resume_url = Column(Text, nullable=True)
    ats_match_details = Column(Text, nullable=True)


class ApplicationEvent(Base):
    __tablename__ = "application_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    stage = Column(String(100), nullable=False)  # 'APPLIED', 'RECRUITER_SCREEN', 'TECH_INTERVIEW', 'OFFER', 'REJECTION'
    event_date = Column(DateTime(timezone=True), nullable=False, default=datetime.datetime.utcnow)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    # Relationships
    application = relationship("Application", back_populates="events")


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    stage_name = Column(String(255), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, default=45)
    interviewer_names = Column(ARRAY(String), nullable=True)
    meeting_link = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    application = relationship("Application", back_populates="interviews")


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    suggested_date = Column(Date, nullable=False)
    is_completed = Column(Boolean, default=False)
    suggested_body = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    application = relationship("Application", back_populates="follow_ups")


class SheetsSyncConfig(Base):
    __tablename__ = "sheets_sync_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    spreadsheet_id = Column(String(255), nullable=False)
    sheet_name = Column(String(100), default="Applications")
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="sheets_config")


class ResumeTailoring(Base):
    __tablename__ = "resume_tailoring"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_url = Column(Text, nullable=True)
    count = Column(Integer, default=1)
    status = Column(String(50), default="PROCESSING")  # 'PROCESSING', 'COMPLETED', 'FAILED'
    results_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="resume_tailoring")

