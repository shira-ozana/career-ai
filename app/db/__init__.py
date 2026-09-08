"""PostgreSQL persistence foundation (SQLAlchemy 2.x).

This package does not connect to the database at import time.
Agents, the CLI, and the existing Profile Analyzer flow do not use it yet.
"""

from app.db.base import Base
from app.db.models import (
    AuthIdentity,
    CandidateProfile,
    CandidateProfileSkill,
    Company,
    Experience,
    Job,
    JobMatch,
    JobMatchStatus,
    JobSearchRequest,
    JobStatus,
    ResumeVersion,
    ResumeVersionType,
    Skill,
    User,
)
from app.db.session import get_engine, get_session, get_session_factory, sqlalchemy_database_url

__all__ = [
    "AuthIdentity",
    "Base",
    "CandidateProfile",
    "CandidateProfileSkill",
    "Company",
    "Experience",
    "Job",
    "JobMatch",
    "JobMatchStatus",
    "JobSearchRequest",
    "JobStatus",
    "ResumeVersion",
    "ResumeVersionType",
    "Skill",
    "User",
    "get_engine",
    "get_session",
    "get_session_factory",
    "sqlalchemy_database_url",
]
