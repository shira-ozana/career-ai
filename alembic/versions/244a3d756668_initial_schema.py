"""initial schema

Revision ID: 244a3d756668
Revises:
Create Date: 2026-09-08 14:40:36.141917

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "244a3d756668"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NOW = sa.text("now()")
GEN_UUID = sa.text("gen_random_uuid()")


def upgrade() -> None:
    """Create the initial Career AI relational schema."""
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), server_default=GEN_UUID, nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_table(
        "companies",
        sa.Column("id", sa.Uuid(), server_default=GEN_UUID, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_companies"),
    )
    op.create_index("ix_companies_name", "companies", ["name"], unique=False)
    op.create_table(
        "skills",
        sa.Column("id", sa.Uuid(), server_default=GEN_UUID, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_skills"),
        sa.UniqueConstraint("name", name="uq_skills_name"),
    )
    op.create_table(
        "auth_identities",
        sa.Column("id", sa.Uuid(), server_default=GEN_UUID, nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("provider_subject", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_auth_identities_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_auth_identities"),
        sa.UniqueConstraint(
            "provider",
            "provider_subject",
            name="uq_auth_identities_provider_subject",
        ),
    )
    op.create_index("ix_auth_identities_user_id", "auth_identities", ["user_id"], unique=False)
    op.create_table(
        "candidate_profiles",
        sa.Column("id", sa.Uuid(), server_default=GEN_UUID, nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("current_title", sa.String(length=255), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("linkedin_url", sa.String(length=2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_candidate_profiles_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_candidate_profiles"),
        sa.UniqueConstraint("user_id", name="uq_candidate_profiles_user_id"),
    )
    op.create_table(
        "jobs",
        sa.Column("id", sa.Uuid(), server_default=GEN_UUID, nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.CheckConstraint("status IN ('active', 'closed')", name="ck_jobs_status"),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_jobs_company_id_companies",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_jobs"),
    )
    op.create_index("ix_jobs_company_id", "jobs", ["company_id"], unique=False)
    op.create_table(
        "experiences",
        sa.Column("id", sa.Uuid(), server_default=GEN_UUID, nullable=False),
        sa.Column("candidate_profile_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.CheckConstraint(
            "end_date IS NULL OR start_date <= end_date",
            name="ck_experiences_dates",
        ),
        sa.ForeignKeyConstraint(
            ["candidate_profile_id"],
            ["candidate_profiles.id"],
            name="fk_experiences_candidate_profile_id_candidate_profiles",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name="fk_experiences_company_id_companies",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_experiences"),
    )
    op.create_index(
        "ix_experiences_candidate_profile_id",
        "experiences",
        ["candidate_profile_id"],
        unique=False,
    )
    op.create_index("ix_experiences_company_id", "experiences", ["company_id"], unique=False)
    op.create_table(
        "candidate_profile_skills",
        sa.Column("candidate_profile_id", sa.Uuid(), nullable=False),
        sa.Column("skill_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["candidate_profile_id"],
            ["candidate_profiles.id"],
            name="fk_profile_skills_profile_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["skill_id"],
            ["skills.id"],
            name="fk_profile_skills_skill_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "candidate_profile_id",
            "skill_id",
            name="pk_candidate_profile_skills",
        ),
    )
    op.create_index(
        "ix_candidate_profile_skills_skill_id",
        "candidate_profile_skills",
        ["skill_id"],
        unique=False,
    )
    op.create_table(
        "job_search_requests",
        sa.Column("id", sa.Uuid(), server_default=GEN_UUID, nullable=False),
        sa.Column("candidate_profile_id", sa.Uuid(), nullable=False),
        sa.Column("target_title", sa.String(length=255), nullable=True),
        sa.Column("preferred_seniority", sa.String(length=64), nullable=True),
        sa.Column("min_years_experience", sa.Integer(), nullable=True),
        sa.Column("max_years_experience", sa.Integer(), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.CheckConstraint(
            "min_years_experience IS NULL OR max_years_experience IS NULL "
            "OR min_years_experience <= max_years_experience",
            name="ck_job_search_requests_years_experience_range",
        ),
        sa.ForeignKeyConstraint(
            ["candidate_profile_id"],
            ["candidate_profiles.id"],
            name="fk_job_search_requests_candidate_profile_id_candidate_profiles",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_job_search_requests"),
    )
    op.create_index(
        "ix_job_search_requests_candidate_profile_id",
        "job_search_requests",
        ["candidate_profile_id"],
        unique=False,
    )
    op.create_table(
        "job_matches",
        sa.Column("id", sa.Uuid(), server_default=GEN_UUID, nullable=False),
        sa.Column("job_search_request_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("match_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("match_reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.CheckConstraint(
            "match_score >= 0 AND match_score <= 100",
            name="ck_job_matches_match_score_range",
        ),
        sa.CheckConstraint("status IN ('pending', 'reviewed')", name="ck_job_matches_status"),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
            name="fk_job_matches_job_id_jobs",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["job_search_request_id"],
            ["job_search_requests.id"],
            name="fk_job_matches_job_search_request_id_job_search_requests",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_job_matches"),
        sa.UniqueConstraint(
            "job_search_request_id",
            "job_id",
            name="uq_job_matches_search_request_job",
        ),
    )
    op.create_index("ix_job_matches_job_id", "job_matches", ["job_id"], unique=False)
    op.create_table(
        "resume_versions",
        sa.Column("id", sa.Uuid(), server_default=GEN_UUID, nullable=False),
        sa.Column("candidate_profile_id", sa.Uuid(), nullable=False),
        sa.Column("job_match_id", sa.Uuid(), nullable=True),
        sa.Column("version_type", sa.String(length=32), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("file_reference", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.CheckConstraint(
            "version_type IN ('original', 'generic', 'tailored')",
            name="ck_resume_versions_version_type",
        ),
        sa.ForeignKeyConstraint(
            ["candidate_profile_id"],
            ["candidate_profiles.id"],
            name="fk_resume_versions_candidate_profile_id_candidate_profiles",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["job_match_id"],
            ["job_matches.id"],
            name="fk_resume_versions_job_match_id_job_matches",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_resume_versions"),
    )
    op.create_index(
        "ix_resume_versions_candidate_profile_id",
        "resume_versions",
        ["candidate_profile_id"],
        unique=False,
    )
    op.create_index(
        "ix_resume_versions_job_match_id",
        "resume_versions",
        ["job_match_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the initial Career AI relational schema."""
    op.drop_index("ix_resume_versions_job_match_id", table_name="resume_versions")
    op.drop_index("ix_resume_versions_candidate_profile_id", table_name="resume_versions")
    op.drop_table("resume_versions")
    op.drop_index("ix_job_matches_job_id", table_name="job_matches")
    op.drop_table("job_matches")
    op.drop_index("ix_job_search_requests_candidate_profile_id", table_name="job_search_requests")
    op.drop_table("job_search_requests")
    op.drop_index("ix_candidate_profile_skills_skill_id", table_name="candidate_profile_skills")
    op.drop_table("candidate_profile_skills")
    op.drop_index("ix_experiences_company_id", table_name="experiences")
    op.drop_index("ix_experiences_candidate_profile_id", table_name="experiences")
    op.drop_table("experiences")
    op.drop_index("ix_jobs_company_id", table_name="jobs")
    op.drop_table("jobs")
    op.drop_table("candidate_profiles")
    op.drop_index("ix_auth_identities_user_id", table_name="auth_identities")
    op.drop_table("auth_identities")
    op.drop_table("skills")
    op.drop_index("ix_companies_name", table_name="companies")
    op.drop_table("companies")
    op.drop_table("users")
