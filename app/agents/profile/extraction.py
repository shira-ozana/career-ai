"""Profile Extraction Agent.

Extracts factual fields from one normalized source. It does not orchestrate
multiple sources, reconcile conflicts, or write a canonical profile.
"""

from __future__ import annotations

import logging

from app.models.profile_ingestion import ExtractedCandidateProfile, NormalizedProfileSource
from app.prompts.profile_extraction import (
    PROFILE_EXTRACTION_SYSTEM_PROMPT,
    build_profile_extraction_user_prompt,
)
from app.tools.llm import StructuredLLM, StructuredLLMClient

logger = logging.getLogger(__name__)


class ProfileExtractionAgent:
    """Extract structured facts from one professional source.

    ``source`` is the extraction input: source type and content only.
    User identity is not accepted and must not be added to the prompt.
    """

    def __init__(self, llm: StructuredLLMClient | None = None) -> None:
        self.llm = llm or StructuredLLM()

    async def extract(self, source: NormalizedProfileSource) -> ExtractedCandidateProfile:
        """Extract facts from a single normalized source."""
        logger.info("Extracting profile facts from source_type=%s", source.source_type)

        extracted = await self.llm.complete_structured(
            system_prompt=PROFILE_EXTRACTION_SYSTEM_PROMPT,
            user_prompt=build_profile_extraction_user_prompt(
                source_type=source.source_type.value,
                content=source.content,
            ),
            response_model=ExtractedCandidateProfile,
        )

        logger.info("Extracted profile facts from source_type=%s", source.source_type)
        return extracted
