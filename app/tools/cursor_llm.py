"""Cursor SDK adapter for structured profile extraction.

``cursor-sdk`` is an agent SDK. It does not offer OpenAI-style structured
outputs or a Pydantic ``text_format``. This module asks a local agent for JSON
text, then validates that text with Pydantic before returning it.

The agent is local because ``tools=[]`` (no built-in tools) is a local-only
option. The workspace is an empty temporary directory, not the Career AI
repository. Each ``complete_structured`` call uses ``AsyncAgent.prompt``, which
creates an agent, waits for one run, and disposes it. Sources do not share a
conversation.
"""

from __future__ import annotations

import json
import logging
import re
import tempfile
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel, ValidationError

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Empty allowlist: the SDK offers no built-in tools, so the model can only
# answer with text. Local agents only. See cursor-sdk AgentOptions.tools.
_NO_BUILTIN_TOOLS: tuple[str, ...] = ()

_WRAPPED_JSON_FENCE = re.compile(
    r"\A```([A-Za-z0-9_+-]*)[ \t]*\n(.*)\n```[ \t]*\Z",
    re.DOTALL,
)


class CursorStructuredOutputError(Exception):
    """Cursor text was empty, fenced incorrectly, or not valid JSON."""


class CursorRunError(Exception):
    """A Cursor run started and ended with a status other than finished."""


class CursorTextCompletion(Protocol):
    """SDK boundary: one prompt in, final assistant text out."""

    async def complete(self, *, prompt: str, model: str, api_key: str) -> str: ...


def build_cursor_structured_prompt(
    *,
    system_prompt: str,
    user_prompt: str,
    response_model: type[BaseModel],
) -> str:
    """Combine the agent prompts with an explicit JSON schema instruction."""
    schema = json.dumps(response_model.model_json_schema(), indent=2)
    return (
        f"{system_prompt.strip()}\n\n"
        f"{user_prompt.strip()}\n\n"
        "Output contract:\n"
        "- Respond with one JSON value and no other text.\n"
        "- The JSON value must validate against the schema below.\n"
        "- Do not wrap the JSON in markdown fences.\n"
        "- Do not add fields that are not in the schema.\n\n"
        f"JSON Schema:\n{schema}\n"
    )


def json_text_from_cursor_response(raw: str) -> str:
    """Return JSON text from a Cursor reply.

    Raw JSON is accepted as-is. A single markdown fence wrapping the whole
    reply is also accepted when the info tag is empty or ``json``. Prose,
    extra fences, and any other fence language are rejected.
    """
    text = raw.strip()
    if not text:
        raise CursorStructuredOutputError("Cursor returned an empty response")

    if text.startswith("```"):
        match = _WRAPPED_JSON_FENCE.match(text)
        if match is None:
            msg = "Cursor response was not a single markdown fence wrapping JSON"
            raise CursorStructuredOutputError(msg)
        language = match.group(1).lower()
        if language not in {"", "json"}:
            msg = "Cursor response fence must be unmarked or json"
            raise CursorStructuredOutputError(msg)
        body = match.group(2).strip()
        if not body or "```" in body:
            msg = "Cursor response fence did not contain a single JSON document"
            raise CursorStructuredOutputError(msg)
        return body

    if "```" in text:
        msg = "Cursor response mixed prose or extra fences with JSON"
        raise CursorStructuredOutputError(msg)
    return text


def parse_cursor_structured_output[ModelT: BaseModel](
    raw: str,
    response_model: type[ModelT],
) -> ModelT:
    """Validate Cursor text into ``response_model``. Invalid JSON is not coerced."""
    payload = json_text_from_cursor_response(raw)
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as exc:
        msg = "Cursor response was not valid JSON"
        raise CursorStructuredOutputError(msg) from exc
    return response_model.model_validate(parsed)


def build_cursor_agent_options(*, model: str, api_key: str, cwd: str) -> Any:
    """Local, text-only agent options. Does not attach the Career AI repo."""
    from cursor_sdk import AgentOptions, LocalAgentOptions

    return AgentOptions(
        model=model,
        api_key=api_key,
        name="career-ai-profile-extraction",
        local=LocalAgentOptions(cwd=cwd),
        tools=_NO_BUILTIN_TOOLS,
    )


