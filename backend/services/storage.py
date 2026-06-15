import json
from typing import Any, Dict, List, Optional
from services.db import get_db_connection

# ─────────────────────────── Profile ────────────────────────────────

def get_profile() -> Optional[Dict[str, Any]]:
    """Retrieve the saved user profile from SQLite database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM profile WHERE id = 1")
        row = cursor.fetchone()
        if not row:
            return None
        
        # Convert row to dict
        profile = dict(row)
        # Parse JSON fields
        try:
            profile["skills"] = json.loads(profile["skills"]) if profile.get("skills") else []
        except Exception:
            profile["skills"] = []
            
        try:
            profile["work_experience"] = json.loads(profile["work_experience"]) if profile.get("work_experience") else []
        except Exception:
            profile["work_experience"] = []
            
        return profile


def save_profile(profile: Dict[str, Any]) -> None:
    """Save or update the user profile in the database."""
    # Ensure ID is 1
    profile_id = 1
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO profile (
                id, name, email, phone, location, linkedin_url, github_url, portfolio_url,
                skills, resume_text, resume_filename, work_experience, llm_provider, llm_model
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            profile_id,
            profile.get("name", ""),
            profile.get("email", ""),
            profile.get("phone", ""),
            profile.get("location", ""),
            profile.get("linkedin_url", ""),
            profile.get("github_url", ""),
            profile.get("portfolio_url", ""),
            json.dumps(profile.get("skills", [])),
            profile.get("resume_text", ""),
            profile.get("resume_filename", ""),
            json.dumps(profile.get("work_experience", [])),
            profile.get("llm_provider", "ollama"),
            profile.get("llm_model", "qwen2.5:14b")
        ))
        conn.commit()


# ─────────────────────────── Applications ───────────────────────────

def get_applications() -> List[Dict[str, Any]]:
    """Retrieve all applications from SQLite database, ordered by applied_at desc."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications ORDER BY applied_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def add_application(app: Dict[str, Any]) -> None:
    """Add a new application log to the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO applications (
                id, job_id, job_title, company, apply_url, source, status, applied_at, cover_letter, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            app.get("id"),
            app.get("job_id", ""),
            app.get("job_title", ""),
            app.get("company", ""),
            app.get("apply_url", ""),
            app.get("source", ""),
            app.get("status", "applied"),
            app.get("applied_at"),
            app.get("cover_letter", ""),
            app.get("notes", "")
        ))
        conn.commit()


def update_application(app_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update specific fields in an application log."""
    # First check if it exists
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        # Build query dynamically based on updates
        fields = []
        params = []
        for k, v in updates.items():
            if v is not None:
                fields.append(f"{k} = ?")
                params.append(v)
        
        if fields:
            params.append(app_id)
            cursor.execute(f"UPDATE applications SET {', '.join(fields)} WHERE id = ?", tuple(params))
            conn.commit()
            
        cursor.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
        return dict(cursor.fetchone())


def delete_application(app_id: str) -> bool:
    """Delete an application log by id."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM applications WHERE id = ?", (app_id,))
        conn.commit()
        return cursor.rowcount > 0


def is_job_applied(job_id: str) -> bool:
    """Check if a job has already been applied to."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM applications WHERE job_id = ?", (job_id,))
        return cursor.fetchone()[0] > 0
