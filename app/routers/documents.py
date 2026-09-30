from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)

from sqlalchemy import select
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.cv_parser import cv_parser
from app.database import get_db
from app.models.candidate import Candidate
from app.schemas.candidate_profile import CandidateProfile
from app.services.document_service import document_service


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


class CandidateDocumentResponse(BaseModel):
    id: int
    master_cv_filename: str | None = None
    profile: CandidateProfile | None = None


@router.get("/candidates", response_model=CandidateDocumentResponse | None)
def get_latest_candidate(
    db: Session = Depends(get_db),
):
    candidate = db.scalar(
        select(Candidate).order_by(Candidate.id.desc()).limit(1)
    )
    if not candidate:
        return None
    profile = CandidateProfile.model_validate(candidate.profile_data) if candidate.profile_data else None
    return CandidateDocumentResponse(
        id=candidate.id,
        master_cv_filename=candidate.master_cv_filename,
        profile=profile,
    )


@router.post(
    "/cv",
    response_model=CandidateDocumentResponse,
)
async def upload_cv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # ---------------------------------------------------------
    # 1. FILE VALIDATION
    # ---------------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is missing.",
        )

    filename = file.filename.lower()

    if not (
        filename.endswith(".pdf")
        or filename.endswith(".docx")
    ):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported.",
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    # ---------------------------------------------------------
    # 2. TEXT EXTRACTION
    # ---------------------------------------------------------

    try:
        cv_text = document_service.extract_text(
            filename=file.filename,
            file_bytes=file_bytes,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read CV: {str(exc)}",
        )

    if len(cv_text.strip()) < 100:
        raise HTTPException(
            status_code=400,
            detail=(
                "Not enough text could be "
                "extracted from the CV."
            ),
        )

    # ---------------------------------------------------------
    # 3. AI CV PARSING
    # ---------------------------------------------------------

    profile = cv_parser.parse(cv_text)

    # ---------------------------------------------------------
    # 4. NAME PROCESSING
    # ---------------------------------------------------------

    full_name_parts = (
        profile.full_name.split()
        if profile.full_name
        else []
    )

    first_name = (
        " ".join(full_name_parts[:-1])
        if len(full_name_parts) > 1
        else profile.full_name
    )

    last_name = (
        full_name_parts[-1]
        if len(full_name_parts) > 1
        else None
    )

    # ---------------------------------------------------------
    # 5. CHECK EXISTING CANDIDATE
    # ---------------------------------------------------------

    candidate = None

    if profile.email:

        candidate = db.scalar(
            select(Candidate).where(
                Candidate.email == profile.email
            )
        )

    # ---------------------------------------------------------
    # 6A. UPDATE EXISTING CANDIDATE
    # ---------------------------------------------------------

    if candidate:

        candidate.first_name = first_name
        candidate.last_name = last_name

        candidate.phone = profile.phone
        candidate.linkedin = profile.linkedin
        candidate.github = profile.github
        candidate.portfolio = profile.portfolio

        candidate.master_cv_filename = (
            file.filename
        )

        candidate.profile_data = (
            profile.model_dump()
        )

    # ---------------------------------------------------------
    # 6B. CREATE NEW CANDIDATE
    # ---------------------------------------------------------

    else:

        candidate = Candidate(
            first_name=first_name,
            last_name=last_name,
            email=profile.email,
            phone=profile.phone,
            linkedin=profile.linkedin,
            github=profile.github,
            portfolio=profile.portfolio,
            master_cv_filename=file.filename,
            profile_data=profile.model_dump(),
        )

        db.add(candidate)

    # ---------------------------------------------------------
    # 7. SAVE
    # ---------------------------------------------------------

    try:

        db.commit()
        db.refresh(candidate)

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Candidate could not be saved.",
        )

    return {
        "id": candidate.id,
        "master_cv_filename": candidate.master_cv_filename,
        "profile": profile,
    }
