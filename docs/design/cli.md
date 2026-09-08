# CLI – terminal interface

## Files

- `app/cli.py` – main implementation
- `app/__main__.py` – enables `python -m app`
- `pyproject.toml` → `[project.scripts] career-ai = "app.cli:main"`

## How to run

Three equivalent forms:

```bash
uv run career-ai analyze-profile examples/sample_profile.json
uv run python -m app analyze-profile examples/sample_profile.json
uv run python -m app.cli analyze-profile examples/sample_profile.json
```

## Current command

### `analyze-profile`

```bash
career-ai analyze-profile <profile_path>
```

| Argument | Meaning |
|----------|---------|
| `profile_path` | Path to a JSON file matching `ProfileInput` |

## CLI flow

```mermaid
flowchart TD
    A[main argv] --> B[argparse]
    B --> C[Load Settings]
    C --> D[Configure logging]
    D --> E{command == analyze-profile?}
    E -->|yes| F[asyncio.run _run_profile_analysis]
    F --> G[Read JSON file]
    G --> H[ProfileInput.model_validate]
    H --> I[ProfileAnalyzerAgent.analyze]
    I --> J[Print analysis JSON]
    E -->|no| K[parser.error]
```

## `_run_profile_analysis` step by step

1. Read the JSON file
2. Validate into `ProfileInput` (invalid input raises Pydantic error)
3. Create the agent
4. Run `await agent.analyze(...)`
5. Print `analysis.model_dump_json(indent=2)` to stdout
6. Return exit code `0`

## Logging

Format:

```text
%(asctime)s | %(levelname)s | %(name)s | %(message)s
```

Log level comes from `LOG_LEVEL` in `.env` (default `INFO`).

During a run you will see logs such as:

- Analyzing profile for ...
- Requesting structured completion ...
- Profile analysis complete ... score=...

The main result (JSON) is printed separately to stdout.

## Sample file

`examples/sample_profile.json` includes:

- Name, headline, about
- Two roles
- Skills
- Career goal toward AI Engineer

You can copy it and adapt it to your real profile.

## What the CLI still lacks

- Commands for other agents
- Saving output to a file (`--output`)
- Interactive mode
- CV file and LinkedIn ingestion (URL or vanity/username, plus LinkedIn PDF for complete profile data)

These are natural extensions after more agents exist. Product inputs are listed in [Architecture](../architecture/overview.md#initial-inputs).
