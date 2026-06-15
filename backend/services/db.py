import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_DIR = Path(__file__).parent.parent / "data"
DB_FILE = DB_DIR / "jobglide.db"

# Pre-populated default user profile from resume data
DEFAULT_PROFILE = {
    "name": "Deepak Jatov",
    "email": "jatovdeepak@gmail.com",
    "phone": "+91-9009022765",
    "location": "Gurugram, India",
    "linkedin_url": "",
    "github_url": "",
    "portfolio_url": "",
    "skills": [
        "React.js", "Redux", "Material UI", "Tailwind CSS", "FastAPI",
        "Node.js", "Express.js", "MongoDB", "PostgreSQL", "ChromaDB (Vector Database)",
        "Large Language Models (LLMs)", "Generative AI Integration", "Azure OpenAI",
        "Azure AI Studio / Foundry", "LangChain", "LangGraph", "CrewAI",
        "Retrieval-Augmented Generation (RAG)", "AI Agents", "Docker", "CI/CD Pipelines",
        "Git", "GitHub", "Python", "TypeScript", "JavaScript (ES6+)", "SQL"
    ],
    "resume_filename": "",
    "work_experience": [
        {
            "company": "Arizon Systems Private Limited",
            "role": "Software Engineer",
            "duration": "Feb 2025 - Present (1 Year 4 Months)",
            "description": (
                "Developed production-grade full-stack applications using React.js, TypeScript, Node.js, Python, and FastAPI. "
                "Built responsive UI layouts with Tailwind CSS and Material UI. Designed and implemented enterprise-grade "
                "RAG systems. Integrated Azure OpenAI, Azure AI Services, and Azure AI Foundry. Developed AI agents and workflows "
                "using LangChain and LangGraph. Architected AI microservices for document ingestion, embeddings, and retrieval."
            )
        }
    ],
    "resume_text": (
        "DEEPAK JATOV\n"
        "Software Engineer | Full Stack & Generative AI Engineer\n"
        "Gurugram, India | +91-9009022765 | jatovdeepak@gmail.com\n\n"
        "SUMMARY:\n"
        "Full Stack & Generative AI Engineer with expertise in React, TypeScript, Python, FastAPI, and modern AI application development. "
        "Experienced in RAG platforms, AI agents, LangChain, LangGraph, Azure OpenAI, vector databases, cloud deployments, microservices, "
        "semantic search, and enterprise AI solutions.\n\n"
        "SKILLS:\n"
        "- Programming: JavaScript (ES6+), TypeScript, Python, HTML5, CSS/CSS3, SQL\n"
        "- Frontend: React.js, Redux, Material UI, Tailwind CSS, Responsive Web Design\n"
        "- Backend: Node.js, Express.js, FastAPI, RESTful APIs, Microservices Architecture\n"
        "- Databases: MongoDB, PostgreSQL, ChromaDB (Vector Database)\n"
        "- AI/ML: Large Language Models (LLMs), Generative AI Integration, Azure OpenAI, Azure AI Studio / Foundry, LangChain, LangGraph, CrewAI, Retrieval-Augmented Generation (RAG), AI Agents\n"
        "- Cloud & DevOps: AWS (EC2, S3), Azure, Docker, CI/CD Pipelines, Azure DevOps, Git, GitHub, Version Control\n"
        "- Other: API & Backend Issue Debugging, SQL & Database Issue Investigation\n\n"
        "WORK EXPERIENCE:\n"
        "Software Engineer at Arizon Systems Private Limited (Feb 2025 - Present | 1 Year 4 Months)\n"
        "- Developed production-grade full-stack applications using React.js, TypeScript, Node.js, Python, and FastAPI.\n"
        "- Built responsive and accessible user interfaces using React, Tailwind CSS, and Material UI.\n"
        "- Designed and implemented enterprise-grade RAG systems.\n"
        "- Integrated Azure OpenAI, Azure AI Services, and Azure AI Foundry.\n"
        "- Developed AI agents and workflows using LangChain and LangGraph.\n"
        "- Architected AI microservices for document ingestion, embeddings, retrieval, and orchestration.\n"
        "- Improved backend/API performance by approximately 25%.\n"
        "- JWT authentication, RBAC, Docker containerization, and CI/CD pipelines.\n\n"
        "PROJECTS:\n"
        "1. Universal RAG SaaS (Generative AI Platform)\n"
        "Technologies: React, Tailwind CSS, FastAPI, OpenAI, ChromaDB, Docker, Render, Vercel\n"
        "- Built multi-tenant SaaS platform with document ingestion pipeline supporting PDF, DOCX, CSV, Excel, and TXT.\n"
        "- Implemented isolated per-user/chat vector indexes and JWT authentication.\n"
        "2. SOP Intelligence System (Enterprise SOP Platform)\n"
        "Technologies: React, FastAPI, Azure OpenAI, Azure Services, RAG, Vector Database\n"
        "- Built enterprise SOP management platform with structured SOP visualization and RAG-powered chat.\n\n"
        "EDUCATION:\n"
        "- MCA, National Institute of Technology, Kurukshetra (2025) | Grade: 7.44/10\n"
        "- 10th, CBSE (2016) | Marks: 79.2%\n"
    ),
    "llm_provider": "ollama",
    "llm_model": "qwen3:latest"
}


