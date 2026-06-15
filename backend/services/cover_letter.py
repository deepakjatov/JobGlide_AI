"""Cover letter generation service supporting Ollama, OpenAI, and Gemini."""

import asyncio
from typing import AsyncGenerator

from config import settings


SYSTEM_PROMPT = """You are an expert career coach and professional writer.
Generate a concise, compelling, ATS-friendly cover letter in exactly 3-4 paragraphs.

Rules:
- First paragraph: Express enthusiasm for the role and company, mention 1-2 specific things about the company/role.
- Second paragraph: Highlight the most relevant 2-3 skills/experiences from the candidate's profile that match the job.
- Third paragraph: Briefly mention a work achievement or project that demonstrates impact.
- Final paragraph: Strong closing with a call to action.
- DO NOT use generic phrases like "I am writing to express my interest".
- Use active voice and confident tone.
- Keep it under 350 words.
- Output ONLY the cover letter text, no subject lines, no "Dear Hiring Manager" headers — start directly with the opening sentence.
"""


def _build_user_message(job_title: str, company: str, job_description: str, profile: dict) -> str:
    skills = ", ".join(profile.get("skills", [])) or "Not specified"
    exp_blocks = []
    for exp in profile.get("work_experience", []):
        exp_blocks.append(
            f"- {exp.get('role', '')} at {exp.get('company', '')} ({exp.get('duration', '')}): {exp.get('description', '')}"
        )
    exp_text = "\n".join(exp_blocks) if exp_blocks else "Not specified"
    resume_snippet = (profile.get("resume_text", "") or "")[:1500]

    return f"""Write a cover letter for the following job application:

JOB TITLE: {job_title}
COMPANY: {company}
JOB DESCRIPTION:
{job_description[:2000]}

CANDIDATE PROFILE:
Name: {profile.get('name', 'The Candidate')}
Skills: {skills}
Work Experience:
{exp_text}
Resume Summary:
{resume_snippet}
"""


# ─────────────────────────── Ollama ─────────────────────────────────

async def generate_with_ollama(
    job_title: str, company: str, job_description: str, profile: dict, model: str
) -> AsyncGenerator[str, None]:
    try:
        import ollama as ollama_sdk
    except ImportError:
        yield "ERROR: ollama package not installed. Run: pip install ollama"
        return

    user_msg = _build_user_message(job_title, company, job_description, profile)

    try:
        loop = asyncio.get_event_loop()

        def _sync_stream():
            # Use Client with explicit host — host is NOT an option/param
            client = ollama_sdk.Client(host=settings.OLLAMA_HOST)
            chunks = []
            stream = client.chat(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                stream=True,
            )
            for chunk in stream:
                # SDK v0.6.x returns ChatResponse objects; extract content safely
                try:
                    content = chunk.message.content or ""
                except AttributeError:
                    # Fallback: dict-style access for older SDK
                    content = chunk.get("message", {}).get("content", "") if isinstance(chunk, dict) else ""
                chunks.append(content)
            return chunks

        chunks = await loop.run_in_executor(None, _sync_stream)
        for c in chunks:
            yield c
    except Exception as e:
        err = str(e)
        if "connection" in err.lower() or "refused" in err.lower():
            yield f"ERROR: Cannot connect to Ollama at {settings.OLLAMA_HOST}. Make sure 'ollama serve' is running."
        else:
            yield f"ERROR: Ollama error — {err}"


# ─────────────────────────── OpenAI ─────────────────────────────────

async def generate_with_openai(
    job_title: str, company: str, job_description: str, profile: dict, model: str
) -> AsyncGenerator[str, None]:
    if not settings.OPENAI_API_KEY:
        yield "ERROR: OPENAI_API_KEY is not configured in .env"
        return

    try:
        from openai import AsyncOpenAI
    except ImportError:
        yield "ERROR: openai package not installed. Run: pip install openai"
        return

    user_msg = _build_user_message(job_title, company, job_description, profile)
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            stream=True,
            max_tokens=600,
            temperature=0.7,
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content or ""
            if content:
                yield content
    except Exception as e:
        yield f"ERROR: OpenAI error — {e}"


