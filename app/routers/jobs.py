from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job import Job
from app.schemas.job import JobCreate, JobResponse
from app.agents.job_analyzer import job_analyzer
from app.schemas.job_analysis import (
    JobAnalysis,
    JobAnalysisRequest
)
from app.schemas.job_analysis import (
    JobAnalysis,
    JobAnalysisRequest,
    JobAnalyzeAndSaveRequest
)

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)
@router.post(
    "/analyze",
    response_model=JobAnalysis
)
def analyze_job(
    request: JobAnalysisRequest
):
    return job_analyzer.analyze(
        request.job_description
    )

@router.post("/", response_model=JobResponse)
def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db)
):
    job = Job(
        company=job_data.company,
        position=job_data.position,
        location=job_data.location,
        job_url=job_data.job_url,
        description=job_data.description
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job

@router.post("/analyze-and-save")
def analyze_and_save_job(
    request: JobAnalyzeAndSaveRequest,
    db: Session = Depends(get_db)
):
    analysis = job_analyzer.analyze(
        request.job_description
    )

    job = Job(
        company=analysis.company or "Unknown",
        position=analysis.position or "Unknown",
        location=analysis.location,
        job_url=request.job_url,
        description=request.job_description,
        status="ANALYZED",
        analysis_data=analysis.model_dump()
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return {
        "job_id": job.id,
        "status": job.status,
        "analysis": analysis
    }

@router.get("/", response_model=list[JobResponse])
def get_jobs(
    db: Session = Depends(get_db)
):
    jobs = db.scalars(
        select(Job).order_by(Job.id.desc())
    ).all()

    return jobs


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    job = db.get(Job, job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    return job