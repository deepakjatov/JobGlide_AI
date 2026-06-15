"""
LinkedIn Easy Apply automation using Playwright.
This service is entirely opt-in and runs as a background task.
"""

import asyncio
import json
import random
import threading
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from services import storage

# ─── Session state ────────────────────────────────────────────────────────────

# Stores the current running task state: progress events, status, etc.
_auto_apply_state: Dict = {
    "running": False,
    "events": [],          # List of {"time", "msg", "type"}
    "applied": 0,
    "skipped": 0,
    "errors": 0,
}

COOKIE_FILE = Path(__file__).parent.parent / "data" / "linkedin_cookies.json"


def get_status() -> Dict:
    """Return a snapshot of the current auto-apply state."""
    return {
        "running": _auto_apply_state["running"],
        "applied": _auto_apply_state["applied"],
        "skipped": _auto_apply_state["skipped"],
        "errors": _auto_apply_state["errors"],
        "events": _auto_apply_state["events"][-50:],  # last 50 events
    }


def _log_event(msg: str, event_type: str = "info") -> None:
    """Append a progress event."""
    _auto_apply_state["events"].append({
        "time": datetime.now(timezone.utc).isoformat(),
        "msg": msg,
        "type": event_type,  # info | success | warning | error
    })
    print(f"[AutoApply] [{event_type.upper()}] {msg}")


# ─── Playwright Bot ────────────────────────────────────────────────────────────

async def _save_cookies(context) -> None:
    COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)
    cookies = await context.cookies()
    with open(COOKIE_FILE, "w") as f:
        json.dump(cookies, f)


async def _load_cookies(context) -> bool:
    if COOKIE_FILE.exists():
        with open(COOKIE_FILE, "r") as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)
        return True
    return False


async def _linkedin_login(page, email: str, password: str) -> bool:
    """Log in to LinkedIn. Returns True on success."""
    _log_event("Navigating to LinkedIn login page...")
    await page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
    await asyncio.sleep(random.uniform(1.5, 3.0))

    try:
        await page.fill("#username", email)
        await asyncio.sleep(random.uniform(0.5, 1.2))
        await page.fill("#password", password)
        await asyncio.sleep(random.uniform(0.5, 1.0))
        await page.click('[type="submit"]')
        await page.wait_for_url("**/feed/**", timeout=15000)
        _log_event("✅ LinkedIn login successful", "success")
        return True
    except Exception as e:
        _log_event(f"❌ Login failed: {e}", "error")
        return False


async def _is_logged_in(page) -> bool:
    """Check if we're already logged in via saved cookies."""
    await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
    await asyncio.sleep(2)
    return "feed" in page.url


def clean_phone_number(phone: str) -> str:
    if not phone:
        return ""
    # Strip spaces, dashes, parentheses
    cleaned = "".join(c for c in phone if c.isdigit() or c == "+")
    
    # Strip country code prefix (e.g. +91, +1)
    if cleaned.startswith("+"):
        for prefix in ["+91", "+1", "+44", "+61", "+86"]:
            if cleaned.startswith(prefix):
                return cleaned[len(prefix):]
        if len(cleaned) > 10:
            return cleaned[-10:]
            
    if len(cleaned) == 12 and cleaned.startswith("91"):
        return cleaned[2:]
    if len(cleaned) == 11 and cleaned.startswith("1"):
        return cleaned[1:]
        
    return cleaned


