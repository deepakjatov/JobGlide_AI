from typing import List

import httpx

from models import Job, JobFilter
from providers.base import JobProvider


class HimalayasProvider(JobProvider):
    """Himalayas.app job search provider (no auth required)."""

    BASE_URL = "https://himalayas.app/jobs/api"

    @property
    def name(self) -> str:
        return "himalayas"

    async def search(self, filters: JobFilter) -> List[Job]:
        all_jobs: List[Job] = []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for keyword in filters.keywords:
                    params = {
                        "q": keyword,
                        "limit": "20",
                        "offset": "0",
                    }

                    response = await client.get(f"{self.BASE_URL}/search", params=params)
                    response.raise_for_status()

                    data = response.json()
                    jobs_data = data.get("jobs", [])

                    for item in jobs_data:
                        title = item.get("title", "")

                        # Filter by location
                        location = item.get("location", "") or ""
                        if filters.locations:
                            location_match = False
                            for loc in filters.locations:
                                if loc.lower() == "remote":
                                    if not location or "remote" in location.lower() or item.get("timezones"):
                                        location_match = True
                                        break
                                elif location and loc.lower() in location.lower():
                                    location_match = True
                                    break
                            if not location_match:
                                continue

                        description = item.get("description", "") or ""
                        salary = None
                        min_salary = item.get("salary_min")
                        max_salary = item.get("salary_max")
                        if min_salary and max_salary:
                            salary = f"{min_salary} - {max_salary}"
                        elif min_salary:
                            salary = str(min_salary)
                        elif max_salary:
                            salary = str(max_salary)

                        job = Job(
                            id=str(item.get("id", "")),
                            title=title,
                            company=item.get("company_name", ""),
                            company_logo=item.get("company_logo"),
                            location=location or "Remote",
                            job_type=item.get("job_type"),
                            apply_url=item.get("url", ""),
                            description=description[:500],
                            posted_date=item.get("published_at"),
                            salary=salary,
                            source="himalayas",
                            skills_matched=self._match_skills(
                                description, filters.skills
                            ),
                        )
                        all_jobs.append(job)

        except Exception as e:
            print(f"[Himalayas] Error: {e}")
            return []

        return all_jobs
