"""Unit tests for ProfileAnalyzerAgent using MockStructuredLLM."""

from __future__ import annotations

import pytest

from app.agents.profile import ProfileAnalyzerAgent
from app.models.profile import ExperienceItem, ProfileAnalysis, ProfileInput
from app.tools.mock_llm import MockStructuredLLM


@pytest.fixture
def sample_profile() -> ProfileInput:
    return ProfileInput(
        name="Shira Ozana",
        headline="Python Developer | Backend Engineer",
        about="Backend engineer building APIs and data services.",
        experience=[
            ExperienceItem(
                title="Software Engineer",
                company="Example Corp",
                duration="2023 – Present",
                description="Built FastAPI microservices.",
            ),
        ],
        skills=["Python", "FastAPI", "PostgreSQL"],
        career_goal="Transition into an AI Engineer role focused on agentic systems",
    )


@pytest.fixture
def custom_analysis() -> ProfileAnalysis:
    return ProfileAnalysis(
        score=85,
        strengths=["Strong Python backend experience"],
        weaknesses=["Limited AI/ML project visibility"],
        missing_skills=["LangGraph", "Vector databases"],
        recommendations=[
            "Add an AI side project to your experience section",
            "Highlight MCP integrations in your about section",
        ],
    )


async def test_agent_analyzes_profile_without_openai(
    sample_profile: ProfileInput,
    custom_analysis: ProfileAnalysis,
) -> None:
    """Agent runs end-to-end with injected mock — no OpenAI client involved."""
    mock_llm = MockStructuredLLM(response=custom_analysis)
    agent = ProfileAnalyzerAgent(llm=mock_llm)

    result = await agent.analyze(sample_profile)

    assert isinstance(result, ProfileAnalysis)
    assert len(mock_llm.calls) == 1


async def test_agent_returns_valid_profile_analysis(
    sample_profile: ProfileInput,
    custom_analysis: ProfileAnalysis,
) -> None:
    """Returned object satisfies the ProfileAnalysis schema."""
    mock_llm = MockStructuredLLM(response=custom_analysis)
    agent = ProfileAnalyzerAgent(llm=mock_llm)

    result = await agent.analyze(sample_profile)

    assert result.score == custom_analysis.score
    assert result.strengths == custom_analysis.strengths
    assert result.weaknesses == custom_analysis.weaknesses
    assert result.missing_skills == custom_analysis.missing_skills
    assert result.recommendations == custom_analysis.recommendations


async def test_agent_exposes_score_and_recommendations(
    sample_profile: ProfileInput,
    custom_analysis: ProfileAnalysis,
) -> None:
    """Score and recommendations from the mock are directly accessible."""
    mock_llm = MockStructuredLLM(response=custom_analysis)
    agent = ProfileAnalyzerAgent(llm=mock_llm)

    result = await agent.analyze(sample_profile)

    assert result.score == 85
    assert len(result.recommendations) == 2
    assert "AI side project" in result.recommendations[0]


async def test_agent_async_flow_records_llm_call(
    sample_profile: ProfileInput,
) -> None:
    """Async analyze forwards prompts and schema to the injected LLM client."""
    mock_llm = MockStructuredLLM()
    agent = ProfileAnalyzerAgent(llm=mock_llm)

    await agent.analyze(sample_profile)

    call = mock_llm.calls[0]
    assert call.response_model is ProfileAnalysis
    assert sample_profile.name in call.user_prompt
    assert call.system_prompt  # non-empty system prompt forwarded