async def _handle_easy_apply_modal(page, profile: dict) -> bool:
    """
    Fill out an Easy Apply modal. Returns True if successfully submitted.
    Handles multi-step forms by clicking Next until Submit is available.
    """
    for step in range(8):  # max 8 steps
        await asyncio.sleep(random.uniform(1.0, 2.0))

        # Fill phone if present
        phone_selector = (
            'input[id*="phoneNumber"], input[id*="nationalNumber"], input[id*="phone"], '
            'input[name*="phoneNumber"], input[name*="phone"], input[name*="nationalNumber"], '
            'input[type="tel"], input[autocomplete*="tel"]'
        )
        phone_input = page.locator(phone_selector).first
        if await phone_input.count() > 0:
            current_val = await phone_input.input_value()
            if not current_val:
                phone_val = clean_phone_number(profile.get("phone", ""))
                if phone_val:
                    await phone_input.fill(phone_val)
                    _log_event(f"Filled phone number: {phone_val}")
                else:
                    _log_event("⚠️ Phone number field detected but no phone number found in profile settings.", "warning")


        # Fill city/location if present
        city_input = page.locator('input[id*="city"], input[name*="location"]').first
        if await city_input.count() > 0:
            val = await city_input.input_value()
            if not val:
                await city_input.fill(profile.get("location", ""))

        # Handle resume file upload if file input exists and a local resume is saved
        file_inputs = page.locator('input[type="file"]')
        for i in range(await file_inputs.count()):
            try:
                accept_attr = await file_inputs.nth(i).get_attribute("accept") or ""
                if "pdf" in accept_attr.lower() or "doc" in accept_attr.lower() or not accept_attr:
                    resume_filename = profile.get("resume_filename", "")
                    if resume_filename:
                        resume_path = Path(__file__).parent.parent / "data" / "resumes" / resume_filename
                        if resume_path.exists():
                            await file_inputs.nth(i).set_input_files(str(resume_path))
                            _log_event(f"Uploaded local resume file: {resume_filename}", "success")
                        else:
                            _log_event(f"⚠️ Resume file {resume_filename} is configured but not found locally at {resume_path}", "warning")
            except Exception as e:
                _log_event(f"⚠️ Failed to upload resume: {e}", "warning")

        # Handle "Yes/No" radio buttons — prefer Yes for work authorization, etc.
        radios = page.locator('fieldset input[type="radio"][value="Yes"]')
        for i in range(await radios.count()):
            try:
                await radios.nth(i).check()
            except Exception:
                pass

        # Handle numeric inputs (years of experience etc.) — set to 2 if empty
        number_inputs = page.locator('input[type="number"]')
        for i in range(await number_inputs.count()):
            try:
                val = await number_inputs.nth(i).input_value()
                if not val:
                    await number_inputs.nth(i).fill("2")
            except Exception:
                pass

        # Check for Submit button
        submit_btn = page.locator('button[aria-label*="Submit application"]').first
        if await submit_btn.count() > 0:
            await submit_btn.click()
            await asyncio.sleep(3.0)
            
            # Dismiss the post-apply confirmation dialog/advertisements immediately
            try:
                # 1. Look for Dismiss (X) button
                close_btn = page.locator('button[aria-label="Dismiss"]').first
                if await close_btn.count() > 0:
                    await close_btn.click()
                    await asyncio.sleep(1.0)
                else:
                    # 2. Look for Done or Not now buttons
                    done_btn = page.locator('button:has-text("Done"), button:has-text("done"), button:has-text("Not now")').first
                    if await done_btn.count() > 0:
                        await done_btn.click()
                        await asyncio.sleep(1.0)
            except Exception as e:
                print(f"[AutoApply] Failed to close post-apply modal: {e}")
                
            return True

        # Check for Next / Review / Continue button
        next_btn = page.locator(
            'button[aria-label*="Continue"], button[aria-label*="Next"], button[aria-label*="Review"]'
        ).first
        if await next_btn.count() > 0:
            await next_btn.click()
        else:
            break  # No navigation found, bail out

    return False


