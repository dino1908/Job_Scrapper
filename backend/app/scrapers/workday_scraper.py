"""
Workday job scraper using Selenium.

Workday requires user to provide company-specific URLs since each company
has its own Workday careers site.
"""
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

from .base_scraper import BaseScraper
from .utils.rate_limiter import rate_limiter
from .utils.stealth_config import get_selenium_options, apply_stealth_to_selenium_driver


class WorkdayScraper(BaseScraper):
    """
    Scraper for Workday career sites.

    Note: Requires company-specific URLs as Workday is used by individual companies.
    Example URL: https://company.wd1.myworkdayjobs.com/CompanyCareers
    """

    def __init__(self):
        """Initialize Workday scraper."""
        super().__init__(source_name='workday')

    def scrape_jobs_from_url(
        self,
        workday_url: str,
        title: str = "",
        limit: int = 50,
        keywords: Optional[List[str]] = None,
        industry: str = ""
    ) -> List[Dict]:
        """
        Scrape jobs from a specific Workday URL.

        Args:
            workday_url: Full Workday careers URL
            title: Optional title query to filter results
            limit: Maximum number of jobs to return
            keywords: Resume-derived keywords
            industry: Resume-derived industry

        Returns:
            List of normalized job dictionaries
        """
        print(f"[Workday] Starting scrape from: {workday_url}")

        jobs = []
        driver = None

        try:
            # Setup Selenium driver
            options = get_selenium_options()
            driver = webdriver.Chrome(options=options)
            driver = apply_stealth_to_selenium_driver(driver)

            # Rate limiting
            rate_limiter.wait_if_needed(self.source_name, min_delay=3.0, max_delay=5.0)

            # Navigate to URL
            driver.get(workday_url)

            # Wait for job listings to load
            wait = WebDriverWait(driver, 15)

            try:
                # Wait for job list container
                wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-automation-id="jobList"], .jobList, [role="list"]'))
                )
            except TimeoutException:
                print("[Workday] Timeout waiting for job list to load")
                return []

            # Small delay for dynamic content
            time.sleep(2)

            # Scroll to load more jobs (Workday uses infinite scroll)
            self._scroll_to_load_jobs(driver, limit)

            # Find job elements
            job_elements = self._find_job_elements(driver)
            print(f"[Workday] Found {len(job_elements)} job elements")

            for elem in job_elements[:limit]:
                try:
                    job_data = self._extract_job_from_element(elem, driver)
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
                    print(f"[Workday] Error extracting job: {e}")
                    continue

        except Exception as e:
            print(f"[Workday] Scraping error: {e}")
        finally:
            if driver:
                driver.quit()

        self.log_scraping_result(len(jobs), 0)
        return jobs

    def scrape_jobs(
        self,
        title: str,
        location: str = "",
        limit: int = 50,
        keywords: Optional[List[str]] = None,
        industry: str = ""
    ) -> List[Dict]:
        """
        Not implemented for Workday - requires specific URLs.

        Use scrape_jobs_from_url() instead with company-specific Workday URLs.
        """
        print("[Workday] scrape_jobs() not implemented. Use scrape_jobs_from_url() with company URLs.")
        return []

    def _scroll_to_load_jobs(self, driver, max_jobs: int):
        """
        Scroll page to trigger infinite scroll loading.

        Args:
            driver: Selenium WebDriver
            max_jobs: Maximum jobs to load
        """
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scrolls = 5

        while scroll_attempts < max_scrolls:
            # Scroll down
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait for new content
            time.sleep(2)

            # Calculate new scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")

            # Break if no new content loaded
            if new_height == last_height:
                break

            last_height = new_height
            scroll_attempts += 1

    def _find_job_elements(self, driver) -> List:
        """
        Find job elements on the page.

        Args:
            driver: Selenium WebDriver

        Returns:
            List of WebElements
        """
        # Try multiple selectors as Workday structure varies
        selectors = [
            'li[data-automation-id="jobListItem"]',
            'li.job-list-item',
            '[data-automation-id="jobList"] li',
            '.jobList li',
            'li[role="listitem"]'
        ]

        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    return elements
            except NoSuchElementException:
                continue

        return []

    def _extract_job_from_element(self, elem, driver) -> Dict:
        """
        Extract job data from a job element.

        Args:
            elem: Selenium WebElement
            driver: Selenium WebDriver

        Returns:
            Raw job dictionary
        """
        # Extract title
        try:
            title_elem = elem.find_element(By.CSS_SELECTOR, 'a[data-automation-id="jobTitle"], .jobTitle, h3 a')
            title = title_elem.text.strip()
            job_link = title_elem.get_attribute('href')
        except NoSuchElementException:
            title = "Unknown Title"
            job_link = driver.current_url

        # Extract location
        try:
            location_elem = elem.find_element(By.CSS_SELECTOR, '[data-automation-id="jobLocation"], .jobLocation')
            location = location_elem.text.strip()
        except NoSuchElementException:
            location = ""

        # Extract job type/time type
        try:
            type_elem = elem.find_element(By.CSS_SELECTOR, '[data-automation-id="timeType"], .timeType')
            employment_type = type_elem.text.strip().lower()
        except NoSuchElementException:
            employment_type = "full-time"

        # Extract description (if available in listing)
        try:
            desc_elem = elem.find_element(By.CSS_SELECTOR, '.jobDescription, [data-automation-id="jobDescription"]')
            description = desc_elem.text.strip()
        except NoSuchElementException:
            description = ""

        # Determine company from URL
        company = self._extract_company_from_url(driver.current_url)

        # Extract skills
        skills = self.extract_skills_from_description(title + " " + description)

        # Determine job type
        job_type = None
        location_lower = location.lower()
        if 'remote' in location_lower:
            job_type = 'remote'
        elif 'hybrid' in location_lower:
            job_type = 'hybrid'

        return {
            'title': title,
            'company': company,
            'location': location,
            'job_type': job_type,
            'employment_type': employment_type,
            'description': description,
            'required_skills': skills,
            'required_experience': None,
            'salary_range': "",
            'apply_url': job_link
        }

    def _extract_company_from_url(self, url: str) -> str:
        """
        Extract company name from Workday URL.

        Args:
            url: Workday URL

        Returns:
            Company name
        """
        # Workday URLs are like: https://company.wd1.myworkdayjobs.com/...
        try:
            parts = url.split('.')
            if len(parts) > 0:
                company = parts[0].replace('https://', '').replace('http://', '')
                return company.title()
        except Exception:
            pass

        return "Unknown Company"


# Create instance
workday_scraper = WorkdayScraper()
