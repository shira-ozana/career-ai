"""Unit tests for ProfileInput / ProfileAnalysis models."""

import pytest
from pydantic import ValidationError

from app.models.profile import ExperienceItem, ProfileAnalysis, ProfileInput


def test_profile_input_normalizes_and_dedupes_skills() -> None:
    profile = ProfileInput(
        name="Shira Ozana",
        headline="Backend Developer",
        about="Building reliable APIs",
        experience=[
            ExperienceItem(
                title="Software Engineer",
                company="Example Corp",
                duration="2023 – Present",
                description="Built FastAPI services",
            )
        ],
        skills=["Python", " python ", "FastAPI", "PYTHON"],
        career_goal="AI Engineer working on agentic systems",
    )

    assert profile.skills == ["Python", "FastAPI"]


def test_profile_analysis_score_bounds() -> None:
    with pytest.raises(ValidationError):
        ProfileAnalysis(
            score=120,
            strengths=["Python"],
            weaknesses=["Weak headline"],
            missing_skills=["RAG"],
            recommendations=["Improve headline"],
        )


def test_profile_analysis_accepts_valid_payload() -> None:
    analysis = ProfileAnalysis(
        score=71,
        strengths=["Python", "Backend"],
        weaknesses=["Limited AI project visibility"],
        missing_skills=["RAG", "MCP", "AI Agents"],
        recommendations=["Improve headline", "Add measurable achievements"],
    )

    assert analysis.score == 71
    assert "RAG" in analysis.missing_skills
