"""Tests for ProfileAnalyzerAgent with a mocked LLM client."""

from __future__ import annotations

from typing import Any

import pytest

from app.agents.profile import ProfileAnalyzerAgent
from app.models.profile import ProfileAnalysis, ProfileInput
from app.tools.llm import StructuredLLM


class FakeStructuredLLM(StructuredLLM):
    """Test double that skips OpenAI and returns a fixed analysis."""

    def __init__(self, analysis: ProfileAnalysis) -> None:
        # Bypass Settings / OpenAI client construction.
        self._analysis = analysis
        self.calls: list[dict[str, Any]] = []

    async def complete_structured(self, **kwargs: Any) -> ProfileAnalysis:
        self.calls.append(kwargs)
        return self._analysis


@pytest.fixture
def sample_profile() -> ProfileInput:
    return ProfileInput(
        name="Shira Ozana",
        headline="Python Developer | Backend",
        about="Experienced backend engineer exploring AI systems.",
        experience=[],
        skills=["Python", "FastAPI", "PostgreSQL"],
        career_goal="Become an AI Engineer focused on agents and RAG",
    )


@pytest.mark.asyncio
async def test_profile_agent_returns_structured_analysis(
    sample_profile: ProfileInput,
) -> None:
    expected = ProfileAnalysis(
        score=71,
        strengths=["Python", "Backend"],
        weaknesses=["Limited AI Agents portfolio evidence"],
        missing_skills=["RAG", "MCP", "AI Agents"],
        recommendations=["Improve headline", "Add measurable achievements"],
    )
    fake_llm = FakeStructuredLLM(expected)
    agent = ProfileAnalyzerAgent(llm=fake_llm)

    result = await agent.analyze(sample_profile)

    assert result == expected
    assert len(fake_llm.calls) == 1
    assert fake_llm.calls[0]["response_model"] is ProfileAnalysis
    assert "Shira Ozana" in fake_llm.calls[0]["user_prompt"]
