"""Provider selection and Cursor adapter tests. No network and no real API key."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.agents.profile import ProfileExtractionAgent
from app.cli import main
from app.config import Settings
from app.models.profile_ingestion import (
    ExtractedCandidateProfile,
    NormalizedProfileSource,
    ProfileSourceType,
)
from app.tools.cursor_llm import (
    CursorRunError,
    CursorSdkTextCompletion,
    CursorStructuredLLMClient,
    CursorStructuredOutputError,
    build_cursor_agent_options,
    json_text_from_cursor_response,
    parse_cursor_structured_output,
)
from app.tools.llm import StructuredLLM
from app.workflows.profile_ingestion import ProfileIngestionFlow

_SAMPLE = "examples/sample_profile_ingestion.json"
_FAKE_CURSOR_KEY = "cursor-test-key"


def _cursor_settings(**overrides: str) -> Settings:
    values: dict[str, str] = {
        "cursor_api_key": _FAKE_CURSOR_KEY,
        "cursor_model": "composer-2.5",
        "openai_api_key": "sk-test",
        "log_level": "WARNING",
    }
    values.update(overrides)
    return Settings(**values)


class ScriptedCompletion:
    """In-memory stand-in for the Cursor SDK text boundary."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.prompts: list[str] = []
        self.models: list[str] = []
        self.api_keys: list[str] = []

    async def complete(self, *, prompt: str, model: str, api_key: str) -> str:
        self.prompts.append(prompt)
        self.models.append(model)
        self.api_keys.append(api_key)
        if not self._responses:
            msg = "scripted completion has no response left"
            raise AssertionError(msg)
        return self._responses.pop(0)


def _profile_json(*, title: str) -> str:
    return json.dumps({"current_title": title, "skills": ["Python"]})


def test_extraction_agent_does_not_reference_cursor() -> None:
    source = Path("app/agents/profile/extraction.py").read_text(encoding="utf-8")
    assert "cursor_sdk" not in source
    assert "CursorStructuredLLMClient" not in source


def test_missing_cursor_api_key_fails_before_sdk() -> None:
    with pytest.raises(ValueError, match="CURSOR_API_KEY is not set"):
        CursorStructuredLLMClient(settings=_cursor_settings(cursor_api_key=""))


def test_cursor_agent_options_disable_tools_and_skip_the_repo(tmp_path: Path) -> None:
    workspace = tmp_path / "empty-cursor-workspace"
    workspace.mkdir()
    options = build_cursor_agent_options(
        model="composer-2.5",
        api_key=_FAKE_CURSOR_KEY,
        cwd=str(workspace),
    )

    assert options.model == "composer-2.5"
    assert options.api_key == _FAKE_CURSOR_KEY
    assert options.cloud is None
    assert options.mcp_servers is None
    assert options.agents is None
    assert options.mode is None
    assert options.tools == ()
    assert options.disallowed_tools is None
    assert options.local.setting_sources is None
    assert options.local.custom_tools is None
    assert Path(options.local.cwd) == workspace
    assert Path(options.local.cwd).resolve() != Path.cwd().resolve()
    assert options.to_json()["tools"] == {"names": []}


def test_json_fence_is_stripped_only_when_it_wraps_the_whole_reply() -> None:
    raw = '```json\n{"current_title": "Engineer"}\n```'
    assert json_text_from_cursor_response(raw) == '{"current_title": "Engineer"}'
    parsed = parse_cursor_structured_output(raw, ExtractedCandidateProfile)
    assert parsed.current_title == "Engineer"


def test_prose_and_non_json_fences_are_rejected() -> None:
    prose = 'Here is the profile:\n{"current_title": "Engineer"}'
    with pytest.raises(CursorStructuredOutputError):
        parse_cursor_structured_output(prose, ExtractedCandidateProfile)

    python_fence = '```python\n{"current_title": "Engineer"}\n```'
    with pytest.raises(CursorStructuredOutputError, match="unmarked or json"):
        json_text_from_cursor_response(python_fence)


def test_invalid_json_is_rejected() -> None:
    with pytest.raises(CursorStructuredOutputError, match="not valid JSON"):
        parse_cursor_structured_output("not json", ExtractedCandidateProfile)


