"""
Scraper orchestrator to coordinate parallel job scraping from multiple sources.
"""
import inspect
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
import traceback

from ..scrapers.linkedin_scraper import linkedin_scraper


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

    def scrape_all_sources_sync(
        self,
        title: str,
        keywords: Optional[List[str]] = None,
        industry: str = "",
        location: str = "",
        recent_days: Optional[int] = None,
        limit_per_source: int = 50
    ) -> Dict[str, List[Dict]]:
        """
        Synchronous version of scrape_all_sources.

        Args:
            title: Job title query
            keywords: Resume-derived keywords
            industry: Resume-derived industry
            location: Location filter
            limit_per_source: Maximum jobs per source

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
                    recent_days,
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
        recent_days: Optional[int],
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
            scrape_kwargs = {
                "title": title,
                "location": location,
                "limit": limit,
                "keywords": keywords,
                "industry": industry,
            }
            # Pass recent_days only to scrapers that support it.
            try:
                params = inspect.signature(scraper.scrape_jobs).parameters
                if recent_days is not None and "recent_days" in params:
                    scrape_kwargs["recent_days"] = recent_days
            except Exception:
                pass

            jobs = scraper.scrape_jobs(
                **scrape_kwargs
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


# Create singleton instance
scraper_orchestrator = ScraperOrchestrator()
