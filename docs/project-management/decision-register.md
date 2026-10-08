# Decision register

Accepted decisions and the places they live. This register does not create new ADRs and does not close open questions.

Implementation evidence is the code and migrations. Design evidence is the linked document or, where the repository had no page yet, the design discussion preserved in [Profile reconciliation](features/profile-reconciliation.md).

## Architectural decisions

| ID | Decision | Status | Where it lives |
|----|----------|--------|----------------|
| ADR 001 | PostgreSQL, SQLAlchemy 2.x, psycopg, Alembic. Supabase is a development host, not an application API | **Designed / decided.** Schema **implemented.** CLI does not use it | [ADR 001](../adr/001-postgresql.md) |
| ADR 002 | Modular monolith. One backend, one database. Job Search is the likely future extraction, not the current deployable | **Designed / decided** and **implemented** as the deployable shape. Extraction is **future / deferred** | [ADR 002](../adr/002-modular-monolith.md) |
| ADR 003 | Application / workflow owns sequencing, persistence, authorization, and status. Agents are capabilities and do not own canonical writes | **Designed / decided.** The CLI and `ProfileIngestionFlow` follow the capability side. Repositories and authorization are not built | [ADR 003](../adr/003-application-owns-workflows.md) |
| ADR 004 | Catalog-first search, separate discovery and matching, `SearchExecution` as a planned run entity, async execution later, `AUTO` / `SELECTED` source policy as a concept | **Designed / decided.** Runtime and `SearchExecution` persistence are **planned** | [ADR 004](../adr/004-catalog-first-job-search.md), [Job Search](../architecture/job-search.md) |

