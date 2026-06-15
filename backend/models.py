from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# ─────────────────────────── Job Search ───────────────────────────

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
    force_refresh: bool = False


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


# ─────────────────────────── User Profile ───────────────────────────

class WorkExperience(BaseModel):
    company: str = ""
    role: str = ""
    duration: str = ""
    description: str = ""


class UserProfile(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin_url: str = ""
    github_url: str = ""
    portfolio_url: str = ""
    skills: List[str] = []
    resume_text: str = ""
    resume_filename: str = ""
    work_experience: List[WorkExperience] = []
    # LLM settings
    llm_provider: str = "ollama"   # "ollama" | "openai" | "gemini"
    llm_model: str = "qwen2.5:14b"


# ─────────────────────────── Applications ───────────────────────────

class Application(BaseModel):
    id: str
    job_id: str = ""
    job_title: str
    company: str
    apply_url: str = ""
    source: str = ""
    status: str = "applied"  # applied | interview | offer | rejected
    applied_at: str
    cover_letter: str = ""
    notes: str = ""


# ─────────────────────────── Apply Requests ───────────────────────────

class QuickApplyRequest(BaseModel):
    job_id: str
    job_title: str
    company: str
    apply_url: str
    source: str = ""


class CoverLetterRequest(BaseModel):
    job_title: str
    company: str
    job_description: str
    provider: str = "ollama"   # "ollama" | "openai" | "gemini"
    model: str = "qwen2.5:14b"


class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    cover_letter: Optional[str] = None


class AutoApplyRequest(BaseModel):
    filters: JobFilter
    max_applications: int = 5
    linkedin_email: str = ""
    linkedin_password: str = ""
