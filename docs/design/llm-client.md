# LLM client

## Files

| File | Role |
|------|------|
| `app/tools/llm.py` | `LLMProvider`, `StructuredLLMClient`, OpenAI `StructuredLLM`, and `create_llm_client` |
| `app/tools/cursor_llm.py` | Cursor adapter. Imported only when that provider is selected |
| `app/tools/mock_llm.py` | Deterministic client for tests and `--mock` |

## Role

Agents call `StructuredLLMClient`. They do not choose a provider, open a connection, or import a vendor SDK.

`create_llm_client(provider, settings)` is the connection entry point. It yields a `StructuredLLMClient` and closes resources it owns when the block ends, including on failure and cancellation.

## Provider identity

`LLMProvider` is the only set of provider ids:

| Member | Value | Default |
|--------|-------|---------|
| `OPENAI` | `openai` | Yes. `analyze-profile` always uses this member |
| `CURSOR` | `cursor` | No |
| `MOCK` | `mock` | No |

`extract-profile --provider` choices are `tuple(provider.value for provider in LLMProvider)`. External strings are parsed with `LLMProvider.parse` at the CLI boundary. `create_llm_client` accepts `LLMProvider`, not a raw string.

Model ids and credentials stay in Settings: `OPENAI_MODEL` (default `gpt-4o-mini`) and `CURSOR_MODEL` (default `composer-2.5`).

## Connection lifecycle

```mermaid
flowchart LR
    CLI[CLI] -->|LLMProvider + Settings| Factory[create_llm_client]
    Factory --> OpenAI[StructuredLLM]
    Factory --> Cursor[CursorStructuredLLMClient]
    Factory --> Mock[MockStructuredLLM]
    OpenAI --> Agent[Agent]
    Cursor --> Agent
    Mock --> Agent
```

| Provider | What the factory opens | What it closes |
|----------|------------------------|----------------|
| `openai` | `StructuredLLM`, which creates `AsyncOpenAI` | That `AsyncOpenAI` client, via `StructuredLLM.aclose()` |
| `cursor` | `CursorStructuredLLMClient` as an async context manager | The bridge and temporary workspace, using the adapter's existing close |
| `mock` | `MockStructuredLLM` | Nothing |

Ownership is explicit:

- A client created by `create_llm_client` is closed by that context manager.
- `StructuredLLM(client=...)` does not close an injected OpenAI client.
- `CursorStructuredLLMClient(text_completion=...)` does not close an injected completion. It closes only the SDK bridge it opened itself.

Both CLI commands use this context manager. `extract-profile` passes the resolved provider. `analyze-profile` passes `LLMProvider.OPENAI` and has no `--provider` flag. The CLI still owns JSON input, stdout, and user-facing errors. A missing API key for the selected `extract-profile` provider is printed to stderr and the command exits `1`.

If an agent is constructed without `llm`, it still builds OpenAI `StructuredLLM` for direct use. That fallback is not a provider switch, and the agent does not close it. The CLI does not use the fallback.

## `StructuredLLM`

A thin OpenAI wrapper that guarantees:

- Async calls
- Structured Outputs
- A validated Pydantic object as the return value

## Component diagram

```mermaid
flowchart TB
    Agent[ProfileAnalyzerAgent] --> SL[StructuredLLM]
    SL --> Settings[get_settings]
    SL --> Client[AsyncOpenAI]
    Client --> API[OpenAI responses.parse]
    API --> Parsed[response.output_parsed]
    Parsed --> Model[T bound BaseModel]
```

## `StructuredLLM` class

### `__init__`

| Parameter | Default | Why override |
|-----------|---------|--------------|
| `settings` | `get_settings()` | Tests / custom config |
| `client` | `AsyncOpenAI(...)` | OpenAI mock |

If no API key is set, `require_openai_api_key()` raises `ValueError`.

`aclose()` closes that `AsyncOpenAI` client only when this object created it. Pass `client` to keep ownership outside `StructuredLLM`. `create_llm_client` calls `aclose()` for the OpenAI provider.

### `complete_structured(...)`

Parameters:

| Parameter | Meaning |
|-----------|---------|
| `system_prompt` | System instructions |
| `user_prompt` | Data to analyze |
| `response_model` | Pydantic output class |
| `model` | Optional; otherwise from Settings |

Internal flow:

```mermaid
sequenceDiagram
    participant SL as StructuredLLM
    participant OA as AsyncOpenAI
    participant API as OpenAI API

    SL->>SL: selected_model = model or settings.openai_model
    SL->>OA: responses.parse(model, input, text_format=response_model)
    OA->>API: HTTP request
    API-->>OA: structured response
    OA-->>SL: response.output_parsed
    alt parsed is None
        SL-->>SL: RuntimeError
    else ok
        SL-->>SL: return parsed model instance
    end
```

## Why `responses.parse` instead of plain chat completions?

Because we want:

