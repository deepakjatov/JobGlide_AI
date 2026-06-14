from typing import List, Optional

from pydantic import BaseModel


class JobFilter(BaseModel):
    keywords: List[str]
    skills: List[str]
    experience: str = "0-3"
    locations: List[str]
    sources: Optional[List[str]] = None


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
