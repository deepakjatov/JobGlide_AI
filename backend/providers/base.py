from abc import ABC, abstractmethod
from typing import List

from models import Job, JobFilter


class JobProvider(ABC):
    """Abstract base class for job search providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this provider."""
        ...

    @abstractmethod
    async def search(self, filters: JobFilter) -> List[Job]:
        """Search for jobs using the given filters."""
        ...

    def _match_skills(self, description: str, skills: List[str]) -> List[str]:
        """Case-insensitive matching of skills against a job description."""
        description_lower = description.lower()
        return [skill for skill in skills if skill.lower() in description_lower]
