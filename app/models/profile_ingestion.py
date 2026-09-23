"""Profile ingestion and extraction contracts.

These models are not ``ProfileInput`` / ``ProfileAnalysis`` and they are not the
persisted ``CandidateProfile``. Nothing in this module writes to the database.

Three boundaries:

- ``ProfileIngestionRequest`` — what the caller supplies (heterogeneous sources).
- ``NormalizedProfileSource`` — text ready for extraction. This is also the
  extraction-agent input (``ProfileExtractionInput``). It has no user id.
- ``ExtractedCandidateProfile`` — facts extracted from one source. Not canonical
  state, and not reconciled across sources.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class _ContractModel(BaseModel):
    """Reject unknown fields so user identity and analysis fields cannot sneak in."""

    model_config = ConfigDict(extra="forbid")


class ProfileSourceType(StrEnum):
    """What a source represents, independent of how the bytes or text arrive."""

    CV = "cv"
    LINKEDIN = "linkedin"
    PORTFOLIO = "portfolio"
    USER_TEXT = "user_text"
    OTHER = "other"


def _normalize_skill_names(value: list[str]) -> list[str]:
    cleaned = [skill.strip() for skill in value if skill and skill.strip()]
    seen: set[str] = set()
    unique: list[str] = []
    for skill in cleaned:
        key = skill.casefold()
        if key not in seen:
            seen.add(key)
            unique.append(skill)
    return unique


def _blank_to_none(value: object) -> object:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return value


class TextProfileSource(_ContractModel):
    """Inline professional text. This is the only source kind executed today."""

    kind: Literal["text"] = "text"
    source_type: ProfileSourceType
    content: str = Field(..., min_length=1, description="Professional text to extract from.")

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("text source content must not be empty")
        return stripped


class FileProfileSource(_ContractModel):
    """A file locator. The file is not opened or parsed in this version."""

    kind: Literal["file"] = "file"
    source_type: ProfileSourceType
    path: str = Field(..., min_length=1, description="File path or filename. Not read yet.")

    @field_validator("path")
    @classmethod
    def path_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("file source path must not be empty")
        return stripped


class UrlProfileSource(_ContractModel):
    """A URL locator. The URL is not fetched in this version."""

    kind: Literal["url"] = "url"
    source_type: ProfileSourceType
    url: str = Field(..., min_length=1, description="Absolute http(s) URL. Not fetched yet.")

    @field_validator("url")
    @classmethod
    def url_must_be_absolute_http(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped.startswith(("http://", "https://")):
            raise ValueError("url must be an absolute http(s) URL")
        remainder = stripped.split("://", 1)[1].strip("/")
        if not remainder:
            raise ValueError("url must be an absolute http(s) URL")
        return stripped


ProfileSource = Annotated[
    TextProfileSource | FileProfileSource | UrlProfileSource,
    Field(discriminator="kind"),
]


class ProfileIngestionRequest(_ContractModel):
    """Caller-supplied profile sources for one ingestion request.

    User identity is not part of this contract. Authentication context, when it
    exists, stays in the application layer.
    """

    sources: list[ProfileSource] = Field(..., min_length=1)


class NormalizedProfileSource(_ContractModel):
    """One source reduced to text plus its semantic type.

    This is the extraction capability input (``ProfileExtractionInput``).
    Normalization of text does not add fields, so the same model is used for
    both. Do not add ``user_id`` here.
    """

    source_type: ProfileSourceType
    content: str = Field(..., min_length=1)


ProfileExtractionInput = NormalizedProfileSource


class ExtractedDate(_ContractModel):
    """Partial calendar date, no finer than the source actually stated.

    Persisted ``Experience`` rows use an exact ``datetime.date``. This model is
    not mapped onto those columns. A null month or day means the source did not
    state that part; it is not implied to be January or the first of the month.
    Approximate qualifiers (for example "circa") are not represented yet.
    """

    year: int = Field(..., ge=1900, le=2100)
    month: int | None = Field(default=None, ge=1, le=12)
    day: int | None = Field(default=None, ge=1, le=31)

    @model_validator(mode="after")
    def precision_matches_stated_parts(self) -> ExtractedDate:
        if self.day is not None and self.month is None:
            raise ValueError("day requires month when a day is stated")
        if self.month is not None and self.day is not None:
            try:
                date(self.year, self.month, self.day)
            except ValueError as exc:
                raise ValueError("day is not valid for the stated month and year") from exc
        return self


class ExtractedExperience(_ContractModel):
    """One role as stated in a single source. Every field may be omitted."""

    company_name: str | None = None
    title: str | None = None
    start_date: ExtractedDate | None = None
    end_date: ExtractedDate | None = None
    is_current: bool | None = Field(
        default=None,
        description=(
            "True when the source says the role is current or Present. "
            "Null when the source does not say. Not an invented end date."
        ),
    )
    description: str | None = None

    @field_validator("company_name", "title", "description", mode="before")
    @classmethod
    def blank_strings_are_missing(cls, value: object) -> object:
        return _blank_to_none(value)

    @model_validator(mode="after")
    def current_role_has_no_end_date(self) -> ExtractedExperience:
        if self.is_current is True and self.end_date is not None:
            raise ValueError("a current role must not include an end_date")
        return self


class ExtractedCandidateProfile(_ContractModel):
    """Factual professional fields extracted from a single source.

    This is not a canonical ``CandidateProfile``. It has no career goal, target
    title, match score, or recommendations. Absence of a fact here does not
    mean that fact should be deleted from a persisted profile.
    """

    current_title: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    experiences: list[ExtractedExperience] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)

    @field_validator("current_title", "location", "linkedin_url", mode="before")
    @classmethod
    def blank_strings_are_missing(cls, value: object) -> object:
        return _blank_to_none(value)

    @field_validator("skills")
    @classmethod
    def normalize_skills(cls, value: list[str]) -> list[str]:
        return _normalize_skill_names(value)


class ExtractedProfileSource(_ContractModel):
    """Extraction result for one source, with that source's type preserved."""

    source_type: ProfileSourceType
    profile: ExtractedCandidateProfile


class ProfileExtractionResult(_ContractModel):
    """Per-source extraction results for one request.

    Sources are not merged. This object is not persisted and is not canonical
    candidate state.
    """

    sources: list[ExtractedProfileSource]
