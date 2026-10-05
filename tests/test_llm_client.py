"""Connection lifecycle tests. No network and no live provider calls."""

from __future__ import annotations

import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.cli import main
from app.config import Settings
from app.models.profile import ProfileAnalysis
from app.tools.cursor_llm import CursorStructuredLLMClient
from app.tools.llm import LLMProvider, StructuredLLM, create_llm_client
from app.tools.mock_llm import MockStructuredLLM

_FAKE_OPENAI_KEY = "sk-test"
_FAKE_CURSOR_KEY = "cursor-test-key"


def _settings(**overrides: str) -> Settings:
    values: dict[str, str] = {
        "openai_api_key": _FAKE_OPENAI_KEY,
        "openai_model": "gpt-4o-mini",
        "cursor_api_key": _FAKE_CURSOR_KEY,
        "cursor_model": "composer-2.5",
        "log_level": "WARNING",
    }
    values.update(overrides)
    return Settings(**values)


class FakeAsyncOpenAI:
    """In-memory stand-in for the OpenAI HTTP client."""

    def __init__(self, *, api_key: str) -> None:
        self.api_key = api_key
        self.close_calls = 0

    async def close(self) -> None:
        self.close_calls += 1


def _analysis() -> ProfileAnalysis:
    return ProfileAnalysis(
        score=80,
        strengths=["Python"],
        weaknesses=["Thin AI portfolio"],
        missing_skills=["RAG"],
        recommendations=["Add an AI project"],
    )


