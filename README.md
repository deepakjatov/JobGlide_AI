# 🚀 JobHunter AI — Resume-Powered Job Search Agent

A full-stack job search application that aggregates jobs from **4 different APIs** using your resume-based filters as defaults. Built with **React (Vite)** and **Python FastAPI**.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.137-009688?logo=fastapi)
![Vite](https://img.shields.io/badge/Vite-8-646CFF?logo=vite)

---

## ✨ Features

- **Resume-Based Default Filters** — Hardcoded filters from your resume (keywords, skills, experience, location) load automatically on startup
- **Editable Filters** — Add/remove filter chips, change experience level, modify keywords from the UI
- **4 Job API Sources:**
  - 🔵 **JSearch** (RapidAPI) — Aggregates from LinkedIn, Indeed, Glassdoor, ZipRecruiter
  - 🟢 **Himalayas** — Free, no auth, remote-focused jobs
  - 🟠 **Adzuna** — India-focused with salary data
  - 🟣 **Remotive** — Curated remote-only jobs
- **Smart Deduplication** — Removes duplicate listings across sources
- **Skill Matching** — Highlights which of your skills match each job description
- **In-Memory Caching** — Avoids burning API quota on repeated searches (30-min TTL)
- **Premium Dark UI** — Glassmorphism design with micro-animations
- **Responsive** — Collapsible sidebar drawer on mobile

---

## 📁 Project Structure

```
job_apply_agent/
├── backend/                    # Python FastAPI server
│   ├── venv/                   # Python virtual environment
│   ├── .env                    # API keys (create from .env.example)
│   ├── .env.example            # Template for API keys
│   ├── requirements.txt        # Python dependencies
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Settings & default resume filters
│   ├── models.py               # Pydantic models (Job, JobFilter, etc.)
│   ├── providers/              # Job API integrations
│   │   ├── base.py             # Abstract JobProvider base class
│   │   ├── jsearch.py          # JSearch (RapidAPI) provider
│   │   ├── himalayas.py        # Himalayas provider (no auth)
│   │   ├── adzuna.py           # Adzuna provider
│   │   └── remotive.py         # Remotive provider (no auth)
│   ├── services/
│   │   ├── aggregator.py       # Multi-API aggregator with dedup & sorting
│   │   └── cache.py            # In-memory cache with TTL
│   └── routers/
│       └── jobs.py             # API routes (/api/jobs/search, /api/filters/default)
│
├── frontend/                   # React (Vite) app
│   ├── src/
│   │   ├── index.css           # Design system (glassmorphism theme)
│   │   ├── App.jsx             # Main layout with sidebar + content
│   │   ├── App.css             # Layout styles
│   │   ├── api/
│   │   │   └── jobsApi.js      # Backend API client
│   │   ├── hooks/
│   │   │   └── useJobs.js      # Custom hook (filter state, search, etc.)
│   │   └── components/
│   │       ├── Header.jsx      # App header with gradient title
│   │       ├── FilterPanel.jsx # Filter sidebar with chips & buttons
│   │       ├── JobCard.jsx     # Individual job result card
│   │       ├── JobList.jsx     # Job grid with source tabs
│   │       └── SearchStats.jsx # Search statistics bar
│   ├── package.json
│   └── vite.config.js
│
└── README.md                   # ← You are here
```

---

## 🛠️ Prerequisites

- **Python 3.12+** (tested with 3.12.4)
- **Node.js 18+** and **npm**
- (Optional) API keys for JSearch and Adzuna (see below)

---

## ⚡ Quick Start

### 1. Clone / Navigate to the project

```bash
cd job_apply_agent
```

### 2. Backend Setup

```bash
# Navigate to backend
cd backend

# Create a Python virtual environment
python -m venv venv

# Activate the virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Windows (CMD):
.\venv\Scripts\activate.bat

# macOS / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create your .env file from the template
copy .env.example .env       # Windows
# cp .env.example .env       # macOS / Linux

# (Optional) Add your API keys to .env — see "API Keys" section below

# Start the backend server
python main.py
# OR using the venv python directly (without activating):
# .\venv\Scripts\python.exe main.py
```

The backend will start at **http://localhost:8000**.

### 3. Frontend Setup

Open a **new terminal**:

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The frontend will start at **http://localhost:5173**.

### 4. Open in Browser

Visit **http://localhost:5173** — you should see the app with your resume filters pre-loaded!

---

## 🔑 API Keys

The app uses 4 job APIs. **Two work without any keys** (Himalayas & Remotive). The other two need free API keys:

| API | Auth Required | Free Tier | Sign Up |
|-----|:---:|---|---|
| **JSearch** | ✅ RapidAPI Key | ~200 req/month | [rapidapi.com/jsearch](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) |
| **Himalayas** | ❌ None | Unlimited | — |
| **Adzuna** | ✅ App ID + Key | 2,500 req/month | [developer.adzuna.com](https://developer.adzuna.com/) |
| **Remotive** | ❌ None | 4 req/day | — |

### Setting up API Keys

Edit `backend/.env`:

```env
JSEARCH_API_KEY=your_rapidapi_key_here
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
```

> **Note:** The app works without any API keys — it will use Himalayas and Remotive. Adding JSearch and Adzuna keys gives you access to many more job listings.

---

## 🎯 Default Resume Filters

These are hardcoded in `backend/config.py` and loaded on app startup:

```python
DEFAULT_FILTERS = {
    "keywords": ["AI Engineer", "GenAI Engineer", "Full Stack Engineer"],
    "skills": ["React", "FastAPI", "RAG", "LLM"],
    "experience": "0-3",
    "locations": ["Remote", "India"],
}
```

**To change defaults permanently**, edit the `DEFAULT_FILTERS` dict in `backend/config.py`.

**To change filters temporarily**, use the UI — add/remove chips, change experience, then click **Apply Filters**. Click **Reset To Resume** to restore defaults.

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/api/filters/default` | Get hardcoded resume filters |
| `POST` | `/api/jobs/search` | Search jobs with custom filters |
| `GET` | `/api/jobs/sources` | Get available API sources & config status |

### Example: Search Jobs

```bash
curl -X POST http://localhost:8000/api/jobs/search \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["AI Engineer"],
    "skills": ["React", "LLM"],
    "experience": "0-3",
    "locations": ["Remote", "India"]
  }'
```

---

## 🎨 UI Features

- **Filter Panel** — Chip-based inputs for Keywords, Skills, Location + Experience dropdown
- **Apply Filters** — Searches all configured APIs concurrently
- **Clear All** — Empties all filter fields
- **Reset To Resume** — Restores hardcoded resume defaults and re-searches
- **Source Tabs** — Filter displayed results by source (All / JSearch / Himalayas / Adzuna / Remotive)
- **Job Cards** — Show company logo, title, location, skill matches, source badge, and Apply link
- **Skeleton Loading** — Shimmer animation while fetching
- **Responsive Design** — Collapsible sidebar on mobile with hamburger menu

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite 8, Vanilla CSS |
| Backend | Python 3.12, FastAPI, Uvicorn |
| HTTP Client | httpx (async) |
| Styling | Glassmorphism dark theme, Inter font |
| Caching | In-memory with TTL |

---

## 📝 License

MIT
