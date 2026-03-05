"""
Scraper orchestrator to coordinate parallel job scraping from multiple sources.
"""
import asyncio
from typing import List, Dict, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
import traceback

from ..scrapers.linkedin_scraper import linkedin_scraper
from ..scrapers.workday_scraper import workday_scraper


class ScraperOrchestrator:
    """Orchestrate parallel job scraping from multiple sources."""

    # LinkedIn-only mode
    SCRAPERS = {
        'linkedin': linkedin_scraper,
    }

    DEFAULT_SCRAPERS = ['linkedin']

    def __init__(self):
        """Initialize scraper orchestrator."""
        self.max_workers = 6  # Maximum parallel scrapers

    async def scrape_all_sources(
        self,
        title: str,
        keywords: Optional[List[str]] = None,
        industry: str = "",
        location: str = "",
        limit_per_source: int = 50,
        sources: Optional[List[str]] = None,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, List[Dict]]:
        """
        Scrape jobs from multiple sources in parallel.

        Args:
            title: Job title query
            keywords: Resume-derived keywords
            industry: Resume-derived industry
            location: Location filter
            limit_per_source: Maximum jobs per source
            sources: Specific sources to scrape (default: all)
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary mapping source names to lists of jobs
        """
        print(
            f"[Orchestrator] Starting scrape: title='{title}', "
            f"industry='{industry}', location='{location}'"
        )

        active_scrapers = {k: v for k, v in self.SCRAPERS.items() if k in self.DEFAULT_SCRAPERS}

        print(f"[Orchestrator] Active scrapers: {list(active_scrapers.keys())}")

        # Run scrapers in parallel
        results = {}
        total_sources = len(active_scrapers)
        completed_sources = 0

        # Use ThreadPoolExecutor for parallel execution
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all scraping tasks
            future_to_source = {
                executor.submit(
                    self._scrape_source_safe,
                    source_name,
                    scraper,
                    title,
                    keywords,
                    industry,
                    location,
                    limit_per_source
                ): source_name
                for source_name, scraper in active_scrapers.items()
            }

            # Collect results as they complete
            for future in asyncio.as_completed(
                [asyncio.wrap_future(f) for f in future_to_source.keys()]
            ):
                source_name = future_to_source[future._future]

                try:
                    jobs = await future
                    results[source_name] = jobs
                    completed_sources += 1

                    # Progress callback
                    if progress_callback:
                        progress = int((completed_sources / total_sources) * 100)
                        progress_callback(progress, source_name, len(jobs))

                    print(f"[Orchestrator] {source_name}: {len(jobs)} jobs scraped")

                except Exception as e:
                    print(f"[Orchestrator] Error scraping {source_name}: {e}")
                    results[source_name] = []
                    completed_sources += 1

        # Summary
        total_jobs = sum(len(jobs) for jobs in results.values())
        print(f"[Orchestrator] Complete: {total_jobs} total jobs from {len(results)} sources")

        return results

    def scrape_all_sources_sync(
        self,
        title: str,
        keywords: Optional[List[str]] = None,
        industry: str = "",
        location: str = "",
        limit_per_source: int = 50,
        sources: Optional[List[str]] = None
    ) -> Dict[str, List[Dict]]:
        """
        Synchronous version of scrape_all_sources.

        Args:
            title: Job title query
            keywords: Resume-derived keywords
            industry: Resume-derived industry
            location: Location filter
            limit_per_source: Maximum jobs per source
            sources: Specific sources to scrape

        Returns:
            Dictionary mapping source names to lists of jobs
        """
        active_scrapers = {k: v for k, v in self.SCRAPERS.items() if k in self.DEFAULT_SCRAPERS}

        print(f"[Orchestrator] Active scrapers: {list(active_scrapers.keys())}")

        results = {}

        # Use ThreadPoolExecutor for parallel execution
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_source = {
                executor.submit(
                    self._scrape_source_safe,
                    source_name,
                    scraper,
                    title,
                    keywords,
                    industry,
                    location,
                    limit_per_source
                ): source_name
                for source_name, scraper in active_scrapers.items()
            }

            # Collect results
            for future, source_name in future_to_source.items():
                try:
                    jobs = future.result()
                    results[source_name] = jobs
                    print(f"[Orchestrator] {source_name}: {len(jobs)} jobs scraped")
                except Exception as e:
                    print(f"[Orchestrator] Error scraping {source_name}: {e}")
                    results[source_name] = []

        total_jobs = sum(len(jobs) for jobs in results.values())
        print(f"[Orchestrator] Complete: {total_jobs} total jobs from {len(results)} sources")

        return results

    def _scrape_source_safe(
        self,
        source_name: str,
        scraper,
        title: str,
        keywords: Optional[List[str]],
        industry: str,
        location: str,
        limit: int
    ) -> List[Dict]:
        """
        Safely scrape a source with error handling.

        Args:
            source_name: Name of the source
            scraper: Scraper instance
            title: Job title query
            keywords: Resume-derived keywords
            industry: Resume-derived industry
            location: Location filter
            limit: Maximum jobs

        Returns:
            List of jobs (empty list on error)
        """
        try:
            print(f"[Orchestrator] Starting {source_name}...")
            jobs = scraper.scrape_jobs(
                title=title,
                location=location,
                limit=limit,
                keywords=keywords,
                industry=industry
            )
            return jobs if jobs else []
        except Exception as e:
            print(f"[Orchestrator] {source_name} failed: {e}")
            traceback.print_exc()
            return []

    def get_all_jobs_flat(self, results: Dict[str, List[Dict]]) -> List[Dict]:
        """
        Flatten results dictionary into a single list.

        Args:
            results: Dictionary of source -> jobs

        Returns:
            Flattened list of all jobs
        """
        all_jobs = []
        for source, jobs in results.items():
            all_jobs.extend(jobs)
        return all_jobs

    def deduplicate_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """
        Remove duplicate jobs based on title and company.

        Args:
            jobs: List of job dictionaries

        Returns:
            Deduplicated list
        """
        seen = set()
        unique_jobs = []

        for job in jobs:
            apply_url = (job.get('apply_url') or "").strip().lower()

            # Prefer URL-based dedupe; fallback to title+company+location
            if apply_url:
                key = ("url", apply_url)
            else:
                key = (
                    "fallback",
                    job.get('title', '').lower().strip(),
                    job.get('company', '').lower().strip(),
                    job.get('location', '').lower().strip()
                )

            if key not in seen and key[0] and key[1]:
                seen.add(key)
                unique_jobs.append(job)

        print(f"[Orchestrator] Deduplication: {len(jobs)} -> {len(unique_jobs)} jobs")
        return unique_jobs

    def scrape_workday_urls(
        self,
        workday_urls: List[str],
        title: str = "",
        keywords: Optional[List[str]] = None,
        industry: str = "",
        limit_per_url: int = 50
    ) -> List[Dict]:
        """
        Scrape jobs from specific Workday URLs.

        Args:
            workday_urls: List of Workday career URLs
            title: Optional title filter
            keywords: Optional keyword filters
            industry: Optional industry filter
            limit_per_url: Maximum jobs per URL

        Returns:
            List of all jobs from Workday sources
        """
        print(f"[Orchestrator] Scraping {len(workday_urls)} Workday URLs")

        all_jobs = []

        with ThreadPoolExecutor(max_workers=3) as executor:  # Limit Workday parallel requests
            futures = [
                executor.submit(
                    workday_scraper.scrape_jobs_from_url,
                    url,
                    title,
                    limit_per_url,
                    keywords,
                    industry
                )
                for url in workday_urls
            ]

            for future in futures:
                try:
                    jobs = future.result()
                    all_jobs.extend(jobs)
                except Exception as e:
                    print(f"[Orchestrator] Workday scraping error: {e}")

        print(f"[Orchestrator] Workday complete: {len(all_jobs)} jobs")
        return all_jobs


# Create singleton instance
scraper_orchestrator = ScraperOrchestrator()
