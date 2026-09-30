from pathlib import Path
import base64
from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.match_agent import match_agent
from app.database import get_db

from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import Job

from app.schemas.candidate_profile import CandidateProfile
from app.schemas.job_analysis import JobAnalysis
from app.schemas.job_match import JobMatchResult

from app.services.match_score_service import (
    match_score_service
)
from app.agents.cv_tailoring_agent import cv_tailoring_agent
from app.schemas.cv_tailoring import CVTailoringPlan
from fastapi.responses import FileResponse

from app.schemas.cv_tailoring import CVTailoringPlan
from app.services.document_generator import document_generator
from app.agents.cv_validator import cv_validator
from app.schemas.cv_validation import CVValidationResult

from app.agents.cv_correction_agent import cv_correction_agent
from app.schemas.cv_correction import CVCorrectionResult

from app.schemas.cv_finalization import CVFinalizationResult

from app.services.pdf_converter import pdf_converter
from fastapi.responses import FileResponse

from app.agents.cover_letter_agent import cover_letter_agent
from app.schemas.cover_letter import CoverLetter

from app.agents.cover_letter_validator import (
    cover_letter_validator,
)

from app.schemas.cover_letter_validation import (
    CoverLetterValidationResult,
)

from app.agents.cover_letter_correction_agent import (
    cover_letter_correction_agent,
)

from app.schemas.cover_letter_correction import (
    CoverLetterCorrectionResult,
)

from app.schemas.cover_letter_finalization import (
    CoverLetterFinalizationResult,
)

from app.services.cover_letter_document_generator import (
    cover_letter_document_generator,
)

from app.services.pdf_converter import (
    pdf_converter,
)

from pathlib import Path
from fastapi.responses import FileResponse

from app.schemas.application_package import ApplicationPackage
from app.schemas.application_summary import ApplicationSummary

from app.schemas.application_approval import (
    ApplicationApprovalResult,
    ApplicationApprovalStatus,
)

router = APIRouter(
    prefix="/applications",
    tags=["Applications"]
)


@router.get("/", response_model=list[ApplicationSummary])
def list_applications(db: Session = Depends(get_db)):
    applications = db.scalars(
        select(Application).order_by(Application.id.desc())
    ).all()
    summaries = []
    for application in applications:
        job = db.get(Job, application.job_id)
        summaries.append(ApplicationSummary(
            id=application.id,
            candidate_id=application.candidate_id,
            job_id=application.job_id,
            company=job.company if job else None,
            position=job.position if job else None,
            match_percentage=application.match_percentage,
            status=application.status,
            created_at=application.created_at,
            submitted_at=application.submitted_at,
        ))
    return summaries

from datetime import datetime, timezone
from pathlib import Path

from app.schemas.application_approval import (
    ApplicationApprovalResult,
)

from app.services.file_hash_service import (
    file_hash_service,
)

from app.schemas.application_form import (
    ApplicationFormInspection,
    ApplicationFormInspectionRequest,
)

from app.services.application_form_inspector import (
    application_form_inspector,
)

from app.schemas.form_mapping import (
    FormMappingResult,
)

from app.agents.form_mapping_agent import (
    form_mapping_agent,
)

from app.schemas.form_answer import (
    SaveFormAnswersRequest,
    SaveFormAnswersResult,
)

from app.schemas.resolved_form import (
    ResolvedFormPlan,
)

from app.services.form_value_resolver import (
    form_value_resolver,
)

from app.schemas.form_fill import (
    FormFillRequest,
    FormFillResult,
)

from app.services.application_form_filler import (
    application_form_filler,
)

from app.schemas.resolved_form import ResolvedFormPlan

from app.services.form_value_resolver import (
    form_value_resolver,
)

from datetime import datetime, timezone

from app.schemas.submission_approval import (
    SubmissionApprovalRequest,
    SubmissionApprovalResult,
    SubmissionApprovalStatus,
)

from app.services.submission_hash_service import (
    submission_hash_service,
)

from datetime import datetime, timezone

from app.schemas.form_submission import (
    FormSubmissionResult,
)
from app.schemas.browser_review import BrowserReviewResultRequest

from app.services.application_form_submitter import (
    application_form_submitter,
)

from app.services.submission_hash_service import (
    submission_hash_service,
)

from app.schemas.resolved_form import ResolvedFormPlan

@router.post(
    "/match/{candidate_id}/{job_id}",
    response_model=JobMatchResult
)
def match_application(
    candidate_id: int,
    job_id: int,
    db: Session = Depends(get_db)
):

    candidate = db.get(
        Candidate,
        candidate_id
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found."
        )

    job = db.get(
        Job,
        job_id
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found."
        )

    if not candidate.profile_data:
        raise HTTPException(
            status_code=400,
            detail="Candidate profile has not been parsed."
        )

    if not job.analysis_data:
        raise HTTPException(
            status_code=400,
            detail="Job has not been analyzed."
        )

    candidate_profile = CandidateProfile.model_validate(
        candidate.profile_data
    )

    job_analysis = JobAnalysis.model_validate(
        job.analysis_data
    )

    match_analysis = match_agent.analyze(
        candidate=candidate_profile,
        job=job_analysis
    )

    score = match_score_service.calculate(
        job=job_analysis,
        match=match_analysis
    )
    result = JobMatchResult(
    **match_analysis.model_dump(),
    match_percentage=score
    )

    application = Application(
        candidate_id=candidate.id,
        job_id=job.id,
        match_percentage=score,
        match_data=result.model_dump(),
        status="MATCHED"
    )
    

    db.add(application)
    db.commit()
    db.refresh(application)

    return JobMatchResult(
        **match_analysis.model_dump(),
        match_percentage=score,
        application_id=application.id,
    )

    return result     

@router.post(
    "/{application_id}/tailor-cv",
    response_model=CVTailoringPlan
)
def tailor_application_cv(
    application_id: int,
    db: Session = Depends(get_db)
):

    application = db.get(
        Application,
        application_id
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found."
        )

    candidate = db.get(
        Candidate,
        application.candidate_id
    )

    job = db.get(
        Job,
        application.job_id
    )

    if not candidate or not candidate.profile_data:
        raise HTTPException(
            status_code=400,
            detail="Candidate profile is unavailable."
        )

    if not job or not job.analysis_data:
        raise HTTPException(
            status_code=400,
            detail="Job analysis is unavailable."
        )

    if not application.match_data:
        raise HTTPException(
            status_code=400,
            detail="Application has not been matched yet."
        )

    candidate_profile = CandidateProfile.model_validate(
        candidate.profile_data
    )

    job_analysis = JobAnalysis.model_validate(
        job.analysis_data
    )

    match_result = JobMatchResult.model_validate(
        application.match_data
    )
    tailoring_plan = cv_tailoring_agent.tailor(
    candidate=candidate_profile,
    job=job_analysis,
    match=match_result
    )

    application.tailoring_data = (
    tailoring_plan.model_dump()
    )

    application.status = "CV_PLAN_READY"

    db.commit()

    return tailoring_plan
@router.post(
    "/{application_id}/generate-cv"
)
def generate_application_cv(
    application_id: int,
    db: Session = Depends(get_db),
):

    # 1. Application var mı?
    application = db.get(
        Application,
        application_id
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found."
        )

    # 2. Candidate var mı?
    candidate = db.get(
        Candidate,
        application.candidate_id
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found."
        )

    # 3. Candidate profile oluşturulmuş mu?
    if not candidate.profile_data:
        raise HTTPException(
            status_code=400,
            detail="Candidate profile is unavailable."
        )

    # 4. Tailoring plan oluşturulmuş mu?
    if not application.tailoring_data:
        raise HTTPException(
            status_code=400,
            detail="CV tailoring plan has not been generated."
        )

    # 5. CV Validator çalıştırılmış mı?
    if not application.validation_data:
        raise HTTPException(
            status_code=400,
            detail="CV must be validated before document generation."
        )

    # 6. Validation sonucunu Pydantic modeline çevir
    validation_result = (
        CVValidationResult.model_validate(
            application.validation_data
        )
    )

    # 7. Validation başarısızsa CV oluşturmayı engelle
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=400,
            detail=(
                "CV generation blocked because "
                "validation failed. "
                "Review validation issues first."
            )
        )

    # 8. Candidate profile'ı hazırla
    candidate_profile = (
        CandidateProfile.model_validate(
            candidate.profile_data
        )
    )

    # 9. Tailoring planını hazırla
    tailoring_plan = (
        CVTailoringPlan.model_validate(
            application.tailoring_data
        )
    )

    # 10. DOCX oluştur
    cv_path = (
        document_generator.generate_tailored_cv(
            candidate=candidate_profile,
            tailoring_plan=tailoring_plan,
            application_id=application.id
        )
    )

    # 11. Application'ı güncelle
    application.cv_path = cv_path

    application.status = "CV_READY"

    db.commit()

    # 12. DOCX dosyasını kullanıcıya gönder
    return FileResponse(
        path=cv_path,
        filename=f"JobPilot_CV_{application.id}.docx",
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        )
    )

