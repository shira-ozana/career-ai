"""Per-source extraction flow tests. No network, API key, or database."""

import json
from pathlib import Path

import pytest

from app.agents.profile import ProfileAnalyzerAgent, ProfileExtractionAgent
from app.cli import main
from app.models.profile import ProfileAnalysis, ProfileInput
from app.models.profile_ingestion import (
    ExtractedCandidateProfile,
    ExtractedDate,
    ExtractedExperience,
    FileProfileSource,
    ProfileExtractionResult,
    ProfileIngestionRequest,
    ProfileSourceType,
    TextProfileSource,
    UrlProfileSource,
)
from app.tools.mock_llm import MockStructuredLLM
from app.workflows.profile_ingestion import (
    ProfileIngestionFlow,
    UnsupportedProfileSourceError,
    normalize_profile_sources,
)


def _request(
    *sources: TextProfileSource | FileProfileSource | UrlProfileSource,
) -> ProfileIngestionRequest:
    return ProfileIngestionRequest(sources=list(sources))


def _extracted_profile(title: str) -> ExtractedCandidateProfile:
    return ExtractedCandidateProfile(
        current_title=title,
        location="Tel Aviv",
        experiences=[
            ExtractedExperience(
                company_name="Example Corp",
                title=title,
                start_date=ExtractedDate(year=2023),
                is_current=True,
                description="Built FastAPI services.",
            )
        ],
        skills=["Python"],
    )


def test_normalize_text_sources_preserves_order_and_type() -> None:
    request = _request(
        TextProfileSource(
            source_type=ProfileSourceType.USER_TEXT,
            content="I am a Senior Software Engineer.",
        ),
        TextProfileSource(
            source_type=ProfileSourceType.PORTFOLIO,
            content="Built a multi-agent Career AI platform.",
        ),
    )

    normalized = normalize_profile_sources(request)

    assert [(source.source_type, source.content) for source in normalized] == [
        (ProfileSourceType.USER_TEXT, "I am a Senior Software Engineer."),
        (ProfileSourceType.PORTFOLIO, "Built a multi-agent Career AI platform."),
    ]
    assert "user_id" not in normalized[0].model_dump()


def test_normalize_file_source_is_unsupported() -> None:
    request = _request(
        FileProfileSource(source_type=ProfileSourceType.CV, path="cv.pdf"),
    )

    with pytest.raises(UnsupportedProfileSourceError) as exc_info:
        normalize_profile_sources(request)

    assert exc_info.value.kind == "file"
    assert exc_info.value.source_type == "cv"
    assert "not supported yet" in str(exc_info.value)


def test_normalize_url_source_is_unsupported() -> None:
    request = _request(
        UrlProfileSource(
            source_type=ProfileSourceType.LINKEDIN,
            url="https://www.linkedin.com/in/example",
        ),
    )

    with pytest.raises(UnsupportedProfileSourceError) as exc_info:
        normalize_profile_sources(request)

    assert exc_info.value.kind == "url"
    assert exc_info.value.source_type == "linkedin"


async def test_extraction_agent_returns_structured_output() -> None:
    expected = _extracted_profile("Senior Software Engineer")
    mock_llm = MockStructuredLLM(extraction_response=expected)
    agent = ProfileExtractionAgent(llm=mock_llm)
    source = normalize_profile_sources(
        _request(
            TextProfileSource(
                source_type=ProfileSourceType.CV,
                content="Senior Software Engineer at Example Corp since 2023.",
            )
        )
    )[0]

    result = await agent.extract(source)

    assert isinstance(result, ExtractedCandidateProfile)
    assert result == expected
    assert len(mock_llm.calls) == 1
    call = mock_llm.calls[0]
    assert call.response_model is ExtractedCandidateProfile
    assert "Senior Software Engineer at Example Corp since 2023." in call.user_prompt
    assert "Source type: cv" in call.user_prompt
    assert "user_id" not in call.user_prompt
    assert call.system_prompt


