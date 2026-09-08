"""Simple persisted status/type values for the initial schema."""

from enum import StrEnum


class JobStatus(StrEnum):
    ACTIVE = "active"
    CLOSED = "closed"


class JobMatchStatus(StrEnum):
    PENDING = "pending"
    REVIEWED = "reviewed"


class ResumeVersionType(StrEnum):
    ORIGINAL = "original"
    GENERIC = "generic"
    TAILORED = "tailored"
