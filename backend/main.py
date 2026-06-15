import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers.jobs import router as jobs_router
from routers.apply import router as apply_router

from services.db import initialize_db

app = FastAPI(title="JobGlide AI API")

@app.on_event("startup")
def on_startup():
    initialize_db()

# CORS configuration
origins = [o.strip() for o in settings.ALLOW_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs_router)
app.include_router(apply_router)


@app.get("/")
async def root():
    return {"status": "ok", "message": "Job Apply Agent API"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
