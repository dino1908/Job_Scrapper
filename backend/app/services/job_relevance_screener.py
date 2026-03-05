"""
LLM-assisted relevance screening for scraped jobs.
"""
from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, Set

import requests

from ..config import settings


class JobRelevanceScreener:
    """Use deterministic rules + Mistral to keep only relevant jobs."""

    def __init__(self):
        self.api_key = (settings.MISTRAL_API_KEY or "").strip()
        self.base_url = "https://api.mistral.ai/v1/chat/completions"
        if self.api_key:
            print("✅ Mistral screener configured")

    def filter_jobs(
        self,
        jobs: List[Dict],
        *,
        role: str,
        location: str,
        batch_size: int = 20
    ) -> List[Dict]:
        """
        Keep only role/location relevant jobs.

        Strategy:
        1) hard deterministic filtering
        2) LLM screening on survivors (if API key available)
        """
        if not jobs:
            return []

        hard_filtered = [job for job in jobs if self._hard_match(job, role=role, location=location)]
        if not hard_filtered:
            return []

        # If API key is not configured, fall back to deterministic filtering only.
        if not self.api_key:
            return hard_filtered

        kept_urls: Set[str] = set()
        screened_jobs: List[Dict] = []

        for start in range(0, len(hard_filtered), batch_size):
            batch = hard_filtered[start:start + batch_size]
            try:
                keep_indexes = self._screen_batch_with_mistral(batch, role=role, location=location)
                keep_jobs = [
                    job for idx, job in enumerate(batch)
                    if idx in keep_indexes
                ]
            except Exception as exc:
                # Preserve hard-filtered jobs if LLM call fails.
                print(f"⚠️  Mistral screening failed, falling back to hard filters: {exc}")
                keep_jobs = batch

            for job in keep_jobs:
                apply_url = (job.get("apply_url") or "").strip().lower()
                if apply_url and apply_url in kept_urls:
                    continue
                if apply_url:
                    kept_urls.add(apply_url)
                screened_jobs.append(job)

        return screened_jobs

    def _screen_batch_with_mistral(
        self,
        batch: List[Dict],
        *,
        role: str,
        location: str
    ) -> Set[int]:
        """Return set of batch indexes to keep."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "mistral-small-latest",
            "temperature": 0,
            "max_tokens": 500,
            "messages": [
                {
                    "role": "user",
                    "content": self._build_prompt(batch=batch, role=role, location=location),
                }
            ],
        }

        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=45,
        )
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]
        parsed = self._parse_json_object(content)
        indexes = parsed.get("relevant_indexes", [])
        if not isinstance(indexes, list):
            return set()

        keep_indexes = set()
        for idx in indexes:
            try:
                numeric = int(idx)
            except (TypeError, ValueError):
                continue
            if 0 <= numeric < len(batch):
                keep_indexes.add(numeric)
        return keep_indexes

    def _build_prompt(self, *, batch: List[Dict], role: str, location: str) -> str:
        """Build compact screening prompt."""
        lines = []
        for idx, job in enumerate(batch):
            description = (job.get("description") or "").strip()
            if len(description) > 350:
                description = description[:350] + "..."
            lines.append(
                f"{idx}. title={job.get('title', '')} | company={job.get('company', '')} | "
                f"location={job.get('location', '')} | job_type={job.get('job_type', '')} | "
                f"description={description}"
            )

        requested_location = location.strip() or "(any)"
        return (
            "You are screening jobs for strict relevance.\n"
            f"Target role: {role.strip()}\n"
            f"Target location: {requested_location}\n\n"
            "Rules:\n"
            "1) Keep only jobs matching the target role; reject unrelated roles.\n"
            "2) If target location is specific (not any), reject jobs outside that location.\n"
            "3) Do not assume PM means software engineer; keep only manager roles that fit the target.\n"
            "4) Prefer precision over recall.\n\n"
            "Return ONLY JSON: {\"relevant_indexes\": [..]}.\n\n"
            "Jobs:\n"
            + "\n".join(lines)
        )

    def _parse_json_object(self, text: str) -> Dict:
        """Parse first JSON object from model output."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in model response")
        return json.loads(match.group(0))

    def _hard_match(self, job: Dict, *, role: str, location: str) -> bool:
        """Fast deterministic gate before LLM screening."""
        return self._role_match(job, role=role) and self._location_match(job, location=location)

    def _role_match(self, job: Dict, *, role: str) -> bool:
        role_norm = self._normalize(role)
        if not role_norm:
            return True

        title_text = self._normalize(job.get("title", ""))
        description_text = self._normalize(job.get("description", ""))
        combined = f"{title_text} {description_text}".strip()
        if not combined:
            return False

        variants = self._role_variants(role_norm)
        if any(variant in combined for variant in variants):
            return True

        role_tokens = [tok for tok in self._tokenize(role_norm) if tok not in {"and", "or"}]
        title_tokens = set(self._tokenize(title_text))
        if not role_tokens or not title_tokens:
            return False

        overlap = sum(1 for tok in role_tokens if tok in title_tokens)
        if len(role_tokens) <= 2:
            return overlap == len(role_tokens)
        return overlap >= max(2, int(round(len(role_tokens) * 0.6)))

    def _location_match(self, job: Dict, *, location: str) -> bool:
        desired = self._normalize(location)
        if not desired:
            return True

        job_location = self._normalize(job.get("location", ""))
        job_type = self._normalize(job.get("job_type", ""))

        if "remote" in desired:
            return "remote" in job_location or "remote" in job_type

        # For specific locations, do not accept remote-only jobs.
        if "remote" in job_location and "remote" not in desired:
            return False

        if not job_location:
            return False

        if desired in job_location:
            return True

        desired_city = self._extract_primary_city_token(desired)
        if desired_city and desired_city not in job_location:
            return False

        desired_tokens = [
            tok for tok in self._tokenize(desired)
            if tok not in {"india", "united", "states", "state", "region"}
        ]
        if not desired_tokens:
            return False

        token_matches = sum(1 for tok in desired_tokens if tok in job_location)
        return token_matches >= 1

    def _role_variants(self, role_norm: str) -> List[str]:
        variants = {role_norm}
        compact = role_norm.replace(".", "").strip()

        if compact == "pm":
            variants.update({
                "product manager",
                "product management",
                "program manager",
                "project manager",
            })
        if "product manager" in compact or "product management" in compact:
            variants.update({"product manager", "product management", "pm"})
        if "program manager" in compact:
            variants.update({"program manager", "program management"})
        if "project manager" in compact:
            variants.update({"project manager", "project management"})

        return sorted(variants, key=len, reverse=True)

    def _extract_primary_city_token(self, location: str) -> Optional[str]:
        first_segment = location.split(",")[0].strip()
        tokens = [tok for tok in self._tokenize(first_segment) if len(tok) >= 3]
        return tokens[0] if tokens else None

    def _tokenize(self, text: str) -> List[str]:
        return [tok for tok in re.split(r"[\s,/\\\-\(\)\|]+", text) if tok]

    def _normalize(self, value: str) -> str:
        return " ".join((value or "").lower().strip().split())


job_relevance_screener = JobRelevanceScreener()

