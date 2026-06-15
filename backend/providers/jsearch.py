from typing import List

import httpx

from config import settings
from models import Job, JobFilter
from providers.base import JobProvider


class JSearchProvider(JobProvider):
    """JSearch (RapidAPI) job search provider."""

    BASE_URL = "https://jsearch.p.rapidapi.com/search"

    @property
    def name(self) -> str:
        return "jsearch"

    async def search(self, filters: JobFilter) -> List[Job]:
        if not settings.JSEARCH_API_KEY:
            print("[JSearch] Skipping — API key not configured.")
            return []

        headers = {
            "x-rapidapi-key": settings.JSEARCH_API_KEY,
            "x-rapidapi-host": "jsearch.p.rapidapi.com",
        }

        all_jobs: List[Job] = []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for keyword in filters.keywords:
                    query = f'{keyword} {" ".join(filters.locations)}'

                    # Map date_posted
                    jsearch_date = "all"
                    if filters.date_posted == "past_24h":
                        jsearch_date = "today"
                    elif filters.date_posted == "past_3d":
                        jsearch_date = "3days"
                    elif filters.date_posted == "past_week":
                        jsearch_date = "week"
                    elif filters.date_posted == "past_month":
                        jsearch_date = "month"

                    # Map job_types
                    type_mapping = {
                        "Full-time": "FULLTIME",
                        "Part-time": "PARTTIME",
                        "Contract": "CONTRACTOR",
                        "Internship": "INTERN"
                    }
                    jsearch_types = []
                    for jt in filters.job_types:
                        mapped = type_mapping.get(jt)
                        if mapped:
                            jsearch_types.append(mapped)

                    params = {
                        "query": query,
                        "date_posted": jsearch_date,
                        "page": "1",
                        "num_pages": "1",
                    }

                    if jsearch_types:
                        params["employment_types"] = ",".join(jsearch_types)

                    if filters.experience in ["0-1", "1-2", "0-3"]:
                        params["job_requirements"] = "under_3_years_experience"

                    response = await client.get(
                        self.BASE_URL, headers=headers, params=params
                    )
                    response.raise_for_status()

                    data = response.json()
                    jobs_data = data.get("data", [])

                    for item in jobs_data:
                        # Build location string
                        location_parts = [
                            item.get("job_city", ""),
                            item.get("job_state", ""),
                            item.get("job_country", ""),
                        ]
                        location = ", ".join(
                            part for part in location_parts if part
                        )

                        # Build salary string
                        salary = None
                        min_salary = item.get("job_min_salary")
                        max_salary = item.get("job_max_salary")
                        if min_salary and max_salary:
                            salary = f"{min_salary} - {max_salary}"
                        elif min_salary:
                            salary = str(min_salary)
                        elif max_salary:
                            salary = str(max_salary)

                        description = item.get("job_description", "") or ""

                        job = Job(
                            id=str(item.get("job_id", "")),
                            title=item.get("job_title", ""),
                            company=item.get("employer_name", ""),
                            company_logo=item.get("employer_logo"),
                            location=location or "Unknown",
                            job_type=item.get("job_employment_type"),
                            apply_url=item.get("job_apply_link", ""),
                            description=description[:500],
                            posted_date=item.get(
                                "job_posted_at_datetime_utc"
                            ),
                            salary=salary,
                            source="jsearch",
                            skills_matched=self._match_skills(
                                description, filters.skills
                            ),
                        )
                        all_jobs.append(job)

        except Exception as e:
            print(f"[JSearch] Error: {e}")
            return []

        return all_jobs
