"""Deterministic LLM test double for agent unit tests.

Why a mock LLM exists
---------------------
``StructuredLLM`` calls the OpenAI Responses API, which requires network access,
API keys, and billable credits. Unit tests for agents should verify orchestration
logic (prompt assembly, schema handling, async flow) without hitting external
services.

How this enables cost-free testing
----------------------------------
``MockStructuredLLM`` implements the same ``complete_structured`` contract as
``StructuredLLM`` but returns a pre-built Pydantic model in-process. Inject it
via ``ProfileAnalyzerAgent(llm=MockStructuredLLM(...))`` or
``ProfileExtractionAgent(llm=MockStructuredLLM(...))`` to exercise the agent
path with zero API calls.

``response`` is returned for ``ProfileAnalysis``. ``extraction_response`` is
returned for ``ExtractedCandidateProfile``. Other schemas raise ``TypeError``.

Provider independence
---------------------
Agents depend on ``StructuredLLMClient`` (a Protocol), not on a vendor SDK.
The CLI injects ``StructuredLLM`` (OpenAI), ``CursorStructuredLLMClient``, or
this mock. Adding a backend means implementing ``complete_structured``; agent
code stays unchanged.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TypeVar

from pydantic import BaseModel

from app.models.profile import ProfileAnalysis
from app.models.profile_ingestion import (
    ExtractedCandidateProfile,
    ExtractedDate,
    ExtractedExperience,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

_DEFAULT_MOCK_ANALYSIS = ProfileAnalysis(
    score=72,
    strengths=[
        "Solid backend engineering foundation with Python and API experience",
        "Clear career direction toward AI engineering",
    ],
    weaknesses=[
        "Limited visible AI/ML project work in the profile",
        "Headline does not yet signal agentic-systems expertise",
    ],
    missing_skills=[
        "RAG pipelines",
        "Vector databases",
        "Agent orchestration frameworks",
    ],
    recommendations=[
        "Add a concrete AI side project to your experience section",
        "Rewrite the headline to mention agents, RAG, or LLM tooling",
        "Quantify impact in recent role descriptions with metrics",
    ],
)

_DEFAULT_MOCK_EXTRACTION = ExtractedCandidateProfile(
    current_title="Senior Software Engineer",
    location="Tel Aviv",
    linkedin_url=None,
    experiences=[
        ExtractedExperience(
            company_name="Example Corp",
            title="Senior Software Engineer",
            start_date=ExtractedDate(year=2023, month=1),
            end_date=None,
            is_current=True,
            description="Built and maintained FastAPI services.",
        )
    ],
    skills=["Python", "FastAPI", "PostgreSQL"],
)


@dataclass
class MockLLMCall:
    """Record of a single ``complete_structured`` invocation for test assertions."""

    system_prompt: str
    user_prompt: str
    response_model: type[BaseModel]
    model: str | None = None


@dataclass
class MockStructuredLLM:
    """In-memory structured LLM that never calls an external API."""

    response: ProfileAnalysis = field(
        default_factory=lambda: _DEFAULT_MOCK_ANALYSIS.model_copy(deep=True),
    )
    extraction_response: ExtractedCandidateProfile = field(
        default_factory=lambda: _DEFAULT_MOCK_EXTRACTION.model_copy(deep=True),
    )
    calls: list[MockLLMCall] = field(default_factory=list)

    async def complete_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        model: str | None = None,
    ) -> T:
        """Return a fixed structured model and record the call for tests."""
        logger.debug(
            "MockStructuredLLM.complete_structured schema=%s (no API call)",
            response_model.__name__,
        )

        self.calls.append(
            MockLLMCall(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_model=response_model,
                model=model,
            ),
        )

        if issubclass(response_model, ProfileAnalysis):
            return self.response.model_copy(deep=True)  # type: ignore[return-value]
        if issubclass(response_model, ExtractedCandidateProfile):
            return self.extraction_response.model_copy(deep=True)  # type: ignore[return-value]

        msg = (
            "MockStructuredLLM does not support "
            f"{response_model.__name__}; "
            "expected ProfileAnalysis or ExtractedCandidateProfile"
        )
        raise TypeError(msg)
