"""
Wellfound (formerly AngelList) job scraper using BeautifulSoup.
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

from .base_scraper import BaseScraper
from .utils.rate_limiter import rate_limiter


class WellfoundScraper(BaseScraper):
    """Scraper for Wellfound.com (formerly AngelList Talent)."""

    def __init__(self):
        """Initialize Wellfound scraper."""
        super().__init__(source_name='wellfound')
        self.base_url = 'https://wellfound.com'

    def scrape_jobs(
        self,
        title: str,
        location: str = "",
        limit: int = 50,
        keywords: Optional[List[str]] = None,
        industry: str = ""
    ) -> List[Dict]:
        """
        Scrape jobs from Wellfound.

        Note: Wellfound has anti-bot measures. This scraper may have limited success.

        Args:
            title: Title query (e.g., 'software engineer')
            location: Location filter
            limit: Maximum number of jobs to return
            keywords: Resume-derived keywords
            industry: Resume-derived industry

        Returns:
            List of normalized job dictionaries
        """
        print(f"[Wellfound] Starting scrape with title: '{title}', location: '{location}'")

        jobs = []

        try:
            # Rate limiting
            rate_limiter.wait_if_needed(self.source_name, min_delay=3.0, max_delay=6.0)

            # Build search URL
            # Wellfound uses role-based URLs
            role_slug = title.lower().replace(' ', '-') if title else 'software-engineer'
            search_url = f"{self.base_url}/role/r/{role_slug}"

            # Make request
            headers = {
                'User-Agent': self.get_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }

            response = requests.get(search_url, headers=headers, timeout=30)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find job listings
            # Note: Wellfound structure may change; these selectors are approximate
            job_elements = soup.find_all('div', {'data-test': 'JobSearchResult'})

            if not job_elements:
                # Try alternative selectors
                job_elements = soup.find_all('div', class_=lambda x: x and 'job' in x.lower())

            print(f"[Wellfound] Found {len(job_elements)} job elements")

            for elem in job_elements:
                if len(jobs) >= limit:
                    break

                try:
                    job_data = self._extract_job_from_element(elem)
                    if job_data:
                        if not self.matches_search_criteria(
                            text_chunks=[
                                job_data.get('title', ''),
                                job_data.get('company', ''),
                                job_data.get('location', ''),
                                job_data.get('description', ''),
                                ' '.join(job_data.get('required_skills', []))
                            ],
                            title=title,
                            keywords=keywords,
                            industry=industry
                        ):
                            continue
                        normalized_job = self.normalize_job_data(job_data)
                        jobs.append(normalized_job)
                except Exception as e:
                    print(f"[Wellfound] Error extracting job: {e}")
                    continue

        except requests.RequestException as e:
            print(f"[Wellfound] Request error: {e}")
            print(f"[Wellfound] Note: Wellfound may require authentication or has anti-bot measures")
        except Exception as e:
            print(f"[Wellfound] Unexpected error: {e}")

        self.log_scraping_result(len(jobs), 0)
        return jobs

    def _extract_job_from_element(self, elem) -> Dict:
        """
        Extract job data from a job element.

        Args:
            elem: BeautifulSoup element

        Returns:
            Raw job dictionary
        """
        # Extract title
        title_elem = elem.find('a', class_=lambda x: x and 'title' in x.lower())
        if not title_elem:
            title_elem = elem.find('h2') or elem.find('h3')

        title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"

        # Extract company
        company_elem = elem.find('div', class_=lambda x: x and 'company' in x.lower())
        if not company_elem:
            company_elem = elem.find('span', class_=lambda x: x and 'company' in x.lower())

        company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"

        # Extract link
        link_elem = elem.find('a', href=True)
        if link_elem:
            job_link = link_elem['href']
            if not job_link.startswith('http'):
                job_link = self.base_url + job_link
        else:
            return None

        # Extract location
        location_elem = elem.find('span', class_=lambda x: x and 'location' in x.lower())
        location = location_elem.get_text(strip=True) if location_elem else ""

        # Extract description
        description_elem = elem.find('div', class_=lambda x: x and 'description' in x.lower())
        description = description_elem.get_text(strip=True) if description_elem else ""

        # Extract skills
        skills = self.extract_skills_from_description(description + " " + title)

        return {
            'title': title,
            'company': company,
            'location': location,
            'job_type': 'remote' if 'remote' in location.lower() else None,
            'employment_type': 'full-time',
            'description': description,
            'required_skills': skills,
            'required_experience': None,
            'salary_range': "",
            'apply_url': job_link
        }


# Create instance
wellfound_scraper = WellfoundScraper()
