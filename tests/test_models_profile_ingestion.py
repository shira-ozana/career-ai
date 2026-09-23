"""Tests for profile ingestion and extraction contracts."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models.profile import ProfileInput
from app.models.profile_ingestion import (
    ExtractedCandidateProfile,
    ExtractedDate,
    ExtractedExperience,
    FileProfileSource,
    NormalizedProfileSource,
    ProfileExtractionInput,
    ProfileIngestionRequest,
    ProfileSourceType,
    TextProfileSource,
    UrlProfileSource,
)


def _text_source(source_type: str, content: str) -> dict[str, str]:
    return {"kind": "text", "source_type": source_type, "content": content}


def test_text_ingestion_request_accepts_one_source() -> None:
    request = ProfileIngestionRequest.model_validate(
        {"sources": [_text_source("cv", "Senior Software Engineer at Example Corp.")]}
    )

    assert len(request.sources) == 1
    source = request.sources[0]
    assert isinstance(source, TextProfileSource)
    assert source.source_type is ProfileSourceType.CV
    assert source.content == "Senior Software Engineer at Example Corp."


def test_multiple_text_sources_keep_distinct_types() -> None:
    request = ProfileIngestionRequest.model_validate(
        {
            "sources": [
                _text_source("user_text", "I am a Senior Software Engineer."),
                _text_source("portfolio", "Built a multi-agent Career AI platform."),
            ]
        }
    )

    assert [source.source_type for source in request.sources] == [
        ProfileSourceType.USER_TEXT,
        ProfileSourceType.PORTFOLIO,
    ]


def test_sample_ingestion_fixture_is_valid() -> None:
    raw = json.loads(
        Path("examples/sample_profile_ingestion.json").read_text(encoding="utf-8")
    )
    request = ProfileIngestionRequest.model_validate(raw)

    assert len(request.sources) == 2


def test_empty_source_list_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ProfileIngestionRequest.model_validate({"sources": []})


def test_blank_text_source_is_rejected() -> None:
    with pytest.raises(ValidationError):
        TextProfileSource(source_type=ProfileSourceType.USER_TEXT, content="   ")


def test_unknown_source_type_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ProfileIngestionRequest.model_validate(
            {"sources": [_text_source("resume", "Senior engineer.")]}
        )


def test_unknown_source_kind_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ProfileIngestionRequest.model_validate(
            {
                "sources": [
                    {
                        "kind": "pdf",
                        "source_type": "cv",
                        "content": "Senior engineer.",
                    }
                ]
            }
        )


def test_file_and_url_sources_are_representable() -> None:
    request = ProfileIngestionRequest.model_validate(
        {
            "sources": [
                {"kind": "file", "source_type": "cv", "path": "  cv.pdf  "},
                {
                    "kind": "url",
                    "source_type": "linkedin",
                    "url": "https://www.linkedin.com/in/example",
                },
            ]
        }
    )

    file_source, url_source = request.sources
    assert isinstance(file_source, FileProfileSource)
    assert file_source.path == "cv.pdf"
    assert isinstance(url_source, UrlProfileSource)
    assert url_source.source_type is ProfileSourceType.LINKEDIN


def test_url_without_http_scheme_is_rejected() -> None:
    with pytest.raises(ValidationError):
        UrlProfileSource(
            source_type=ProfileSourceType.PORTFOLIO,
            url="example.com/work",
        )


def test_empty_file_path_is_rejected() -> None:
    with pytest.raises(ValidationError):
        FileProfileSource(source_type=ProfileSourceType.CV, path="  ")


def test_user_id_is_not_part_of_the_ingestion_or_extraction_contract() -> None:
    assert "user_id" not in ProfileIngestionRequest.model_fields
    assert "user_id" not in NormalizedProfileSource.model_fields
    assert ProfileExtractionInput is NormalizedProfileSource

    with pytest.raises(ValidationError):
        ProfileIngestionRequest.model_validate(
            {
                "user_id": "user-1",
                "sources": [_text_source("user_text", "I am an engineer.")],
            }
        )


def test_extracted_profile_omits_analysis_and_search_fields() -> None:
    forbidden = {
        "career_goal",
        "target_title",
        "match_score",
        "profile_score",
        "recommendations",
        "score",
    }
    assert forbidden.isdisjoint(ExtractedCandidateProfile.model_fields)

    with pytest.raises(ValidationError):
        ExtractedCandidateProfile.model_validate(
            {"current_title": "Engineer", "career_goal": "Staff engineer"}
        )


def test_extracted_profile_allows_partial_facts_and_normalizes_skills() -> None:
    profile = ExtractedCandidateProfile(
        current_title="  ",
        skills=["Python", " python ", "FastAPI", ""],
    )

    assert profile.current_title is None
    assert profile.location is None
    assert profile.experiences == []
    assert profile.skills == ["Python", "FastAPI"]


def test_extracted_date_preserves_partial_precision() -> None:
    year_only = ExtractedDate(year=2023)
    month_precision = ExtractedDate(year=2023, month=1)

    assert year_only.month is None
    assert year_only.day is None
    assert month_precision.day is None


def test_extracted_date_rejects_day_without_month() -> None:
    with pytest.raises(ValidationError):
        ExtractedDate(year=2023, day=1)


def test_extracted_date_rejects_impossible_calendar_day() -> None:
    with pytest.raises(ValidationError):
        ExtractedDate(year=2023, month=2, day=31)


def test_current_experience_rejects_an_invented_end_date() -> None:
    with pytest.raises(ValidationError):
        ExtractedExperience(
            company_name="Example Corp",
            title="Engineer",
            start_date=ExtractedDate(year=2023),
            end_date=ExtractedDate(year=2024),
            is_current=True,
        )


def test_current_experience_allows_open_end() -> None:
    experience = ExtractedExperience(
        company_name="Example Corp",
        title="Engineer",
        start_date=ExtractedDate(year=2023, month=1),
        is_current=True,
    )

    assert experience.end_date is None
    assert experience.is_current is True


def test_analyzer_sample_profile_is_still_profile_input() -> None:
    raw = json.loads(Path("examples/sample_profile.json").read_text(encoding="utf-8"))
    profile = ProfileInput.model_validate(raw)

    assert profile.name
    assert profile.career_goal
