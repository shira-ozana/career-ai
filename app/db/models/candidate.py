"""Canonical candidate profile, experiences, and profile-skill links."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.catalog import Company, Skill
    from app.db.models.resume import ResumeVersion
    from app.db.models.search import JobSearchRequest
    from app.db.models.user import User


class CandidateProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Canonical professional state for one user. Not a specific resume version."""

    __tablename__ = "candidate_profiles"

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    current_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    user: Mapped[User] = relationship(back_populates="candidate_profile")
    experiences: Mapped[list[Experience]] = relationship(
        back_populates="candidate_profile",
        cascade="all, delete-orphan",
    )
    skills: Mapped[list[Skill]] = relationship(
        secondary="candidate_profile_skills",
        back_populates="candidate_profiles",
    )
    job_search_requests: Mapped[list[JobSearchRequest]] = relationship(
        back_populates="candidate_profile",
        cascade="all, delete-orphan",
    )
    resume_versions: Mapped[list[ResumeVersion]] = relationship(
        back_populates="candidate_profile",
        cascade="all, delete-orphan",
    )


class Experience(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One structured role/period on a candidate profile."""

    __tablename__ = "experiences"
    __table_args__ = (
        CheckConstraint(
            "end_date IS NULL OR start_date <= end_date",
            name="dates",
        ),
    )

    candidate_profile_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("companies.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    candidate_profile: Mapped[CandidateProfile] = relationship(back_populates="experiences")
    company: Mapped[Company] = relationship(back_populates="experiences")


class CandidateProfileSkill(Base):
    """Junction between CandidateProfile and Skill."""

    __tablename__ = "candidate_profile_skills"

    candidate_profile_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "candidate_profiles.id",
            ondelete="CASCADE",
            name="fk_profile_skills_profile_id",
        ),
        primary_key=True,
    )
    skill_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "skills.id",
            ondelete="CASCADE",
            name="fk_profile_skills_skill_id",
        ),
        primary_key=True,
        index=True,
    )
