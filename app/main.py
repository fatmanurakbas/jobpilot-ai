from fastapi import FastAPI

from app.routers.jobs import router as jobs_router
from app.routers.agents import router as agents_router
from app.routers.documents import router as documents_router
from app.routers.applications import router as applications_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="JobPilot AI API",
    description="AI-powered job application assistant",
    version="0.3.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router)
app.include_router(agents_router)
app.include_router(documents_router)
app.include_router(applications_router)


@app.get("/")
def root():
    return {
        "message": "JobPilot AI is running."
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }