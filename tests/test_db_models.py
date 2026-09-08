"""Tests for ORM metadata, relationships, and constraints.

These tests inspect SQLAlchemy mappings only. They do not open a database
connection or require DATABASE_URL.
"""

from __future__ import annotations

from sqlalchemy import CheckConstraint, UniqueConstraint, inspect

from app.db.base import Base
from app.db.models import (
    AuthIdentity,
    CandidateProfile,
    CandidateProfileSkill,
    Company,
    Experience,
    Job,
    JobMatch,
    JobSearchRequest,
    ResumeVersion,
    Skill,
    User,
)

EXPECTED_TABLES = {
    "users",
    "auth_identities",
    "candidate_profiles",
    "companies",
    "experiences",
    "skills",
    "candidate_profile_skills",
    "jobs",
    "job_search_requests",
    "job_matches",
    "resume_versions",
}


def _column_names(model: type) -> set[str]:
    return set(model.__table__.columns.keys())


def _unique_column_groups(model: type) -> set[tuple[str, ...]]:
    groups: set[tuple[str, ...]] = set()
    for constraint in model.__table__.constraints:
        if isinstance(constraint, UniqueConstraint):
            groups.add(tuple(col.name for col in constraint.columns))
    for column in model.__table__.columns:
        if column.unique:
            groups.add((column.name,))
    return groups


def _check_sql(model: type) -> set[str]:
    return {
        str(constraint.sqltext)
        for constraint in model.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }


def _relationship_names(model: type) -> set[str]:
    return set(inspect(model).relationships.keys())


def test_metadata_contains_expected_tables() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_no_unimplemented_entities_are_mapped() -> None:
    table_names = set(Base.metadata.tables)
    assert "tailored_cvs" not in table_names
    assert "workflow_states" not in table_names
    assert "educations" not in table_names
    assert "institutions" not in table_names


def test_user_columns_and_email_unique() -> None:
    assert {"id", "display_name", "email", "phone", "created_at", "updated_at"} <= _column_names(
        User
    )
    assert User.__table__.c.phone.nullable is True
    assert User.__table__.c.email.nullable is False
    assert ("email",) in _unique_column_groups(User)


def test_user_relationships() -> None:
    relationships = inspect(User).relationships
    assert relationships["candidate_profile"].uselist is False
    assert relationships["auth_identities"].uselist is True


def test_auth_identity_unique_provider_subject() -> None:
    assert ("provider", "provider_subject") in _unique_column_groups(AuthIdentity)
    assert AuthIdentity.__table__.c.user_id.nullable is False


def test_candidate_profile_is_one_to_one_and_excludes_search_intent() -> None:
    columns = _column_names(CandidateProfile)
    assert "user_id" in columns
    assert "current_title" in columns
    assert "target_title" not in columns
    assert "career_goal" not in columns
    assert ("user_id",) in _unique_column_groups(CandidateProfile)
    assert inspect(CandidateProfile).relationships["user"].uselist is False
    assert inspect(CandidateProfile).relationships["job_search_requests"].uselist is True


def test_experience_belongs_to_profile_and_company() -> None:
    table = Experience.__table__
    assert table.c.end_date.nullable is True
    assert table.c.company_id.nullable is False
    assert "company_name" not in table.c
    names = _relationship_names(Experience)
    assert names == {"candidate_profile", "company"}
    assert any("start_date <= end_date" in sql for sql in _check_sql(Experience))


def test_skill_name_is_unique() -> None:
    assert ("name",) in _unique_column_groups(Skill)


def test_candidate_profile_skill_composite_primary_key() -> None:
    pk = {col.name for col in CandidateProfileSkill.__table__.primary_key.columns}
    assert pk == {"candidate_profile_id", "skill_id"}


def test_job_is_catalog_entity_not_user_owned() -> None:
    columns = _column_names(Job)
    assert "user_id" not in columns
    assert "candidate_profile_id" not in columns
    assert "company_id" in columns
    assert any("active" in sql and "closed" in sql for sql in _check_sql(Job))


def test_job_search_request_holds_target_title() -> None:
    columns = _column_names(JobSearchRequest)
    assert "candidate_profile_id" in columns
    assert "target_title" in columns
    assert JobSearchRequest.__table__.c.target_title.nullable is True
    assert JobSearchRequest.__table__.c.preferred_seniority.nullable is True
    assert JobSearchRequest.__table__.c.min_years_experience.nullable is True
    assert JobSearchRequest.__table__.c.max_years_experience.nullable is True
    assert JobSearchRequest.__table__.c.location.nullable is True


def test_job_match_belongs_to_search_request_and_job() -> None:
    columns = _column_names(JobMatch)
    assert "job_search_request_id" in columns
    assert "job_id" in columns
    assert "candidate_profile_id" not in columns
    assert ("job_search_request_id", "job_id") in _unique_column_groups(JobMatch)
    names = _relationship_names(JobMatch)
    assert "job_search_request" in names
    assert "job" in names


def test_resume_version_supports_original_generic_and_tailored() -> None:
    table = ResumeVersion.__table__
    assert table.c.job_match_id.nullable is True
    assert table.c.summary.nullable is True
    assert table.c.file_reference.nullable is True
    sql = " ".join(_check_sql(ResumeVersion))
    assert "original" in sql
    assert "generic" in sql
    assert "tailored" in sql


def test_company_is_minimal_reusable_identity() -> None:
    assert _column_names(Company) == {"id", "name", "created_at", "updated_at"}
    assert _relationship_names(Company) == {"experiences", "jobs"}