async def test_workflow_extracts_each_text_source_independently() -> None:
    expected = _extracted_profile("Senior Software Engineer")
    mock_llm = MockStructuredLLM(extraction_response=expected)
    flow = ProfileIngestionFlow(agent=ProfileExtractionAgent(llm=mock_llm))
    request = _request(
        TextProfileSource(
            source_type=ProfileSourceType.USER_TEXT,
            content="I am a Senior Software Engineer.",
        ),
        TextProfileSource(
            source_type=ProfileSourceType.PORTFOLIO,
            content="Built a multi-agent Career AI platform.",
        ),
    )

    result = await flow.run(request)

    assert isinstance(result, ProfileExtractionResult)
    assert [item.source_type for item in result.sources] == [
        ProfileSourceType.USER_TEXT,
        ProfileSourceType.PORTFOLIO,
    ]
    assert result.sources[0].profile == expected
    assert result.sources[1].profile == expected
    assert result.sources[0].profile is not result.sources[1].profile
    assert len(mock_llm.calls) == 2
    assert "I am a Senior Software Engineer." in mock_llm.calls[0].user_prompt
    assert "multi-agent Career AI platform" not in mock_llm.calls[0].user_prompt
    assert "Built a multi-agent Career AI platform." in mock_llm.calls[1].user_prompt
    assert "I am a Senior Software Engineer." not in mock_llm.calls[1].user_prompt
    assert mock_llm.calls[0].response_model is ExtractedCandidateProfile
    assert mock_llm.calls[1].response_model is ExtractedCandidateProfile


async def test_file_execution_fails_before_any_extraction() -> None:
    mock_llm = MockStructuredLLM()
    flow = ProfileIngestionFlow(agent=ProfileExtractionAgent(llm=mock_llm))
    request = _request(
        TextProfileSource(
            source_type=ProfileSourceType.USER_TEXT,
            content="I am a Senior Software Engineer.",
        ),
        FileProfileSource(source_type=ProfileSourceType.CV, path="missing-cv.pdf"),
    )

    with pytest.raises(UnsupportedProfileSourceError):
        await flow.run(request)

    assert mock_llm.calls == []


async def test_url_execution_fails_with_unsupported_error() -> None:
    mock_llm = MockStructuredLLM()
    flow = ProfileIngestionFlow(agent=ProfileExtractionAgent(llm=mock_llm))
    request = _request(
        UrlProfileSource(
            source_type=ProfileSourceType.PORTFOLIO,
            url="https://example.com/portfolio",
        ),
    )

    with pytest.raises(UnsupportedProfileSourceError) as exc_info:
        await flow.run(request)

    assert exc_info.value.kind == "url"
    assert mock_llm.calls == []


async def test_profile_analyzer_still_returns_analysis() -> None:
    profile = ProfileInput(
        name="Shira Ozana",
        headline="Python Developer",
        skills=["Python"],
        career_goal="AI Engineer",
    )
    analysis = ProfileAnalysis(
        score=80,
        strengths=["Python"],
        weaknesses=["Thin AI portfolio"],
        missing_skills=["RAG"],
        recommendations=["Add an AI project"],
    )
    mock_llm = MockStructuredLLM(response=analysis)
    agent = ProfileAnalyzerAgent(llm=mock_llm)

    result = await agent.analyze(profile)

    assert result == analysis
    assert mock_llm.calls[0].response_model is ProfileAnalysis


def test_extract_profile_cli_mock_prints_per_source_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["extract-profile", "examples/sample_profile_ingestion.json", "--mock"])

    assert exc_info.value.code == 0
    payload = json.loads(capsys.readouterr().out)
    assert [item["source_type"] for item in payload["sources"]] == ["user_text", "portfolio"]
    assert payload["sources"][0]["profile"]["skills"] == ["Python", "FastAPI", "PostgreSQL"]
    assert "career_goal" not in payload["sources"][0]["profile"]
    assert "score" not in payload["sources"][0]["profile"]


def test_extract_profile_cli_reports_unsupported_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    request_path = tmp_path / "request.json"
    request_path.write_text(
        json.dumps(
            {
                "sources": [
                    {"kind": "file", "source_type": "cv", "path": "cv.pdf"},
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit) as exc_info:
        main(["extract-profile", str(request_path), "--mock"])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "not supported yet" in captured.err
    assert captured.out == ""


def test_analyze_profile_command_remains_available(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["analyze-profile", "--help"])

    assert exc_info.value.code == 0
    assert "profile_path" in capsys.readouterr().out
