"""
Remotive job scraper using their public API.
"""
import requests
from typing import List, Dict, Optional
from .base_scraper import BaseScraper
from .utils.rate_limiter import rate_limiter


class RemotiveScraper(BaseScraper):
    """Scraper for Remotive.com using their API."""

    def __init__(self):
        """Initialize Remotive scraper."""
        super().__init__(source_name='remotive')
        self.api_url = 'https://remotive.com/api/remote-jobs'

    def scrape_jobs(
        self,
        title: str,
        location: str = "",
        limit: int = 50,
        keywords: Optional[List[str]] = None,
        industry: str = ""
    ) -> List[Dict]:
        """
        Scrape jobs from Remotive.

        Args:
            title: Title query (used to filter results)
            location: Location filter (not used - all jobs are remote)
            limit: Maximum number of jobs to return
            keywords: Resume-derived keywords
            industry: Resume-derived industry

        Returns:
            List of normalized job dictionaries
        """
        print(f"[Remotive] Starting scrape with title: '{title}'")

        try:
            # Rate limiting
            rate_limiter.wait_if_needed(self.source_name, min_delay=1.0, max_delay=2.0)

            # Make API request
            headers = {
                'User-Agent': self.get_user_agent(),
                'Accept': 'application/json'
            }

            params = {}
            if title:
                params['search'] = title

            response = requests.get(self.api_url, headers=headers, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            jobs = data.get('jobs', [])

            # Normalize jobs
            normalized_jobs = []
            for job_data in jobs:
                if len(normalized_jobs) >= limit:
                    break

                if not self.matches_search_criteria(
                    text_chunks=[
                        job_data.get('title', ''),
                        job_data.get('category', ''),
                        job_data.get('company_name', ''),
                        ' '.join(job_data.get('tags', [])),
                        job_data.get('description', '')
                    ],
                    title=title,
                    keywords=keywords,
                    industry=industry
                ):
                    continue

                try:
                    normalized_job = self._normalize_remotive_job(job_data)
                    normalized_jobs.append(normalized_job)
                except Exception as e:
                    print(f"[Remotive] Error normalizing job: {e}")
                    continue

            self.log_scraping_result(len(normalized_jobs), len(jobs) - len(normalized_jobs))
            return normalized_jobs

        except requests.RequestException as e:
            print(f"[Remotive] Request error: {e}")
            return []
        except Exception as e:
            print(f"[Remotive] Unexpected error: {e}")
            return []

    def _normalize_remotive_job(self, job_data: Dict) -> Dict:
        """
        Normalize Remotive job data.

        Args:
            job_data: Raw job data from Remotive API

        Returns:
            Normalized job dictionary
        """
        # Extract skills from description and tags
        description = job_data.get('description', '')
        tags = job_data.get('tags', [])

        skills = []
        if isinstance(tags, list):
            skills.extend(tags)

        # Add skills from description
        skills.extend(self.extract_skills_from_description(description))

        # Remove duplicates
        skills = list(set(skills))

        raw_data = {
            'title': job_data.get('title', 'Unknown Position'),
            'company': job_data.get('company_name', 'Unknown Company'),
            'location': self._extract_location(job_data),
            'job_type': 'remote',  # All Remotive jobs are remote
            'employment_type': self._extract_employment_type(job_data),
            'description': description,
            'required_skills': skills[:20],  # Limit to 20 skills
            'required_experience': None,
            'salary_range': job_data.get('salary', ''),
            'apply_url': job_data.get('url', '')
        }

        return self.normalize_job_data(raw_data)

    def _extract_location(self, job_data: Dict) -> str:
        """
        Extract location information.

        Args:
            job_data: Raw job data

        Returns:
            Location string
        """
        candidate_required_location = job_data.get('candidate_required_location', '')
        if candidate_required_location:
            return f"Remote ({candidate_required_location})"
        return "Remote (Worldwide)"

    def _extract_employment_type(self, job_data: Dict) -> str:
        """
        Extract employment type from job data.

        Args:
            job_data: Raw job data

        Returns:
            Employment type string
        """
        job_type = job_data.get('job_type', '').lower()

        if 'contract' in job_type:
            return 'contract'
        elif 'part-time' in job_type or 'part time' in job_type:
            return 'part-time'
        elif 'full-time' in job_type or 'full time' in job_type:
            return 'full-time'

        # Default to full-time
        return 'full-time'


# Create instance
remotive_scraper = RemotiveScraper()
