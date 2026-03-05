"""
Base scraper class providing common functionality for all job scrapers.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import time
import random
from datetime import datetime
import re
from tenacity import retry, stop_after_attempt, wait_exponential


class BaseScraper(ABC):
    """Abstract base class for job scrapers."""

    def __init__(self, source_name: str):
        """
        Initialize the scraper.

        Args:
            source_name: Name of the job source (e.g., 'indeed', 'linkedin')
        """
        self.source_name = source_name
        self.jobs_scraped = []

    @abstractmethod
    def scrape_jobs(
        self,
        title: str,
        location: str = "",
        limit: int = 50,
        keywords: Optional[List[str]] = None,
        industry: str = ""
    ) -> List[Dict]:
        """
        Scrape jobs from the source.

        Args:
            title: Title query (e.g., 'python developer')
            location: Location filter
            limit: Maximum number of jobs to scrape
            keywords: Resume-derived keywords used for filtering
            industry: Resume-derived industry used for filtering

        Returns:
            List of job dictionaries
        """
        pass

    def matches_search_criteria(
        self,
        *,
        text_chunks: List[str],
        title: str,
        keywords: Optional[List[str]] = None,
        industry: str = ""
    ) -> bool:
        """
        Check if a job matches title/keywords/industry search criteria.

        Args:
            text_chunks: Job text fields to evaluate
            title: Target title
            keywords: Keyword list
            industry: Industry filter

        Returns:
            True if the job passes filters, else False
        """
        combined_text = " ".join([chunk for chunk in text_chunks if chunk]).lower()
        if not combined_text:
            return False

        # Title must match either exact phrase or a meaningful subset of tokens.
        title_ok = True
        if title:
            title_lower = title.lower().strip()
            if title_lower in combined_text:
                title_ok = True
            else:
                title_tokens = [t for t in re.split(r"[\s,/\\-]+", title_lower) if len(t) > 2]
                token_matches = sum(1 for token in title_tokens if token in combined_text)
                required_matches = 1 if len(title_tokens) <= 2 else 2
                title_ok = token_matches >= required_matches

        # If keywords are provided, require at least one keyword match.
        keyword_ok = True
        keyword_list = [kw.lower().strip() for kw in (keywords or []) if kw and kw.strip()]
        if keyword_list:
            keyword_ok = any(keyword in combined_text for keyword in keyword_list)

        # If industry is provided, require industry text to appear.
        industry_ok = True
        if industry:
            industry_lower = industry.lower().strip()
            generic_industries = {"technology", "tech", "software", "it", "information technology"}
            if industry_lower not in generic_industries:
                industry_ok = industry_lower in combined_text

        return title_ok and keyword_ok and industry_ok

    def normalize_job_data(self, raw_data: Dict) -> Dict:
        """
        Normalize raw job data to standard format.

        Args:
            raw_data: Raw job data from scraper

        Returns:
            Normalized job dictionary
        """
        normalized = {
            'title': self._clean_text(raw_data.get('title', '')),
            'company': self._clean_text(raw_data.get('company', '')),
            'location': self._clean_text(raw_data.get('location', '')),
            'job_type': self._normalize_job_type(raw_data.get('job_type', '')),
            'employment_type': self._normalize_employment_type(raw_data.get('employment_type', '')),
            'description': self._clean_text(raw_data.get('description', '')),
            'required_skills': raw_data.get('required_skills', []),
            'required_experience': raw_data.get('required_experience'),
            'salary_range': raw_data.get('salary_range'),
            'apply_url': raw_data.get('apply_url', ''),
            'source': self.source_name,
            'posted_date': raw_data.get('posted_date'),
            'scraped_at': datetime.utcnow()
        }

        # Validate required fields
        if not normalized['title'] or not normalized['company'] or not normalized['apply_url']:
            raise ValueError(f"Missing required fields in job data: {raw_data}")

        return normalized

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove extra whitespace
        text = ' '.join(text.split())

        # Remove special characters
        text = text.replace('\x00', '')

        return text.strip()

    def _normalize_job_type(self, job_type: str) -> Optional[str]:
        """
        Normalize job type to standard values.

        Args:
            job_type: Raw job type string

        Returns:
            Normalized job type (remote/hybrid/onsite) or None
        """
        if not job_type:
            return None

        job_type_lower = job_type.lower()

        if 'remote' in job_type_lower:
            return 'remote'
        elif 'hybrid' in job_type_lower:
            return 'hybrid'
        elif 'on-site' in job_type_lower or 'onsite' in job_type_lower or 'office' in job_type_lower:
            return 'onsite'

        return None

    def _normalize_employment_type(self, employment_type: str) -> Optional[str]:
        """
        Normalize employment type to standard values.

        Args:
            employment_type: Raw employment type string

        Returns:
            Normalized employment type or None
        """
        if not employment_type:
            return None

        employment_lower = employment_type.lower()

        if 'full' in employment_lower and 'time' in employment_lower:
            return 'full-time'
        elif 'part' in employment_lower and 'time' in employment_lower:
            return 'part-time'
        elif 'contract' in employment_lower:
            return 'contract'
        elif 'intern' in employment_lower:
            return 'internship'

        return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def retry_with_backoff(self, func, *args, **kwargs):
        """
        Retry a function with exponential backoff.

        Args:
            func: Function to retry
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result
        """
        return func(*args, **kwargs)

    def random_delay(self, min_seconds: float = 2.0, max_seconds: float = 5.0):
        """
        Add a random delay to avoid rate limiting.

        Args:
            min_seconds: Minimum delay in seconds
            max_seconds: Maximum delay in seconds
        """
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def extract_skills_from_description(self, description: str) -> List[str]:
        """
        Extract skills from job description using keyword matching.

        Args:
            description: Job description text

        Returns:
            List of extracted skills
        """
        if not description:
            return []

        # Common tech skills to look for
        skill_keywords = [
            # Programming Languages
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'php',
            'go', 'golang', 'rust', 'swift', 'kotlin', 'scala', 'r', 'matlab',

            # Frontend
            'react', 'angular', 'vue', 'vue.js', 'svelte', 'html', 'css', 'sass',
            'less', 'tailwind', 'bootstrap', 'jquery', 'webpack', 'redux',

            # Backend
            'node.js', 'express', 'fastapi', 'django', 'flask', 'spring', 'spring boot',
            '.net', 'asp.net', 'rails', 'laravel', 'nest.js',

            # Databases
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
            'cassandra', 'dynamodb', 'oracle', 'sqlite',

            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'jenkins',
            'ci/cd', 'terraform', 'ansible', 'github actions', 'gitlab',

            # Data & ML
            'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'scikit-learn',
            'pandas', 'numpy', 'data analysis', 'data science', 'ai', 'nlp',

            # Other
            'git', 'agile', 'scrum', 'rest', 'api', 'graphql', 'microservices',
            'linux', 'unix', 'bash', 'powershell'
        ]

        description_lower = description.lower()
        found_skills = []

        for skill in skill_keywords:
            if skill in description_lower:
                # Capitalize properly
                if skill == 'api':
                    found_skills.append('API')
                elif skill == 'html':
                    found_skills.append('HTML')
                elif skill == 'css':
                    found_skills.append('CSS')
                elif skill == 'sql':
                    found_skills.append('SQL')
                else:
                    found_skills.append(skill.title())

        # Remove duplicates while preserving order
        seen = set()
        unique_skills = []
        for skill in found_skills:
            if skill.lower() not in seen:
                seen.add(skill.lower())
                unique_skills.append(skill)

        return unique_skills

    def get_user_agent(self) -> str:
        """
        Get a random user agent string.

        Returns:
            User agent string
        """
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        return random.choice(user_agents)

    def log_scraping_result(self, success_count: int, error_count: int):
        """
        Log scraping results.

        Args:
            success_count: Number of jobs successfully scraped
            error_count: Number of errors encountered
        """
        print(f"[{self.source_name}] Scraped {success_count} jobs, {error_count} errors")
