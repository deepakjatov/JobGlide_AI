import asyncio
from datetime import datetime, timezone
from typing import List
import dateutil.parser

from config import settings
from models import Job, JobFilter, JobSearchResponse
from providers.adzuna import AdzunaProvider
from providers.himalayas import HimalayasProvider
from providers.jsearch import JSearchProvider
from providers.remotive import RemotiveProvider
from providers.jobspy import JobSpyProvider
from services.cache import CacheManager


def _is_recent(date_str: str, max_days: int) -> bool:
    if not date_str:
        return True
    try:
        dt = dateutil.parser.isoparse(date_str)
    except Exception:
        try:
            dt = dateutil.parser.parse(date_str)
        except Exception:
            return True

    now = datetime.now(timezone.utc) if dt.tzinfo else datetime.now()
    delta = now - dt
    return delta.days <= max_days


def _match_job_type(job_type: str, filter_types: List[str]) -> bool:
    if not job_type:
        return False
    jt_lower = job_type.lower()
    for ft in filter_types:
        ft_lower = ft.lower()
        if ft_lower in jt_lower:
            return True
        if ft_lower == "internship" and "intern" in jt_lower:
            return True
    return False


def _match_experience_level(job_title: str, job_desc: str, filter_levels: List[str]) -> bool:
    title_lower = job_title.lower()
    desc_lower = job_desc.lower()
    for fl in filter_levels:
        fl_lower = fl.lower()
        if fl_lower == "entry level":
            if "entry" in title_lower or "junior" in title_lower or "jr" in title_lower or "no experience" in desc_lower[:100]:
                return True
        elif fl_lower == "internship":
            if "intern" in title_lower or "internship" in title_lower:
                return True
        elif fl_lower == "associate":
            if "associate" in title_lower:
                return True
        elif fl_lower == "mid-senior level":
            if "senior" in title_lower or "sr" in title_lower or "lead" in title_lower or "mid" in title_lower or "mid-senior" in title_lower:
                return True
        elif fl_lower == "director":
            if "director" in title_lower or "head" in title_lower:
                return True
        elif fl_lower == "executive":
            if any(term in title_lower for term in ["vp", "vice president", "cto", "cfo", "ceo", "executive", "co-founder"]):
                return True
        
        if fl_lower in title_lower or fl_lower in desc_lower[:100]:
            return True
    return False


def _match_workplace_type(location: str, filter_types: List[str]) -> bool:
    if not location:
        return "remote" in [wt.lower() for wt in filter_types]
    loc_lower = location.lower()
    for wt in filter_types:
        wt_lower = wt.lower()
        if wt_lower == "remote":
            if "remote" in loc_lower or "wfh" in loc_lower or "work from home" in loc_lower:
                return True
        elif wt_lower == "hybrid":
            if "hybrid" in loc_lower:
                return True
        elif wt_lower == "on-site":
            if "onsite" in loc_lower or "on-site" in loc_lower or ("remote" not in loc_lower and "hybrid" not in loc_lower):
                return True
    return False


