from datetime import datetime

from sqlalchemy import String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    company: Mapped[str] = mapped_column(String(150))
    position: Mapped[str] = mapped_column(String(150))

    location: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    job_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    description: Mapped[str] = mapped_column(Text)

    status: Mapped[str] = mapped_column(
        String(50),
        default="FOUND"
    )

    analysis_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )