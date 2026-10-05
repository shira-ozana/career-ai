"""Structured LLM providers and connection lifecycle.

``StructuredLLMClient`` is the agent-facing contract. ``LLMProvider`` is the
closed set of backends. ``create_llm_client`` is the only place that opens a
backend for the CLI and closes resources this layer owns.

``CursorStructuredLLMClient`` is imported only when the Cursor provider is
selected, so the OpenAI and mock paths do not load ``cursor_sdk``.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from enum import StrEnum
from typing import Protocol, TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.tools.mock_llm import MockStructuredLLM

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMProvider(StrEnum):
    """Supported structured-LLM backends.

    Member order is the ``extract-profile --provider`` choice order. OpenAI is
    the default. Parse CLI and other external strings with ``parse`` before
    they enter internal interfaces.
    """

    OPENAI = "openai"
    CURSOR = "cursor"
    MOCK = "mock"

    @classmethod
    def parse(cls, value: str) -> LLMProvider:
        """Validate a provider id from an application boundary."""
        try:
            return cls(value)
        except ValueError:
            supported = ", ".join(provider.value for provider in cls)
            msg = f"Unsupported LLM provider: {value!r}. Choose one of: {supported}."
            raise ValueError(msg) from None


class StructuredLLMClient(Protocol):
    """Contract for structured LLM backends.

    Agents depend on this protocol rather than a concrete SDK. ``StructuredLLM``
    (OpenAI), ``CursorStructuredLLMClient``, and ``MockStructuredLLM`` all
    implement it. Agent code does not import a provider SDK.
    """

    async def complete_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        model: str | None = None,
    ) -> T: ...


class StructuredLLM:
    """Generate Pydantic-validated structured responses via OpenAI."""

    def __init__(
        self,
        settings: Settings | None = None,
        client: AsyncOpenAI | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._owns_client = client is None
        self.client = client or AsyncOpenAI(api_key=self.settings.require_openai_api_key())

    async def aclose(self) -> None:
        """Close the OpenAI client when this object created it.

        An injected client stays open. The caller that created it owns cleanup.
        """
        if not self._owns_client:
            return
        self._owns_client = False
        await self.client.close()

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


@asynccontextmanager
async def create_llm_client(
    provider: LLMProvider,
    settings: Settings,
) -> AsyncIterator[StructuredLLMClient]:
    """Yield a structured LLM client and close resources this layer owns.

    Cleanup runs when the block finishes, raises, or is cancelled. This
    function does not close an OpenAI client injected into ``StructuredLLM``,
    or a Cursor text completion injected into ``CursorStructuredLLMClient``.
    Callers that build those objects keep ownership.
    """
    if not isinstance(provider, LLMProvider):
        msg = (
            "provider must be an LLMProvider. "
            "Parse external values with LLMProvider.parse before creating a client."
        )
        raise TypeError(msg)

    if provider is LLMProvider.MOCK:
        logger.info("Using MockStructuredLLM (no external API)")
        yield MockStructuredLLM()
        return

    if provider is LLMProvider.OPENAI:
        logger.info("Using OpenAI StructuredLLM")
        llm = StructuredLLM(settings=settings)
        try:
            yield llm
        finally:
            await llm.aclose()
        return

    if provider is LLMProvider.CURSOR:
        # Imported here so OpenAI and mock paths do not load cursor_sdk.
        from app.tools.cursor_llm import CursorStructuredLLMClient

        logger.info(
            "Using CursorStructuredLLMClient model=%s",
            settings.cursor_model_name(),
        )
        cursor_llm = CursorStructuredLLMClient(settings=settings)
        async with cursor_llm:
            yield cursor_llm
        return

    msg = f"Unsupported LLM provider: {provider.value}"
    raise ValueError(msg)