async def run_auto_apply(
    linkedin_email: str,
    linkedin_password: str,
    profile: dict,
    max_applications: int = 5,
    keywords: List[str] = None,
) -> None:
    """
    Main Playwright bot coroutine.
    Runs LinkedIn Easy Apply for matching jobs and logs progress.
    """
    from playwright.async_api import async_playwright

    if _auto_apply_state["running"]:
        _log_event("Auto-apply is already running. Stop it first.", "warning")
        return

    # Reset state
    _auto_apply_state.update({
        "running": True,
        "events": [],
        "applied": 0,
        "skipped": 0,
        "errors": 0,
    })

    _log_event("🚀 Starting LinkedIn Easy Apply automation...")
    _log_event(f"Target: up to {max_applications} applications")

    search_keyword = (keywords[0] if keywords else "Software Engineer")

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=False,  # Visible browser so user can intervene
                slow_mo=50,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
            )
            page = await context.new_page()

            # Try cookies first
            cookies_loaded = await _load_cookies(context)
            logged_in = False
            if cookies_loaded:
                _log_event("Trying saved session cookies...")
                logged_in = await _is_logged_in(page)

            if not logged_in:
                if not linkedin_email or not linkedin_password:
                    _log_event("❌ No credentials provided and no saved session. Aborting.", "error")
                    _auto_apply_state["running"] = False
                    await browser.close()
                    return
                logged_in = await _linkedin_login(page, linkedin_email, linkedin_password)

            if not logged_in:
                _auto_apply_state["running"] = False
                await browser.close()
                return

            await _save_cookies(context)

            # Search for Easy Apply jobs
            search_url = (
                f"https://www.linkedin.com/jobs/search/"
                f"?keywords={search_keyword.replace(' ', '%20')}"
                f"&f_LF=f_AL"   # Easy Apply filter
                f"&f_TPR=r259200"  # Past 3 days
                f"&sortBy=DD"   # Sort by date
            )
            _log_event(f"🔍 Searching LinkedIn for: {search_keyword} (Easy Apply only)")
            await page.goto(search_url, wait_until="domcontentloaded")
            await asyncio.sleep(random.uniform(2, 4))

            applied_count = 0

            # Collect job cards
            job_cards = await page.locator(".job-card-container").all()
            _log_event(f"Found {len(job_cards)} job listings on this page")

            for card in job_cards:
                if applied_count >= max_applications:
                    break
                if not _auto_apply_state["running"]:
                    _log_event("⏹️ Auto-apply stopped by user.", "warning")
                    break

                try:
                    # Get LinkedIn job ID from card and check if already applied
                    li_job_id = await card.get_attribute("data-job-id")
                    if li_job_id:
                        real_job_id = f"linkedin-{li_job_id}"
                        if storage.is_job_applied(real_job_id):
                            _log_event(f"⏭️ Skipping already applied job: {real_job_id}", "info")
                            _auto_apply_state["skipped"] += 1
                            continue
                    else:
                        real_job_id = f"linkedin-auto-{uuid.uuid4().hex[:8]}"

                    # Click the card
                    await card.click()
                    await asyncio.sleep(random.uniform(1.5, 3.0))

                    # Get job title & company
                    title_el = page.locator(".job-details-jobs-unified-top-card__job-title").first
                    company_el = page.locator(".job-details-jobs-unified-top-card__company-name").first
                    job_title = (await title_el.text_content() or "Unknown Role").strip()
                    company = (await company_el.text_content() or "Unknown Company").strip()

                    _log_event(f"📋 Reviewing: {job_title} @ {company}")

                    # Check for Easy Apply button
                    easy_btn = page.locator('button.jobs-apply-button[aria-label*="Easy Apply"]').first
                    if await easy_btn.count() == 0:
                        _log_event(f"⏭️  Skipped (not Easy Apply): {job_title}", "warning")
                        _auto_apply_state["skipped"] += 1
                        continue

                    # Click Easy Apply
                    await easy_btn.click()
                    await asyncio.sleep(random.uniform(1.5, 2.5))

                    # Fill and submit the modal
                    success = await _handle_easy_apply_modal(page, profile)

                    if success:
                        applied_count += 1
                        _auto_apply_state["applied"] += 1
                        _log_event(f"✅ Applied: {job_title} @ {company}", "success")

                        # Log to application tracker
                        storage.add_application({
                            "id": str(uuid.uuid4()),
                            "job_id": real_job_id,
                            "job_title": job_title,
                            "company": company,
                            "apply_url": page.url,
                            "source": "linkedin",
                            "status": "applied",
                            "applied_at": datetime.now(timezone.utc).isoformat(),
                            "cover_letter": "",
                            "notes": "Applied via LinkedIn Easy Apply automation",
                        })
                    else:
                        _log_event(f"⚠️  Could not complete form: {job_title}", "warning")
                        _auto_apply_state["skipped"] += 1
                        # Close any open modal
                        close_btn = page.locator('button[aria-label="Dismiss"]').first
                        if await close_btn.count() > 0:
                            await close_btn.click()
                            await asyncio.sleep(1.0)
                            # Handle LinkedIn's "Discard this application?" confirmation dialog
                            discard_btn = page.locator(
                                'button[data-control-name="discard_application_confirm_btn"], '
                                'button[data-test-dialog-primary-btn], '
                                'button:has-text("Discard"), '
                                'button:has-text("discard")'
                            ).first
                            if await discard_btn.count() > 0:
                                await discard_btn.click()
                                await asyncio.sleep(1.5)
                        
                        # Verify the modal overlay is gone, reload page if still stuck
                        modal_overlay = page.locator('.artdeco-modal-overlay, #artdeco-modal-outlet').first
                        if await modal_overlay.count() > 0 and await modal_overlay.is_visible():
                            _log_event("Stuck modal or overlay detected. Reloading page to clean state...", "warning")
                            await page.reload(wait_until="domcontentloaded")
                            await asyncio.sleep(3.0)

                    # Random human-like delay between applications
                    delay = random.uniform(10, 25)
                    _log_event(f"⏳ Waiting {delay:.0f}s before next application...")
                    await asyncio.sleep(delay)

                except Exception as e:
                    _auto_apply_state["errors"] += 1
                    _log_event(f"❌ Error on job card: {e}", "error")
                    # Try to close any open modal/dialog to recover state for the next card
                    try:
                        close_btn = page.locator('button[aria-label="Dismiss"]').first
                        if await close_btn.count() > 0:
                            await close_btn.click()
                            await asyncio.sleep(1.0)
                            discard_btn = page.locator(
                                'button[data-control-name="discard_application_confirm_btn"], '
                                'button[data-test-dialog-primary-btn], '
                                'button:has-text("Discard"), '
                                'button:has-text("discard")'
                            ).first
                            if await discard_btn.count() > 0:
                                await discard_btn.click()
                                await asyncio.sleep(1.5)
                    except Exception:
                        pass
                    # If overlay is still present, force reload the page
                    try:
                        modal_overlay = page.locator('.artdeco-modal-overlay, #artdeco-modal-outlet').first
                        if await modal_overlay.count() > 0 and await modal_overlay.is_visible():
                            _log_event("Overlay still visible on error. Reloading page to reset DOM...", "warning")
                            await page.reload(wait_until="domcontentloaded")
                            await asyncio.sleep(3.0)
                    except Exception:
                        pass
                    await asyncio.sleep(3)

            _log_event(
                f"🏁 Done! Applied: {_auto_apply_state['applied']}, "
                f"Skipped: {_auto_apply_state['skipped']}, "
                f"Errors: {_auto_apply_state['errors']}",
                "success",
            )
            await browser.close()

    except Exception as e:
        tb = traceback.format_exc()
        err_msg = str(e) or type(e).__name__ or "Unknown error"
        _log_event(f"❌ Fatal error: {err_msg}", "error")
        _log_event(f"Traceback: {tb}", "error")
        print(f"[AutoApply] FATAL:\n{tb}")
    finally:
        _auto_apply_state["running"] = False


def run_auto_apply_sync(
    linkedin_email: str,
    linkedin_password: str,
    profile: dict,
    max_applications: int = 5,
    keywords: List[str] = None,
) -> None:
    """
    Synchronous wrapper that runs the async Playwright bot in a fresh event loop
    on a dedicated thread. This avoids conflicts with FastAPI's event loop.
    """
    asyncio.run(
        run_auto_apply(
            linkedin_email=linkedin_email,
            linkedin_password=linkedin_password,
            profile=profile,
            max_applications=max_applications,
            keywords=keywords,
        )
    )


def stop_auto_apply() -> None:
    """Signal the running auto-apply task to stop."""
    _auto_apply_state["running"] = False
    _log_event("⏹️ Stop signal sent.", "warning")
