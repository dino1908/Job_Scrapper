"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class JobType(str, Enum):
    """Job type enum."""
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    ANY = "any"


class EmploymentType(str, Enum):
    """Employment type enum."""
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"


class ResumeProfile(BaseModel):
    """Structured search profile extracted by LLM."""
    title: str = Field(default="", description="Primary target/current job title")
    keywords: List[str] = Field(default_factory=list, description="Search keywords from resume")
    industry: str = Field(default="", description="Primary industry")
    job_type_preference: str = Field(default="any", description="remote/hybrid/onsite/any")
    location: str = Field(default="", description="Location preference")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Software Engineer",
                "keywords": ["Python", "FastAPI", "AWS", "Microservices"],
                "industry": "Technology",
                "job_type_preference": "remote",
                "location": "San Francisco, CA"
            }
        }


class ResumeUploadResponse(BaseModel):
    """Response after uploading and analyzing resume."""
    session_id: str
    resume_filename: str
    resume_profile: ResumeProfile
    message: str = "Resume analyzed successfully"


class JobSchema(BaseModel):
    """Job schema for API responses."""
    id: int
    title: str
    company: str
    location: Optional[str] = None
    job_type: Optional[str] = None
    employment_type: Optional[str] = None
    description: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)
    required_experience: Optional[float] = None
    salary_range: Optional[str] = None
    apply_url: str
    source: str
    posted_date: Optional[datetime] = None
    scraped_at: datetime

    class Config:
        from_attributes = True


class ScrapeJobsRequest(BaseModel):
    """Request to start job scraping from direct user inputs."""
    role_titles: str = Field(
        ...,
        description="Comma-separated role titles (e.g., 'SDE, Backend Engineer')"
    )
    locations: str = Field(
        default="",
        description="Comma-separated locations (e.g., 'New York, Remote, San Francisco')"
    )
    target_jobs: int = Field(
        default=25,
        ge=1,
        le=200,
        description="Target number of jobs to scrape"
    )
    recent_days: int = Field(
        default=10,
        ge=1,
        le=30,
        description="Prefer jobs posted within this many recent days"
    )


class ScrapeJobsResponse(BaseModel):
    """Response after starting scraping task."""
    task_id: str
    status: str = "pending"
    message: str = "Scraping task started"
    parsed_roles: List[str] = Field(default_factory=list)
    parsed_locations: List[str] = Field(default_factory=list)
    target_jobs: int = 25


class ScrapingStatusResponse(BaseModel):
    """Scraping task status response."""
    task_id: str
    status: str  # pending/running/completed/failed
    progress: int  # 0-100
    total_jobs_scraped: int
    sources_completed: List[str]
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class JobsRequest(BaseModel):
    """Request to list scraped jobs."""
    limit: Optional[int] = Field(200, ge=1, le=200, description="Maximum results to return")
    task_id: Optional[str] = Field(None, description="Optional task ID for context")


class JobsResponse(BaseModel):
    """Response with scraped jobs."""
    task_id: Optional[str] = None
    total_jobs: int
    jobs: List[JobSchema]


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