class JobAggregator:
    """Aggregates job results from multiple providers with caching and deduplication."""

    def __init__(self) -> None:
        self.providers = [
            JSearchProvider(),
            HimalayasProvider(),
            AdzunaProvider(),
            RemotiveProvider(),
            JobSpyProvider(),
        ]
        self.cache = CacheManager()

    async def search(self, filters: JobFilter) -> JobSearchResponse:
        # 1. Check SQLite database first (unless force_refresh is True)
        if not filters.force_refresh:
            try:
                from services.db import get_all_jobs
                db_jobs_raw = get_all_jobs()
                if db_jobs_raw:
                    db_jobs = []
                    for j in db_jobs_raw:
                        try:
                            db_jobs.append(Job(**j))
                        except Exception as parse_err:
                            print(f"[Aggregator] Failed to parse DB job row: {parse_err}")

                    # Apply Unified Post-Filtering Pass
                    filtered_jobs: List[Job] = []
                    for job in db_jobs:
                        # Job Freshness (Date Posted)
                        if filters.date_posted != "anytime":
                            days_limit = {"past_24h": 1, "past_3d": 3, "past_week": 7, "past_month": 30}.get(filters.date_posted, 30)
                            if not _is_recent(job.posted_date, days_limit):
                                continue

                        # Job Type
                        if filters.job_types and not _match_job_type(job.job_type, filters.job_types):
                            continue

                        # Experience Level
                        if filters.experience_levels and not _match_experience_level(job.title, job.description, filters.experience_levels):
                            continue

                        # Workplace Type
                        if filters.workplace_types and not _match_workplace_type(job.location, filters.workplace_types):
                            continue

                        filtered_jobs.append(job)

                    if filtered_jobs:
                        print(f"[Aggregator] Returning {len(filtered_jobs)} filtered jobs from SQLite database.")
                        filtered_jobs.sort(key=lambda j: (j.posted_date or ""), reverse=True)
                        filtered_jobs.sort(key=lambda j: len(j.skills_matched), reverse=True)
                        return JobSearchResponse(
                            jobs=filtered_jobs,
                            total=len(filtered_jobs),
                            sources_searched=[],
                            cached=True,
                        )
            except Exception as e:
                print(f"[Aggregator] SQLite cache lookup failed: {e}")

        # 2. Check in-memory cache next
        cache_key = self.cache.make_key(filters)
        cached = self.cache.get(cache_key)
        if cached is not None:
            print("[Aggregator] Returning in-memory cached results.")
            response = JobSearchResponse(**cached)
            response.cached = True
            return response

        # Determine which providers to use
        active_providers = self.providers
        if filters.sources:
            active_providers = [
                p for p in self.providers if p.name in filters.sources
            ]

        # Call all providers concurrently
        results = await asyncio.gather(
            *[provider.search(filters) for provider in active_providers],
            return_exceptions=True,
        )

        all_jobs: List[Job] = []
        sources_searched: List[str] = []

        for provider, result in zip(active_providers, results):
            if isinstance(result, Exception):
                print(f"[Aggregator] {provider.name} failed: {result}")
                continue
            if result:
                sources_searched.append(provider.name)
                all_jobs.extend(result)
            else:
                # Provider returned empty list (possibly skipped or no results)
                sources_searched.append(provider.name)

        # Deduplicate by normalized title + company
        seen = set()
        unique_jobs: List[Job] = []
        for job in all_jobs:
            dedup_key = (job.title.lower().strip(), job.company.lower().strip())
            if dedup_key not in seen:
                seen.add(dedup_key)
                unique_jobs.append(job)

        # Persist all unique aggregated jobs to SQLite database
        try:
            from services.db import save_jobs
            save_jobs(unique_jobs)
            print(f"[Aggregator] Persisted {len(unique_jobs)} unique jobs to database.")
        except Exception as e:
            print(f"[Aggregator] Failed to persist jobs to database: {e}")

        # Apply Unified Post-Filtering Pass
        filtered_jobs: List[Job] = []
        for job in unique_jobs:
            # 1. Job Freshness (Date Posted)
            if filters.date_posted != "anytime":
                days_limit = {"past_24h": 1, "past_3d": 3, "past_week": 7, "past_month": 30}.get(filters.date_posted, 30)
                if not _is_recent(job.posted_date, days_limit):
                    continue

            # 2. Job Type
            if filters.job_types and not _match_job_type(job.job_type, filters.job_types):
                continue

            # 3. Experience Level
            if filters.experience_levels and not _match_experience_level(job.title, job.description, filters.experience_levels):
                continue

            # 4. Workplace Type
            if filters.workplace_types and not _match_workplace_type(job.location, filters.workplace_types):
                continue

            filtered_jobs.append(job)

        # Sort: by skills_matched count (descending), then by posted_date (descending)
        filtered_jobs.sort(
            key=lambda j: (j.posted_date or ""),
            reverse=True,
        )
        # Stable sort: now sort by skills_matched count descending (stable preserves date order within ties)
        filtered_jobs.sort(
            key=lambda j: len(j.skills_matched),
            reverse=True,
        )

        response = JobSearchResponse(
            jobs=filtered_jobs,
            total=len(filtered_jobs),
            sources_searched=sources_searched,
            cached=False,
        )

        # Cache the results
        self.cache.set(
            cache_key,
            response.model_dump(),
            ttl_minutes=settings.CACHE_TTL_MINUTES,
        )

        return response
