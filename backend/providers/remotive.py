from typing import List

import httpx

from models import Job, JobFilter
from providers.base import JobProvider


class RemotiveProvider(JobProvider):
    """Remotive job search provider (no auth, limited to 4 req/day)."""

    BASE_URL = "https://remotive.com/api/remote-jobs"

    @property
    def name(self) -> str:
        return "remotive"

    async def search(self, filters: JobFilter) -> List[Job]:
        all_jobs: List[Job] = []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                params = {
                    "category": "software-dev",
                    "limit": "100",
                }

                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()

                data = response.json()
                jobs_data = data.get("jobs", [])

                for item in jobs_data:
                    title = item.get("title", "")
                    description = item.get("description", "") or ""

                    # Filter: check if any keyword appears in title
                    keyword_match = any(
                        kw.lower() in title.lower()
                        for kw in filters.keywords
                    )

                    # Filter: check if any skill appears in description
                    skill_match = any(
                        skill.lower() in description.lower()
                        for skill in filters.skills
                    )

                    if not keyword_match and not skill_match:
                        continue

                    salary = item.get("salary") or None

                    job = Job(
                        id=str(item.get("id", "")),
                        title=title,
                        company=item.get("company_name", ""),
                        company_logo=item.get("company_logo_url"),
                        location=item.get(
                            "candidate_required_location", "Remote"
                        ),
                        job_type=item.get("job_type"),
                        apply_url=item.get("url", ""),
                        description=description[:500],
                        posted_date=item.get("publication_date"),
                        salary=salary,
                        source="remotive",
                        skills_matched=self._match_skills(
                            description, filters.skills
                        ),
                    )
                    all_jobs.append(job)

        except Exception as e:
            print(f"[Remotive] Error: {e}")
            return []

        return all_jobs