def test_json_that_breaks_the_schema_is_rejected() -> None:
    with pytest.raises(ValidationError):
        parse_cursor_structured_output(
            '{"career_goal": "AI Engineer"}',
            ExtractedCandidateProfile,
        )


async def test_cursor_client_validates_structured_output_for_the_agent() -> None:
    scripted = ScriptedCompletion([_profile_json(title="Senior Software Engineer")])
    client = CursorStructuredLLMClient(
        settings=_cursor_settings(),
        text_completion=scripted,
    )
    agent = ProfileExtractionAgent(llm=client)

    result = await agent.extract(
        NormalizedProfileSource(
            source_type=ProfileSourceType.CV,
            content="Senior Software Engineer at Example Corp.",
        )
    )

    assert result.current_title == "Senior Software Engineer"
    assert scripted.models == ["composer-2.5"]
    assert scripted.api_keys == [_FAKE_CURSOR_KEY]
    assert "Senior Software Engineer at Example Corp." in scripted.prompts[0]
    assert "JSON Schema" in scripted.prompts[0]
    assert "ExtractedCandidateProfile" in scripted.prompts[0]


async def test_cursor_client_keeps_source_extractions_independent() -> None:
    scripted = ScriptedCompletion(
        [
            _profile_json(title="From user text"),
            _profile_json(title="From portfolio"),
        ]
    )
    client = CursorStructuredLLMClient(
        settings=_cursor_settings(),
        text_completion=scripted,
    )
    flow = ProfileIngestionFlow(agent=ProfileExtractionAgent(llm=client))
    request = json.loads(Path(_SAMPLE).read_text(encoding="utf-8"))
    from app.models.profile_ingestion import ProfileIngestionRequest

    result = await flow.run(ProfileIngestionRequest.model_validate(request))

    assert [item.profile.current_title for item in result.sources] == [
        "From user text",
        "From portfolio",
    ]
    assert len(scripted.prompts) == 2
    assert "I am a Senior Software Engineer" in scripted.prompts[0]
    assert "multi-agent Career AI platform" not in scripted.prompts[0]
    assert "Built a multi-agent Career AI platform" in scripted.prompts[1]
    assert "I am a Senior Software Engineer" not in scripted.prompts[1]


async def test_schema_mismatch_from_cursor_text_raises_validation_error() -> None:
    scripted = ScriptedCompletion(['{"career_goal": "AI Engineer"}'])
    client = CursorStructuredLLMClient(
        settings=_cursor_settings(),
        text_completion=scripted,
    )

    with pytest.raises(ValidationError):
        await client.complete_structured(
            system_prompt="system",
            user_prompt="user",
            response_model=ExtractedCandidateProfile,
        )


async def test_sdk_runner_uses_one_shot_prompts_without_launching_a_real_bridge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    launched: dict[str, object] = {}
    prompts: list[object] = []

    class FakeClient:
        async def aclose(self) -> None:
            launched["closed"] = True

    async def launch(workspace: str) -> FakeClient:
        launched["workspace"] = workspace
        return FakeClient()

    async def prompt(*, client: object, prompt: str, options: object) -> SimpleNamespace:
        assert isinstance(client, FakeClient)
        prompts.append(options)
        title = "First" if len(prompts) == 1 else "Second"
        return SimpleNamespace(
            id=f"run-{len(prompts)}",
            status="finished",
            result=_profile_json(title=title),
        )

    monkeypatch.setattr("app.tools.cursor_llm.launch_cursor_client", launch)
    monkeypatch.setattr("app.tools.cursor_llm.prompt_cursor", prompt)

    runner = CursorSdkTextCompletion()
    await runner.open()
    first = await runner.complete(prompt="one", model="composer-2.5", api_key=_FAKE_CURSOR_KEY)
    second = await runner.complete(prompt="two", model="composer-2.5", api_key=_FAKE_CURSOR_KEY)
    await runner.close()

    assert "First" in first
    assert "Second" in second
    assert launched["closed"] is True
    workspace = Path(str(launched["workspace"]))
    assert workspace.name.startswith("career-ai-cursor-")
    assert not workspace.exists()
    assert workspace.resolve() != Path.cwd().resolve()
    assert len(prompts) == 2
    options = prompts[0]
    assert options.tools == ()  # type: ignore[attr-defined]
    assert options.local.cwd == str(workspace)  # type: ignore[attr-defined]
    assert options.mcp_servers is None  # type: ignore[attr-defined]
    assert options.cloud is None  # type: ignore[attr-defined]


