# Profile ingestion

**Implemented** for text sources. File and URL acquisition, reconciliation, human review, and canonical persistence are not part of this slice.

Technical contracts and date rules: [Profile ingestion design](../../design/profile-ingestion.md). Runtime sequence: [Profile ingestion flow](../../flows/profile-ingestion.md). Analyzer, which is a different contract: [Profile agent](../../design/profile-agent.md).

## What the code does

`extract-profile` reads a `ProfileIngestionRequest` JSON file, normalizes sources, and calls `ProfileExtractionAgent` once per text source. The CLI prints a `ProfileExtractionResult`. `ProfileIngestionFlow` does not merge sources and does not open a database session.

```text
ProfileIngestionRequest
  → normalize text sources
    → ProfileExtractionAgent, one source at a time
      → ProfileExtractionResult on stdout
```

Providers for this command are `mock`, `openai` (the default), and `cursor`. `analyze-profile` always uses OpenAI. Provider details: [LLM client](../../design/llm-client.md).

A file or URL source raises `UnsupportedProfileSourceError` during normalization, before any model call. If a request mixes text with a file or URL, the whole request fails. Earlier text sources in that request are not extracted.

## Stage status

The ingestion design separates six stages. Only the first three exist, and only for text.

| Stage | Status |
|-------|--------|
| 1. Request / source acquisition | **Partial.** The request model accepts `TextProfileSource`, `FileProfileSource`, and `UrlProfileSource`. Only text content is available to extraction. Files are not opened. URLs are not fetched |
| 2. Source normalization | **Implemented** for text. Output is `NormalizedProfileSource` (`source_type` and `content`), also used as `ProfileExtractionInput` |
| 3. Per-source extraction | **Implemented** for text. One prompt per source. The result is `ExtractedProfileSource` (`source_type` plus `ExtractedCandidateProfile`) |
| 4. Reconciliation | **In design.** Not called by the flow. [Profile reconciliation](profile-reconciliation.md) |
| 5. Human review | **Not implemented** |
| 6. Canonical persistence | **Not implemented.** `CandidateProfile` is an ORM model. This flow does not write it |

`kind` is how the material arrives (`text`, `file`, `url`). `source_type` is what it means (`cv`, `linkedin`, `portfolio`, `user_text`, `other`).

## Contracts that exist

Defined in `app/models/profile_ingestion.py`:

- `ProfileIngestionRequest`
- `TextProfileSource`, `FileProfileSource`, `UrlProfileSource` (union `ProfileSource`)
- `NormalizedProfileSource` (`ProfileExtractionInput`)
- `ExtractedCandidateProfile` and `ExtractedExperience` / `ExtractedDate`
- `ExtractedProfileSource`
- `ProfileExtractionResult`

`ExtractedCandidateProfile` has no `user_id`, target title, or analysis score. Absence of a field means the source did not state it. It does not mean the canonical profile should drop that fact. The canonical merge rule is **designed / decided** and not executed. See [CV and LinkedIn ingestion](../../architecture/data.md#cv-and-linkedin-ingestion).

`ProfileInput` is the analyzer input. It is not this contract and it is not the ORM `CandidateProfile`.

## Handoff snapshot (8 October 2026)

| | |
|--|--|
| Current status | Text extraction **implemented**. Acquisition beyond inline text **planned**. Reconciliation **in design** |
| Implemented functionality | Normalize text sources, extract each source, validate structured output, print JSON. Cursor and OpenAI adapters behind `StructuredLLMClient`. Mock for tests and `--mock` |
| Accepted decisions | Per-source extraction (D-11). Extraction is not canonical state (D-12). No implicit deletion when persistence is added (D-13). [Decision register](../decision-register.md) |
| Open questions | Reconciliation questions in [Profile reconciliation](profile-reconciliation.md#open-questions). They block a persistence design |
| Files that implement this slice | `app/models/profile_ingestion.py`, `app/prompts/profile_extraction.py`, `app/agents/profile/extraction.py`, `app/workflows/profile_ingestion.py`, `app/cli.py`, `app/tools/llm.py`, `app/tools/cursor_llm.py`, `app/tools/mock_llm.py`, `examples/sample_profile_ingestion.json`, `tests/test_models_profile_ingestion.py`, `tests/test_profile_extraction.py`, `tests/test_llm_providers.py`, `tests/test_llm_client.py` |
| Tests | Unit tests with a mock or scripted provider. No live OpenAI or Cursor call. No database |
| Known limitations | No file/PDF/URL acquisition. No saved source identity, content hash, or extraction history. No canonical write. A manual Cursor run with two text sources was reported in the prior conversation and is not an automated test |
| Next recommended step | Continue reconciliation design. Do not add canonical writes or file parsing until the open review rules are decided |

Sample files under `examples/` are fixtures for the CLI, not a person's real profile.
