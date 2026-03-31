"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


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


class JobsResponse(BaseModel):
    """Response with scraped jobs."""
    total_jobs: int
    jobs: List[JobSchema]
