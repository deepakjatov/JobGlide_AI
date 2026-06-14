from typing import List

import httpx

from config import settings
from models import Job, JobFilter
from providers.base import JobProvider


class AdzunaProvider(JobProvider):
    """Adzuna job search provider."""

    BASE_URL = "https://api.adzuna.com/v1/api/jobs"

    @property
    def name(self) -> str:
        return "adzuna"

    async def search(self, filters: JobFilter) -> List[Job]:
        if not settings.ADZUNA_APP_ID or not settings.ADZUNA_APP_KEY:
            print("[Adzuna] Skipping — API keys not configured.")
            return []

        all_jobs: List[Job] = []

        # Determine country code based on locations
        country = "in"  # Default to India
        for loc in filters.locations:
            loc_lower = loc.lower()
            if "india" in loc_lower:
                country = "in"
                break
            elif "uk" in loc_lower or "united kingdom" in loc_lower:
                country = "gb"
                break
            elif "us" in loc_lower or "usa" in loc_lower or "united states" in loc_lower:
                country = "us"
                break

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for keyword in filters.keywords:
                    url = f"{self.BASE_URL}/{country}/search/1"

                    # If Remote is requested, append "remote" to search terms
                    search_term = keyword
                    if any(loc.lower() == "remote" for loc in filters.locations):
                        search_term = f"{keyword} remote"

                    params = {
                        "app_id": settings.ADZUNA_APP_ID,
                        "app_key": settings.ADZUNA_APP_KEY,
                        "what": search_term,
                        "results_per_page": "20",
                        "content-type": "application/json",
                    }

                    response = await client.get(url, params=params)
                    response.raise_for_status()

                    data = response.json()
                    results = data.get("results", [])

                    for item in results:
                        description = item.get("description", "") or ""

                        # Build salary string
                        salary = None
                        salary_min = item.get("salary_min")
                        salary_max = item.get("salary_max")
                        if salary_min and salary_max:
                            salary = f"{salary_min} - {salary_max}"
                        elif salary_min:
                            salary = str(salary_min)
                        elif salary_max:
                            salary = str(salary_max)

                        # Extract company and location
                        company_data = item.get("company", {}) or {}
                        location_data = item.get("location", {}) or {}

                        job = Job(
                            id=str(item.get("id", "")),
                            title=item.get("title", ""),
                            company=company_data.get("display_name", ""),
                            company_logo=None,
                            location=location_data.get(
                                "display_name", "Unknown"
                            ),
                            job_type=None,
                            apply_url=item.get("redirect_url", ""),
                            description=description[:500],
                            posted_date=item.get("created"),
                            salary=salary,
                            source="adzuna",
                            skills_matched=self._match_skills(
                                description, filters.skills
                            ),
                        )
                        all_jobs.append(job)

        except Exception as e:
            print(f"[Adzuna] Error: {e}")
            return []

        return all_jobs
