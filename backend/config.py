from pydantic_settings import BaseSettings


DEFAULT_FILTERS = {
    "keywords": ["AI Engineer", "GenAI Engineer", "Full Stack Engineer", "Software Engineer"],
    "skills": ["React", "FastAPI", "RAG", "LLM"],
    "experience": "1-2",
    "locations": ["Remote", "India"],
    "date_posted": "past_3d",
    "job_types": [],
    "experience_levels": [],
    "workplace_types": ["Remote"],
}


class Settings(BaseSettings):
    # Job search providers
    JSEARCH_API_KEY: str = ""
    ADZUNA_APP_ID: str = ""
    ADZUNA_APP_KEY: str = ""
    CACHE_TTL_MINUTES: int = 30
    ALLOW_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://localhost:3000"

    # LLM providers
    OLLAMA_HOST: str = "http://localhost:11434"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # LinkedIn automation
    LINKEDIN_EMAIL: str = ""
    LINKEDIN_PASSWORD: str = ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

    def __init__(self, **values):
        super().__init__(**values)
        # Normalize OLLAMA_HOST connection string
        if not self.OLLAMA_HOST.startswith("http://") and not self.OLLAMA_HOST.startswith("https://"):
            self.OLLAMA_HOST = f"http://{self.OLLAMA_HOST}"
        if "0.0.0.0" in self.OLLAMA_HOST:
            self.OLLAMA_HOST = self.OLLAMA_HOST.replace("0.0.0.0", "127.0.0.1")


settings = Settings()

