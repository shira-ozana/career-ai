"""Persisted resume versions derived from a candidate profile."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.candidate import CandidateProfile
    from app.db.models.search import JobMatch


class ResumeVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A meaningful resume representation, not an intermediate editing draft.

    ``version_type`` distinguishes original, generic, and tailored resumes.
    A tailored version may reference a ``JobMatch``; original/generic versions
    typically do not.
    """

    __tablename__ = "resume_versions"
    __table_args__ = (
        CheckConstraint(
            "version_type IN ('original', 'generic', 'tailored')",
            name="version_type",
        ),
    )

    candidate_profile_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("candidate_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_match_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("job_matches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    version_type: Mapped[str] = mapped_column(String(32), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_reference: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    candidate_profile: Mapped[CandidateProfile] = relationship(back_populates="resume_versions")
    job_match: Mapped[JobMatch | None] = relationship(back_populates="resume_versions")
