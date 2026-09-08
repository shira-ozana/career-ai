"""Job search intent and match results."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.models.enums import JobMatchStatus

if TYPE_CHECKING:
    from app.db.models.candidate import CandidateProfile
    from app.db.models.catalog import Job
    from app.db.models.resume import ResumeVersion


class JobSearchRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Intent and criteria for one job search against a candidate profile."""

    __tablename__ = "job_search_requests"
    __table_args__ = (
        CheckConstraint(
            "min_years_experience IS NULL OR max_years_experience IS NULL "
            "OR min_years_experience <= max_years_experience",
            name="years_experience_range",
        ),
    )

    candidate_profile_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preferred_seniority: Mapped[str | None] = mapped_column(String(64), nullable=True)
    min_years_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_years_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    candidate_profile: Mapped[CandidateProfile] = relationship(
        back_populates="job_search_requests",
    )
    job_matches: Mapped[list[JobMatch]] = relationship(
        back_populates="job_search_request",
        cascade="all, delete-orphan",
    )


class JobMatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Result of matching one JobSearchRequest to one Job."""

    __tablename__ = "job_matches"
    __table_args__ = (
        UniqueConstraint(
            "job_search_request_id",
            "job_id",
            name="uq_job_matches_search_request_job",
        ),
        CheckConstraint(
            "match_score >= 0 AND match_score <= 100",
            name="match_score_range",
        ),
        CheckConstraint(
            "status IN ('pending', 'reviewed')",
            name="status",
        ),
    )

    job_search_request_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("job_search_requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    job_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("jobs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    match_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    match_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=JobMatchStatus.PENDING.value,
        server_default=JobMatchStatus.PENDING.value,
    )

    job_search_request: Mapped[JobSearchRequest] = relationship(back_populates="job_matches")
    job: Mapped[Job] = relationship(back_populates="job_matches")
    resume_versions: Mapped[list[ResumeVersion]] = relationship(back_populates="job_match")
