# 3. Architecture

## MVP big picture

```mermaid
flowchart TB
    User([User]) -->|JSON path| CLI[app/cli.py]
    CLI -->|ProfileInput| Agent[ProfileAnalyzerAgent]
    Agent -->|profile JSON + prompts| LLM[StructuredLLM]
    LLM -->|responses.parse| OpenAI[OpenAI API]
    OpenAI -->|structured JSON| LLM
    LLM -->|ProfileAnalysis| Agent
    Agent -->|ProfileAnalysis| CLI
    CLI -->|JSON stdout| User

    Settings[Settings / .env] -.-> LLM
    Models[Pydantic models] -.-> Agent
    Prompts[Prompt templates] -.-> Agent
```

## Responsibility layers

```mermaid
flowchart LR
    subgraph L1["1. Interface"]
        CLI[CLI]
    end

    subgraph L2["2. Agent"]
        PA[ProfileAnalyzerAgent]
    end

    subgraph L3["3. Domain Contracts"]
        PI[ProfileInput]
        PO[ProfileAnalysis]
    end

    subgraph L4["4. AI Infrastructure"]
        PR[Prompts]
        SL[StructuredLLM]
        OA[OpenAI]
    end

    CLI --> PA
    PA --> PI
    PA --> PO
    PA --> PR
    PA --> SL
    SL --> OA
```

| Layer | Question it answers | Allowed dependencies |
|-------|---------------------|----------------------|
| Interface | How do we invoke it? | Agent + Models |
| Agent | What is the business flow? | Models, Prompts, Tools |
| Domain Contracts | What does the data look like? | Pydantic only |
| AI Infrastructure | How do we talk to the LLM? | OpenAI SDK + Settings |

## Target architecture (future)

This is the full vision from the product spec – **not implemented yet**:

```mermaid
flowchart TB
    User([User]) --> Orch[Career Orchestrator]
    Orch --> Profile[Profile Agent]
    Orch --> Market[Job Market Agent]
    Orch --> Content[Content Agent]
    Orch --> Resume[Resume Agent]
    Orch --> LinkedIn[LinkedIn Agent]
    Orch --> Coach[Career Coach Agent]
    Orch --> Skills[Skills Agent]
    Orch --> Learn[Learning Agent]
    Orch --> Memory[Memory Agent / RAG]

    Profile --> Memory
    Skills --> Memory
    Content --> Memory
```

The current MVP is only the **Profile Agent** node, invoked manually via CLI instead of an Orchestrator.

## Design principles already in use

### 1. Typed contracts before the LLM
Input and output are Pydantic models.  
The LLM does not return free-form text — it returns a structure that is validated.

### 2. Thin agents, thicker tools
`ProfileAnalyzerAgent` does not know OpenAI HTTP details.  
It only builds prompts and calls `StructuredLLM`.

### 3. Dependency injection for tests
You can pass a fake `llm=` into the agent:

```python
ProfileAnalyzerAgent(llm=fake_llm)
```

Tests then need no real network calls.

### 4. Central config
All runtime settings (model, API key, log level) go through `Settings`.

## Repeatable pattern for every future agent

Every new agent should look like this:

```text
app/agents/<name>/
  agent.py          # Agent class
  __init__.py       # Public export

app/models/<name>.py     # Input/Output models
app/prompts/<name>.py    # system/user prompts
tests/test_<name>_agent.py
```

Shared flow:

```mermaid
sequenceDiagram
    participant I as Interface CLI/API
    participant A as Agent
    participant M as Models
    participant P as Prompts
    participant L as StructuredLLM

    I->>M: validate input
    I->>A: analyze(input)
    A->>P: build prompts
    A->>L: complete_structured(response_model)
    L-->>A: parsed Pydantic output
    A-->>I: typed result
```

## What is still missing architecturally

| Component | Why we need it |
|-----------|----------------|
| Orchestrator (`workflows/`) | Connect multiple agents into a full MVP flow |
| Memory (`memory/`) | Remember analyses, goals, writing style |
| API (`api/`) | Interface beyond CLI |
| Job / Content / Resume Agents | Next product capabilities |

## One-sentence summary

The current architecture is a **single typed pipeline** from profile JSON to analysis JSON, with a scaffold ready to grow into a multi-agent system.
