"""Profile Analyzer Agent input/output contracts.

``ProfileInput`` / ``ExperienceItem`` / ``ProfileAnalysis`` are analysis-specific
Pydantic I/O models. They are not the persisted ``CandidateProfile`` /
``Experience`` ORM entities, and they are not the future ingestion contract
for CV or LinkedIn sources.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ExperienceItem(BaseModel):
    """One work-experience entry in a Profile Analyzer input.

    Company is a free-text name and duration is a display string. This is not
    the persisted ``Experience`` row (which uses ``company_id`` and dates).
    """

    title: str = Field(..., min_length=1, description="Job title")
    company: str = Field(..., min_length=1, description="Company name")
    duration: str | None = Field(
        default=None,
        description="Employment duration, e.g. '2022 – Present'",
    )
    description: str | None = Field(
        default=None,
        description="Role summary and key achievements",
    )


class ProfileInput(BaseModel):
    """Analysis-specific input for ``ProfileAnalyzerAgent``.

    Used by the CLI and agent to score an already-structured profile JSON
    against a career goal. Do not treat this as the canonical persisted
    ``CandidateProfile`` or as the future CV/LinkedIn ingestion model.
    """

    name: str = Field(..., min_length=1, description="Full name")
    headline: str = Field(..., min_length=1, description="LinkedIn headline")
    about: str = Field(default="", description="About / summary section")
    experience: list[ExperienceItem] = Field(
        default_factory=list,
        description="Work experience entries",
    )
    skills: list[str] = Field(
        default_factory=list,
        description="Listed skills",
    )
    career_goal: str = Field(
        ...,
        min_length=1,
        description="Target role or career objective",
    )

    @field_validator("skills")
    @classmethod
    def normalize_skills(cls, value: list[str]) -> list[str]:
        cleaned = [skill.strip() for skill in value if skill and skill.strip()]
        # Preserve order while removing duplicates (case-insensitive).
        seen: set[str] = set()
        unique: list[str] = []
        for skill in cleaned:
            key = skill.casefold()
            if key not in seen:
                seen.add(key)
                unique.append(skill)
        return unique


class ProfileAnalysis(BaseModel):
    """Structured analysis result from the Profile Analyzer Agent."""

    score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Overall profile strength score from 0 to 100",
    )
    strengths: list[str] = Field(
        ...,
        min_length=1,
        description="Clear professional strengths",
    )
    weaknesses: list[str] = Field(
        ...,
        min_length=1,
        description="Gaps or weak areas in the profile",
    )
    missing_skills: list[str] = Field(
        ...,
        description="Skills important for the career goal but not present",
    )
    recommendations: list[str] = Field(
        ...,
        min_length=1,
        description="Actionable improvement recommendations",
    )
