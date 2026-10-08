# Profile reconciliation

**In design. Implementation has not started.**

There is no reconciliation module, no `ReviewItem` model, and no workflow-state table. `tests/test_db_models.py` expects `workflow_states` to be absent. `ProfileIngestionFlow` stops at per-source extraction. See [Profile ingestion](profile-ingestion.md).

Earlier architecture pages already sketch a later reconciliation step. This page is the handoff of the design discussion that followed those pages. Where the two disagree, both are quoted from their sources and neither is withdrawn. See [Unresolved discrepancies](../decision-register.md#unresolved-discrepancies).

## What already exists around this feature

| Piece | Role for reconciliation |
|-------|-------------------------|
| Per-source `ExtractedCandidateProfile` | Evidence from one source. Not canonical state. [Ingestion design](../../design/profile-ingestion.md) |
| `CandidateProfile` and child rows | Canonical professional state. Not written by ingestion. [Data architecture](../../architecture/data.md) |
| `SAFE_MERGE` / `NEEDS_REVIEW` / `INVALID / INSUFFICIENT` | Outcome names in [Future architecture](../../architecture/future-architecture.md#reconciliation) and [Ingestion design](../../design/profile-ingestion.md#reconciliation-and-canonical-merge) |
| Human review for meaningful conflicts | **Designed / decided** in those pages. No review API |
| Resumable workflow, LangGraph as a candidate | **Future / deferred.** [LangGraph](../../architecture/future-architecture.md#langgraph) |

`ExtractedExperience.company_name` is an optional string. ORM `Experience.company_id` is required. `ExtractedDate` may omit month and day. ORM `Experience` dates are exact `date` values. Those contract differences are real. They do not decide how experience identity will be reconciled.

## Accepted rules

Rules below were accepted in the design discussion. They are not code. Examples are illustrative, not a description of a real user.

### 1. No implicit deletion

If a new CV omits an existing skill or experience, the canonical information stays. A tailored CV may omit valid professional facts. This matches the merge rule already in [Data architecture](../../architecture/data.md#cv-and-linkedin-ingestion).

### 2. Existing consistent facts

If an extracted fact agrees with the canonical profile, no canonical change is required.

### 3. New facts require review

A new fact that does not conflict with the canonical profile is still proposed to the user before the canonical profile changes.

Illustrative case: canonical skills are Python and React. A new CV lists Python, React, and LangGraph. LangGraph is a `PROPOSED_ADDITION`. It is not inserted silently.

This rule disagrees with the architecture pages that allow a non-conflicting new skill to `SAFE_MERGE` without review. The disagreement is open. See the [decision register](../decision-register.md#1-new-non-conflicting-facts-automatic-merge-or-proposed-addition).

### 4. Conflicts require review

Illustrative case: canonical location Tel Aviv, new source Ramat Gan. The result is a review item. The canonical location stays Tel Aviv until the user resolves it.

### 5. The user is authoritative

The user may:

- `ACCEPT_PROPOSED`
- `KEEP_CURRENT`
- `REPLACE_WITH_VALUE`

`REPLACE_WITH_VALUE` requires the replacement. Illustrative case: current Tel Aviv, proposed Ramat Gan, user-selected replacement Petah Tikva. The design must allow that third value.

### 6. Validate user decisions

A user decision is authoritative and still validated. Validation may be structural, domain-level, or semantic. Primitive types are not assumed to cover every professional value. Years of experience may be stated as "8+ years", "about 10 years", or "6–7 years". Field-specific semantic contracts may be needed.

The current `JobSearchRequest` columns `min_years_experience` and `max_years_experience` are integers. That schema is search intent. It is not a decision about how reconciliation validates phrases.

### 7. Preserve provenance

A review item identifies the evidence that caused the proposal. Source type alone is not enough. A specific source instance must be identifiable.

### 8. New evidence can reopen review

If the same conflict appears again from the same previously reviewed evidence, the user is not asked the same question again.

If a new document states the same conflicting value, that is new evidence and may reopen review.

Re-uploading identical document content does not automatically count as new evidence.

### 9. Persist review history

Keep:

- evidence / source identity
- canonical value at review time
- proposed value
- review item
- user decision
- replacement value, when there is one
- decision timestamp

Current canonical state and decision history are separate.

### 10. Extraction storage is hybrid

Keep the complete extraction output for audit, discussed as JSONB. Store the business-relevant reconciliation and review information in columns that can be queried directly. Do not normalize every extracted fact before the access pattern needs it.

The current database has no JSONB column. [Data architecture](../../architecture/data.md) still treats JSONB as unused. Adopting hybrid storage is a future schema design, not a change that has been migrated.

### 11. Reuse an extraction when the process version matches

The same source content with the same extraction-process version normally reuses existing output. The LLM is not rerun without a reason.

A meaningful change in model, prompt, or extraction schema may justify a new extraction. Changing the model does not automatically reprocess every historical document. Reprocessing is an application policy or an explicit trigger.

The extraction process version should capture the configuration changes that matter. The exact version fields are not finalized.

### 12. Source identity

A source instance has a stable identity. A content hash may detect exact duplicate content. Source type alone is not an identity.

Possible future `ProfileSource` metadata, not a schema:

- id
- candidate_profile_id
- source_type
- content_hash
- created_at
- filename, URL, or storage reference

### 13. Extraction history

One source may have many extraction results as the model, prompt, or schema changes.

```text
ProfileSource 1 —— N ProfileSourceExtraction
```

Possible extraction metadata, not finalized: provider, model, prompt version, extraction version, created_at.

### 14. Ingestion execution context

`ProfileIngestionRun` is one execution of the ingestion workflow. It is the context in which several sources were processed and conflicts were found. It is not an authentication session and not a database session.

Conceptual lifecycle, not a finalized state set:

```text
RUNNING → RECONCILING → WAITING_FOR_USER → COMPLETED
```

A source may participate in more than one ingestion run.

### 15. Review items

`ReviewItem` is one proposed change or conflict that needs the user. Conceptual types:

- `CONFLICT`
- `PROPOSED_ADDITION`

Review items belong to an ingestion / reconciliation execution. One run may produce many review items. A review item may reference supporting evidence.

If several sources propose the same value, the design may consolidate them into one review item. If they propose different values, the current lean is separate review items, each for one conflict. That lean is not finalized.

### 16. Review decisions

`ReviewDecision` stores the user's resolution. Persistence is required. Cardinality and lifecycle are not finalized.

### 17. Human in the loop

Meaningful canonical updates wait for a person.

```text
New evidence
  → extraction
    → reconciliation
      → ReviewItem
        → WAITING_FOR_USER
          → user decision
            → validation
              → canonical update, or keep current
```

The wait may last hours or days, so the workflow has to pause and resume. LangGraph is a leading candidate for that orchestration. It has not been selected. Business reconciliation policy belongs to application services, not to a workflow engine. [ADR 003](../../adr/003-application-owns-workflows.md).

## Open questions

These are open. This page does not answer them.

1. Exact `ProfileIngestionRun` schema.
2. How a `ProfileIngestionRun` references the `ProfileSource` and `ProfileSourceExtraction` rows that participated.
3. Whether an extraction is reused across multiple runs.
4. Exact relationship between `ProfileSourceExtraction` and `ReviewItem`.
5. Whether review-item evidence needs an N:M association table.
6. Exact `ReviewItem` cardinality and lifecycle.
7. Whether multiple conflicts for the same field in one run are resolved together or independently.
8. If the user resolves one location conflict, what happens to other pending location conflicts from the same run.
9. Exact `ReviewDecision` schema and cardinality.
10. How to prevent duplicate reviews when the evidence and the decision are the same.
11. How canonical profile changes are applied safely after user decisions.
12. Which fields the first reconciliation implementation slice supports.
13. How to reconcile `Experience` identity across sources.
14. Whether and when to introduce LangGraph.
15. How to persist resumable workflow state.

Related questions already deferred elsewhere, and not reopened here: queue technology, object storage, and Job Search execution. [Intentionally deferred decisions](../../architecture/overview.md#intentionally-deferred-decisions).

## Handoff snapshot (8 October 2026)

| | |
|--|--|
| Current status | **In design.** Implementation **not started** |
| Implemented functionality | None for this feature. Text extraction, which would feed it, is implemented |
| Accepted decisions | Rules 1–17 above, with the explicit exceptions that are marked not finalized. Rule 3 is accepted in this discussion and conflicts with the written `SAFE_MERGE` policy |
| Open questions | The fifteen questions in this page, plus the discrepancies in the [decision register](../decision-register.md#unresolved-discrepancies) |
| Files changed for this feature | No application, test, or migration files |
| Tests executed | None for reconciliation. Existing tests cover extraction and the current schema only |
| Known limitations | No pause/resume runtime, no provenance tables, no policy implementation. Experience and date shapes differ between extraction models and ORM columns |
| Next recommended step | Resolve the `SAFE_MERGE` versus `PROPOSED_ADDITION` discrepancy and the open schema questions in the design conversation before any migration or workflow code |
