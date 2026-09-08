"""ORM models. Importing this package registers all tables on ``Base.metadata``."""

from app.db.models.candidate import CandidateProfile, CandidateProfileSkill, Experience
from app.db.models.catalog import Company, Job, Skill
from app.db.models.enums import JobMatchStatus, JobStatus, ResumeVersionType
from app.db.models.resume import ResumeVersion
from app.db.models.search import JobMatch, JobSearchRequest
from app.db.models.user import AuthIdentity, User

__all__ = [
    "AuthIdentity",
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
]