1. A schema enforced by Pydantic
2. Automatic parsing into a Python object
3. Fewer bugs from broken JSON strings

## TypeVar `T`

```python
T = TypeVar("T", bound=BaseModel)
```

This lets the type checker understand:

```python
analysis = await llm.complete_structured(..., response_model=ProfileAnalysis)
# analysis: ProfileAnalysis
```

## How we test without real OpenAI calls

Tests do not call the real `StructuredLLM`.
They use `MockStructuredLLM`, which returns a fixed result.

`response` is used when the schema is `ProfileAnalysis`. `extraction_response` is used when the schema is `ExtractedCandidateProfile`. Both agents depend on `StructuredLLMClient`, not on OpenAI.

Benefits:

- Fast and stable tests
- No API cost
- No network dependency

## Provider contract

**Implemented.** Agents depend on `StructuredLLMClient.complete_structured(...)`, not on a vendor SDK.

| Provider | Class | Used by |
|----------|-------|---------|
| OpenAI | `StructuredLLM` | `analyze-profile`, and `extract-profile` by default |
| Mock | `MockStructuredLLM` | tests and `extract-profile --mock` |
| Cursor | `CursorStructuredLLMClient` | `extract-profile --provider cursor` |

`ProfileExtractionAgent` and `ProfileAnalyzerAgent` do not know which provider is injected. The CLI selects it and passes the client from `create_llm_client`.

## Cursor provider

**Implemented** for text extraction. Optional. The package is the official Python SDK `cursor-sdk` (imported as `cursor_sdk`). There is no TypeScript bridge in this application.

`cursor-sdk` is an **agent SDK**, not an OpenAI-compatible Chat Completions endpoint. It has no structured-output / Pydantic response format. The adapter therefore:

1. Sends the agent system prompt, user prompt, and the Pydantic JSON schema as one prompt.
2. Runs a **local** Cursor agent with `AsyncAgent.prompt` (one-shot: create, wait, dispose).
3. Reads the final assistant text from `RunResult.result`.
4. Accepts raw JSON, or one markdown fence around the entire reply when the fence language is empty or `json`.
5. Rejects prose, other fence languages, and invalid JSON.
6. Validates with Pydantic (`json.loads`, then `model_validate`). Schema failures raise `ValidationError`.

A run whose status is not `finished` is not parsed.

### Why async, and why local

`ProfileExtractionAgent` is async, so the adapter uses `AsyncClient.launch_bridge` and `AsyncAgent.prompt`. `create_llm_client` holds one async client for the command and closes it afterward, including when extraction fails or the task is cancelled. Each source is a new one-shot prompt, so two sources do not share a conversation.

Tool restrictions exist for **local** agents only. Cloud agents cannot take `tools=[]`, so this path does not use a cloud agent.

### Authentication and model

| Env var | Settings field | Role |
|---------|----------------|------|
| `CURSOR_API_KEY` | `cursor_api_key` | User or service-account key. Passed as `api_key`. Never logged. |
| `CURSOR_MODEL` | `cursor_model` | Model id. Default `composer-2.5`, the SDK quick-start model. |

`--provider cursor` fails before any SDK call when the key is missing. The default is not chosen by `Cursor.models.list()`; that would be an extra account call, and the catalog depends on the key's team.

### Tools and capabilities

The extraction run is text in, JSON text out. `AgentOptions` is:

| Option | Value | Effect |
|--------|-------|--------|
| Runtime | `local` | Required for an empty tool allowlist |
| `local.cwd` and bridge workspace | Empty temporary directory | Not the Career AI repository |
| `tools` | `[]` | No built-in tools. The model can only respond with text |
| `mcp_servers` | unset | No inline MCP |
| `agents` | unset | No inline subagents |
| `local.custom_tools` | unset | No Python tools |
| `local.setting_sources` | unset | SDK default: inline config only, not project/user/team/plugins/MDM |
| `mode` | unset | Server starts in agent mode. With no tools it cannot edit files or run commands |
| `cloud` | unset | Not a cloud coding agent |

`tools=[]` is the SDK's documented switch for "no built-in tools". Shell, edit, read, web search, MCP, and subagents are not offered. Project hooks under the Career AI repo are not on this workspace because `cwd` is an empty temp directory. Hooks remain file-based; this adapter does not add a programmatic hook callback.

### Tests

Unit tests fake `launch_cursor_client` / `prompt_cursor` or inject a text completion. They do not call Cursor and do not need a real key.

## Future extension points

| Improvement | Why |
|-------------|-----|
| Retries / timeout | Resilience to network issues |
| Cost/token logging | Cost tracking |
| More providers | Anthropic or a local model, behind the same protocol |
| Caching | Avoid repeated calls for the same profile |

Task-based model routing, fallbacks, and evaluation are not extensions of this client. They are recorded in [Future architecture](../architecture/future-architecture.md#model-routing) and stay unbuilt until a second task needs a different policy.