async def launch_cursor_client(workspace: str) -> Any:
    """Start a bridge whose workspace is the empty extraction directory."""
    from cursor_sdk import AsyncClient

    return await AsyncClient.launch_bridge(
        workspace=workspace,
        allow_api_key_env_fallback=False,
    )


async def prompt_cursor(*, client: Any, prompt: str, options: Any) -> Any:
    """One-shot prompt. The SDK creates the agent, waits, and disposes it."""
    from cursor_sdk import AsyncAgent

    return await AsyncAgent.prompt(prompt, options, client=client)


class CursorSdkTextCompletion:
    """Async Cursor client held for one CLI command.

    The bridge stays open across extraction calls. Each call still uses a new
    one-shot agent, so conversation state is not reused.
    """

    def __init__(self) -> None:
        self._workspace: tempfile.TemporaryDirectory[str] | None = None
        self._client: Any = None

    async def open(self) -> None:
        if self._client is not None:
            return
        self._workspace = tempfile.TemporaryDirectory(prefix="career-ai-cursor-")
        try:
            self._client = await launch_cursor_client(self._workspace.name)
        except Exception:
            self._workspace.cleanup()
            self._workspace = None
            raise

    async def close(self) -> None:
        client = self._client
        self._client = None
        try:
            if client is not None:
                await client.aclose()
        finally:
            if self._workspace is not None:
                self._workspace.cleanup()
                self._workspace = None

    async def complete(self, *, prompt: str, model: str, api_key: str) -> str:
        if self._client is None or self._workspace is None:
            msg = "Cursor SDK client is not open"
            raise RuntimeError(msg)

        options = build_cursor_agent_options(
            model=model,
            api_key=api_key,
            cwd=self._workspace.name,
        )
        try:
            result = await prompt_cursor(client=self._client, prompt=prompt, options=options)
        except Exception as exc:
            _log_cursor_startup_failure(exc, model=model)
            raise

        logger.info(
            "Cursor run ended run_id=%s status=%s model=%s",
            getattr(result, "id", ""),
            result.status,
            model,
        )
        if result.status != "finished":
            msg = f"Cursor run ended with status {result.status!r}"
            raise CursorRunError(msg)
        text = result.result or ""
        if not text.strip():
            raise CursorStructuredOutputError("Cursor returned an empty response")
        return text


def _log_cursor_startup_failure(exc: Exception, *, model: str) -> None:
    """Log a startup failure without the API key or the prompt."""
    from cursor_sdk import CursorAgentError

    if isinstance(exc, CursorAgentError):
        logger.error(
            "Cursor run did not start model=%s code=%s retryable=%s request_id=%s",
            model,
            exc.code,
            exc.is_retryable,
            exc.request_id,
        )
        return
    logger.error("Cursor run did not start model=%s", model)


class CursorStructuredLLMClient:
    """``StructuredLLMClient`` backed by the Cursor Python SDK."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        text_completion: CursorTextCompletion | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._api_key = self.settings.require_cursor_api_key()
        self._text_completion = text_completion
        self._sdk: CursorSdkTextCompletion | None = None

    async def __aenter__(self) -> CursorStructuredLLMClient:
        if self._text_completion is None:
            sdk = CursorSdkTextCompletion()
            try:
                await sdk.open()
            except Exception:
                await sdk.close()
                raise
            self._sdk = sdk
            self._text_completion = sdk
        return self

    async def __aexit__(self, *exc: object) -> None:
        sdk = self._sdk
        self._sdk = None
        if sdk is not None:
            self._text_completion = None
            await sdk.close()

    async def complete_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        model: str | None = None,
    ) -> T:
        if self._text_completion is None:
            msg = (
                "CursorStructuredLLMClient is not open. "
                "Use it as an async context manager."
            )
            raise RuntimeError(msg)

        selected_model = model or self.settings.cursor_model_name()
        logger.info(
            "Requesting Cursor structured completion model=%s schema=%s",
            selected_model,
            response_model.__name__,
        )
        prompt = build_cursor_structured_prompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=response_model,
        )
        text = await self._text_completion.complete(
            prompt=prompt,
            model=selected_model,
            api_key=self._api_key,
        )
        try:
            parsed = parse_cursor_structured_output(text, response_model)
        except ValidationError:
            logger.error(
                "Cursor JSON did not match schema=%s",
                response_model.__name__,
            )
            raise
        logger.info(
            "Cursor structured completion validated schema=%s",
            response_model.__name__,
        )
        return parsed
