"""Reusable catalog entities: companies, skills, and jobs."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.models.enums import JobStatus

if TYPE_CHECKING:
    from app.db.models.candidate import CandidateProfile, Experience
    from app.db.models.search import JobMatch


class Company(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Reusable organization identity shared by experiences and jobs."""

    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    experiences: Mapped[list[Experience]] = relationship(back_populates="company")
    jobs: Mapped[list[Job]] = relationship(back_populates="company")


class Skill(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Reusable global skill or technology identity."""

    __tablename__ = "skills"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    candidate_profiles: Mapped[list[CandidateProfile]] = relationship(
        secondary="candidate_profile_skills",
        back_populates="skills",
    )


class Job(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """System-level job catalog entry, not owned by a user."""

    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'closed')",
            name="status",
        ),
    )

    company_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("companies.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=JobStatus.ACTIVE.value,
        server_default=JobStatus.ACTIVE.value,
    )
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    company: Mapped[Company] = relationship(back_populates="jobs")
    job_matches: Mapped[list[JobMatch]] = relationship(back_populates="job")
