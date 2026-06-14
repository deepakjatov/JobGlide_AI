from typing import List

from fastapi import APIRouter

from config import DEFAULT_FILTERS, settings
from models import JobFilter, JobSearchResponse
from services.aggregator import JobAggregator

router = APIRouter(prefix="/api")

aggregator = JobAggregator()


@router.post("/jobs/search", response_model=JobSearchResponse)
async def search_jobs(filters: JobFilter) -> JobSearchResponse:
    """Search for jobs across all configured providers."""
    return await aggregator.search(filters)


@router.get("/filters/default")
async def get_default_filters() -> dict:
    """Return the default search filters."""
    return DEFAULT_FILTERS


@router.get("/jobs/sources")
async def get_available_sources() -> List[dict]:
    """Return list of available sources with their configuration status."""
    sources = [
        {
            "name": "linkedin",
            "configured": True,
            "requires_key": False,
        },
        {
            "name": "indeed",
            "configured": True,
            "requires_key": False,
        },
        {
            "name": "google",
            "configured": True,
            "requires_key": False,
        },
        {
            "name": "jsearch",
            "configured": bool(settings.JSEARCH_API_KEY),
            "requires_key": True,
        },
        {
            "name": "himalayas",
            "configured": True,
            "requires_key": False,
        },
        {
            "name": "adzuna",
            "configured": bool(
                settings.ADZUNA_APP_ID and settings.ADZUNA_APP_KEY
            ),
            "requires_key": True,
        },
        {
            "name": "remotive",
            "configured": True,
            "requires_key": False,
        },
    ]
    return sources
