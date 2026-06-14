import asyncio
from typing import List

from config import settings
from models import Job, JobFilter, JobSearchResponse
from providers.adzuna import AdzunaProvider
from providers.himalayas import HimalayasProvider
from providers.jsearch import JSearchProvider
from providers.remotive import RemotiveProvider
from providers.jobspy import JobSpyProvider
from services.cache import CacheManager


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
        # Check cache first
        cache_key = self.cache.make_key(filters)
        cached = self.cache.get(cache_key)
        if cached is not None:
            print("[Aggregator] Returning cached results.")
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

        # Sort: by skills_matched count (descending), then by posted_date (descending)
        unique_jobs.sort(
            key=lambda j: (j.posted_date or ""),
            reverse=True,
        )
        # Stable sort: now sort by skills_matched count descending (stable preserves date order within ties)
        unique_jobs.sort(
            key=lambda j: len(j.skills_matched),
            reverse=True,
        )

        response = JobSearchResponse(
            jobs=unique_jobs,
            total=len(unique_jobs),
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
