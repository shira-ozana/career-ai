"""Thin OpenAI client wrapper for structured outputs."""

from __future__ import annotations

import logging
from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class StructuredLLM:
    """Generate Pydantic-validated structured responses via OpenAI."""

    def __init__(
        self,
        settings: Settings | None = None,
        client: AsyncOpenAI | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.client = client or AsyncOpenAI(api_key=self.settings.require_openai_api_key())

    async def complete_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        model: str | None = None,
    ) -> T:
        """Call OpenAI with Structured Outputs and parse into a Pydantic model."""
        selected_model = model or self.settings.openai_model
        logger.info(
            "Requesting structured completion model=%s schema=%s",
            selected_model,
            response_model.__name__,
        )

        response = await self.client.responses.parse(
            model=selected_model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text_format=response_model,
        )

        parsed = response.output_parsed
        if parsed is None:
            msg = "OpenAI returned an empty structured response"
            raise RuntimeError(msg)
        return parsed