def get_db_connection():
    """Return a connection to the SQLite database."""
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db() -> None:
    """Create data directory and initialize database tables if they do not exist."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Create profile table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                name TEXT,
                email TEXT,
                phone TEXT,
                location TEXT,
                linkedin_url TEXT,
                github_url TEXT,
                portfolio_url TEXT,
                skills TEXT,
                resume_text TEXT,
                resume_filename TEXT,
                work_experience TEXT,
                llm_provider TEXT,
                llm_model TEXT
            )
        """)
        
        # 2. Create jobs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                title TEXT,
                company TEXT,
                company_logo TEXT,
                location TEXT,
                job_type TEXT,
                apply_url TEXT,
                description TEXT,
                posted_date TEXT,
                salary TEXT,
                source TEXT,
                skills_matched TEXT,
                fetched_at TEXT
            )
        """)
        
        # 3. Create applications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id TEXT PRIMARY KEY,
                job_id TEXT,
                job_title TEXT,
                company TEXT,
                apply_url TEXT,
                source TEXT,
                status TEXT,
                applied_at TEXT,
                cover_letter TEXT,
                notes TEXT
            )
        """)
        
        conn.commit()
        
        # 4. Pre-populate the user profile if empty
        cursor.execute("SELECT COUNT(*) FROM profile WHERE id = 1")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO profile (
                    id, name, email, phone, location, linkedin_url, github_url, portfolio_url,
                    skills, resume_text, resume_filename, work_experience, llm_provider, llm_model
                ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                DEFAULT_PROFILE["name"],
                DEFAULT_PROFILE["email"],
                DEFAULT_PROFILE["phone"],
                DEFAULT_PROFILE["location"],
                DEFAULT_PROFILE["linkedin_url"],
                DEFAULT_PROFILE["github_url"],
                DEFAULT_PROFILE["portfolio_url"],
                json.dumps(DEFAULT_PROFILE["skills"]),
                DEFAULT_PROFILE["resume_text"],
                DEFAULT_PROFILE["resume_filename"],
                json.dumps(DEFAULT_PROFILE["work_experience"]),
                DEFAULT_PROFILE["llm_provider"],
                DEFAULT_PROFILE["llm_model"]
            ))
            conn.commit()
            print("[DB] Pre-populated database profile with provided resume data successfully.")


def save_jobs(jobs: list) -> None:
    """Save a list of Job Pydantic model instances or dicts to the SQLite jobs table."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for job in jobs:
            # Handle if it is a Pydantic model
            job_dict = job.model_dump() if hasattr(job, "model_dump") else job
            
            cursor.execute("""
                INSERT OR REPLACE INTO jobs (
                    id, title, company, company_logo, location, job_type, apply_url, description,
                    posted_date, salary, source, skills_matched, fetched_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_dict.get("id"),
                job_dict.get("title", ""),
                job_dict.get("company", ""),
                job_dict.get("company_logo", ""),
                job_dict.get("location", ""),
                job_dict.get("job_type", ""),
                job_dict.get("apply_url", ""),
                job_dict.get("description", ""),
                job_dict.get("posted_date", ""),
                job_dict.get("salary", ""),
                job_dict.get("source", ""),
                json.dumps(job_dict.get("skills_matched", [])),
                now_iso
            ))
        conn.commit()


def get_all_jobs() -> list:
    """Retrieve all saved jobs from SQLite database, ordered by fetched_at desc."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs ORDER BY fetched_at DESC")
        rows = cursor.fetchall()
        jobs = []
        for row in rows:
            job_dict = dict(row)
            try:
                job_dict["skills_matched"] = json.loads(job_dict["skills_matched"]) if job_dict.get("skills_matched") else []
            except Exception:
                job_dict["skills_matched"] = []
            jobs.append(job_dict)
        return jobs