# ─────────────────────────── Gemini ─────────────────────────────────

async def generate_with_gemini(
    job_title: str, company: str, job_description: str, profile: dict, model: str
) -> AsyncGenerator[str, None]:
    if not settings.GEMINI_API_KEY:
        yield "ERROR: GEMINI_API_KEY is not configured in .env"
        return

    try:
        import google.generativeai as genai
    except ImportError:
        yield "ERROR: google-generativeai package not installed. Run: pip install google-generativeai"
        return

    user_msg = _build_user_message(job_title, company, job_description, profile)
    genai.configure(api_key=settings.GEMINI_API_KEY)

    try:
        gemini_model = genai.GenerativeModel(
            model_name=model,
            system_instruction=SYSTEM_PROMPT,
        )
        loop = asyncio.get_event_loop()

        def _sync_stream():
            chunks = []
            response = gemini_model.generate_content(user_msg, stream=True)
            for chunk in response:
                if chunk.text:
                    chunks.append(chunk.text)
            return chunks

        chunks = await loop.run_in_executor(None, _sync_stream)
        for c in chunks:
            yield c
    except Exception as e:
        yield f"ERROR: Gemini error — {e}"


# ─────────────────────────── Provider Dispatch ──────────────────────

async def generate_cover_letter(
    job_title: str,
    company: str,
    job_description: str,
    profile: dict,
    provider: str,
    model: str,
) -> AsyncGenerator[str, None]:
    """Route to the correct LLM provider and stream the cover letter."""
    if provider == "openai":
        async for chunk in generate_with_openai(job_title, company, job_description, profile, model):
            yield chunk
    elif provider == "gemini":
        async for chunk in generate_with_gemini(job_title, company, job_description, profile, model):
            yield chunk
    else:
        # Default: ollama
        async for chunk in generate_with_ollama(job_title, company, job_description, profile, model):
            yield chunk


# ─────────────────────────── Provider Discovery ─────────────────────

async def get_available_providers() -> list:
    """Return a structured list of available LLM providers and their models."""
    providers = []

    # 1. Ollama — probe via SDK (same mechanism that generation uses)
    try:
        import ollama as ollama_sdk
        import asyncio

        loop = asyncio.get_event_loop()

        def _list_models():
            client = ollama_sdk.Client(host=settings.OLLAMA_HOST)
            result = client.list()
            # SDK v0.6.x: result.models is a list of Model objects
            try:
                return [m.model for m in result.models]
            except AttributeError:
                # Fallback: dict-style for older SDK
                return [m.get("name", "") for m in result.get("models", [])] if isinstance(result, dict) else []

        raw_models = await loop.run_in_executor(None, _list_models)
        # Filter out embedding models
        text_models = [m for m in raw_models if m and "embed" not in m.lower()]
        providers.append({
            "provider": "ollama",
            "label": "🦙 Ollama (Local)",
            "available": True,
            "models": text_models,
        })
    except Exception as e:
        providers.append({
            "provider": "ollama",
            "label": "🦙 Ollama (Local)",
            "available": False,
            "models": [],
            "reason": f"Ollama is not reachable at {settings.OLLAMA_HOST}. Run: ollama serve",
        })

    # 2. OpenAI
    if settings.OPENAI_API_KEY:
        providers.append({
            "provider": "openai",
            "label": "🤖 OpenAI",
            "available": True,
            "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
        })
    else:
        providers.append({
            "provider": "openai",
            "label": "🤖 OpenAI",
            "available": False,
            "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
            "reason": "Add OPENAI_API_KEY to backend/.env",
        })

    # 3. Gemini
    if settings.GEMINI_API_KEY:
        providers.append({
            "provider": "gemini",
            "label": "💎 Gemini",
            "available": True,
            "models": ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
        })
    else:
        providers.append({
            "provider": "gemini",
            "label": "💎 Gemini",
            "available": False,
            "models": ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
            "reason": "Add GEMINI_API_KEY to backend/.env",
        })

    return providers
