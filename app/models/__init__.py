"""Pydantic contracts for agent capabilities and profile ingestion.

Analyzer models (``ProfileInput`` / ``ProfileAnalysis``) are not the ingestion
contract and are not SQLAlchemy persistence models. Ingestion and extraction
models live in ``app.models.profile_ingestion`` and are not canonical
``CandidateProfile`` state.
"""

from app.models.profile import ExperienceItem, ProfileAnalysis, ProfileInput
from app.models.profile_ingestion import (
    ExtractedCandidateProfile,
    ExtractedDate,
    ExtractedExperience,
    ExtractedProfileSource,
    FileProfileSource,
    NormalizedProfileSource,
    ProfileExtractionInput,
    ProfileExtractionResult,
    ProfileIngestionRequest,
    ProfileSource,
    ProfileSourceType,
    TextProfileSource,
    UrlProfileSource,
)

__all__ = [
    "ExperienceItem",
    "ExtractedCandidateProfile",
    "ExtractedDate",
    "ExtractedExperience",
    "ExtractedProfileSource",
    "FileProfileSource",
    "NormalizedProfileSource",
    "ProfileAnalysis",
    "ProfileExtractionInput",
    "ProfileExtractionResult",
    "ProfileIngestionRequest",
    "ProfileInput",
    "ProfileSource",
    "ProfileSourceType",
    "TextProfileSource",
    "UrlProfileSource",
]
