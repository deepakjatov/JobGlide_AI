from typing import List, Optional

from pydantic import BaseModel


class JobFilter(BaseModel):
    keywords: List[str]
    skills: List[str]
    experience: str = "1-2"
    locations: List[str]
    sources: Optional[List[str]] = None
    date_posted: str = "past_3d"
    job_types: List[str] = []
    experience_levels: List[str] = []
    workplace_types: List[str] = []


class Job(BaseModel):
    id: str
    title: str
    company: str
    company_logo: Optional[str] = None
    location: str
    job_type: Optional[str] = None
    apply_url: str
    description: str
    posted_date: Optional[str] = None
    salary: Optional[str] = None
    source: str
    skills_matched: List[str] = []


class JobSearchResponse(BaseModel):
    jobs: List[Job]
    total: int
    sources_searched: List[str]
    cached: bool = False