async def test_sdk_runner_rejects_unsuccessful_and_empty_runs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeClient:
        async def aclose(self) -> None:
            return None

    async def launch(workspace: str) -> FakeClient:
        return FakeClient()

    responses = iter(
        [
            SimpleNamespace(id="run-err", status="error", result=_profile_json(title="Ignored")),
            SimpleNamespace(id="run-empty", status="finished", result="  "),
        ]
    )

    async def prompt(*, client: object, prompt: str, options: object) -> SimpleNamespace:
        return next(responses)

    monkeypatch.setattr("app.tools.cursor_llm.launch_cursor_client", launch)
    monkeypatch.setattr("app.tools.cursor_llm.prompt_cursor", prompt)

    runner = CursorSdkTextCompletion()
    await runner.open()
    with pytest.raises(CursorRunError, match="error"):
        await runner.complete(prompt="one", model="composer-2.5", api_key=_FAKE_CURSOR_KEY)
    with pytest.raises(CursorStructuredOutputError, match="empty"):
        await runner.complete(prompt="two", model="composer-2.5", api_key=_FAKE_CURSOR_KEY)
    await runner.close()


async def test_cursor_logs_do_not_include_the_api_key(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    class FakeClient:
        async def aclose(self) -> None:
            return None

    async def launch(workspace: str) -> FakeClient:
        return FakeClient()

    async def prompt(*, client: object, prompt: str, options: object) -> SimpleNamespace:
        return SimpleNamespace(id="run-1", status="finished", result="{}")

    monkeypatch.setattr("app.tools.cursor_llm.launch_cursor_client", launch)
    monkeypatch.setattr("app.tools.cursor_llm.prompt_cursor", prompt)

    runner = CursorSdkTextCompletion()
    await runner.open()
    with caplog.at_level("DEBUG"):
        await runner.complete(
            prompt="secret prompt",
            model="composer-2.5",
            api_key=_FAKE_CURSOR_KEY,
        )
    await runner.close()

    assert _FAKE_CURSOR_KEY not in caplog.text


async def test_openai_structured_client_still_uses_responses_parse() -> None:
    expected = ExtractedCandidateProfile(current_title="From OpenAI")

    class Responses:
        def __init__(self) -> None:
            self.kwargs: dict[str, object] | None = None

        async def parse(self, **kwargs: object) -> SimpleNamespace:
            self.kwargs = kwargs
            return SimpleNamespace(output_parsed=expected)

    class Client:
        def __init__(self) -> None:
            self.responses = Responses()

    client = Client()
    llm = StructuredLLM(settings=_cursor_settings(), client=client)  # type: ignore[arg-type]
    result = await llm.complete_structured(
        system_prompt="system",
        user_prompt="user",
        response_model=ExtractedCandidateProfile,
    )

    assert result == expected
    assert client.responses.kwargs is not None
    assert client.responses.kwargs["model"] == "gpt-4o-mini"
    assert client.responses.kwargs["text_format"] is ExtractedCandidateProfile


def test_extract_profile_help_lists_providers(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["extract-profile", "--help"])

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "--provider" in help_text
    assert "{mock,openai,cursor}" in help_text
    assert "--mock" in help_text


def test_analyze_profile_rejects_provider_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["analyze-profile", "--help"])
    assert exc_info.value.code == 0
    assert "--provider" not in capsys.readouterr().out

    with pytest.raises(SystemExit) as exc_info:
        main(["analyze-profile", _SAMPLE, "--provider", "cursor"])
    assert exc_info.value.code == 2


