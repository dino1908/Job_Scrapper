"""
API routes for job scrapper application.
"""
from datetime import datetime, timedelta
from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Job, UserSession, ScrapingTask
from ..schemas import (
    ScrapeJobsRequest,
    ScrapeJobsResponse,
    ScrapingStatusResponse,
    JobsRequest,
    JobsResponse,
    JobSchema,
)
from ..services.scraper_orchestrator import scraper_orchestrator

router = APIRouter()


def _parse_csv_list(value: str) -> List[str]:
    """Parse comma-separated input into clean unique values."""
    if not value:
        return []

    parsed = []
    seen = set()
    for part in value.split(","):
        cleaned = part.strip()
        normalized = cleaned.lower()
        if not cleaned or normalized in seen:
            continue
        seen.add(normalized)
        parsed.append(cleaned)
    return parsed


# ==================== Job Scraping ====================

@router.post("/scrape-jobs", response_model=ScrapeJobsResponse)
async def scrape_jobs(
    request: ScrapeJobsRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start a background job scraping task.

    Inputs:
    - role_titles: comma-separated titles
    - locations: comma-separated locations
    """
    parsed_roles = _parse_csv_list(request.role_titles)
    parsed_locations = _parse_csv_list(request.locations)

    if not parsed_roles:
        raise HTTPException(
            status_code=400,
            detail="At least one role title is required (comma-separated supported)"
        )

    if not parsed_locations:
        parsed_locations = [""]

    # System target: min 100, max 200
    target_jobs = max(100, min(request.target_jobs, 200))

    # Keep a lightweight session row to satisfy ScrapingTask foreign key.
    session = UserSession(
        id=str(uuid.uuid4()),
        resume_filename="manual-search",
        resume_text="",
        resume_profile={
            "role_titles": parsed_roles,
            "locations": parsed_locations,
            "target_jobs": target_jobs,
            "recent_days": request.recent_days,
        }
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    task = ScrapingTask(
        id=str(uuid.uuid4()),
        session_id=session.id,
        status="pending",
        progress=0
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    background_tasks.add_task(
        _background_scraping_task,
        task.id,
        parsed_roles,
        parsed_locations,
        target_jobs,
        request.recent_days
    )

    return ScrapeJobsResponse(
        task_id=task.id,
        status="pending",
        message="Scraping task started successfully",
        parsed_roles=parsed_roles,
        parsed_locations=parsed_locations,
        target_jobs=target_jobs
    )


def _background_scraping_task(
    task_id: str,
    roles: List[str],
    locations: List[str],
    target_jobs: int,
    recent_days: int
):
    """
    Background task to scrape LinkedIn jobs for all role/location combinations.
    """
    from ..database import SessionLocal

    db = SessionLocal()

    try:
        task = db.query(ScrapingTask).filter(ScrapingTask.id == task_id).first()
        task.status = "running"
        task.started_at = datetime.utcnow()
        task.progress = 1
        db.commit()

        # Replace previous result set with the latest run.
        db.query(Job).delete()
        db.commit()

        combos = [(role, location) for role in roles for location in locations]
        total_combos = len(combos)

        collected_jobs = []
        seen = set()
        cutoff = datetime.utcnow() - timedelta(days=recent_days)

        for index, (role, location) in enumerate(combos):
            if len(collected_jobs) >= target_jobs:
                break

            remaining = target_jobs - len(collected_jobs)
            per_combo_limit = min(200, max(100, remaining))

            results = scraper_orchestrator.scrape_all_sources_sync(
                title=role,
                keywords=None,
                industry="",
                location=location,
                limit_per_source=per_combo_limit,
                sources=["linkedin"]
            )
            flat_jobs = scraper_orchestrator.get_all_jobs_flat(results)

            for job in flat_jobs:
                posted_date = job.get("posted_date")
                if posted_date and posted_date < cutoff:
                    continue

                apply_url = (job.get("apply_url") or "").strip().lower()
                if apply_url:
                    key = ("url", apply_url)
                else:
                    key = (
                        "fallback",
                        (job.get("title") or "").strip().lower(),
                        (job.get("company") or "").strip().lower(),
                        (job.get("location") or "").strip().lower(),
                    )
                if key in seen:
                    continue
                seen.add(key)
                collected_jobs.append(job)

                if len(collected_jobs) >= target_jobs:
                    break

            task.progress = min(95, int(((index + 1) / max(1, total_combos)) * 100))
            db.commit()

        collected_jobs.sort(
            key=lambda job: job.get("posted_date") or datetime.min,
            reverse=True
        )
        final_jobs = collected_jobs[:target_jobs]

        saved_count = 0
        for job_data in final_jobs:
            existing = db.query(Job).filter(
                Job.apply_url == job_data["apply_url"],
                Job.source == job_data["source"]
            ).first()

            if not existing:
                db.add(Job(**job_data))
                saved_count += 1

        db.commit()

        task.status = "completed"
        task.completed_at = datetime.utcnow()
        task.total_jobs_scraped = saved_count
        task.progress = 100
        task.sources_completed = ["linkedin"]
        db.commit()

        print(
            f"[API] Scraping task {task_id} completed: "
            f"{saved_count} jobs saved from {len(final_jobs)} collected"
        )

    except Exception as exc:
        task = db.query(ScrapingTask).filter(ScrapingTask.id == task_id).first()
        if task:
            task.status = "failed"
            task.error_message = str(exc)
            task.completed_at = datetime.utcnow()
            db.commit()
        print(f"[API] Scraping task {task_id} failed: {exc}")

    finally:
        db.close()


@router.get("/scraping-status/{task_id}", response_model=ScrapingStatusResponse)
def get_scraping_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Get the status of a scraping task."""
    task = db.query(ScrapingTask).filter(ScrapingTask.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Scraping task not found")

    return ScrapingStatusResponse(
        task_id=task.id,
        status=task.status,
        progress=task.progress,
        total_jobs_scraped=task.total_jobs_scraped,
        sources_completed=task.sources_completed or [],
        error_message=task.error_message,
        started_at=task.started_at,
        completed_at=task.completed_at
    )


# ==================== Jobs Listing ====================

@router.post("/jobs", response_model=JobsResponse)
def get_jobs(
    request: JobsRequest,
    db: Session = Depends(get_db)
):
    """Get latest scraped jobs sorted by posted date (desc)."""
    query = db.query(Job).filter(Job.source == "linkedin")

    recent_cutoff = datetime.utcnow() - timedelta(days=10)
    recent_jobs = query.filter(Job.posted_date >= recent_cutoff).all()
    if recent_jobs:
        all_jobs = recent_jobs
    else:
        all_jobs = query.all()

    all_jobs.sort(
        key=lambda job: (job.posted_date or datetime.min, job.scraped_at or datetime.min),
        reverse=True
    )
    jobs = all_jobs[:request.limit]

    return JobsResponse(
        task_id=request.task_id,
        total_jobs=len(jobs),
        jobs=[JobSchema.model_validate(job) for job in jobs]
    )
