from pydantic_settings import BaseSettings


DEFAULT_FILTERS = {
    "keywords": ["AI Engineer", "GenAI Engineer", "Full Stack Engineer", "Software Engineer"],
    "skills": ["React", "FastAPI", "RAG", "LLM"],
    "experience": "0-3",
    "locations": ["Remote", "India"],
}


class Settings(BaseSettings):
    JSEARCH_API_KEY: str = ""
    ADZUNA_APP_ID: str = ""
    ADZUNA_APP_KEY: str = ""
    CACHE_TTL_MINUTES: int = 30
    ALLOW_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://localhost:3000"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
