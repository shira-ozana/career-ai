# Architecture

Career AI Assistant is a multi-agent system for career growth and LinkedIn/CV optimization.

## Current MVP

```text
User
  └── Profile Analyzer Agent
        ├── Pydantic models (input/output)
        ├── Prompt templates
        └── OpenAI Structured Outputs
```

## Target architecture

```text
                User
                  |
          Career Orchestrator
                  |
 --------------------------------
 |              |               |
Profile      Market          Content
Agent        Agent           Agent
 |
Skills / LinkedIn / Resume / Coach
 |
Memory System (RAG)
```

## Design principles

1. **Agents are focused** – each agent owns one responsibility and a typed I/O contract.
2. **Structured outputs first** – LLM responses are validated with Pydantic models.
3. **Memory is first-class** – long-term user context will live behind a Memory Agent/RAG layer.
4. **Learn → Plan → Build** – every component is introduced with rationale, architecture fit, then code + tests.

## Next agents (planned)

- Skills Agent
- Career Coach Agent
- Content Agent
- LinkedIn Agent
- Resume Agent
- Job Market Agent
- Memory Agent
- Learning Agent
