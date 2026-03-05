"""
Indeed job scraper using BeautifulSoup.
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from urllib.parse import urlencode
import re

from .base_scraper import BaseScraper
from .utils.rate_limiter import rate_limiter


class IndeedScraper(BaseScraper):
    """Scraper for Indeed.com using BeautifulSoup."""

    def __init__(self):
        """Initialize Indeed scraper."""
        super().__init__(source_name='indeed')
        self.base_url = 'https://www.indeed.com'

    def scrape_jobs(
        self,
        title: str,
        location: str = "",
        limit: int = 50,
        keywords: Optional[List[str]] = None,
        industry: str = ""
    ) -> List[Dict]:
        """
        Scrape jobs from Indeed.

        Args:
            title: Title query (e.g., 'python developer')
            location: Location filter
            limit: Maximum number of jobs to return
            keywords: Resume-derived keywords
            industry: Resume-derived industry

        Returns:
            List of normalized job dictionaries
        """
        print(f"[Indeed] Starting scrape with title: '{title}', location: '{location}'")

        jobs = []
        page = 0
        max_pages = min(10, (limit // 15) + 1)  # Indeed shows ~15 jobs per page

        while len(jobs) < limit and page < max_pages:
            try:
                # Rate limiting
                rate_limiter.wait_if_needed(self.source_name, min_delay=2.0, max_delay=5.0)

                # Build search URL
                params = {
                    'q': title,
                    'l': location,
                    'start': page * 10
                }
                search_url = f"{self.base_url}/jobs?{urlencode(params)}"

                # Make request
                headers = {
                    'User-Agent': self.get_user_agent(),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }

                response = requests.get(search_url, headers=headers, timeout=30)
                response.raise_for_status()

                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')

                # Find job cards
                job_cards = soup.find_all('div', class_=lambda x: x and 'job_seen_beacon' in x)

                if not job_cards:
                    # Try alternative selectors
                    job_cards = soup.find_all('div', {'class': 'slider_item'})

                if not job_cards:
                    # Try table-based layout
                    job_cards = soup.find_all('td', {'class': 'resultContent'})

                if not job_cards:
                    print(f"[Indeed] No job cards found on page {page}")
                    break

                print(f"[Indeed] Found {len(job_cards)} job cards on page {page}")

                # Extract job data
                for card in job_cards:
                    if len(jobs) >= limit:
                        break

                    try:
                        job_data = self._extract_job_from_card(card, soup)
                        if job_data:
                            if not self.matches_search_criteria(
                                text_chunks=[
                                    job_data.get('title', ''),
                                    job_data.get('company', ''),
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
                        print(f"[Indeed] Error extracting job: {e}")
                        continue

                page += 1

            except requests.RequestException as e:
                print(f"[Indeed] Request error on page {page}: {e}")
                break
            except Exception as e:
                print(f"[Indeed] Unexpected error on page {page}: {e}")
                break

        self.log_scraping_result(len(jobs), 0)
        return jobs

    def _extract_job_from_card(self, card, soup) -> Dict:
        """
        Extract job data from a job card element.

        Args:
            card: BeautifulSoup element representing a job card
            soup: Full page soup for context

        Returns:
            Raw job dictionary
        """
        # Extract job title
        title_elem = card.find('h2', class_='jobTitle') or card.find('a', class_='jcs-JobTitle')
        if not title_elem:
            title_elem = card.find('span', title=True)

        title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"

        # Extract company name
        company_elem = card.find('span', {'class': 'companyName'})
        if not company_elem:
            company_elem = card.find('span', {'data-testid': 'company-name'})

        company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"

        # Extract location
        location_elem = card.find('div', {'class': 'companyLocation'})
        if not location_elem:
            location_elem = card.find('span', {'data-testid': 'text-location'})

        location = location_elem.get_text(strip=True) if location_elem else ""

        # Extract job link
        link_elem = card.find('a', {'class': 'jcs-JobTitle'}) or card.find('a', href=re.compile(r'/rc/clk|/viewjob'))
        if not link_elem:
            link_elem = title_elem.find_parent('a') if title_elem else None

        if link_elem and link_elem.get('href'):
            job_link = link_elem['href']
            if not job_link.startswith('http'):
                job_link = self.base_url + job_link
        else:
            # Skip jobs without links
            return None

        # Extract job description (summary)
        description_elem = card.find('div', {'class': 'job-snippet'})
        if not description_elem:
            description_elem = card.find('div', {'class': 'jobCardShelfContainer'})

        description = description_elem.get_text(strip=True) if description_elem else ""

        # Extract salary if available
        salary_elem = card.find('div', {'class': 'salary-snippet'})
        if not salary_elem:
            salary_elem = card.find('span', {'class': 'salary-snippet-container'})

        salary = salary_elem.get_text(strip=True) if salary_elem else ""

        # Extract skills from description
        skills = self.extract_skills_from_description(description)

        # Determine job type
        job_type = None
        if description:
            description_lower = description.lower()
            if 'remote' in description_lower:
                job_type = 'remote'
            elif 'hybrid' in description_lower:
                job_type = 'hybrid'

        return {
            'title': title,
            'company': company,
            'location': location,
            'job_type': job_type,
            'employment_type': 'full-time',  # Indeed doesn't always show this
            'description': description,
            'required_skills': skills,
            'required_experience': None,
            'salary_range': salary,
            'apply_url': job_link
        }


# Create instance
indeed_scraper = IndeedScraper()