ADR 003 says Profile Ingestion introduces the first application service and repository. The ingestion slice that shipped is text extraction without either. That gap is already stated in [Future architecture](../architecture/future-architecture.md#agents-are-capabilities). The ADR text has not been revised.

## Product and identity

| ID | Decision | Status |
|----|----------|--------|
| D-01 | The product covers ingestion, analysis, LinkedIn optimization, job discovery, matching, tailored CVs, and persistent job-search context | Product direction **designed / decided**. Only analysis and text extraction run |
| D-02 | `User` is the internal product identity. `AuthIdentity` is an external provider link. `(provider, provider_subject)` identifies that link. One user may have many identities | **Designed / decided** and present in the schema. No authentication flow |
| D-03 | Matching on email is not sufficient proof for automatic account linking | **Designed / decided.** No linking code. `users.email` is unique |
| D-04 | Authentication answers who the actor is. Authorization answers what that actor may access. Application services enforce ownership. Repositories are not the authorization layer | **Designed / decided.** Not implemented |
| D-05 | User-owned: `CandidateProfile`, `Experience` through the profile, `ResumeVersion`, `JobSearchRequest`, `JobMatch` through the search request. Global catalog: `Job`, `Company`, `Skill` | **Designed / decided.** Tables exist. No ownership checks |
| D-06 | `CandidateProfile` is the current canonical professional profile. Job-specific CV edits belong on `ResumeVersion` | **Designed / decided.** Schema matches this split. Ingestion does not write either |
| D-07 | Search intent (target title, experience range, and the other criteria on `JobSearchRequest`) is not canonical professional fact. A search range must not overwrite years of experience on the profile | **Designed / decided.** `target_title` is on `JobSearchRequest` only |
| D-08 | `ResumeVersion` represents original, generic, and tailored resumes. There is no separate TailoredCV entity. A tailored version may reference a `JobMatch` | **Designed / decided** and mapped. The absence of `tailored_cvs` is tested |

`Company` ownership if Job Search is later extracted is an existing **open question**. [Data architecture](../architecture/data.md) says not to redesign `Company` now.

## Ingestion and models

| ID | Decision | Status |
|----|----------|--------|
| D-09 | `ProfileInput` / `ProfileAnalysis` are the analyzer contract. They are not `CandidateProfile` | **Implemented** |
| D-10 | Ingestion contracts (`ProfileIngestionRequest`, text/file/URL sources, `NormalizedProfileSource`, `ExtractedCandidateProfile`, `ExtractedProfileSource`, `ProfileExtractionResult`) are separate from the ORM | **Implemented** as Pydantic models. File and URL kinds are not acquired |
| D-11 | Each source is extracted separately. Unrelated sources are not concatenated into one prompt, because provenance and conflicts depend on that split | **Implemented** for text |
| D-12 | A source extraction is not the canonical profile. `ProfileIngestionFlow` normalizes and extracts. It does not persist | **Implemented** |
| D-13 | Canonical updates use merge. A source that omits a skill or an experience does not delete that canonical fact | **Designed / decided.** Not implemented |
| D-14 | `StructuredLLMClient` is the provider protocol. Concrete providers are OpenAI, Cursor, and the mock | **Implemented** |
| D-15 | The Cursor path validates assistant text with strict JSON parsing and Pydantic because `cursor-sdk` does not offer the OpenAI structured-output contract. The agent uses an empty tool allowlist and an isolated temporary workspace | **Implemented.** Details in [LLM client](../design/llm-client.md) |
| D-16 | Task → model policy / router → provider adapter → concrete model. Model identity and prompt version both matter | Routing, prompt versions, and execution-metadata storage are **future / deferred**. The adapter boundary is **implemented**. [Future architecture](../architecture/future-architecture.md#model-routing) |

## Job search and documents

| ID | Decision | Status |
|----|----------|--------|
| D-17 | `Job` is a global catalog entity. External discovery enriches that catalog. Discovery and matching stay separate | **Designed / decided.** Catalog tables exist. No discovery runtime |
| D-18 | `JobSearchRequest` is user-specific search intent. `JobMatch` is one job's relevance to one search. Uniqueness is one match per `(JobSearchRequest, Job)` | Intent and match **tables implemented.** Matching runtime **planned** |
| D-19 | `SearchExecution` is one run of a request. Conceptual lifecycle `PENDING` → `RUNNING` → `COMPLETED` \| `PARTIAL` \| `FAILED`. `PARTIAL` may mean a provider failed while others succeeded | **Planned.** Not an enum in code. `SourceExecution` is **future / deferred** |
| D-20 | External source policy `AUTO` (default) vs `SELECTED` is conceptual. The catalog always participates | **Designed / decided.** No policy columns |
| D-21 | Job freshness is a different clock from search-execution time. Important actions can verify one job without rerunning the search | **Designed / decided.** Freshness columns **deferred** |
| D-22 | Heavy job search is asynchronous. Queue technology is not chosen. Workers do not imply a microservice | **Designed / decided** as direction. **Not implemented** |
| D-23 | Original resume and generated files eventually live in object storage. `file_reference` is a placeholder string | **Future / deferred.** Column exists |

## Reconciliation design discussion

These rules were accepted in the Profile Reconciliation design discussion. They are **in design**. No schema or module implements them. Several say "exact shape not finalized" inside the rule itself.

The full statement, examples, and open questions are in [Profile reconciliation](features/profile-reconciliation.md). Short form:

| ID | Accepted point | Still open |
|----|----------------|------------|
| D-24 | No implicit deletion when a new CV omits a fact (same rule as D-13) | How a user-requested deletion is represented |
| D-25 | A fact that already agrees with the canonical profile needs no canonical change | — |
| D-26 | A new, non-conflicting fact is a proposed addition and needs review before it changes the canonical profile | Disagrees with the SAFE_MERGE wording already in the architecture docs. See below |
| D-27 | A conflicting value becomes a review item. It does not overwrite the canonical value | — |
| D-28 | The user may accept the proposal, keep the current value, or replace it with a different value. A replacement requires the new value | Decision cardinality and lifecycle |
| D-29 | User decisions are authoritative and still validated. Structural, domain, and sometimes semantic checks. Years of experience may be phrases, not only integers | Which fields the first slice supports |
| D-30 | A review item identifies the specific source instance, not only the source type | Source identity schema |
| D-31 | The same conflict from the same previously reviewed evidence should not ask the same question again. New evidence may reopen review. Re-uploading identical content is not automatically new evidence | How identical evidence is detected |
| D-32 | Review history keeps evidence identity, the canonical value at review time, the proposed value, the review item, the decision, any replacement, and the decision time. History is separate from current canonical state | Decision schema |
| D-33 | Extraction storage is hybrid: full extraction output retained for audit, and business-relevant review data stored structurally. Do not normalize every extracted fact up front | JSONB is not in the current schema. Exact tables are open |
| D-34 | The same content with the same extraction-process version normally reuses an existing extraction. A model change does not by itself reprocess history | Whether one extraction is reused across runs |
| D-35 | A source instance has a stable identity. A content hash can detect exact duplicate content | Field list |
| D-36 | One source may have many extractions over time (`ProfileSource` 1:N `ProfileSourceExtraction`) | Which metadata columns |
| D-37 | `ProfileIngestionRun` is one ingestion-workflow execution, not an auth session and not a database session. A source may participate in many runs | Schema, links to sources and extractions, and the state set |
| D-38 | `ReviewItem` is one proposed change or conflict (`CONFLICT` or `PROPOSED_ADDITION`) in a run | Cardinality, lifecycle, and whether evidence is N:M |
| D-39 | `ReviewDecision` is persisted | Cardinality and lifecycle |
| D-40 | Human review happens before meaningful canonical updates. The workflow must be able to wait and resume. Business policy stays in application services | How workflow state is stored. LangGraph is a candidate only |

Conceptual run states discussed, and not finalized:

```text
RUNNING → RECONCILING → WAITING_FOR_USER → COMPLETED
```

LangGraph is a leading candidate for pause, resume, and checkpoints. It is **not** selected and it is **not** a dependency. `app/workflows/__init__.py` states that LangGraph is not used.

## Unresolved discrepancies

These are disagreements between records. They are open. Later work needs an explicit decision before code treats either side as the rule.

### 1. New non-conflicting facts: automatic merge or proposed addition

[Future architecture](../architecture/future-architecture.md#reconciliation) and [Profile ingestion design](../design/profile-ingestion.md#reconciliation-and-canonical-merge) describe reconciliation outcomes `SAFE_MERGE`, `NEEDS_REVIEW`, and `INVALID / INSUFFICIENT`. They say a new skill that does not contradict a canonical skill can be a `SAFE_MERGE`, and that human review is not required for every trivial addition.

The later design discussion (D-26, D-38) says even that new skill is a `PROPOSED_ADDITION` and must be proposed to the user before the canonical profile changes. The illustrative case is canonical skills Python and React, and a new CV that also lists LangGraph.

No reconciliation code implements either policy. This register does not choose one. The outcome names (`SAFE_MERGE` / `NEEDS_REVIEW`) and the review types (`CONFLICT` / `PROPOSED_ADDITION`) are also unmapped.

### 2. What the next implementation slice is

The repository `README.md` direction lists canonical `CandidateProfile` merge next, and file/URL acquisition and reconciliation after that.

[Architecture overview](../architecture/overview.md#next-implementation-milestone) also places canonical merge ahead, and describes file/URL acquisition and reconciliation as still later.

The active design thread is Profile Reconciliation, and several of its open questions are about how canonical updates are applied. No canonical write has been implemented.

This register does not replace those sequences with a new one.

### 3. ADR 003's ingestion milestone versus the shipped slice

ADR 003 describes Profile Ingestion as the slice that introduces an application service and a repository. The shipped slice stops at text extraction. The consequence text and the code differ. See [Future architecture](../architecture/future-architecture.md#agents-are-capabilities).

### 4. JSONB

[ADR 001](../adr/001-postgresql.md) and [Data architecture](../architecture/data.md) leave JSONB as a future option. The current migration does not use it.

D-33 accepts a hybrid direction for extraction audit data, including a JSONB document, when reconciliation persistence is designed. The exact schema is open, so D-33 is not a schema change and it does not withdraw the current-schema statement.

### 5. Product framing in the README

The repository `README.md` learning goals describe a portfolio-grade modular monolith. The working agreement treats Career AI as a usable product whose engineering bar is the same as a product, and also as a learning project. The architecture (modular monolith, one database) is the same in both. The "demo versus product" emphasis is not identical. No architecture change follows from that wording.
