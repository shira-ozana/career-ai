"""Prompt templates for agents."""

from app.prompts.profile import PROFILE_ANALYZER_SYSTEM_PROMPT, build_profile_user_prompt
from app.prompts.profile_extraction import (
    PROFILE_EXTRACTION_SYSTEM_PROMPT,
    build_profile_extraction_user_prompt,
)

__all__ = [
    "PROFILE_ANALYZER_SYSTEM_PROMPT",
    "PROFILE_EXTRACTION_SYSTEM_PROMPT",
    "build_profile_extraction_user_prompt",
    "build_profile_user_prompt",
]
