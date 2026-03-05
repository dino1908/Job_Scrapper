"""
RemoteOK job scraper using their public API.
"""
import requests
from typing import List, Dict, Optional
from .base_scraper import BaseScraper
from .utils.rate_limiter import rate_limiter


class RemoteOKScraper(BaseScraper):
    """Scraper for RemoteOK.com using their API."""

    def __init__(self):
        """Initialize RemoteOK scraper."""
        super().__init__(source_name='remoteok')
        self.api_url = 'https://remoteok.com/api'

    def scrape_jobs(
        self,
        title: str,
        location: str = "",
        limit: int = 50,
        keywords: Optional[List[str]] = None,
        industry: str = ""
    ) -> List[Dict]:
        """
        Scrape jobs from RemoteOK.

        Args:
            title: Title query used to filter results
            location: Location filter (not used - all jobs are remote)
            limit: Maximum number of jobs to return
            keywords: Resume-derived keywords
            industry: Resume-derived industry

        Returns:
            List of normalized job dictionaries
        """
        print(f"[RemoteOK] Starting scrape with title: '{title}'")

        try:
            # Rate limiting
            rate_limiter.wait_if_needed(self.source_name, min_delay=1.0, max_delay=2.0)

            # Make API request
            headers = {
                'User-Agent': self.get_user_agent(),
                'Accept': 'application/json'
            }

            response = requests.get(self.api_url, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()

            # First item is metadata, skip it
            jobs = data[1:] if len(data) > 1 else []

            # Filter and normalize jobs
            normalized_jobs = []
            for job_data in jobs:
                if len(normalized_jobs) >= limit:
                    break

                # Filter with title/keywords/industry criteria
                if not self.matches_search_criteria(
                    text_chunks=[
                        job_data.get('position', ''),
                        job_data.get('company', ''),
                        ' '.join(job_data.get('tags', [])),
                        job_data.get('description', '')
                    ],
                    title=title,
                    keywords=keywords,
                    industry=industry
                ):
                    continue

                try:
                    normalized_job = self._normalize_remoteok_job(job_data)
                    normalized_jobs.append(normalized_job)
                except Exception as e:
                    print(f"[RemoteOK] Error normalizing job: {e}")
                    continue

            self.log_scraping_result(len(normalized_jobs), len(jobs) - len(normalized_jobs))
            return normalized_jobs

        except requests.RequestException as e:
            print(f"[RemoteOK] Request error: {e}")
            return []
        except Exception as e:
            print(f"[RemoteOK] Unexpected error: {e}")
            return []

    def _normalize_remoteok_job(self, job_data: Dict) -> Dict:
        """
        Normalize RemoteOK job data.

        Args:
            job_data: Raw job data from RemoteOK API

        Returns:
            Normalized job dictionary
        """
        # Extract skills from tags
        tags = job_data.get('tags', [])
        skills = [tag for tag in tags if tag] if isinstance(tags, list) else []

        # Build apply URL
        slug = job_data.get('slug', '')
        apply_url = f"https://remoteok.com/remote-jobs/{slug}" if slug else job_data.get('url', '')

        raw_data = {
            'title': job_data.get('position', 'Unknown Position'),
            'company': job_data.get('company', 'Unknown Company'),
            'location': job_data.get('location', 'Remote'),
            'job_type': 'remote',  # All RemoteOK jobs are remote
            'employment_type': self._extract_employment_type(job_data),
            'description': job_data.get('description', ''),
            'required_skills': skills,
            'required_experience': None,
            'salary_range': self._extract_salary(job_data),
            'apply_url': apply_url
        }

        return self.normalize_job_data(raw_data)

    def _extract_employment_type(self, job_data: Dict) -> str:
        """
        Extract employment type from job data.

        Args:
            job_data: Raw job data

        Returns:
            Employment type string
        """
        # Check tags for employment type indicators
        tags = job_data.get('tags', [])
        if isinstance(tags, list):
            tags_lower = [tag.lower() for tag in tags]
            if 'contract' in tags_lower:
                return 'contract'
            elif 'part-time' in tags_lower or 'part time' in tags_lower:
                return 'part-time'

        # Default to full-time
        return 'full-time'

    def _extract_salary(self, job_data: Dict) -> str:
        """
        Extract salary information.

        Args:
            job_data: Raw job data

        Returns:
            Salary string or empty string
        """
        salary_min = job_data.get('salary_min')
        salary_max = job_data.get('salary_max')

        if salary_min and salary_max:
            return f"${salary_min:,} - ${salary_max:,}"
        elif salary_min:
            return f"${salary_min:,}+"

        return ""


# Create instance
remoteok_scraper = RemoteOKScraper()
