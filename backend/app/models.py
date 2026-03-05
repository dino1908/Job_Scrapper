"""
SQLAlchemy database models.
"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON, ForeignKey
from datetime import datetime
import uuid

from .database import Base


class Job(Base):
    """Job posting model."""

    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    location = Column(String(255))
    job_type = Column(String(50))  # remote/hybrid/onsite
    employment_type = Column(String(50))  # full-time/part-time/contract
    description = Column(Text)
    required_skills = Column(JSON)  # List[str]
    required_experience = Column(Float)  # Years of experience
    salary_range = Column(String(100))
    apply_url = Column(String(512), nullable=False)
    source = Column(String(50), nullable=False, index=True)  # indeed/linkedin/etc
    posted_date = Column(DateTime, index=True)
    scraped_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<Job {self.id}: {self.title} at {self.company}>"


class UserSession(Base):
    """User session model to store resume analysis results."""

    __tablename__ = "user_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_filename = Column(String(255))
    resume_text = Column(Text)
    resume_profile = Column(JSON)  # ResumeProfile as dict
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<UserSession {self.id}>"


class ScrapingTask(Base):
    """Background scraping task status tracking."""

    __tablename__ = "scraping_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("user_sessions.id"), nullable=False)
    status = Column(String(20), default="pending")  # pending/running/completed/failed
    progress = Column(Integer, default=0)  # 0-100
    total_jobs_scraped = Column(Integer, default=0)
    sources_completed = Column(JSON, default=list)  # List of completed sources
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ScrapingTask {self.id}: {self.status}>"