def test_cursor_adapter_import_stays_inside_the_factory() -> None:
    source = Path("app/tools/llm.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    for node in module.body:
        if isinstance(node, ast.Import):
            imported = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            imported = [node.module or ""]
        else:
            continue
        assert all("cursor" not in name for name in imported)

    factory = next(
        node
        for node in module.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "create_llm_client"
    )
    cursor_imports = [
        node
        for node in ast.walk(factory)
        if isinstance(node, ast.ImportFrom) and node.module == "app.tools.cursor_llm"
    ]
    assert len(cursor_imports) == 1
    assert "import cursor_sdk" not in source
    assert "from cursor_sdk" not in source
    cli_source = Path("app/cli.py").read_text(encoding="utf-8")
    assert "cursor_llm" not in cli_source
    assert "CursorStructuredLLMClient" not in cli_source


def test_provider_parse_is_the_external_boundary() -> None:
    assert LLMProvider.parse("openai") is LLMProvider.OPENAI
    assert LLMProvider.OPENAI == "openai"


async def test_factory_rejects_raw_provider_strings() -> None:
    with pytest.raises(TypeError, match="LLMProvider.parse"):
        async with create_llm_client("openai", _settings()):  # type: ignore[arg-type]
            return None


async def test_mock_factory_does_not_open_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_openai(**kwargs: object) -> None:
        raise AssertionError(kwargs)

    monkeypatch.setattr("app.tools.llm.AsyncOpenAI", fail_openai)

    async with create_llm_client(LLMProvider.MOCK, _settings()) as llm:
        assert isinstance(llm, MockStructuredLLM)


async def test_openai_factory_closes_owned_client_on_success(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    created: list[FakeAsyncOpenAI] = []

    def build(*, api_key: str) -> FakeAsyncOpenAI:
        client = FakeAsyncOpenAI(api_key=api_key)
        created.append(client)
        return client

    monkeypatch.setattr("app.tools.llm.AsyncOpenAI", build)

    with caplog.at_level("INFO"):
        async with create_llm_client(LLMProvider.OPENAI, _settings()) as llm:
            assert isinstance(llm, StructuredLLM)
            assert created[0].close_calls == 0

    assert created[0].close_calls == 1
    assert created[0].api_key == _FAKE_OPENAI_KEY
    assert _FAKE_OPENAI_KEY not in caplog.text
    assert _FAKE_CURSOR_KEY not in caplog.text


async def test_openai_factory_closes_owned_client_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: list[FakeAsyncOpenAI] = []

    def build(*, api_key: str) -> FakeAsyncOpenAI:
        client = FakeAsyncOpenAI(api_key=api_key)
        created.append(client)
        return client

    monkeypatch.setattr("app.tools.llm.AsyncOpenAI", build)

    with pytest.raises(RuntimeError, match="boom"):
        async with create_llm_client(LLMProvider.OPENAI, _settings()):
            raise RuntimeError("boom")

    assert created[0].close_calls == 1


async def test_openai_factory_closes_owned_client_on_cancellation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: list[FakeAsyncOpenAI] = []

    def build(*, api_key: str) -> FakeAsyncOpenAI:
        client = FakeAsyncOpenAI(api_key=api_key)
        created.append(client)
        return client

    monkeypatch.setattr("app.tools.llm.AsyncOpenAI", build)

    async def use_client() -> None:
        async with create_llm_client(LLMProvider.OPENAI, _settings()):
            await asyncio.sleep(30)

    task = asyncio.create_task(use_client())
    for _ in range(20):
        if created:
            break
        await asyncio.sleep(0)
    assert created
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert created[0].close_calls == 1


async def test_injected_openai_client_is_not_closed() -> None:
    injected = FakeAsyncOpenAI(api_key="external-key")
    llm = StructuredLLM(settings=_settings(), client=injected)  # type: ignore[arg-type]

    await llm.aclose()
    await llm.aclose()

    assert injected.close_calls == 0


async def test_owned_openai_client_close_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created: list[FakeAsyncOpenAI] = []

    def build(*, api_key: str) -> FakeAsyncOpenAI:
        client = FakeAsyncOpenAI(api_key=api_key)
        created.append(client)
        return client

    monkeypatch.setattr("app.tools.llm.AsyncOpenAI", build)
    llm = StructuredLLM(settings=_settings())

    await llm.aclose()
    await llm.aclose()

    assert created[0].close_calls == 1


async def test_openai_factory_missing_key_opens_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_openai(**kwargs: object) -> None:
        raise AssertionError(kwargs)

    monkeypatch.setattr("app.tools.llm.AsyncOpenAI", fail_openai)

    with pytest.raises(ValueError, match="OPENAI_API_KEY is not set"):
        async with create_llm_client(LLMProvider.OPENAI, _settings(openai_api_key="")):
            raise AssertionError("client should not be yielded")


async def test_cursor_factory_missing_key_does_not_launch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def launch(workspace: str) -> object:
        raise AssertionError(workspace)

    monkeypatch.setattr("app.tools.cursor_llm.launch_cursor_client", launch)

    with pytest.raises(ValueError, match="CURSOR_API_KEY is not set"):
        async with create_llm_client(LLMProvider.CURSOR, _settings(cursor_api_key="")):
            raise AssertionError("client should not be yielded")


async def test_cursor_factory_closes_bridge_on_success_and_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closed: list[bool] = []

    class FakeClient:
        async def aclose(self) -> None:
            closed.append(True)

    async def launch(workspace: str) -> FakeClient:
        assert workspace
        return FakeClient()

    async def prompt(*, client: object, prompt: str, options: object) -> SimpleNamespace:
        return SimpleNamespace(id="run-1", status="finished", result="{}")

    monkeypatch.setattr("app.tools.cursor_llm.launch_cursor_client", launch)
    monkeypatch.setattr("app.tools.cursor_llm.prompt_cursor", prompt)

    async with create_llm_client(LLMProvider.CURSOR, _settings()) as llm:
        assert isinstance(llm, CursorStructuredLLMClient)

    assert closed == [True]

    async def fail_prompt(*, client: object, prompt: str, options: object) -> SimpleNamespace:
        raise RuntimeError("prompt failed")

    monkeypatch.setattr("app.tools.cursor_llm.prompt_cursor", fail_prompt)
    with pytest.raises(RuntimeError, match="prompt failed"):
        async with create_llm_client(LLMProvider.CURSOR, _settings()) as llm:
            await llm.complete_structured(
                system_prompt="system",
                user_prompt="user",
                response_model=ProfileAnalysis,
            )

    assert closed == [True, True]


async def test_cursor_factory_closes_bridge_on_cancellation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = {"opened": False, "closed": False}

    class FakeClient:
        async def aclose(self) -> None:
            state["closed"] = True

    async def launch(workspace: str) -> FakeClient:
        state["opened"] = True
        return FakeClient()

    monkeypatch.setattr("app.tools.cursor_llm.launch_cursor_client", launch)

    async def use_client() -> None:
        async with create_llm_client(LLMProvider.CURSOR, _settings()):
            await asyncio.sleep(30)

    task = asyncio.create_task(use_client())
    for _ in range(20):
        if state["opened"]:
            break
        await asyncio.sleep(0)
    assert state["opened"] is True
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert state["closed"] is True


async def test_injected_cursor_completion_is_not_closed() -> None:
    class InjectedCompletion:
        def __init__(self) -> None:
            self.closed = False

        async def complete(self, *, prompt: str, model: str, api_key: str) -> str:
            return "{}"

        async def aclose(self) -> None:
            self.closed = True

    injected = InjectedCompletion()
    client = CursorStructuredLLMClient(settings=_settings(), text_completion=injected)
    async with client:
        text = await injected.complete(prompt="p", model="composer-2.5", api_key=_FAKE_CURSOR_KEY)
        assert text == "{}"

    assert injected.closed is False


def test_analyze_profile_uses_openai_factory_and_closes_it(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    created: list[FakeAsyncOpenAI] = []
    expected = _analysis()

    class Responses:
        async def parse(self, **kwargs: object) -> SimpleNamespace:
            assert kwargs["model"] == "gpt-4o-mini"
            return SimpleNamespace(output_parsed=expected)

    class Client(FakeAsyncOpenAI):
        def __init__(self, *, api_key: str) -> None:
            super().__init__(api_key=api_key)
            self.responses = Responses()
            created.append(self)

    monkeypatch.setattr("app.cli.get_settings", lambda: _settings())
    monkeypatch.setattr("app.tools.llm.AsyncOpenAI", Client)

    with pytest.raises(SystemExit) as exc_info:
        main(["analyze-profile", "examples/sample_profile.json"])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert created[0].close_calls == 1
    assert created[0].api_key == _FAKE_OPENAI_KEY
    assert _FAKE_OPENAI_KEY not in captured.out
    assert _FAKE_OPENAI_KEY not in captured.err
    assert '"score": 80' in captured.out
