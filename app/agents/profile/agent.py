"""Profile Analyzer Agent – first Career AI agent."""

from __future__ import annotations

import logging

from app.models.profile import ProfileAnalysis, ProfileInput
from app.prompts.profile import PROFILE_ANALYZER_SYSTEM_PROMPT, build_profile_user_prompt
from app.tools.llm import StructuredLLM, StructuredLLMClient

logger = logging.getLogger(__name__)


class ProfileAnalyzerAgent:
    """Analyze a professional profile and return structured recommendations.

    Pass ``llm`` to inject a client. The CLI opens that client with
    ``create_llm_client`` and closes it when the command finishes. Omitting
    ``llm`` constructs OpenAI ``StructuredLLM`` for direct use; this agent
    does not choose a provider and does not close that fallback client.
    """

    def __init__(self, llm: StructuredLLMClient | None = None) -> None:
        self.llm = llm or StructuredLLM()

    async def analyze(self, profile: ProfileInput) -> ProfileAnalysis:
        """Run a full profile analysis against the user's career goal."""
        logger.info("Analyzing profile for %s (goal=%s)", profile.name, profile.career_goal)

        user_prompt = build_profile_user_prompt(
            profile.model_dump_json(indent=2),
        )

        analysis = await self.llm.complete_structured(
            system_prompt=PROFILE_ANALYZER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=ProfileAnalysis,
        )

        logger.info(
            "Profile analysis complete for %s: score=%s",
            profile.name,
            analysis.score,
        )
        return analysis