@router.post(
    "/{application_id}/validate-cv",
    response_model=CVValidationResult,
)
def validate_application_cv(
    application_id: int,
    db: Session = Depends(get_db),
):

    application = db.get(
        Application,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    candidate = db.get(
        Candidate,
        application.candidate_id,
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found.",
        )

    if not candidate.profile_data:
        raise HTTPException(
            status_code=400,
            detail="Candidate profile is unavailable.",
        )

    if not application.tailoring_data:
        raise HTTPException(
            status_code=400,
            detail="CV tailoring plan has not been generated.",
        )

    candidate_profile = CandidateProfile.model_validate(
        candidate.profile_data
    )

    tailoring_plan = CVTailoringPlan.model_validate(
        application.tailoring_data
    )

    validation_result = cv_validator.validate(
        candidate=candidate_profile,
        tailoring_plan=tailoring_plan,
    )

    application.validation_data = (
        validation_result.model_dump()
    )

    if validation_result.is_valid:
        application.status = "CV_VALIDATED"
    else:
        application.status = "CV_VALIDATION_FAILED"

    db.commit()

    return validation_result

@router.post(
    "/{application_id}/correct-cv",
    response_model=CVCorrectionResult,
)
def correct_application_cv(
    application_id: int,
    db: Session = Depends(get_db),
):

    application = db.get(
        Application,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    candidate = db.get(
        Candidate,
        application.candidate_id,
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found.",
        )

    if not candidate.profile_data:
        raise HTTPException(
            status_code=400,
            detail="Candidate profile is unavailable.",
        )

    if not application.tailoring_data:
        raise HTTPException(
            status_code=400,
            detail="CV tailoring plan is unavailable.",
        )

    if not application.validation_data:
        raise HTTPException(
            status_code=400,
            detail="CV must be validated before correction.",
        )

    candidate_profile = CandidateProfile.model_validate(
        candidate.profile_data
    )

    tailoring_plan = CVTailoringPlan.model_validate(
        application.tailoring_data
    )

    validation_result = CVValidationResult.model_validate(
        application.validation_data
    )

    correction_result = cv_correction_agent.correct(
        candidate=candidate_profile,
        tailoring_plan=tailoring_plan,
        validation=validation_result,
    )

    application.correction_data = (
        correction_result.model_dump()
    )

    # The corrected plan becomes the current tailoring plan.
    application.tailoring_data = (
        correction_result.corrected_plan.model_dump()
    )

    # Previous validation is no longer valid because
    # the CV content has changed.
    application.validation_data = None
    application.cv_path = None
    application.pdf_path = None
    application.status = "CV_CORRECTED"
    

    db.commit()

    return correction_result

@router.post(
    "/{application_id}/finalize-cv",
    response_model=CVFinalizationResult,
)
def finalize_application_cv(
    application_id: int,
    db: Session = Depends(get_db),
):

    MAX_CORRECTION_ATTEMPTS = 3

    # ---------------------------------------------------------
    # 1. APPLICATION
    # ---------------------------------------------------------

    application = db.get(
        Application,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    # ---------------------------------------------------------
    # 2. CANDIDATE
    # ---------------------------------------------------------

    candidate = db.get(
        Candidate,
        application.candidate_id,
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found.",
        )

    if not candidate.profile_data:
        raise HTTPException(
            status_code=400,
            detail="Candidate profile is unavailable.",
        )

    # ---------------------------------------------------------
    # 3. TAILORING PLAN
    # ---------------------------------------------------------

    if not application.tailoring_data:
        raise HTTPException(
            status_code=400,
            detail="CV tailoring plan has not been generated.",
        )

    candidate_profile = CandidateProfile.model_validate(
        candidate.profile_data
    )

    tailoring_plan = CVTailoringPlan.model_validate(
        application.tailoring_data
    )

    corrections_made = []

    correction_attempts = 0

    # ---------------------------------------------------------
    # 4. VALIDATION / CORRECTION LOOP
    # ---------------------------------------------------------

    while True:

        validation_result = cv_validator.validate(
            candidate=candidate_profile,
            tailoring_plan=tailoring_plan,
        )

        application.validation_data = (
            validation_result.model_dump()
        )

        # ---------------------------------------------
        # PASS
        # ---------------------------------------------

        if validation_result.is_valid:
            break

        # ---------------------------------------------
        # MAX ATTEMPTS REACHED
        # ---------------------------------------------

        if (
            correction_attempts
            >= MAX_CORRECTION_ATTEMPTS
        ):

            application.status = (
                "CV_VALIDATION_FAILED"
            )

            application.cv_path = None

            db.commit()

            return CVFinalizationResult(
                success=False,
                application_id=application.id,
                attempts=correction_attempts,
                corrections_made=corrections_made,
                validation=validation_result,
                cv_path=None,
                pdf_path=None,
                message=(
                    "CV could not be validated "
                    "after the maximum number "
                    "of correction attempts."
                ),
            )

        # ---------------------------------------------
        # CORRECTION
        # ---------------------------------------------

        correction_result = (
            cv_correction_agent.correct(
                candidate=candidate_profile,
                tailoring_plan=tailoring_plan,
                validation=validation_result,
            )
        )

        correction_attempts += 1

        corrections_made.extend(
            correction_result.corrections_made
        )

        tailoring_plan = (
            correction_result.corrected_plan
        )

        # Save newest plan
        application.tailoring_data = (
            tailoring_plan.model_dump()
        )

        application.correction_data = (
            correction_result.model_dump()
        )

        application.cv_path = None

    # ---------------------------------------------------------
    # 5. FINAL VALIDATION PASSED
    # ---------------------------------------------------------

    application.validation_data = (
        validation_result.model_dump()
    )

    application.status = "CV_VALIDATED"

    # ---------------------------------------------------------
    # 6. GENERATE DOCX
    # ---------------------------------------------------------

    cv_path = (
        document_generator.generate_tailored_cv(
            candidate=candidate_profile,
            tailoring_plan=tailoring_plan,
            application_id=application.id,
        )
    )

    application.cv_path = cv_path
    try:
        pdf_path = pdf_converter.convert_docx_to_pdf(
           cv_path
        )

    except Exception as exc:

        application.pdf_path = None
        application.status = "CV_PDF_FAILED"

        db.commit()

        raise HTTPException(
            status_code=500,
            detail=(
                "DOCX was generated successfully, "
                "but PDF conversion failed: "
                f"{exc}"
        ),
    )

    application.pdf_path = pdf_path
    
    application.status = "CV_READY"

    db.commit()

    # ---------------------------------------------------------
    # 7. RESPONSE
    # ---------------------------------------------------------

    return CVFinalizationResult(
        success=True,
        application_id=application.id,
        attempts=correction_attempts,
        corrections_made=corrections_made,
        validation=validation_result,
        cv_path=cv_path,
         pdf_path=pdf_path,
        message=(
            "CV validated successfully "
            "DOCX/PDF generated."
        ),
    )
from pathlib import Path
from fastapi.responses import FileResponse


@router.get("/{application_id}/cv/pdf")
def download_cv_pdf(
    application_id: int,
    db: Session = Depends(get_db),
):

    application = db.get(
        Application,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    if not application.pdf_path:
        raise HTTPException(
            status_code=404,
            detail=(
                "PDF CV has not been generated yet. "
                "Run finalize-cv first."
            ),
        )

    pdf_path = Path(
        application.pdf_path
    )

    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Generated PDF file was not found.",
        )

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"application_{application_id}_cv.pdf",
    )
@router.get("/{application_id}/cv/docx")
def download_cv_docx(
    application_id: int,
    db: Session = Depends(get_db),
):

    application = db.get(
        Application,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    if not application.cv_path:
        raise HTTPException(
            status_code=404,
            detail=(
                "DOCX CV has not been generated yet. "
                "Run finalize-cv first."
            ),
        )

    docx_path = Path(
        application.cv_path
    )

    if not docx_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Generated DOCX file was not found.",
        )

    return FileResponse(
        path=docx_path,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
        filename=f"application_{application_id}_cv.docx",
    )

@router.post(
    "/{application_id}/generate-cover-letter",
    response_model=CoverLetter,
)
def generate_cover_letter(
    application_id: int,
    db: Session = Depends(get_db),
):

    # ---------------------------------------------------------
    # APPLICATION
    # ---------------------------------------------------------

    application = db.get(
        Application,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    # ---------------------------------------------------------
    # CANDIDATE
    # ---------------------------------------------------------

    candidate = db.get(
        Candidate,
        application.candidate_id,
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found.",
        )

    if not candidate.profile_data:
        raise HTTPException(
            status_code=400,
            detail="Candidate profile is unavailable.",
        )

    # ---------------------------------------------------------
    # JOB
    # ---------------------------------------------------------

    job = db.get(
        Job,
        application.job_id,
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    # ---------------------------------------------------------
    # FINAL CV PLAN REQUIRED
    # ---------------------------------------------------------

    if not application.tailoring_data:
        raise HTTPException(
            status_code=400,
            detail="CV tailoring plan is unavailable.",
        )

    if not application.validation_data:
        raise HTTPException(
            status_code=400,
            detail="CV must be validated first.",
        )

    validation = CVValidationResult.model_validate(
        application.validation_data
    )

    if not validation.is_valid:
        raise HTTPException(
            status_code=400,
            detail=(
                "Cover letter generation requires "
                "a valid final CV tailoring plan."
            ),
        )

    # ---------------------------------------------------------
    # PYDANTIC MODELS
    # ---------------------------------------------------------

    candidate_profile = CandidateProfile.model_validate(
        candidate.profile_data
    )

    tailoring_plan = CVTailoringPlan.model_validate(
        application.tailoring_data
    )

    # ---------------------------------------------------------
    # JOB DATA
    # ---------------------------------------------------------

    job_data = {
        "title": getattr(job, "title", None),
        "company": getattr(job, "company", None),
        "location": getattr(job, "location", None),
        "description": getattr(job, "description", None),
        "requirements": getattr(job, "requirements", None),
    }

    # ---------------------------------------------------------
    # GENERATE
    # ---------------------------------------------------------

    result = cover_letter_agent.generate(
        candidate=candidate_profile,
        tailoring_plan=tailoring_plan,
        job_data=job_data,
    )

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------

    application.cover_letter_data = (
        result.model_dump()
    )

    application.cover_letter_validation_data = None
    application.cover_letter_path = None

    application.status = (
        "COVER_LETTER_DRAFTED"
    )

    db.commit()

    return result

@router.post(
    "/{application_id}/validate-cover-letter",
    response_model=CoverLetterValidationResult,
)
def validate_cover_letter(
    application_id: int,
    db: Session = Depends(get_db),
):

    # ---------------------------------------------------------
    # APPLICATION
    # ---------------------------------------------------------

    application = db.get(
        Application,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    # ---------------------------------------------------------
    # COVER LETTER
    # ---------------------------------------------------------

    if not application.cover_letter_data:
        raise HTTPException(
            status_code=400,
            detail=(
                "Cover letter has not been generated."
            ),
        )

    # ---------------------------------------------------------
    # CANDIDATE
    # ---------------------------------------------------------

    candidate = db.get(
        Candidate,
        application.candidate_id,
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found.",
        )

    if not candidate.profile_data:
        raise HTTPException(
            status_code=400,
            detail="Candidate profile is unavailable.",
        )

    # ---------------------------------------------------------
    # JOB
    # ---------------------------------------------------------

    job = db.get(
        Job,
        application.job_id,
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    # ---------------------------------------------------------
    # PYDANTIC MODELS
    # ---------------------------------------------------------

    candidate_profile = CandidateProfile.model_validate(
        candidate.profile_data
    )

    cover_letter = CoverLetter.model_validate(
        application.cover_letter_data
    )

    # ---------------------------------------------------------
    # JOB DATA
    # ---------------------------------------------------------

    job_data = {
        "title": getattr(
            job,
            "title",
            None,
        ),
        "company": getattr(
            job,
            "company",
            None,
        ),
        "location": getattr(
            job,
            "location",
            None,
        ),
        "description": getattr(
            job,
            "description",
            None,
        ),
        "requirements": getattr(
            job,
            "requirements",
            None,
        ),
    }

    # ---------------------------------------------------------
    # VALIDATE
    # ---------------------------------------------------------

    validation_result = (
        cover_letter_validator.validate(
            candidate=candidate_profile,
            cover_letter=cover_letter,
            job_data=job_data,
        )
    )

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------

    application.cover_letter_validation_data = (
        validation_result.model_dump()
    )

    if validation_result.is_valid:
        application.status = (
            "COVER_LETTER_VALIDATED"
        )

    else:
        application.status = (
            "COVER_LETTER_VALIDATION_FAILED"
        )

    db.commit()

    return validation_result

@router.post(
    "/{application_id}/correct-cover-letter",
    response_model=CoverLetterCorrectionResult,
)
def correct_cover_letter(
    application_id: int,
    db: Session = Depends(get_db),
):

    application = db.get(
        Application,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    if not application.cover_letter_data:
        raise HTTPException(
            status_code=400,
            detail="Cover letter has not been generated.",
        )

    if not application.cover_letter_validation_data:
        raise HTTPException(
            status_code=400,
            detail="Cover letter must be validated first.",
        )

    candidate = db.get(
        Candidate,
        application.candidate_id,
    )

    if not candidate or not candidate.profile_data:
        raise HTTPException(
            status_code=400,
            detail="Candidate profile is unavailable.",
        )

    job = db.get(
        Job,
        application.job_id,
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    candidate_profile = CandidateProfile.model_validate(
        candidate.profile_data
    )

    cover_letter = CoverLetter.model_validate(
        application.cover_letter_data
    )

    validation = CoverLetterValidationResult.model_validate(
        application.cover_letter_validation_data
    )

    job_data = {
        "title": getattr(job, "title", None),
        "company": getattr(job, "company", None),
        "location": getattr(job, "location", None),
        "description": getattr(job, "description", None),
        "requirements": getattr(job, "requirements", None),
    }

    correction_result = (
        cover_letter_correction_agent.correct(
            candidate=candidate_profile,
            cover_letter=cover_letter,
            validation=validation,
            job_data=job_data,
        )
    )

    # Save audit information.
    application.cover_letter_correction_data = (
        correction_result.model_dump()
    )

    # Replace draft with corrected version.
    application.cover_letter_data = (
        correction_result.corrected_cover_letter.model_dump()
    )

    # IMPORTANT:
    # Previous validation belongs to the old version.
    application.cover_letter_validation_data = None

    # Any previously generated document is now stale.
    application.cover_letter_path = None

    application.status = "COVER_LETTER_CORRECTED"

    db.commit()

    return correction_result

@router.post(
    "/{application_id}/finalize-cover-letter",
    response_model=CoverLetterFinalizationResult,
)
def finalize_cover_letter(
    application_id: int,
    db: Session = Depends(get_db),
):

    application = db.get(
        Application,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    if not application.cover_letter_data:
        raise HTTPException(
            status_code=400,
            detail="Cover letter has not been generated.",
        )

    candidate = db.get(
        Candidate,
        application.candidate_id,
    )

    if not candidate or not candidate.profile_data:
        raise HTTPException(
            status_code=400,
            detail="Candidate profile is unavailable.",
        )

    job = db.get(
        Job,
        application.job_id,
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    candidate_profile = CandidateProfile.model_validate(
        candidate.profile_data
    )

    cover_letter = CoverLetter.model_validate(
        application.cover_letter_data
    )

    job_data = {
        "title": getattr(job, "title", None),
        "company": getattr(job, "company", None),
        "location": getattr(job, "location", None),
        "description": getattr(job, "description", None),
        "requirements": getattr(job, "requirements", None),
    }

    correction_attempts = 0
    warning_cleanup_attempts = 0

    max_correction_attempts = 3
    max_warning_cleanup_attempts = 1

    corrections_made: list[str] = []

    # -----------------------------------------------------
    # VALIDATE -> CORRECT -> REVALIDATE
    # -----------------------------------------------------

    while True:

        validation = cover_letter_validator.validate(
            candidate=candidate_profile,
            cover_letter=cover_letter,
            job_data=job_data,
        )

        application.cover_letter_validation_data = (
            validation.model_dump()
        )

        errors = [
            issue
            for issue in validation.issues
            if issue.severity.lower() == "error"
        ]

        warnings = [
            issue
            for issue in validation.issues
            if issue.severity.lower() == "warning"
        ]

        # ---------------------------------------------
        # CLEAN
        # ---------------------------------------------

        if validation.is_valid and not warnings:
            break

        # ---------------------------------------------
        # ERRORS
        # ---------------------------------------------

        if errors:

            if (
                correction_attempts
                >= max_correction_attempts
            ):
                application.status = (
                    "COVER_LETTER_VALIDATION_FAILED"
                )

                application.cover_letter_path = None
                application.cover_letter_pdf_path = None

                db.commit()

                return CoverLetterFinalizationResult(
                    success=False,
                    application_id=application.id,
                    correction_attempts=correction_attempts,
                    warning_cleanup_attempts=(
                        warning_cleanup_attempts
                    ),
                    corrections_made=corrections_made,
                    final_validation=validation,
                    cover_letter_path=None,
                    cover_letter_pdf_path=None,
                    message=(
                        "Cover letter could not pass "
                        "factual validation."
                    ),
                )

            correction = (
                cover_letter_correction_agent.correct(
                    candidate=candidate_profile,
                    cover_letter=cover_letter,
                    validation=validation,
                    job_data=job_data,
                )
            )

            correction_attempts += 1

        # ---------------------------------------------
        # WARNINGS ONLY
        # ---------------------------------------------

        else:

            if (
                warning_cleanup_attempts
                >= max_warning_cleanup_attempts
            ):
                # Warnings do not block finalization.
                break

            correction = (
                cover_letter_correction_agent.correct(
                    candidate=candidate_profile,
                    cover_letter=cover_letter,
                    validation=validation,
                    job_data=job_data,
                )
            )

            warning_cleanup_attempts += 1

        # ---------------------------------------------
        # APPLY CORRECTION
        # ---------------------------------------------

        corrections_made.extend(
            correction.corrections_made
        )

        cover_letter = (
            correction.corrected_cover_letter
        )

        application.cover_letter_data = (
            cover_letter.model_dump()
        )

        application.cover_letter_correction_data = (
            correction.model_dump()
        )

        # Previous validation/document is stale.
        application.cover_letter_validation_data = None
        application.cover_letter_path = None
        application.cover_letter_pdf_path = None

    # -----------------------------------------------------
    # FINAL VALIDATION STATE
    # -----------------------------------------------------

    application.cover_letter_data = (
        cover_letter.model_dump()
    )

    application.cover_letter_validation_data = (
        validation.model_dump()
    )

    # -----------------------------------------------------
    # GENERATE DOCX
    # -----------------------------------------------------

    try:

        docx_path = (
            cover_letter_document_generator.generate(
                cover_letter=cover_letter,
                application_id=application.id,
            )
        )

    except Exception as exc:

        application.status = (
            "COVER_LETTER_DOCUMENT_FAILED"
        )

        application.cover_letter_path = None
        application.cover_letter_pdf_path = None

        db.commit()

        raise HTTPException(
            status_code=500,
            detail=(
                "Cover letter passed validation, "
                f"but DOCX generation failed: {exc}"
            ),
        )

    application.cover_letter_path = docx_path

    # -----------------------------------------------------
    # GENERATE PDF
    # -----------------------------------------------------

    try:

        pdf_path = pdf_converter.convert_docx_to_pdf(
            docx_path
        )

    except Exception as exc:

        application.status = (
            "COVER_LETTER_PDF_FAILED"
        )

        application.cover_letter_pdf_path = None

        db.commit()

        raise HTTPException(
            status_code=500,
            detail=(
                "Cover letter DOCX was generated, "
                f"but PDF conversion failed: {exc}"
            ),
        )

    # -----------------------------------------------------
    # READY
    # -----------------------------------------------------

    application.cover_letter_pdf_path = pdf_path

    application.status = "COVER_LETTER_READY"

    db.commit()

    return CoverLetterFinalizationResult(
        success=True,
        application_id=application.id,
        correction_attempts=correction_attempts,
        warning_cleanup_attempts=(
            warning_cleanup_attempts
        ),
        corrections_made=corrections_made,
        final_validation=validation,
        cover_letter_path=docx_path,
        cover_letter_pdf_path=pdf_path,
        message=(
            "Cover letter validated and generated "
            "successfully."
        ),
    )

# ============================================================
# DOWNLOAD FINAL CV - DOCX
# ============================================================

@router.get("/{application_id}/cv/docx")
def download_cv_docx(
    application_id: int,
    db: Session = Depends(get_db),
):
    application = db.get(Application, application_id)

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    if not application.cv_path:
        raise HTTPException(
            status_code=404,
            detail="Final CV DOCX has not been generated.",
        )

    file_path = Path(application.cv_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="CV DOCX file does not exist.",
        )

    return FileResponse(
        path=str(file_path),
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
        filename=f"application_{application_id}_cv.docx",
    )


# ============================================================
# DOWNLOAD FINAL CV - PDF
# ============================================================

@router.get("/{application_id}/cv/pdf")
def download_cv_pdf(
    application_id: int,
    db: Session = Depends(get_db),
):
    application = db.get(Application, application_id)

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    if not application.pdf_path:
        raise HTTPException(
            status_code=404,
            detail="Final CV PDF has not been generated.",
        )

    file_path = Path(application.pdf_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="CV PDF file does not exist.",
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=f"application_{application_id}_cv.pdf",
    )


# ============================================================
# DOWNLOAD COVER LETTER - DOCX
# ============================================================

@router.get("/{application_id}/cover-letter/docx")
def download_cover_letter_docx(
    application_id: int,
    db: Session = Depends(get_db),
):
    application = db.get(Application, application_id)

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    if not application.cover_letter_path:
        raise HTTPException(
            status_code=404,
            detail="Cover letter DOCX has not been generated.",
        )

    file_path = Path(application.cover_letter_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Cover letter DOCX file does not exist.",
        )

    return FileResponse(
        path=str(file_path),
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
        filename=f"application_{application_id}_cover_letter.docx",
    )


# ============================================================
# DOWNLOAD COVER LETTER - PDF
# ============================================================

@router.get("/{application_id}/cover-letter/pdf")
def download_cover_letter_pdf(
    application_id: int,
    db: Session = Depends(get_db),
):
    application = db.get(Application, application_id)

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    if not application.cover_letter_pdf_path:
        raise HTTPException(
            status_code=404,
            detail="Cover letter PDF has not been generated.",
        )

    file_path = Path(application.cover_letter_pdf_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Cover letter PDF file does not exist.",
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=f"application_{application_id}_cover_letter.pdf",
    )

@router.get(
    "/{application_id}/package",
    response_model=ApplicationPackage,
)
def get_application_package(
    application_id: int,
    db: Session = Depends(get_db),
):
    application = db.get(
        Application,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    # --------------------------------------------------------
    # CV VALIDATION
    # --------------------------------------------------------

    cv_validation = None

    if application.validation_data:
        cv_validation = CVValidationResult.model_validate(
            application.validation_data
        )

    # --------------------------------------------------------
    # COVER LETTER VALIDATION
    # --------------------------------------------------------

    cover_letter_validation = None

    if application.cover_letter_validation_data:
        cover_letter_validation = (
            CoverLetterValidationResult.model_validate(
                application.cover_letter_validation_data
            )
        )

    # --------------------------------------------------------
    # FILE STATES
    # --------------------------------------------------------

    cv_docx_ready = (
        bool(application.cv_path)
        and Path(application.cv_path).exists()
    )

    cv_pdf_ready = (
        bool(application.pdf_path)
        and Path(application.pdf_path).exists()
    )

    cover_letter_docx_ready = (
        bool(application.cover_letter_path)
        and Path(application.cover_letter_path).exists()
    )

    cover_letter_pdf_ready = (
        bool(application.cover_letter_pdf_path)
        and Path(application.cover_letter_pdf_path).exists()
    )

    # --------------------------------------------------------
    # VALIDATION STATES
    # --------------------------------------------------------

    cv_validated = bool(
        cv_validation
        and cv_validation.is_valid
    )

    cover_letter_validated = bool(
        cover_letter_validation
        and cover_letter_validation.is_valid
    )

    # --------------------------------------------------------
    # REVIEW READINESS
    # --------------------------------------------------------

    ready_for_review = all(
        [
            cv_validated,
            cover_letter_validated,
            cv_docx_ready,
            cv_pdf_ready,
            cover_letter_docx_ready,
            cover_letter_pdf_ready,
        ]
    )

    return ApplicationPackage(
        application_id=application.id,
        status=application.status,
        form_prepared_at=application.form_prepared_at,
        form_verification=application.form_verification_data,
        submitted_at=application.submitted_at,
        submission_url=application.submission_url,
        submission_confirmation=application.submission_confirmation,
        submission_screenshot_available=bool(
            application.submission_screenshot_path
            and Path(application.submission_screenshot_path).exists()
        ),

        candidate_id=application.candidate_id,
        job_id=application.job_id,

        match_percentage=application.match_percentage,

        cv_plan_ready=bool(application.tailoring_data),
        cv_validation_ready=bool(application.validation_data),
        cover_letter_ready=bool(application.cover_letter_data),
        cover_letter_validation_ready=bool(application.cover_letter_validation_data),

        cv_validated=cv_validated,
        cover_letter_validated=cover_letter_validated,

        cv_docx_ready=cv_docx_ready,
        cv_pdf_ready=cv_pdf_ready,

        cover_letter_docx_ready=(
            cover_letter_docx_ready
        ),

        cover_letter_pdf_ready=(
            cover_letter_pdf_ready
        ),

        cv_path=application.cv_path,
        cv_pdf_path=application.pdf_path,

        cover_letter_path=(
            application.cover_letter_path
        ),

        cover_letter_pdf_path=(
            application.cover_letter_pdf_path
        ),

        cv_validation=cv_validation,

        cover_letter_validation=(
            cover_letter_validation
        ),

        ready_for_review=ready_for_review,
    )

@router.post(
    "/{application_id}/approve-package",
    response_model=ApplicationApprovalResult,
)
def approve_application_package(
    application_id: int,
    db: Session = Depends(get_db),
):
    application = db.get(
        Application,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    # -----------------------------------------------------
    # VALIDATIONS
    # -----------------------------------------------------

    if not application.validation_data:
        raise HTTPException(
            status_code=400,
            detail="CV validation is unavailable.",
        )

    if not application.cover_letter_validation_data:
        raise HTTPException(
            status_code=400,
            detail="Cover letter validation is unavailable.",
        )

    cv_validation = CVValidationResult.model_validate(
        application.validation_data
    )

    cover_validation = (
        CoverLetterValidationResult.model_validate(
            application.cover_letter_validation_data
        )
    )

    if not cv_validation.is_valid:
        raise HTTPException(
            status_code=400,
            detail="CV has not passed validation.",
        )

    if not cover_validation.is_valid:
        raise HTTPException(
            status_code=400,
            detail="Cover letter has not passed validation.",
        )

    # -----------------------------------------------------
    # FINAL FILES
    # -----------------------------------------------------

    required_paths = [
        application.cv_path,
        application.pdf_path,
        application.cover_letter_path,
        application.cover_letter_pdf_path,
    ]

    if not all(required_paths):
        raise HTTPException(
            status_code=400,
            detail="Application package is incomplete.",
        )

    for file_path in required_paths:
        if not Path(file_path).exists():
            raise HTTPException(
                status_code=400,
                detail=f"Package file is missing: {file_path}",
            )

    # -----------------------------------------------------
    # HASH APPROVED FILES
    # -----------------------------------------------------

    # PDF is what we will eventually submit.
    cv_hash = file_hash_service.sha256(
        application.pdf_path
    )

    cover_letter_hash = file_hash_service.sha256(
        application.cover_letter_pdf_path
    )

    # -----------------------------------------------------
    # APPROVE
    # -----------------------------------------------------

    approved_at = datetime.now(timezone.utc)

    application.package_approved = True
    application.package_approved_at = approved_at

    application.approved_cv_hash = cv_hash

    application.approved_cover_letter_hash = (
        cover_letter_hash
    )

    application.status = "PACKAGE_APPROVED"

    db.commit()

    return ApplicationApprovalResult(
        application_id=application.id,
        approved=True,
        approved_at=approved_at,
        cv_hash=cv_hash,
        cover_letter_hash=cover_letter_hash,
        message=(
            "Application package approved successfully."
        ),
    )

@router.get(
    "/{application_id}/approval-status",
    response_model=ApplicationApprovalStatus,
)
def get_application_approval_status(
    application_id: int,
    db: Session = Depends(get_db),
):
    application = db.get(
        Application,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    if not application.package_approved:
        return ApplicationApprovalStatus(
            application_id=application.id,
            approved=False,
            approval_valid=False,
            approved_at=None,
            cv_unchanged=False,
            cover_letter_unchanged=False,
            message="Application package has not been approved.",
        )

    if (
        not application.pdf_path
        or not application.cover_letter_pdf_path
    ):
        return ApplicationApprovalStatus(
            application_id=application.id,
            approved=True,
            approval_valid=False,
            approved_at=application.package_approved_at,
            cv_unchanged=False,
            cover_letter_unchanged=False,
            message="Approved package files are unavailable.",
        )

    try:
        current_cv_hash = file_hash_service.sha256(
            application.pdf_path
        )

        current_cover_hash = file_hash_service.sha256(
            application.cover_letter_pdf_path
        )

    except FileNotFoundError:
        return ApplicationApprovalStatus(
            application_id=application.id,
            approved=True,
            approval_valid=False,
            approved_at=application.package_approved_at,
            cv_unchanged=False,
            cover_letter_unchanged=False,
            message="One or more approved files are missing.",
        )

    cv_unchanged = (
        current_cv_hash
        == application.approved_cv_hash
    )

    cover_letter_unchanged = (
        current_cover_hash
        == application.approved_cover_letter_hash
    )

    approval_valid = (
        cv_unchanged
        and cover_letter_unchanged
    )

    return ApplicationApprovalStatus(
        application_id=application.id,
        approved=True,
        approval_valid=approval_valid,
        approved_at=application.package_approved_at,
        cv_unchanged=cv_unchanged,
        cover_letter_unchanged=cover_letter_unchanged,
        message=(
            "Approval is valid."
            if approval_valid
            else "Application package changed after approval."
        ),
    )

@router.post(
    "/{application_id}/inspect-form",
    response_model=ApplicationFormInspection,
)
async def inspect_application_form(
    application_id: int,
    request: ApplicationFormInspectionRequest,
    db: Session = Depends(get_db),
):
    application = db.get(
        Application,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    # -----------------------------------------------------
    # PACKAGE APPROVAL
    # -----------------------------------------------------

    if not application.package_approved:
        raise HTTPException(
            status_code=403,
            detail=(
                "Application package has not been approved."
            ),
        )

    if (
        not application.pdf_path
        or not application.cover_letter_pdf_path
        or not application.approved_cv_hash
        or not application.approved_cover_letter_hash
    ):
        raise HTTPException(
            status_code=403,
            detail="Approved package is incomplete.",
        )

    try:
        current_cv_hash = file_hash_service.sha256(
            application.pdf_path
        )

        current_cover_hash = file_hash_service.sha256(
            application.cover_letter_pdf_path
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=403,
            detail="Approved package files are missing.",
        )

    approval_valid = (
        current_cv_hash
        == application.approved_cv_hash
        and
        current_cover_hash
        == application.approved_cover_letter_hash
    )

    if not approval_valid:
        raise HTTPException(
            status_code=403,
            detail=(
                "Application package changed after approval. "
                "A new approval is required."
            ),
        )

    # -----------------------------------------------------
    # READ-ONLY INSPECTION
    # -----------------------------------------------------

    try:
        result = await application_form_inspector.inspect(
            str(request.url)
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Application page inspection failed: {exc}",
        )

    return result

@router.post(
    "/{application_id}/map-form",
    response_model=FormMappingResult,
)
async def map_application_form(
    application_id: int,
    request: ApplicationFormInspectionRequest,
    db: Session = Depends(get_db),
):
    # -------------------------------------------------
    # 1. APPLICATION
    # -------------------------------------------------

    application = db.get(
        Application,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    # -------------------------------------------------
    # 2. PACKAGE APPROVAL CHECK
    # -------------------------------------------------

    if not application.package_approved:
        raise HTTPException(
            status_code=403,
            detail="Application package is not approved.",
        )

    if (
        not application.pdf_path
        or not application.cover_letter_pdf_path
        or not application.approved_cv_hash
        or not application.approved_cover_letter_hash
    ):
        raise HTTPException(
            status_code=403,
            detail="Approved package is incomplete.",
        )

    # -------------------------------------------------
    # 3. APPROVED FILE HASH CHECK
    # -------------------------------------------------

    try:
        current_cv_hash = file_hash_service.sha256(
            application.pdf_path
        )

        current_cover_hash = file_hash_service.sha256(
            application.cover_letter_pdf_path
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=403,
            detail="Approved package files are missing.",
        )

    if (
        current_cv_hash != application.approved_cv_hash
        or current_cover_hash
        != application.approved_cover_letter_hash
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Application package changed after approval. "
                "A new approval is required."
            ),
        )

    # -------------------------------------------------
    # 4. CANDIDATE PROFILE
    # -------------------------------------------------

    candidate = db.get(
        Candidate,
        application.candidate_id,
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found.",
        )

    if not candidate.profile_data:
        raise HTTPException(
            status_code=400,
            detail="Candidate profile is unavailable.",
        )

    candidate_profile = CandidateProfile.model_validate(
        candidate.profile_data
    )

    # -------------------------------------------------
    # 5. APPROVED COVER LETTER
    # -------------------------------------------------

    approved_cover_letter = None

    if (
        application.cover_letter_data
        and application.cover_letter_validation_data
    ):
        cover_validation = (
            CoverLetterValidationResult.model_validate(
                application.cover_letter_validation_data
            )
        )

        if cover_validation.is_valid:
            approved_cover_letter = (
                application.cover_letter_data
            )

    # -------------------------------------------------
    # 6. FORM INSPECTION
    # -------------------------------------------------

    try:
        inspection = (
            await application_form_inspector.inspect(
                str(request.url)
            )
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Form inspection failed: {exc}",
        )

    # -------------------------------------------------
    # 7. FORM MAPPING
    # -------------------------------------------------

    try:
        mappings = form_mapping_agent.map_fields(
            candidate=candidate_profile,
            inspection=inspection,
            cover_letter=approved_cover_letter,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Form mapping failed: {exc}",
        )

    # -------------------------------------------------
    # 8. COUNTS
    # -------------------------------------------------

    auto_fill_count = sum(
        1
        for item in mappings
        if item.status == "AUTO_FILL"
    )

    file_upload_count = sum(
        1
        for item in mappings
        if item.status == "FILE_UPLOAD"
    )

    needs_user_input_count = sum(
        1
        for item in mappings
        if item.status == "NEEDS_USER_INPUT"
    )

    skip_count = sum(
        1
        for item in mappings
        if item.status == "SKIP"
    )

    # Form ancak eksik kullanıcı cevabı yoksa
    # otomatik doldurma aşamasına geçebilir.
    ready_to_fill = (
        needs_user_input_count == 0
    )

    # -------------------------------------------------
    # 9. RESPONSE
    # -------------------------------------------------

    return FormMappingResult(
        application_id=application.id,
        url=inspection.final_url,
        mappings=mappings,
        auto_fill_count=auto_fill_count,
        file_upload_count=file_upload_count,
        needs_user_input_count=needs_user_input_count,
        skip_count=skip_count,
        ready_to_fill=ready_to_fill,
    )

@router.post(
    "/{application_id}/form-answers",
    response_model=SaveFormAnswersResult,
)
def save_form_answers(
    application_id: int,
    request: SaveFormAnswersRequest,
    db: Session = Depends(get_db),
):
    application = db.get(
        Application,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    current_answers = dict(
        application.form_answers or {}
    )

    for answer in request.answers:
        field_name = answer.field_name.strip()
        value = answer.value.strip()

        if not field_name:
            raise HTTPException(
                status_code=400,
                detail="field_name cannot be empty.",
            )

        if not value:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Answer for '{field_name}' "
                    "cannot be empty."
                ),
            )

        current_answers[field_name] = value

    application.form_answers = current_answers

    db.commit()
    db.refresh(application)

    return SaveFormAnswersResult(
        application_id=application.id,
        saved_answers=current_answers,
        message="Form answers saved successfully.",
    )

@router.post(
    "/{application_id}/resolve-form",
    response_model=ResolvedFormPlan,
)
async def resolve_application_form(
    application_id: int,
    request: ApplicationFormInspectionRequest,
    db: Session = Depends(get_db),
):
    application = db.get(
        Application,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    # ---------------------------------------------
    # APPROVAL + HASH CHECK
    # ---------------------------------------------

    if not application.package_approved:
        raise HTTPException(
            status_code=403,
            detail="Application package is not approved.",
        )

    if (
        not application.pdf_path
        or not application.cover_letter_pdf_path
        or not application.approved_cv_hash
        or not application.approved_cover_letter_hash
    ):
        raise HTTPException(
            status_code=403,
            detail="Approved package is incomplete.",
        )

    try:
        current_cv_hash = file_hash_service.sha256(
            application.pdf_path
        )

        current_cover_hash = file_hash_service.sha256(
            application.cover_letter_pdf_path
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=403,
            detail="Approved package files are missing.",
        )

    if (
        current_cv_hash != application.approved_cv_hash
        or current_cover_hash
        != application.approved_cover_letter_hash
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Application package changed after approval."
            ),
        )

    # ---------------------------------------------
    # CANDIDATE
    # ---------------------------------------------

    candidate = db.get(
        Candidate,
        application.candidate_id,
    )

    if not candidate or not candidate.profile_data:
        raise HTTPException(
            status_code=400,
            detail="Candidate profile is unavailable.",
        )

    candidate_profile = CandidateProfile.model_validate(
        candidate.profile_data
    )

    # ---------------------------------------------
    # APPROVED COVER LETTER
    # ---------------------------------------------

    approved_cover_letter = None

    if (
        application.cover_letter_data
        and application.cover_letter_validation_data
    ):
        cover_validation = (
            CoverLetterValidationResult.model_validate(
                application.cover_letter_validation_data
            )
        )

        if cover_validation.is_valid:
            approved_cover_letter = (
                application.cover_letter_data
            )

    # ---------------------------------------------
    # INSPECT
    # ---------------------------------------------

    try:
        inspection = (
            await application_form_inspector.inspect(
                str(request.url)
            )
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Form inspection failed: {exc}",
        )

    # ---------------------------------------------
    # MAP
    # ---------------------------------------------

    try:
        mappings = form_mapping_agent.map_fields(
            candidate=candidate_profile,
            inspection=inspection,
            cover_letter=approved_cover_letter,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Form mapping failed: {exc}",
        )

    # ---------------------------------------------
    # RESOLVE
    # ---------------------------------------------

    resolved_fields = [
        form_value_resolver.resolve(
            mapping=mapping,
            candidate=candidate_profile,
            application=application,
        )
        for mapping in mappings
    ]

    # ---------------------------------------------
    # COUNTS
    # ---------------------------------------------

    fill_count = sum(
        field.action == "FILL"
        for field in resolved_fields
    )

    upload_count = sum(
        field.action == "UPLOAD"
        for field in resolved_fields
    )

    unresolved_count = sum(
        field.action == "UNRESOLVED"
        for field in resolved_fields
    )

    skip_count = sum(
        field.action == "SKIP"
        for field in resolved_fields
    )

    return ResolvedFormPlan(
        application_id=application.id,
        url=inspection.final_url,
        fields=resolved_fields,
        fill_count=fill_count,
        upload_count=upload_count,
        unresolved_count=unresolved_count,
        skip_count=skip_count,
        ready_to_fill=(
            unresolved_count == 0
        ),
    )


@router.post("/{application_id}/browser-review-plan")
async def get_browser_review_plan(
    application_id: int,
    request: ApplicationFormInspectionRequest,
    db: Session = Depends(get_db),
):
    """Return a freshly revalidated plan for the loopback desktop agent."""
    plan = await resolve_application_form(application_id, request, db)
    if not plan.ready_to_fill:
        raise HTTPException(status_code=400, detail="Form plan is not ready.")
    application = db.get(Application, application_id)
    application.status = "BROWSER_REVIEW_PENDING"
    application.submission_approved = False
    application.submission_approved_at = None
    application.approved_submission_hash = None
    application.approved_submission_url = None
    application.approved_form_screenshot_hash = None
    db.commit()
    uploads = {}
    for field in plan.fields:
        if field.action == "UPLOAD" and field.file_path:
            path = Path(field.file_path)
            if not path.exists():
                raise HTTPException(status_code=400, detail=f"Upload file is missing: {path.name}")
            uploads[str(field.field_index)] = {
                "filename": path.name,
                "content_base64": base64.b64encode(path.read_bytes()).decode("ascii"),
            }
    return {"plan": plan.model_dump(), "uploads": uploads}


@router.post("/{application_id}/browser-review-result")
def save_browser_review_result(
    application_id: int,
    request: BrowserReviewResultRequest,
    db: Session = Depends(get_db),
):
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")
    if not application.package_approved:
        raise HTTPException(status_code=403, detail="Application package is not approved.")
    if not request.verification.get("verified") or request.verification.get("failed_count", 1) != 0:
        raise HTTPException(status_code=400, detail="Visible browser form verification failed.")
    try:
        image_bytes = base64.b64decode(request.screenshot_base64, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid screenshot data.")
    if not image_bytes or len(image_bytes) > 12 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Screenshot must be under 12 MB.")
    if not image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(status_code=400, detail="Browser review screenshot is not a PNG image.")
    screenshot_dir = Path("generated") / f"application_{application_id}"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = screenshot_dir / "filled_application_form.png"
    screenshot_path.write_bytes(image_bytes)
    application.form_prepared_at = datetime.now(timezone.utc).replace(tzinfo=None)
    application.form_verification_data = request.verification
    application.status = "AWAITING_USER_REVIEW"
    application.submission_approved = False
    application.submission_approved_at = None
    application.approved_submission_hash = None
    application.approved_submission_url = None
    application.approved_form_screenshot_hash = None
    db.commit()
    return {
        "application_id": application_id,
        "status": "AWAITING_USER_REVIEW",
        "final_url": request.final_url,
        "verification": request.verification,
    }

@router.post(
    "/{application_id}/fill-form",
    response_model=FormFillResult,
)
async def fill_application_form(
    application_id: int,
    request: FormFillRequest,
    db: Session = Depends(get_db),
):
    application = db.get(
        Application,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    # ---------------------------------------------
    # 1. APPROVAL CHECK
    # ---------------------------------------------

    if not application.package_approved:
        raise HTTPException(
            status_code=403,
            detail="Application package is not approved.",
        )

    if (
        not application.pdf_path
        or not application.cover_letter_pdf_path
        or not application.approved_cv_hash
        or not application.approved_cover_letter_hash
    ):
        raise HTTPException(
            status_code=403,
            detail="Approved package is incomplete.",
        )

    # ---------------------------------------------
    # 2. HASH CHECK
    # ---------------------------------------------

    try:
        current_cv_hash = file_hash_service.sha256(
            application.pdf_path
        )

        current_cover_hash = file_hash_service.sha256(
            application.cover_letter_pdf_path
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=403,
            detail="Approved package files are missing.",
        )

    if (
        current_cv_hash != application.approved_cv_hash
        or current_cover_hash
        != application.approved_cover_letter_hash
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Application package changed after approval. "
                "A new approval is required."
            ),
        )

    # ---------------------------------------------
    # 3. CANDIDATE
    # ---------------------------------------------

    candidate = db.get(
        Candidate,
        application.candidate_id,
    )

    if not candidate or not candidate.profile_data:
        raise HTTPException(
            status_code=400,
            detail="Candidate profile is unavailable.",
        )

    candidate_profile = CandidateProfile.model_validate(
        candidate.profile_data
    )

    # ---------------------------------------------
    # 4. APPROVED COVER LETTER
    # ---------------------------------------------

    approved_cover_letter = None

    if (
        application.cover_letter_data
        and application.cover_letter_validation_data
    ):
        cover_validation = (
            CoverLetterValidationResult.model_validate(
                application.cover_letter_validation_data
            )
        )

        if cover_validation.is_valid:
            approved_cover_letter = (
                application.cover_letter_data
            )

    # ---------------------------------------------
    # 5. INSPECT
    # ---------------------------------------------

    try:
        inspection = (
            await application_form_inspector.inspect(
                request.url
            )
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Form inspection failed: {exc}",
        )

    # ---------------------------------------------
    # 6. MAP
    # ---------------------------------------------

    try:
        mappings = form_mapping_agent.map_fields(
            candidate=candidate_profile,
            inspection=inspection,
            cover_letter=approved_cover_letter,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Form mapping failed: {exc}",
        )

    # ---------------------------------------------
    # 7. RESOLVE
    # ---------------------------------------------

    resolved_fields = [
        form_value_resolver.resolve(
            mapping=mapping,
            candidate=candidate_profile,
            application=application,
        )
        for mapping in mappings
    ]

    fill_count = sum(
        field.action == "FILL"
        for field in resolved_fields
    )

    upload_count = sum(
        field.action == "UPLOAD"
        for field in resolved_fields
    )

    unresolved_count = sum(
        field.action == "UNRESOLVED"
        for field in resolved_fields
    )

    skip_count = sum(
        field.action == "SKIP"
        for field in resolved_fields
    )

    plan = ResolvedFormPlan(
        application_id=application.id,
        url=inspection.final_url,
        fields=resolved_fields,
        fill_count=fill_count,
        upload_count=upload_count,
        unresolved_count=unresolved_count,
        skip_count=skip_count,
        ready_to_fill=(
            unresolved_count == 0
        ),
    )

    # ---------------------------------------------
    # 8. DO NOT FILL INCOMPLETE FORMS
    # ---------------------------------------------

    if not plan.ready_to_fill:
        unresolved_names = [
            field.field_name
            for field in plan.fields
            if field.action == "UNRESOLVED"
        ]

        raise HTTPException(
            status_code=400,
            detail={
                "message": (
                    "Form contains unresolved fields."
                ),
                "fields": unresolved_names,
            },
        )

    # ---------------------------------------------
    # 9. PLAYWRIGHT FILL
    #    IMPORTANT: NO SUBMISSION
    # ---------------------------------------------

    application.status = "FORM_PREPARING"
    application.form_verification_data = None
    application.submission_approved = False
    application.submission_approved_at = None
    application.approved_submission_hash = None
    application.approved_submission_url = None
    application.approved_form_screenshot_hash = None
    db.commit()

    try:
        result = await application_form_filler.fill(
            plan
        )

    except Exception as exc:
        application.status = "FORM_PREPARATION_FAILED"
        db.commit()
        raise HTTPException(
            status_code=502,
            detail=f"Form filling failed: {exc}",
        )

    result.status = "FORM_PREPARED" if result.success else "FORM_PREPARATION_FAILED"
    result.prepared_at = datetime.now(timezone.utc).isoformat() if result.success else None
    if result.success:
        application.status = "FORM_PREPARED"
        application.form_prepared_at = datetime.now(timezone.utc).replace(tzinfo=None)
        application.form_verification_data = result.verification.model_dump() if result.verification else None
        application.submission_approved = False
        application.submission_approved_at = None
        application.approved_submission_hash = None
        application.approved_submission_url = None
        application.approved_form_screenshot_hash = None
        db.commit()
    return result

@router.get(
    "/{application_id}/form-screenshot",
)
def get_form_screenshot(
    application_id: int,
    db: Session = Depends(get_db),
):
    application = db.get(
        Application,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    screenshot_path = (
        Path("generated")
        / f"application_{application_id}"
        / "filled_application_form.png"
    )

    if not screenshot_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Form screenshot not found.",
        )

    return FileResponse(
        path=str(screenshot_path),
        media_type="image/png",
        filename=(
            f"application_{application_id}_"
            "form_preview.png"
        ),
    )

@router.get("/{application_id}/submission-screenshot")
def get_submission_screenshot(
    application_id: int,
    db: Session = Depends(get_db),
):
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found.")
    screenshot_path = application.submission_screenshot_path
    if not screenshot_path or not Path(screenshot_path).exists():
        raise HTTPException(status_code=404, detail="Submission screenshot not found.")
    return FileResponse(path=screenshot_path, media_type="image/png", filename=f"application_{application_id}_submission.png")

@router.post(
    "/{application_id}/approve-submission",
    response_model=SubmissionApprovalResult,
)
def approve_submission(
    application_id: int,
    request: SubmissionApprovalRequest,
    db: Session = Depends(get_db),
):
    # 1. Application kaydını bul
    application = db.get(
        Application,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    # 2. Önce application package onaylanmış olmalı
    if not application.package_approved:
        raise HTTPException(
            status_code=403,
            detail=(
                "Application package must be approved "
                "before submission approval."
            ),
        )

    # 3. Onaylanmış CV ve Cover Letter bilgileri mevcut mu?
    if (
        not application.pdf_path
        or not application.cover_letter_pdf_path
        or not application.approved_cv_hash
        or not application.approved_cover_letter_hash
    ):
        raise HTTPException(
            status_code=403,
            detail="Approved application package is incomplete.",
        )

    # 4. CV ve Cover Letter dosyaları hâlâ mevcut mu?
    try:
        current_cv_hash = file_hash_service.sha256(
            application.pdf_path
        )

        current_cover_letter_hash = (
            file_hash_service.sha256(
                application.cover_letter_pdf_path
            )
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )

    # 5. Package approval sonrasında dosyalar değişmiş mi?
    if (
        current_cv_hash
        != application.approved_cv_hash
        or current_cover_letter_hash
        != application.approved_cover_letter_hash
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Application package changed after "
                "package approval. Approve the package again."
            ),
        )

    # 6. Kullanıcının incelediği form screenshot'ını bul
    screenshot_path = (
        Path("generated")
        / f"application_{application.id}"
        / "filled_application_form.png"
    )

    if not screenshot_path.exists():
        raise HTTPException(
            status_code=400,
            detail=(
                "Filled form screenshot is missing. "
                "Fill and review the form before "
                "submission approval."
            ),
        )

    # 7. Screenshot hash'ini oluştur
    try:
        screenshot_hash = file_hash_service.sha256(
            str(screenshot_path)
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=400,
            detail="Filled form screenshot is missing.",
        )

    # 8. Final submission hash'ini oluştur
    #
    # Bu hash:
    # - application
    # - candidate
    # - job
    # - URL
    # - CV
    # - cover letter
    # - form answers
    # - screenshot
    #
    # bilgilerini temsil ediyor.
    try:
        submission_hash = (
            submission_hash_service.create_hash(
                application=application,
                url=request.url,
            )
        )

    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    # 9. Final human approval zamanını oluştur
    approved_at = datetime.now(
        timezone.utc
    )

    # 10. Approval bilgilerini Application'a kaydet
    application.submission_approved = True

    application.submission_approved_at = (
        approved_at
    )

    application.approved_submission_hash = (
        submission_hash
    )

    application.approved_submission_url = (
        request.url
    )

    application.approved_form_screenshot_hash = (
        screenshot_hash
    )

    # 11. Veritabanına kaydet
    db.commit()

    db.refresh(application)

    # 12. Sonucu döndür
    return SubmissionApprovalResult(
        application_id=application.id,
        approved=True,
        approved_at=(
            application.submission_approved_at
        ),
        submission_hash=submission_hash,
        url=request.url,
        message=(
            "Final submission approved. "
            "No form has been submitted."
        ),
    )

@router.get(
    "/{application_id}/submission-approval-status",
    response_model=SubmissionApprovalStatus,
)
def get_submission_approval_status(
    application_id: int,
    db: Session = Depends(get_db),
):
    application = db.get(
        Application,
        application_id,
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    if (
        not application.submission_approved
        or not application.approved_submission_hash
        or not application.approved_submission_url
    ):
        return SubmissionApprovalStatus(
            application_id=application.id,
            approved=False,
            approval_valid=False,
            approved_at=application.submission_approved_at,
            url_unchanged=False,
            submission_unchanged=False,
            message="Submission has not been approved.",
        )

    try:
        current_hash = (
            submission_hash_service.create_hash(
                application=application,
                url=application.approved_submission_url,
            )
        )

    except (ValueError, FileNotFoundError):
        return SubmissionApprovalStatus(
            application_id=application.id,
            approved=True,
            approval_valid=False,
            approved_at=application.submission_approved_at,
            url_unchanged=True,
            submission_unchanged=False,
            message=(
                "Submission approval is no longer valid."
            ),
        )

    submission_unchanged = (
        current_hash
        == application.approved_submission_hash
    )

    return SubmissionApprovalStatus(
        application_id=application.id,
        approved=True,
        approval_valid=submission_unchanged,
        approved_at=application.submission_approved_at,
        url_unchanged=True,
        submission_unchanged=submission_unchanged,
        message=(
            "Submission approval is valid."
            if submission_unchanged
            else
            "Submission changed after approval."
        ),
    )


@router.post(
    "/{application_id}/submit-application",
    response_model=FormSubmissionResult,
)
async def submit_application(
    application_id: int,
    db: Session = Depends(get_db),
):
    # -----------------------------------------
    # 1. APPLICATION
    # -----------------------------------------

    application = db.scalar(
        select(Application)
        .where(Application.id == application_id)
        .with_for_update()
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    # Aynı başvuru ikinci kez gönderilmesin.
    if application.submitted_at is not None or application.status in {
        "SUBMISSION_IN_PROGRESS",
        "SUBMISSION_UNCONFIRMED",
    }:
        raise HTTPException(
            status_code=409,
            detail=(
                "Application has already been submitted."
            ),
        )

    # -----------------------------------------
    # 2. FINAL SUBMISSION APPROVAL
    # -----------------------------------------

    if not application.submission_approved:
        raise HTTPException(
            status_code=403,
            detail=(
                "Final submission approval is required."
            ),
        )

    if (
        not application.approved_submission_hash
        or not application.approved_submission_url
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Final submission approval is incomplete."
            ),
        )

    # -----------------------------------------
    # 3. PACKAGE APPROVAL
    # -----------------------------------------

    if not application.package_approved:
        raise HTTPException(
            status_code=403,
            detail=(
                "Application package is not approved."
            ),
        )

    if (
        not application.pdf_path
        or not application.cover_letter_pdf_path
        or not application.approved_cv_hash
        or not application.approved_cover_letter_hash
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Approved application package "
                "is incomplete."
            ),
        )

    # -----------------------------------------
    # 4. CV + COVER LETTER HASH CHECK
    # -----------------------------------------

    try:
        current_cv_hash = file_hash_service.sha256(
            application.pdf_path
        )

        current_cover_letter_hash = (
            file_hash_service.sha256(
                application.cover_letter_pdf_path
            )
        )

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )

    if (
        current_cv_hash
        != application.approved_cv_hash
        or current_cover_letter_hash
        != application.approved_cover_letter_hash
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Application package changed "
                "after package approval. "
                "Approve the package again."
            ),
        )

    # -----------------------------------------
    # 5. FINAL SUBMISSION HASH CHECK
    # -----------------------------------------

    try:
        current_submission_hash = (
            submission_hash_service.create_hash(
                application=application,
                url=(
                    application
                    .approved_submission_url
                ),
            )
        )

    except (
        ValueError,
        FileNotFoundError,
    ) as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )

    if (
        current_submission_hash
        != application.approved_submission_hash
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Submission changed after final "
                "approval. Review and approve "
                "the submission again."
            ),
        )

    # -----------------------------------------
    # 6. CANDIDATE
    # -----------------------------------------

    candidate = db.get(
        Candidate,
        application.candidate_id,
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found.",
        )

    if not candidate.profile_data:
        raise HTTPException(
            status_code=400,
            detail=(
                "Candidate profile is missing."
            ),
        )

    candidate_profile = (
        CandidateProfile.model_validate(
            candidate.profile_data
        )
    )

    # -----------------------------------------
    # 7. COVER LETTER DATA
    # -----------------------------------------

    if not application.cover_letter_data:
        raise HTTPException(
            status_code=400,
            detail=(
                "Cover letter data is missing."
            ),
        )

    cover_letter = (
        application.cover_letter_data
    )

    # -----------------------------------------
    # 8. FORMU YENİDEN INSPECT ET
    # -----------------------------------------

    try:
        inspection = (
            await application_form_inspector.inspect(
                application.approved_submission_url
            )
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "Application form could not "
                f"be inspected: {exc}"
            ),
        )

    # -----------------------------------------
    # 9. FORMU YENİDEN MAP ET
    # -----------------------------------------

    try:
        mappings = form_mapping_agent.map_fields(
            candidate=candidate_profile,
            inspection=inspection,
            cover_letter=cover_letter,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=(
                "Application form mapping "
                f"failed: {exc}"
            ),
        )

    # -----------------------------------------
    # 10. HER MAPPING'İ TEK TEK RESOLVE ET
    #
    # FormValueResolver.resolve():
    #
    # resolve(
    #     mapping,
    #     candidate,
    #     application,
    # )
    #
    # şeklinde çalışıyor.
    # -----------------------------------------

    resolved_fields = []

    for mapping in mappings:

        resolved_field = (
            form_value_resolver.resolve(
                mapping=mapping,
                candidate=candidate_profile,
                application=application,
            )
        )

        resolved_fields.append(
            resolved_field
        )

    # -----------------------------------------
    # 11. RESOLUTION COUNTS
    # -----------------------------------------

    fill_count = sum(
        1
        for field in resolved_fields
        if field.action == "FILL"
    )

    upload_count = sum(
        1
        for field in resolved_fields
        if field.action == "UPLOAD"
    )

    unresolved_count = sum(
        1
        for field in resolved_fields
        if field.action == "UNRESOLVED"
    )

    skip_count = sum(
        1
        for field in resolved_fields
        if field.action == "SKIP"
    )

    # -----------------------------------------
    # 12. RESOLVED FORM PLAN
    # -----------------------------------------

    plan = ResolvedFormPlan(
        application_id=application.id,
        url=inspection.final_url,
        fields=resolved_fields,
        fill_count=fill_count,
        upload_count=upload_count,
        unresolved_count=unresolved_count,
        skip_count=skip_count,
        ready_to_fill=(
            unresolved_count == 0
        ),
    )

    # -----------------------------------------
    # 13. UNRESOLVED FIELD VAR MI?
    # -----------------------------------------

    if not plan.ready_to_fill:

        unresolved_fields = [
            field.field_name
            or field.field_label
            or f"field_{field.field_index}"
            for field in plan.fields
            if field.action == "UNRESOLVED"
        ]

        raise HTTPException(
            status_code=400,
            detail={
                "message": (
                    "Form contains unresolved "
                    "fields."
                ),
                "fields": unresolved_fields,
            },
        )

    # -----------------------------------------
    # 14. SUBMIT'TEN HEMEN ÖNCE
    #     FINAL HASH CHECK
    # -----------------------------------------

    try:
        pre_submit_hash = (
            submission_hash_service.create_hash(
                application=application,
                url=(
                    application
                    .approved_submission_url
                ),
            )
        )

    except (
        ValueError,
        FileNotFoundError,
    ) as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )

    if (
        pre_submit_hash
        != application.approved_submission_hash
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Submission approval became "
                "invalid before submission."
            ),
        )

    # -----------------------------------------
    # 15. URL DEĞİŞMEDİ Mİ?
    # -----------------------------------------

    if (
        plan.url
        != application.approved_submission_url
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Application form URL changed "
                "after final approval."
            ),
        )

    # -----------------------------------------
    # 16. PLAYWRIGHT SUBMISSION
    #
    # BURADAN SONRASI GERÇEKTEN
    # SUBMIT BUTONUNA BASABİLİR.
    # -----------------------------------------

    application.status = "SUBMISSION_IN_PROGRESS"
    application.submission_attempted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()

    try:
        result = (
            await application_form_submitter.submit(
                plan
            )
        )

    except Exception as exc:
        application.status = "SUBMISSION_UNCONFIRMED"
        db.commit()
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        )

    # -----------------------------------------
    # 17. CONFIRMATION YOKSA
    #     DB'YE SUBMITTED YAZMA
    # -----------------------------------------

    application.submission_url = result.final_url
    application.submission_confirmation = result.confirmation
    screenshot_path = Path("generated") / f"application_{application.id}" / "submission_confirmation.png"
    application.submission_screenshot_path = str(screenshot_path) if screenshot_path.exists() else None
    if result.success and result.submitted and result.confirmation and result.screenshot_available and application.submission_screenshot_path:
        application.submitted_at = datetime.now(timezone.utc).replace(tzinfo=None)
        application.status = "SUBMITTED"
        result.status = "SUBMITTED"
        result.submitted_at = application.submitted_at.replace(tzinfo=timezone.utc).isoformat()
    else:
        application.submitted_at = None
        application.status = "SUBMISSION_UNCONFIRMED"
        result.status = "SUBMISSION_UNCONFIRMED"
        result.submitted = False
        result.success = False

    db.commit()
    db.refresh(application)

    # -----------------------------------------
    # 19. RESULT
    # -----------------------------------------

    return result
