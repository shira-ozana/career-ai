"""Deterministic profile ingestion flow for text sources.

Sequences normalization and per-source extraction. It does not reconcile
sources, apply canonical merge, or persist. A future workflow engine can call
these functions and the extraction agent without rewriting them.
"""

from __future__ import annotations

import logging

from app.agents.profile.extraction import ProfileExtractionAgent
from app.models.profile_ingestion import (
    ExtractedProfileSource,
    FileProfileSource,
    NormalizedProfileSource,
    ProfileExtractionResult,
    ProfileIngestionRequest,
    TextProfileSource,
    UrlProfileSource,
)

logger = logging.getLogger(__name__)


class UnsupportedProfileSourceError(Exception):
    """Raised when a source kind cannot be acquired yet.

    Text sources are executable. File and URL sources are valid request
    inputs, but reading a file or fetching a URL is intentionally not
    implemented. This error is raised before any extraction call.
    """

    def __init__(self, *, kind: str, source_type: str) -> None:
        self.kind = kind
        self.source_type = source_type
        super().__init__(
            f"Profile source kind {kind!r} is not supported yet "
            f"(source_type={source_type!r}). "
            "Only text sources can be normalized and extracted."
        )


def normalize_profile_sources(
    request: ProfileIngestionRequest,
) -> list[NormalizedProfileSource]:
    """Turn supported sources into extraction inputs.

    Fails the whole request on the first file or URL source. Earlier text
    sources in that request are not extracted, so a partial result is not
    returned as success.
    """
    normalized: list[NormalizedProfileSource] = []
    for source in request.sources:
        if isinstance(source, TextProfileSource):
            normalized.append(
                NormalizedProfileSource(
                    source_type=source.source_type,
                    content=source.content,
                )
            )
            continue
        if isinstance(source, (FileProfileSource, UrlProfileSource)):
            raise UnsupportedProfileSourceError(
                kind=str(source.kind),
                source_type=source.source_type.value,
            )
        msg = f"Unsupported profile source: {type(source).__name__}"
        raise TypeError(msg)
    return normalized


class ProfileIngestionFlow:
    """Normalize a request and extract each text source independently."""

    def __init__(self, agent: ProfileExtractionAgent | None = None) -> None:
        self.agent = agent or ProfileExtractionAgent()

    async def run(self, request: ProfileIngestionRequest) -> ProfileExtractionResult:
        """Return per-source extraction results. Does not merge or persist."""
        normalized = normalize_profile_sources(request)
        logger.info("Extracting %s text profile source(s)", len(normalized))

        extracted: list[ExtractedProfileSource] = []
        for source in normalized:
            profile = await self.agent.extract(source)
            extracted.append(
                ExtractedProfileSource(
                    source_type=source.source_type,
                    profile=profile,
                )
            )
        return ProfileExtractionResult(sources=extracted)
