"""Apply router — profile, applications, cover letter, auto-apply endpoints."""

import asyncio
import threading
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from models import (
    Application,
    ApplicationUpdate,
    AutoApplyRequest,
    CoverLetterRequest,
    QuickApplyRequest,
    UserProfile,
)
from services import cover_letter as cl_service
from services import storage
from services import auto_apply as auto_apply_service
from services.auto_apply import run_auto_apply_sync

router = APIRouter(prefix="/api")


# ─────────────────────────── Profile ────────────────────────────────

@router.get("/profile")
async def get_profile():
    """Retrieve the saved user profile."""
    profile = storage.get_profile()
    if profile is None:
        return {}
    return profile


import shutil
from pathlib import Path

RESUME_DIR = Path(__file__).parent.parent / "data" / "resumes"


@router.post("/profile")
async def save_profile(profile: UserProfile):
    """Save or update the user profile."""
    storage.save_profile(profile.model_dump())
    return {"ok": True}


@router.post("/profile/resume")
async def upload_resume(file: UploadFile = File(...)):
    """Save resume file locally and parse text if it is a PDF."""
    RESUME_DIR.mkdir(parents=True, exist_ok=True)
    
    file_path = RESUME_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    extracted_text = ""
    if file.filename.lower().endswith(".pdf"):
        try:
            import pypdf
            reader = pypdf.PdfReader(str(file_path))
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            extracted_text = "\n".join(text_parts).strip()
        except Exception as e:
            print(f"[ResumeUpload] PDF parsing failed: {e}")
            extracted_text = f"Error extracting text from PDF: {e}"
    elif file.filename.lower().endswith(".txt"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                extracted_text = f.read().strip()
        except Exception:
            try:
                with open(file_path, "r", encoding="cp1252") as f:
                    extracted_text = f.read().strip()
            except Exception:
                pass
                
    profile = storage.get_profile() or {}
    profile["resume_filename"] = file.filename
    if extracted_text:
        profile["resume_text"] = extracted_text
        
    storage.save_profile(profile)
    
    return {
        "ok": True,
        "filename": file.filename,
        "extracted_text": extracted_text[:1000] + ("..." if len(extracted_text) > 1000 else "")
    }


# ─────────────────────────── Applications ───────────────────────────

@router.get("/applications")
async def list_applications(status: Optional[str] = None):
    """List all tracked job applications, optionally filtered by status."""
    apps = storage.get_applications()
    if status:
        apps = [a for a in apps if a.get("status") == status]
    return apps


@router.post("/applications", response_model=Application)
async def add_application_manual(app: Application):
    """Manually log a new job application."""
    storage.add_application(app.model_dump())
    return app


@router.patch("/applications/{app_id}")
async def update_application(app_id: str, updates: ApplicationUpdate):
    """Update status, notes, or cover letter on a tracked application."""
    updated = storage.update_application(app_id, updates.model_dump(exclude_none=True))
    if updated is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return updated


@router.delete("/applications/{app_id}")
async def delete_application(app_id: str):
    """Remove a tracked application."""
    success = storage.delete_application(app_id)
    if not success:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"ok": True}


@router.get("/applications/applied-ids")
async def get_applied_job_ids():
    """Return list of job IDs that have already been applied to."""
    apps = storage.get_applications()
    return [a.get("job_id") for a in apps if a.get("job_id")]


# ─────────────────────────── Quick Apply ────────────────────────────

@router.post("/apply/quick")
async def quick_apply(req: QuickApplyRequest):
    """Log a quick apply and return the apply URL for the frontend to open."""
    app_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    application = {
        "id": app_id,
        "job_id": req.job_id,
        "job_title": req.job_title,
        "company": req.company,
        "apply_url": req.apply_url,
        "source": req.source,
        "status": "applied",
        "applied_at": now,
        "cover_letter": "",
        "notes": "",
    }
    storage.add_application(application)
    return {"ok": True, "app_id": app_id, "apply_url": req.apply_url}


# ─────────────────────────── Cover Letter ───────────────────────────

@router.get("/apply/llm-providers")
async def get_llm_providers():
    """Return available LLM providers and their models."""
    return await cl_service.get_available_providers()


@router.post("/apply/cover-letter")
async def generate_cover_letter(req: CoverLetterRequest):
    """Generate a cover letter using the selected LLM provider. Streams the response."""
    profile = storage.get_profile() or {}

    async def stream_generator():
        async for chunk in cl_service.generate_cover_letter(
            job_title=req.job_title,
            company=req.company,
            job_description=req.job_description,
            profile=profile,
            provider=req.provider,
            model=req.model,
        ):
            yield chunk

    return StreamingResponse(
        stream_generator(),
        media_type="text/plain",
        headers={"X-Accel-Buffering": "no"},
    )


# ─────────────────────────── Auto Apply ─────────────────────────────

@router.post("/apply/auto/start")
async def start_auto_apply(req: AutoApplyRequest):
    """Start the LinkedIn Easy Apply automation on a dedicated background thread."""
    if auto_apply_service.get_status()["running"]:
        raise HTTPException(status_code=409, detail="Auto-apply is already running")

    profile = storage.get_profile() or {}
    keywords = req.filters.keywords if req.filters else ["Software Engineer"]

    # Use credentials from request; fall back to .env
    from config import settings
    email = req.linkedin_email or settings.LINKEDIN_EMAIL
    password = req.linkedin_password or settings.LINKEDIN_PASSWORD

    if not email or not password:
        raise HTTPException(
            status_code=400,
            detail="LinkedIn credentials are required. Set them in Settings or backend/.env",
        )

    # Launch on a dedicated daemon thread with its own event loop
    # (Playwright requires its own asyncio loop, separate from FastAPI's)
    thread = threading.Thread(
        target=run_auto_apply_sync,
        kwargs={
            "linkedin_email": email,
            "linkedin_password": password,
            "profile": profile,
            "max_applications": req.max_applications,
            "keywords": keywords,
        },
        daemon=True,
        name="AutoApplyThread",
    )
    thread.start()
    return {"ok": True, "message": "Auto-apply started in background thread"}


@router.get("/apply/auto/test")
async def test_playwright():
    """Quick diagnostic: check Playwright + Chromium are installed correctly."""
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://example.com")
            title = await page.title()
            await browser.close()
        return {"ok": True, "page_title": title, "message": "Playwright is working correctly"}
    except Exception as e:
        import traceback
        return {"ok": False, "error": str(e) or type(e).__name__, "traceback": traceback.format_exc()}


@router.post("/apply/auto/stop")
async def stop_auto_apply():
    """Stop the running auto-apply task."""
    auto_apply_service.stop_auto_apply()
    return {"ok": True, "message": "Stop signal sent"}


@router.get("/apply/auto/status")
async def auto_apply_status():
    """Poll the current auto-apply progress."""
    return auto_apply_service.get_status()
