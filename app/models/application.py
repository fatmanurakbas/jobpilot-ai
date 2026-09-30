from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    DateTime,
    Text
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy import String

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String

class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)

    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id")
    )

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id")
    )

    match_percentage: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )
    
    match_data: Mapped[dict | None] = mapped_column(
    JSONB,
    nullable=True
    )

    tailoring_data: Mapped[dict | None] = mapped_column(
    JSONB,
    nullable=True
    )

    validation_data: Mapped[dict | None] = mapped_column(
    JSONB,
    nullable=True
    )

    correction_data: Mapped[dict | None] = mapped_column(
    JSONB,
    nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="FOUND"
    )

    cv_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    pdf_path: Mapped[str | None] = mapped_column(
    String,
    nullable=True,
    )

    cover_letter_data: Mapped[dict | None] = mapped_column(
    JSONB,
    nullable=True,
   )

    cover_letter_validation_data: Mapped[
    dict | None
    ] = mapped_column(
    JSONB,
    nullable=True,
    )

    cover_letter_correction_data: Mapped[
    dict | None
    ] = mapped_column(
    JSONB,
    nullable=True,
    )

    cover_letter_path: Mapped[str | None] = mapped_column(
    String,
    nullable=True,
    )

    cover_letter_pdf_path: Mapped[str | None] = mapped_column(
    String,
    nullable=True,
    )  

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    applied_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    package_approved: Mapped[bool] = mapped_column(
    Boolean,
    default=False,
    nullable=False,
    )

    package_approved_at: Mapped[datetime | None] = mapped_column(
    DateTime,
    nullable=True,
   )

    approved_cv_hash: Mapped[str | None] = mapped_column(
    String(64),
    nullable=True,
   )

    approved_cover_letter_hash: Mapped[str | None] = mapped_column(
    String(64),
    nullable=True,
   )

    form_answers: Mapped[dict | None] = mapped_column(
    JSONB,
    nullable=True,
   )

    submission_approved: Mapped[bool] = mapped_column(
    Boolean,
    nullable=False,
    default=False,
   )

    submission_approved_at: Mapped[datetime | None] = mapped_column(
    DateTime,
    nullable=True,
    )

    approved_submission_hash: Mapped[str | None] = mapped_column(
    String(64),
    nullable=True,
    )

    approved_submission_url: Mapped[str | None] = mapped_column(
    Text,
    nullable=True,
    )
    approved_form_screenshot_hash: Mapped[str | None] = mapped_column(
    String(64),
    nullable=True,
   )

    submitted_at: Mapped[datetime | None] = mapped_column(
    DateTime,
    nullable=True,
    )

    submission_url: Mapped[str | None] = mapped_column(
    Text,
    nullable=True,
    )

    submission_confirmation: Mapped[str | None] = mapped_column(
    Text,
    nullable=True,
   )

    form_prepared_at: Mapped[datetime | None] = mapped_column(
    DateTime,
    nullable=True,
    )

    form_verification_data: Mapped[dict | None] = mapped_column(
    JSONB,
    nullable=True,
    )

    submission_attempted_at: Mapped[datetime | None] = mapped_column(
    DateTime,
    nullable=True,
    )

    submission_screenshot_path: Mapped[str | None] = mapped_column(
    String(500),
    nullable=True,
    )
