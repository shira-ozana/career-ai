# CV tailoring

**Designed / decided** as a product capability and as the `ResumeVersion` model. Generation is **not implemented**.

`app/agents/resume/` is a placeholder. No flow reads a `JobMatch` and writes a resume. There is no `TailoredCV` entity. `tests/test_db_models.py` asserts `tailored_cvs` is absent.

Schema and retention rules: [Data architecture](../../architecture/data.md#resume-file-storage). Product role: [CV Tailoring](../../architecture/overview.md#cv-tailoring).

## What `ResumeVersion` is

A `ResumeVersion` belongs to a `CandidateProfile`. `version_type` is `original`, `generic`, or `tailored`.

| Type | `JobMatch` |
|------|------------|
| `original` | Not required |
| `generic` | Not required |
| `tailored` | Optional foreign key. This is the job-specific resume |

`job_match_id` is nullable. Deleting a match sets it to null (`ON DELETE SET NULL`). The row can store `summary` and `file_reference`.

`file_reference` is a string for a future object-storage path. Object storage is not implemented. The column does not mean a PDF exists.

Job-specific wording stays on `ResumeVersion`. It does not replace canonical facts on `CandidateProfile`. A tailored CV that omits a skill is not, by itself, a deletion of that skill. That merge rule is **designed / decided** for a future canonical update. Reconciliation, which would enforce it, is [in design](profile-reconciliation.md).

Before tailoring, the architecture says the application should be able to verify that one job's freshness without rerunning search. Freshness columns and the tailoring flow are both absent. [Job freshness vs execution time](../../architecture/job-search.md#job-freshness-vs-execution-time).

`ResumeVersion` is not a chat log and not workflow state.

## Handoff snapshot (8 October 2026)

| | |
|--|--|
| Current status | Schema **implemented**. Tailoring runtime **planned** |
| Implemented functionality | `ResumeVersion` mapping and the three version types |
| Accepted decisions | One resume-version entity, not a separate TailoredCV table. Optional link to `JobMatch`. Canonical profile stays independent of job-specific edits |
| Open questions | Object storage product. How much of the generated document is stored versus referenced. Freshness check before generation. Model policy for a future `CV_TAILORING` task, which is **deferred** in [Future architecture](../../architecture/future-architecture.md#model-routing) |
| Files | `app/db/models/resume.py`, `app/db/models/enums.py` (`ResumeVersionType`), `tests/test_db_models.py` |
| Tests | ORM metadata only. No generation test |
| Known limitations | No original file is stored. No generic or tailored document is produced. The resume placeholder package has no agent |
| Next recommended step | Do not add a tailoring agent or a TailoredCV table. Canonical profile updates go through the reconciliation design first |
