import asyncio
from typing import List
import pandas as pd
from jobspy import scrape_jobs

from models import Job, JobFilter
from providers.base import JobProvider


class JobSpyProvider(JobProvider):
    """JobSpy provider scraping LinkedIn, Indeed, and Google Jobs without API keys."""

    @property
    def name(self) -> str:
        return "jobspy"

    async def search(self, filters: JobFilter) -> List[Job]:
        all_jobs: List[Job] = []

        # Determine location query string for JobSpy
        # JobSpy works well with location strings like "Remote, India" or "Remote, USA"
        loc_str = "Remote" if "Remote" in filters.locations else ""
        if not loc_str:
            loc_str = filters.locations[0] if filters.locations else "United States"

        # Determine country code context
        is_us = any(
            loc.lower() in ["us", "usa", "united states", "united kingdom", "gb"]
            for loc in filters.locations
        )
        country_indeed = "USA" if is_us else "India"

        # Search each keyword
        for keyword in filters.keywords:
            try:
                # scrape_jobs is a blocking synchronous call, run in thread pool
                df = await asyncio.to_thread(
                    scrape_jobs,
                    site_name=["linkedin", "indeed", "google"],
                    search_term=keyword,
                    location=loc_str,
                    results_wanted=15,  # Moderate to avoid rate limits / IP bans
                    country_indeed=country_indeed,
                )

                if df is None or df.empty:
                    continue

                for _, row in df.iterrows():
                    site = str(row.get("site", "jobspy")).lower()
                    title = str(row.get("title", ""))
                    company = str(row.get("company", ""))

                    # Build location string
                    city = row.get("city")
                    state = row.get("state")
                    loc_parts = [
                        str(p)
                        for p in [city, state]
                        if p and str(p).lower() != "nan"
                    ]
                    job_location = ", ".join(loc_parts) if loc_parts else "Remote"

                    # Build salary string
                    salary = None
                    min_amt = row.get("min_amount")
                    max_amt = row.get("max_amount")
                    interval = row.get("interval")
                    if min_amt and max_amt and not (
                        str(min_amt) == "nan" or str(max_amt) == "nan"
                    ):
                        salary = f"{min_amt} - {max_amt}"
                        if interval and str(interval) != "nan":
                            salary += f" ({interval})"
                    elif min_amt and not str(min_amt) == "nan":
                        salary = f"{min_amt}"
                        if interval and str(interval) != "nan":
                            salary += f" ({interval})"

                    description = str(row.get("description", "")) or ""

                    # Unique identifier: use job_url or build one
                    job_url = str(row.get("job_url", ""))
                    job_id = job_url or f"{site}-{title}-{company}"

                    job = Job(
                        id=job_id,
                        title=title,
                        company=company,
                        company_logo=None,
                        location=job_location,
                        job_type=str(row.get("job_type", "Full-time"))
                        if row.get("job_type") and str(row.get("job_type")) != "nan"
                        else "Full-time",
                        apply_url=job_url,
                        description=description[:500],
                        posted_date=str(row.get("date_posted"))
                        if row.get("date_posted") and str(row.get("date_posted")) != "nan"
                        else None,
                        salary=salary,
                        source=site,  # "linkedin", "indeed", "google"
                        skills_matched=self._match_skills(
                            description, filters.skills
                        ),
                    )
                    all_jobs.append(job)

            except Exception as e:
                print(f"[JobSpy] Error scraping '{keyword}': {e}")

        return all_jobs
