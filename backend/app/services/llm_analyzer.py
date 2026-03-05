"""
LLM-based resume analyzer using Mistral AI.
"""
import json
import re
from typing import Dict, List
import requests
from ..config import settings
from ..schemas import ResumeProfile


class LLMAnalyzer:
    """Analyze resume text using Mistral AI to extract structured data."""

    def __init__(self):
        """Initialize Mistral client."""
        self.api_key = (settings.MISTRAL_API_KEY or "").strip()
        self.base_url = "https://api.mistral.ai/v1/chat/completions"

        if self.api_key:
            print("✅ Mistral API configured")

    def analyze_resume(self, resume_text: str) -> ResumeProfile:
        """
        Analyze resume text and extract structured profile.

        Args:
            resume_text: Raw resume text

        Returns:
            ResumeProfile with extracted data

        Raises:
            ValueError: If analysis fails
        """
        # Try Mistral first
        if self.api_key:
            try:
                return self._analyze_with_mistral(resume_text)
            except Exception as e:
                print(f"⚠️  Mistral analysis failed: {e}")

        # Fallback to basic extraction
        print("⚠️  Falling back to basic extraction")
        return self._basic_extraction(resume_text)

    def _analyze_with_mistral(self, resume_text: str) -> ResumeProfile:
        """
        Analyze resume using Mistral AI.

        Args:
            resume_text: Raw resume text

        Returns:
            ResumeProfile
        """
        prompt = self._build_analysis_prompt(resume_text)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "mistral-large-latest",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 1000
        }

        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        result = response.json()
        result_text = result["choices"][0]["message"]["content"]

        # Parse JSON response
        profile_data = self._parse_llm_response(result_text)
        return ResumeProfile(**profile_data)

    def _build_analysis_prompt(self, resume_text: str) -> str:
        """
        Build the analysis prompt for Mistral.

        Args:
            resume_text: Raw resume text

        Returns:
            Formatted prompt
        """
        return f"""Analyze this resume and extract job search inputs for a scraper.

Return ONLY valid JSON with these exact keys:
1. "title": primary target/current role title as a string
2. "keywords": array of 8-20 relevant search keywords (skills, tools, domain terms)
3. "industry": one primary industry as a string
4. "location": location preference or current location as a string
5. "job_type_preference": one of "remote", "hybrid", "onsite", or "any"

Rules:
- Keep "title" concise and specific (for example: "Senior Backend Engineer")
- "keywords" should be practical search terms, not full sentences
- Return only JSON, no markdown

Resume:
{resume_text}

JSON Response:"""

    def _parse_llm_response(self, response_text: str) -> Dict:
        """
        Parse LLM response and extract JSON.

        Args:
            response_text: Raw LLM response

        Returns:
            Parsed dictionary

        Raises:
            ValueError: If parsing fails
        """
        # Try to extract JSON from response
        try:
            # First, try direct JSON parsing
            parsed = json.loads(response_text)
            return self._normalize_profile_data(parsed)
        except json.JSONDecodeError:
            # Try to find JSON in markdown code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group(1))
                    return self._normalize_profile_data(parsed)
                except json.JSONDecodeError:
                    pass

            # Try to find any JSON object
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group(0))
                    return self._normalize_profile_data(parsed)
                except json.JSONDecodeError:
                    pass

            raise ValueError(f"Failed to parse JSON from LLM response: {response_text[:200]}")

    def _normalize_profile_data(self, profile_data: Dict) -> Dict:
        """
        Normalize LLM output to ResumeProfile schema.

        Supports both the new structure and legacy keys.
        """
        title = (profile_data.get("title") or "").strip()
        if not title and profile_data.get("roles"):
            roles = profile_data.get("roles") or []
            if isinstance(roles, list) and roles:
                title = str(roles[0]).strip()

        keywords = profile_data.get("keywords") or []
        if not keywords and profile_data.get("skills"):
            keywords = profile_data.get("skills") or []
        if isinstance(keywords, str):
            keywords = [kw.strip() for kw in keywords.split(",") if kw.strip()]
        if not isinstance(keywords, list):
            keywords = []

        normalized_keywords: List[str] = []
        seen = set()
        for keyword in keywords:
            if not keyword:
                continue
            clean_keyword = str(keyword).strip()
            if clean_keyword and clean_keyword.lower() not in seen:
                seen.add(clean_keyword.lower())
                normalized_keywords.append(clean_keyword)

        industry = (profile_data.get("industry") or "").strip()
        if not industry and profile_data.get("industries"):
            industries = profile_data.get("industries") or []
            if isinstance(industries, list) and industries:
                industry = str(industries[0]).strip()

        job_type_preference = str(
            profile_data.get("job_type_preference", "any")
        ).strip().lower()
        if job_type_preference not in {"remote", "hybrid", "onsite", "any"}:
            job_type_preference = "any"

        return {
            "title": title,
            "keywords": normalized_keywords[:20],
            "industry": industry,
            "location": str(profile_data.get("location", "")).strip(),
            "job_type_preference": job_type_preference
        }

    def _basic_extraction(self, resume_text: str) -> ResumeProfile:
        """
        Basic regex-based extraction as fallback.

        Args:
            resume_text: Raw resume text

        Returns:
            ResumeProfile with basic extracted data
        """
        # Extract skills/keywords
        common_keywords = [
            'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
            'node.js', 'express', 'fastapi', 'django', 'flask', 'sql', 'mysql',
            'postgresql', 'mongodb', 'redis', 'aws', 'azure', 'gcp', 'docker',
            'kubernetes', 'git', 'agile', 'scrum', 'ci/cd', 'machine learning',
            'data analysis', 'api', 'rest', 'graphql', 'html', 'css', 'sass'
        ]

        text_lower = resume_text.lower()
        keywords = [keyword for keyword in common_keywords if keyword in text_lower]

        # Extract target title
        title_patterns = [
            r'(senior software engineer|software engineer|backend engineer|frontend engineer|full[\s-]?stack engineer)',
            r'(data scientist|data analyst|machine learning engineer|ai engineer)',
            r'(product manager|project manager|engineering manager)',
            r'(devops engineer|site reliability engineer|qa engineer)'
        ]

        title = ""
        for pattern in title_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                title = str(matches[0]).strip().title()
                break

        if not title:
            title = "Software Engineer"

        # Infer industry
        industry = "Technology"
        industry_hints = {
            "finance": ["fintech", "bank", "trading", "payments", "finance"],
            "healthcare": ["healthcare", "medical", "hospital", "clinical"],
            "ecommerce": ["ecommerce", "retail", "marketplace"],
            "education": ["education", "edtech", "learning", "university"],
            "gaming": ["gaming", "game development", "unity", "unreal"]
        }
        for candidate_industry, hints in industry_hints.items():
            if any(hint in text_lower for hint in hints):
                industry = candidate_industry.title()
                break

        # Check for remote preference
        job_type_preference = "any"
        if 'remote' in text_lower:
            job_type_preference = "remote"
        elif 'hybrid' in text_lower:
            job_type_preference = "hybrid"
        elif 'on-site' in text_lower or 'onsite' in text_lower:
            job_type_preference = "onsite"

        return ResumeProfile(
            title=title,
            keywords=keywords[:20],
            industry=industry,
            job_type_preference=job_type_preference,
            location=""
        )


# Create singleton instance
llm_analyzer = LLMAnalyzer()
