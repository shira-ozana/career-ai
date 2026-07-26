# Career AI Assistant

Personal career manager powered by AI agents.

Helps you analyze LinkedIn/CV profiles, close skill gaps, tailor resumes, create professional content, and track long-term career growth.

## Status

**Stage 2 MVP** – Profile Analyzer Agent with OpenAI Structured Outputs.

## Features (current)

- Typed profile input/output via Pydantic
- Profile Analyzer Agent (`score`, strengths, weaknesses, missing skills, recommendations)
- OpenAI Structured Outputs integration
- CLI for local analysis
- Unit tests with mocked LLM

## Project layout

```text
career-ai/
├── app/
│   ├── agents/          # Independent agents (profile first)
│   ├── models/          # Pydantic domain models
│   ├── prompts/         # Prompt templates
│   ├── tools/           # Shared tools (LLM client, etc.)
│   ├── memory/          # Future long-term memory / RAG
│   ├── workflows/       # Future multi-agent orchestration
│   └── api/             # Future FastAPI surface
├── examples/            # Sample payloads
├── tests/
├── docs/
└── pyproject.toml
```

## Requirements

- Python 3.13+
- [uv](https://github.com/astral-sh/uv)
- OpenAI API key

## Setup

```bash
cd ~/Downloads/career-ai
uv sync --extra dev
cp .env.example .env
# Edit .env and set OPENAI_API_KEY
```

## Run Profile Agent

```bash
uv run career-ai analyze-profile examples/sample_profile.json
```

Or:

```bash
uv run python -m app.cli analyze-profile examples/sample_profile.json
```

Example output shape:

```json
{
  "score": 71,
  "strengths": ["Python", "Backend"],
  "weaknesses": ["Limited AI Agents portfolio evidence"],
  "missing_skills": ["RAG", "MCP", "AI Agents"],
  "recommendations": ["Improve headline", "Add measurable achievements"]
}
```

## Tests

```bash
uv run pytest
```

## Roadmap

1. Skills gap agent
2. Career plan agent
3. Content agent (first LinkedIn post)
4. Memory / RAG persistence
5. FastAPI API + orchestration (LangGraph / Agents SDK)

## Learning goals

- Professional Python (typing, Pydantic, async, testing)
- Modern AI tooling (OpenAI, Structured Outputs, agents)
- Portfolio-grade multi-agent system design
