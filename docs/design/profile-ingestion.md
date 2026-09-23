# Profile ingestion and extraction

Text sources can be extracted into structured facts. This is not canonical profile persistence, and it is not the [Profile Analyzer](profile-agent.md).

| Topic | Status |
|-------|--------|
| `ProfileIngestionRequest` with text, file, and URL sources | **Implemented** as the input contract |
| Text normalization and per-source extraction | **Implemented** |
| CLI `extract-profile` | **Implemented** |
| File reading and URL fetching | Represented on the request; acquisition **not implemented** |
| `ExtractedCandidateProfile` as canonical `CandidateProfile` | **Not** the same model; extraction is not persisted |
| Reconciliation and human-in-the-loop | **Decided** as a later step; **not implemented** |
| Merge into `CandidateProfile` with no implicit deletion | **Decided**; **not implemented** |
| Database writes, queues, LangGraph, authentication | **Not implemented** |

## Runtime flow

**Implemented** for text. File and URL requests fail before extraction.

```text
ProfileIngestionRequest
  -> normalize supported sources
    -> ProfileExtractionAgent (one call per text source)
      -> ProfileExtractionResult
        -> JSON on stdout
```

`ProfileIngestionFlow` in `app/workflows/profile_ingestion.py` owns that sequence. `ProfileExtractionAgent` extracts a single source. It does not loop, merge, or touch the database.

A later workflow engine can call `normalize_profile_sources` and `ProfileExtractionAgent` directly. This slice does not introduce one.

## Contracts

Models live in `app/models/profile_ingestion.py`. They use `extra="forbid"`, so `user_id`, `career_goal`, scores, and recommendations are rejected rather than carried into the prompt.

User identity belongs to application context. It is not an extraction input.

### `ProfileIngestionRequest`

What the caller supplies.

```text
ProfileIngestionRequest
  sources: list[ProfileSource]   # at least one
```

`ProfileSource` is a discriminated union on `kind`:

| Kind | Model | Payload | Execution |
|------|--------|---------|-----------|
| `text` | `TextProfileSource` | `content` | Normalized and extracted |
| `file` | `FileProfileSource` | `path` | Accepted, then `UnsupportedProfileSourceError` |
| `url` | `UrlProfileSource` | `url` | Accepted, then `UnsupportedProfileSourceError` |

`source_type` is the semantic kind of material, separate from how it arrives:

`cv` · `linkedin` · `portfolio` · `user_text` · `other`

File paths are not opened. URLs are not fetched. A request that contains any file or URL fails during normalization, before any model call, including when earlier sources are text. The error is intentional: those kinds are not silently treated as text.

### `NormalizedProfileSource` / `ProfileExtractionInput`

Content ready for extraction, and the agent input. They are the same model in this slice because text normalization only keeps `source_type` and `content`.

```text
source_type
content
```

No `user_id`.

### `ExtractedCandidateProfile`

Facts from **one** source:

| Field | Meaning |
|-------|---------|
| `current_title` | Optional |
| `location` | Optional |
| `linkedin_url` | Optional free text as stated. Not fetched. |
| `experiences` | Optional list of `ExtractedExperience` |
| `skills` | Optional list of strings |

`ExtractedExperience` fields are all optional: `company_name`, `title`, `start_date`, `end_date`, `description`, and `is_current`.

`is_current` is included so "Present" is not stored as an invented end date. `true` means the source says the role is current, and `end_date` must then be null. `null` means the source did not say.

The flow wraps each profile in `ExtractedProfileSource` (`source_type` + `profile`). `source_type` is copied from the normalized source by the application. The model is not asked to echo it.

`ProfileExtractionResult.sources` is the per-source list. Sources are not merged.

Skill strings are trimmed, blanks are dropped, and case-insensitive duplicates are removed. That is list hygiene, not the persisted `Skill` entity.

These fields are intentionally absent: `career_goal`, `target_title`, preferred jobs, `match_score`, `profile_score`, recommendations. Those belong to search intent or to [profile analysis](models.md).

The extraction schema is not the SQLAlchemy `CandidateProfile` / `Experience` schema. `Experience` rows store `company_id` and exact dates. This slice does not map onto them.

## Dates

**Decided** for the extraction contract. Not mapped to PostgreSQL.

Real sources say `2023`, `Jan 2023`, or `2023 – Present`. `ExtractedDate` stores only the stated parts:

| Field | Required? |
|-------|-----------|
| `year` | yes, when a date is present |
| `month` | only if the source stated a month |
| `day` | only if the source stated a day; requires `month` |

A missing month or day is not filled in as January or the first of the month. A day that cannot exist in that month and year is rejected. Partial dates are not ordered against each other here. Words such as "circa" are not modeled; only explicit year, month, and day are.

An open-ended role uses `is_current=true` and `end_date=null`.

## Per-source extraction

Each normalized source is a separate agent call. A CV and a portfolio in one request produce two `ExtractedProfileSource` values. Prompts contain one source. The flow does not concatenate sources and does not ask the model to choose a canonical truth.

That leaves disagreements available for a later reconciliation step. This slice does not implement that step.

## Reconciliation and canonical merge

**Decided. Not implemented.**

Future flow, after extraction:

```text
extracted source facts
  + existing canonical CandidateProfile
    -> reconciliation
         SAFE_MERGE
         NEEDS_REVIEW -> human review
         INVALID / INSUFFICIENT
    -> approved canonical update
```

The model may extract facts. It must not unilaterally resolve a meaningful conflict in canonical user data. That resolution is application policy, and meaningful conflicts need human review.

**Merge rule for the future canonical update:** merge, and do not implicitly delete. A fact missing from a newly supplied source stays on `CandidateProfile`. A CV tailored to one job may omit valid skills or experience on purpose. Deletion or replacement needs an explicit action, not absence.

No workflow-state tables are added for this.

## CLI

```bash
uv run career-ai extract-profile examples/sample_profile_ingestion.json --mock
```

`--mock` uses `MockStructuredLLM` and does not call OpenAI. The mock returns one fixed `ExtractedCandidateProfile` for every source. The command still emits one result per source, with that source's `source_type`.

Omit `--mock` only when `OPENAI_API_KEY` is set. `analyze-profile` is unchanged.

File and URL requests exit with code `1` and an explicit "not supported yet" message.

## Files

| File | Role |
|------|------|
| `app/models/profile_ingestion.py` | Ingestion and extraction contracts |
| `app/prompts/profile_extraction.py` | Extraction prompt |
| `app/agents/profile/extraction.py` | Single-source extraction capability |
| `app/workflows/profile_ingestion.py` | Normalize, then extract each text source |
| `app/cli.py` | `extract-profile` |
| `examples/sample_profile_ingestion.json` | Two text sources |
