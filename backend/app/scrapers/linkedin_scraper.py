"""LinkedIn job scraper using LinkedIn guest job search endpoints."""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import re
from urllib.parse import urlsplit, urlunsplit
import requests
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper
from .utils.rate_limiter import rate_limiter


class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn public guest jobs pages."""

    def __init__(self):
        """Initialize LinkedIn scraper."""
        super().__init__(source_name='linkedin')
        self.base_url = 'https://www.linkedin.com'
        self.search_api_url = f"{self.base_url}/jobs-guest/jobs/api/seeMoreJobPostings/search"
        self.max_jobs = 200
        self.recent_days = 10

    def scrape_jobs(
        self,
        title: str,
        location: str = "",
        limit: int = 30,
        keywords: Optional[List[str]] = None,
        industry: str = "",
        recent_days: Optional[int] = None
    ) -> List[Dict]:
        """
        Scrape jobs from LinkedIn.

        Args:
            title: Title query (e.g., 'software engineer')
            location: Location filter
            limit: Maximum number of jobs to return (capped at 30)
            keywords: Resume-derived keywords
            industry: Resume-derived industry

        Returns:
            List of normalized job dictionaries
        """
        # Target at least 50 by default, up to max_jobs.
        limit = min(max(limit, 50), self.max_jobs)
        effective_recent_days = recent_days if recent_days is not None else self.recent_days
        effective_recent_days = max(1, int(effective_recent_days))
        title = (title or "").strip() or "software engineer"
        location = (location or "").strip()
        print(f"[LinkedIn] Starting scrape with title='{title}', location='{location}'")

        title_tokens = [token for token in re.split(r"[\s,/\\-]+", title) if token]
        title_short = " ".join(title_tokens[:4]) if title_tokens else title

        effective_query_terms = [title]
        if keywords:
            effective_query_terms.extend([kw.strip() for kw in keywords[:3] if kw and kw.strip()])
        effective_query = " ".join([term for term in effective_query_terms if term])

        headers = {
            'User-Agent': self.get_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive'
        }

        # Use exact user-supplied location when provided.
        location_variants_raw = [location] if location else [""]
        location_variants = []
        seen_locations = set()
        for loc in location_variants_raw:
            normalized_loc = (loc or "").strip().lower()
            if normalized_loc in seen_locations:
                continue
            seen_locations.add(normalized_loc)
            location_variants.append(loc)

        # Keep query variants focused to avoid drifting into unrelated roles.
        query_variants_raw = [
            effective_query,
            title,
            title_short,
        ]

        title_lower = title.lower().strip().replace(".", "")
        if title_lower == "pm":
            query_variants_raw.extend(["product manager", "program manager", "project manager"])
        elif "product manager" in title_lower:
            query_variants_raw.extend(["product manager", "product management"])

        query_variants = []
        seen_queries = set()
        for query_variant in query_variants_raw:
            normalized_query = (query_variant or "").strip().lower()
            if not normalized_query or normalized_query in seen_queries:
                continue
            seen_queries.add(normalized_query)
            query_variants.append(query_variant)

        unique_jobs: List[Dict] = []
        seen_keys = set()
        cutoff = datetime.utcnow() - timedelta(days=effective_recent_days)

        for query_text in query_variants:
            if len(unique_jobs) >= limit:
                break
            if not query_text or not query_text.strip():
                continue

            for query_location in location_variants:
                if len(unique_jobs) >= limit:
                    break

                batch = self._run_search(
                    query=query_text.strip(),
                    location=query_location,
                    headers=headers,
                    limit=limit,
                    recent_days=effective_recent_days
                )

                for job in batch:
                    posted_date = job.get("posted_date")
                    if posted_date and posted_date < cutoff:
                        continue

                    unique_key = (
                        job.get("source"),
                        job.get("apply_url") or "",
                        job.get("title", "").lower().strip(),
                        job.get("company", "").lower().strip()
                    )
                    if unique_key in seen_keys:
                        continue
                    seen_keys.add(unique_key)
                    unique_jobs.append(job)

                    if len(unique_jobs) >= limit:
                        break

                print(
                    f"[LinkedIn] query='{query_text}' location='{query_location or 'Any'}' "
                    f"added={len(batch)} total={len(unique_jobs)}"
                )

        unique_jobs.sort(key=lambda job: job.get("posted_date") or datetime.min, reverse=True)
        self.log_scraping_result(len(unique_jobs), 0)
        return unique_jobs[:limit]

    def _run_search(
        self,
        *,
        query: str,
        location: str,
        headers: Dict[str, str],
        limit: int,
        recent_days: int
    ) -> List[Dict]:
        """Execute one LinkedIn search run and return normalized jobs."""
        all_jobs: List[Dict] = []
        start = 0
        page_size = 25
        # Go deeper than requested limit because we'll dedupe/filter later.
        max_pages = min(20, max(3, (limit * 2 + page_size - 1) // page_size))

        for _ in range(max_pages):
            rate_limiter.wait_if_needed(self.source_name, min_delay=1.0, max_delay=2.0)
            params = {
                "keywords": query,
                "location": location or "",
                "start": start,
                "f_TPR": f"r{recent_days * 24 * 60 * 60}",
                "sortBy": "DD"
            }
            start += page_size

            try:
                response = requests.get(
                    self.search_api_url,
                    params=params,
                    headers=headers,
                    timeout=30
                )
                response.raise_for_status()
            except requests.RequestException as exc:
                print(f"[LinkedIn] Search request failed for query='{query}': {exc}")
                break

            soup = BeautifulSoup(response.text, "html.parser")
            cards = soup.select("li")
            if not cards:
                break

            for card in cards:
                if len(all_jobs) >= (limit * 2):
                    break

                job_data = self._extract_job_from_card(card)
                if not job_data:
                    continue

                try:
                    normalized = self.normalize_job_data(job_data)
                    all_jobs.append(normalized)
                except Exception as exc:
                    print(f"[LinkedIn] Failed to normalize job: {exc}")

            if len(all_jobs) >= (limit * 2):
                break

        return all_jobs

    def _extract_job_from_card(self, card) -> Optional[Dict]:
        """Extract job fields from LinkedIn guest search card HTML."""
        title_elem = card.select_one("h3.base-search-card__title") or card.select_one("h3")
        company_elem = (
            card.select_one("h4.base-search-card__subtitle a")
            or card.select_one("h4.base-search-card__subtitle")
        )
        location_elem = card.select_one("span.job-search-card__location")
        link_elem = card.select_one("a.base-card__full-link") or card.select_one("a[href*='/jobs/view/']")
        time_elem = card.select_one("time")

        title = title_elem.get_text(" ", strip=True) if title_elem else ""
        company = company_elem.get_text(" ", strip=True) if company_elem else ""
        location = location_elem.get_text(" ", strip=True) if location_elem else ""
        link = link_elem.get("href", "").strip() if link_elem else ""

        if not title or not company or not link:
            return None

        if link.startswith("/"):
            link = f"{self.base_url}{link}"

        # Canonicalize URL to avoid duplicate entries with different tracking params.
        parsed_link = urlsplit(link)
        link = urlunsplit((parsed_link.scheme, parsed_link.netloc, parsed_link.path, "", ""))

        posted_date = self._parse_linkedin_posted_date(time_elem)

        location_lower = location.lower()
        job_type = None
        if "remote" in location_lower:
            job_type = "remote"
        elif "hybrid" in location_lower:
            job_type = "hybrid"

        job_id = self._extract_job_id(link)
        if not job_id:
            data_urn = card.get("data-entity-urn", "")
            urn_match = re.search(r"jobPosting:(\d+)", data_urn)
            job_id = urn_match.group(1) if urn_match else ""

        return {
            "title": title,
            "company": company,
            "location": location,
            "job_type": job_type,
            "employment_type": "full-time",
            "description": "",
            "required_skills": [],
            "required_experience": None,
            "salary_range": "",
            "apply_url": link,
            "posted_date": posted_date
        }

    def _extract_job_id(self, url: str) -> str:
        """Extract LinkedIn numeric job id from URL."""
        match = re.search(r"/jobs/view/(\d+)", url)
        return match.group(1) if match else ""

    def _parse_linkedin_posted_date(self, time_elem) -> Optional[datetime]:
        """Parse posted date from LinkedIn time element."""
        if not time_elem:
            return None

        datetime_attr = (time_elem.get("datetime") or "").strip()
        if datetime_attr:
            try:
                return datetime.fromisoformat(datetime_attr.replace("Z", "+00:00")).replace(tzinfo=None)
            except ValueError:
                pass

        relative_text = time_elem.get_text(" ", strip=True).lower()
        if not relative_text:
            return None

        return self._parse_relative_date(relative_text)

    def _parse_relative_date(self, text: str) -> Optional[datetime]:
        """Parse relative date strings like '2 days ago'."""
        now = datetime.utcnow()

        if "today" in text or "just now" in text:
            return now
        if "yesterday" in text:
            return now - timedelta(days=1)

        patterns = [
            (r"(\d+)\s*hour", "hours"),
            (r"(\d+)\s*day", "days"),
            (r"(\d+)\s*week", "weeks"),
            (r"(\d+)\s*month", "days"),  # approximated below
        ]

        for pattern, unit in patterns:
            match = re.search(pattern, text)
            if not match:
                continue
            value = int(match.group(1))
            if unit == "hours":
                return now - timedelta(hours=value)
            if unit == "days":
                return now - timedelta(days=value)
            if unit == "weeks":
                return now - timedelta(weeks=value)
            if "month" in pattern:
                return now - timedelta(days=value * 30)

        return None


# Create instance
linkedin_scraper = LinkedInScraper()