def test_extract_profile_provider_mock_matches_mock_flag(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as mock_flag:
        main(["extract-profile", _SAMPLE, "--mock"])
    mock_out = capsys.readouterr().out

    with pytest.raises(SystemExit) as provider_flag:
        main(["extract-profile", _SAMPLE, "--provider", "mock"])
    provider_out = capsys.readouterr().out

    assert mock_flag.value.code == 0
    assert provider_flag.value.code == 0
    assert json.loads(mock_out) == json.loads(provider_out)


def test_extract_profile_mock_and_other_provider_conflict() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["extract-profile", _SAMPLE, "--mock", "--provider", "cursor"])
    assert exc_info.value.code == 2


def test_extract_profile_cursor_missing_key_exits(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        "app.cli.get_settings",
        lambda: _cursor_settings(cursor_api_key=""),
    )

    with pytest.raises(SystemExit) as exc_info:
        main(["extract-profile", _SAMPLE, "--provider", "cursor"])

    assert exc_info.value.code == 1
    assert "CURSOR_API_KEY is not set" in capsys.readouterr().err


def test_extract_profile_cursor_cli_validates_two_sources_offline(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    prompts: list[str] = []

    class FakeClient:
        async def aclose(self) -> None:
            return None

    async def launch(workspace: str) -> FakeClient:
        return FakeClient()

    async def prompt(*, client: object, prompt: str, options: object) -> SimpleNamespace:
        prompts.append(prompt)
        title = "CLI user text" if len(prompts) == 1 else "CLI portfolio"
        return SimpleNamespace(
            id=f"run-{len(prompts)}",
            status="finished",
            result=_profile_json(title=title),
        )

    monkeypatch.setattr("app.cli.get_settings", lambda: _cursor_settings())
    monkeypatch.setattr("app.tools.cursor_llm.launch_cursor_client", launch)
    monkeypatch.setattr("app.tools.cursor_llm.prompt_cursor", prompt)

    with pytest.raises(SystemExit) as exc_info:
        main(["extract-profile", _SAMPLE, "--provider", "cursor"])

    assert exc_info.value.code == 0
    payload = json.loads(capsys.readouterr().out)
    assert [item["profile"]["current_title"] for item in payload["sources"]] == [
        "CLI user text",
        "CLI portfolio",
    ]
    assert len(prompts) == 2


def test_extract_profile_default_provider_is_openai(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class RecordingLLM:
        def __init__(self, settings: Settings | None = None, client: object | None = None) -> None:
            self.settings = settings

        async def complete_structured(
            self,
            *,
            system_prompt: str,
            user_prompt: str,
            response_model: type[ExtractedCandidateProfile],
            model: str | None = None,
        ) -> ExtractedCandidateProfile:
            return ExtractedCandidateProfile(current_title="default openai")

    monkeypatch.setattr("app.cli.get_settings", lambda: _cursor_settings())
    monkeypatch.setattr("app.cli.StructuredLLM", RecordingLLM)

    with pytest.raises(SystemExit) as exc_info:
        main(["extract-profile", _SAMPLE])

    assert exc_info.value.code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["sources"][0]["profile"]["current_title"] == "default openai"


def test_extract_profile_openai_provider_stays_on_structured_llm(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    constructed: list[Settings] = []

    class RecordingLLM:
        def __init__(self, settings: Settings | None = None, client: object | None = None) -> None:
            assert settings is not None
            constructed.append(settings)

        async def complete_structured(
            self,
            *,
            system_prompt: str,
            user_prompt: str,
            response_model: type[ExtractedCandidateProfile],
            model: str | None = None,
        ) -> ExtractedCandidateProfile:
            if "Source type: user_text" in user_prompt:
                return ExtractedCandidateProfile(current_title="OpenAI user text")
            return ExtractedCandidateProfile(current_title="OpenAI portfolio")

    monkeypatch.setattr("app.cli.get_settings", lambda: _cursor_settings())
    monkeypatch.setattr("app.cli.StructuredLLM", RecordingLLM)

    with pytest.raises(SystemExit) as exc_info:
        main(["extract-profile", _SAMPLE, "--provider", "openai"])

    assert exc_info.value.code == 0
    payload = json.loads(capsys.readouterr().out)
    assert [item["profile"]["current_title"] for item in payload["sources"]] == [
        "OpenAI user text",
        "OpenAI portfolio",
    ]
    assert constructed[0].openai_api_key == "sk-test"
    assert _FAKE_CURSOR_KEY not in capsys.readouterr().out
