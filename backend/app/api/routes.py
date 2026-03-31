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
from ..services.job_relevance_screener import job_relevance_screener
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


def _job_dedupe_key(job: dict):
    """Generate stable dedupe key for scraped jobs."""
    apply_url = (job.get("apply_url") or "").strip().lower()
    if apply_url:
        return ("url", apply_url)
    return (
        "fallback",
        (job.get("title") or "").strip().lower(),
        (job.get("company") or "").strip().lower(),
        (job.get("location") or "").strip().lower(),
    )


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

    target_jobs = request.target_jobs

    # Keep a lightweight session row to satisfy ScrapingTask foreign key.
    session = UserSession(
        id=str(uuid.uuid4()),
        resume_filename="manual-search",
        resume_text="",
        resume_profile={
            "role_titles": parsed_roles,
            "locations": parsed_locations,
            "target_jobs": target_jobs,
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
        target_jobs
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
    target_jobs: int
):
    """
    Background task to scrape LinkedIn jobs for role/location combinations.

    Behavior:
    - scrape the most recent day first
    - screen with Mistral for strict role/location relevance
    - if target count is not met, expand backward window by 1 day each round
    """
    from ..database import SessionLocal

    db = SessionLocal()

    try:
        task = db.query(ScrapingTask).filter(ScrapingTask.id == task_id).first()
        task.status = "running"
        task.started_at = datetime.utcnow()
        task.progress = 1
        task.sources_completed = []
        db.commit()

        # Replace previous result set with the latest run.
        db.query(Job).delete()
        db.commit()

        combos = [(role, location) for role in roles for location in locations]
        total_combos = max(1, len(combos))
        if not combos:
            raise ValueError("No role/location combinations found")

        collected_jobs = []
        selected_keys = set()
        screening_cache = {}
        saved_count = 0

        initial_window_days = 1
        window_step_days = 1
        max_backfill_days = 180
        max_rounds = ((max_backfill_days - initial_window_days) // window_step_days) + 1
        current_window_days = initial_window_days
        round_index = 0

        while len(collected_jobs) < target_jobs and current_window_days <= max_backfill_days:
            round_index += 1
            round_added = 0

            print(
                f"[API] Task {task_id}: round {round_index}/{max_rounds}, "
                f"window={current_window_days}d, collected={len(collected_jobs)}/{target_jobs}"
            )
            task.sources_completed = [f"linkedin:last_{current_window_days}_days"]
            db.commit()

            cutoff = datetime.utcnow() - timedelta(days=current_window_days)

            for combo_index, (role, location) in enumerate(combos):
                if len(collected_jobs) >= target_jobs:
                    break

                remaining = target_jobs - len(collected_jobs)
                # Fetch deeper than remaining because strict screening removes many jobs.
                per_combo_limit = min(250, max(120, remaining * 3))
                new_jobs_to_persist = []

                results = scraper_orchestrator.scrape_all_sources_sync(
                    title=role,
                    keywords=None,
                    industry="",
                    location=location,
                    recent_days=current_window_days,
                    limit_per_source=per_combo_limit
                )
                flat_jobs = scraper_orchestrator.get_all_jobs_flat(results)

                # Build unscreened list; skip already-selected jobs and stale postings.
                candidates = []
                local_keys = set()
                role_key = role.strip().lower()
                location_key = location.strip().lower()
                for job in flat_jobs:
                    posted_date = job.get("posted_date")
                    if posted_date and posted_date < cutoff:
                        continue

                    dedupe_key = _job_dedupe_key(job)
                    if dedupe_key in selected_keys or dedupe_key in local_keys:
                        continue
                    local_keys.add(dedupe_key)

                    cache_key = (dedupe_key, role_key, location_key)
                    cached_relevant = screening_cache.get(cache_key)
                    if cached_relevant is True:
                        collected_jobs.append(job)
                        selected_keys.add(dedupe_key)
                        new_jobs_to_persist.append(job)
                        round_added += 1
                        if len(collected_jobs) >= target_jobs:
                            break
                        continue
                    if cached_relevant is False:
                        continue

                    candidates.append(job)

                if len(collected_jobs) < target_jobs and candidates:
                    screened_jobs = job_relevance_screener.filter_jobs(
                        candidates,
                        role=role,
                        location=location
                    )
                    screened_keys = {_job_dedupe_key(job) for job in screened_jobs}
                    for candidate in candidates:
                        c_key = _job_dedupe_key(candidate)
                        c_cache_key = (c_key, role_key, location_key)
                        screening_cache[c_cache_key] = c_key in screened_keys

                    for job in screened_jobs:
                        dedupe_key = _job_dedupe_key(job)
                        if dedupe_key in selected_keys:
                            continue
                        selected_keys.add(dedupe_key)
                        collected_jobs.append(job)
                        new_jobs_to_persist.append(job)
                        round_added += 1
                        if len(collected_jobs) >= target_jobs:
                            break

                if new_jobs_to_persist:
                    for job_data in new_jobs_to_persist:
                        apply_url = (job_data.get("apply_url") or "").strip()
                        source = (job_data.get("source") or "").strip()
                        if not apply_url or not source:
                            continue
                        db.add(Job(**job_data))
                        saved_count += 1
                    db.commit()

                combo_progress = int(((combo_index + 1) / total_combos) * 8)
                round_progress = int((round_index / max(1, max_rounds)) * 12)
                count_progress = int((len(collected_jobs) / max(1, target_jobs)) * 80)
                task.progress = min(95, max(1, count_progress + combo_progress + round_progress))
                task.total_jobs_scraped = saved_count
                db.commit()

            if len(collected_jobs) >= target_jobs:
                break

            if round_added == 0:
                print(
                    f"[API] Task {task_id}: no new relevant jobs in "
                    f"{current_window_days}d window"
                )

            current_window_days += window_step_days

        task.status = "completed"
        task.completed_at = datetime.utcnow()
        task.total_jobs_scraped = saved_count
        task.progress = 100
        task.sources_completed = ["linkedin"]
        db.commit()

        print(
            f"[API] Scraping task {task_id} completed: "
            f"{saved_count} jobs saved from {len(collected_jobs)} collected"
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
    """Get currently available scraped jobs sorted by posted date (desc)."""
    query = db.query(Job).filter(Job.source == "linkedin")
    all_jobs = query.all()

    all_jobs.sort(
        key=lambda job: (job.posted_date or datetime.min, job.scraped_at or datetime.min),
        reverse=True
    )
    jobs = all_jobs[:request.limit]

    return JobsResponse(
        total_jobs=len(jobs),
        jobs=[JobSchema.model_validate(job) for job in jobs]
    )
