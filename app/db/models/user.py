"""User identity and authentication-provider links."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.candidate import CandidateProfile


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Application-level user identity, independent of auth providers."""

    __tablename__ = "users"

    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)

    candidate_profile: Mapped[CandidateProfile | None] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    auth_identities: Mapped[list[AuthIdentity]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class AuthIdentity(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Link between a Career AI user and an external authentication subject."""

    __tablename__ = "auth_identities"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_subject",
            name="uq_auth_identities_provider_subject",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_subject: Mapped[str] = mapped_column(String(255), nullable=False)

    user: Mapped[User] = relationship(back_populates="auth_identities")
