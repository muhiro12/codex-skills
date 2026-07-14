# Context Archive Policy

## Purpose

Maintain a local evidence archive that future AI agents can read as decision context.
This is not a human-first note system and not a replacement for Slack, Backlog, GitHub, ChatGPT, or any other original source.

## Storage Boundaries

Use the same logical schema across domains, but keep physical roots separate:

```text
context-capture/
  SKILL.md
  references/
  archives/
    private/
      raw/
      derived/
    work/
      raw/
      derived/
    shared-safe/
      raw/
      derived/
```

- `private`: personal material that should not be mixed with work evidence.
- `work`: work evidence that may be searched across work projects when permitted.
- `shared-safe`: masked or explicitly shareable fragments moved across boundaries on purpose.

Resolve `archives/` relative to the `context-capture` skill directory. The legacy
`~/context-archives/<scope>` layout may be used as a migration source, but new
captures should default to the skill-owned archive unless the user explicitly
chooses another root.

Use `python3 scripts/migrate_skill_data.py --only context-archives` from the
skills root as the standard dry-run migration check. Apply it only after the
scope and sensitivity are clear; it copies missing files and does not overwrite
conflicts.

Do not create a cross-domain root that mixes private and work raw data.
Ask before moving or copying work material into `shared-safe`.
Keep skill-owned archive directories owner-only (`0700`) and archive files owner-readable and owner-writable only (`0600`). `shared-safe` describes the content's approved use boundary; it does not make the local filesystem copy world-readable.
Do not follow symbolic links while discovering, migrating, validating in bulk, or backfilling archive files. Rewrite an approved existing record through a same-directory temporary file and atomic replacement.

## Evidence Layers

- `raw` is the near-original evidence copy, but it is still a cut-out from the source system and may omit edited messages, deleted messages, missing channels, lost formatting, offline conversations, or material outside the user's observation.
- `derived` is an agent-created interpretation, summary, timeline, decision memo, context document, stance note, or cross-raw analysis.
- Derived records must cite raw records through `source_refs`.
- Raw records should not be edited for meaning after capture; add a new raw record or derived note instead.

Use these derived record types as the official places for non-raw knowledge:

- `derived-summary`, `derived-timeline`, `derived-decision`, `derived-note`: event-local interpretation.
- `derived-context`: environment supplements such as people roles, affiliations, organization structure, contract shape, tenure, glossary entries, and operating rules.
- `derived-stance`: durable observer judgment axes or long-running evaluation principles.
- `derived-analysis`: cross-raw retrospectives, trend analysis, score/evaluation work, and long-range synthesis.

For cross-raw analysis, prefer filenames ending in `-analysis.md` and include `analysis_kind` such as `trend`, `retrospective`, `evaluation`, or `bias-check`.

## Observer Perspective

Archives are records collected from one observer's viewpoint or from material that observer provided.
Frontmatter should include `observer_perspective` for new records. During later evaluation, treat the archive as "observed evidence" rather than a neutral map of all events.
Do not infer that missing archive or memory evidence means an event did not occur; absence means only "not found in the searched/authorized observation scope."

## Use Policies

`sensitivity` classifies the content. `use_policies` constrains how it may be used.
Use these labels when applicable:

- `internal-reference-only`
- `private-reference-only`
- `work-internal-only`
- `do-not-share-externally`
- `rephrase-before-direct-discussion`
- `may-share-after-redaction`
- `unknown`

For person evaluations or claims the subject has not confirmed, default to internal reference and prefer `rephrase-before-direct-discussion` unless the user explicitly authorizes a different handling policy.

## Metadata Fields

Raw records require:

- `id`: stable archive identifier.
- `record_type`: `raw`.
- `source`: `slack`, `backlog`, `github`, `chatgpt`, `transcript`, `manual`, `email`, or `other`.
- `scope`: `private`, `work`, or `shared-safe`.
- `capture_method`: `paste`, `manual`, `copy`, `transcript`, `import`, or `other`.
- `captured_at`: ISO timestamp with timezone.
- `occurred_at`: source event timestamp, or `null` if unknown.
- `people`: array of people or handles.
- `projects`: array of project names or ids.
- `topics`: array of retrieval terms.
- `sensitivity`: `public`, `internal`, `masked-work`, `private`, `confidential`, `restricted`, or `unknown`.
- `cross_project`: boolean.
- `attachments`: array of relative or absolute attachment paths.

Derived records require:

- `id`
- `record_type`: `derived-summary`, `derived-timeline`, `derived-decision`, `derived-note`, `derived-context`, `derived-stance`, or `derived-analysis`.
- `source_refs`: array of raw or derived file paths.
- `created_at`: ISO timestamp with timezone.

New raw and derived records should also include:

- `observer_perspective`: short description of the viewpoint or source boundary represented by the record.
- `coverage_limitations`: array of known evidence limits, or `[]`.
- `use_policies`: array of handling labels.

Long-lived derived records should include:

- `last_updated`: ISO timestamp for the last content update.
- `review_due`: ISO timestamp or `null` for staleness review.
- `supersedes`: array of prior derived records replaced by this record, if any.
- `revision_note`: short note explaining the latest correction or update, if any.

## Redaction

Prefer user-approved masking before writing sensitive content.
Use explicit inline redaction markers so later agents know the copy is not fully raw.
Do not silently remove names, obligations, dates, or responsibility boundaries.

## Revision History

Raw records are immutable-ish. Correct raw misunderstanding through a new raw capture or a derived correction note.
Derived records may be updated, but corrections must leave a visible trail through `supersedes`, `revision_note`, and/or a `## Revision History` body section.
Never silently replace an earlier person-role, count, responsibility, or evaluation claim.

## Metadata Backfill

Existing archive files created before the observer/use-policy fields remain readable.
Use `python3 scripts/backfill_archive_metadata.py` from the `context-capture` skill directory to dry-run metadata-only additions, then rerun with `--apply` only after reviewing the planned changes.
The backfill must not rewrite raw bodies, reclassify old derived records, or infer new facts. It may add conservative metadata such as legacy coverage limitations, unknown raw use policy, internal-reference derived use policy, and derived lifecycle fields.
It must skip symbolic links and non-Markdown files and must replace an accepted regular file atomically.

## Not in v1

Do not require SQLite, embeddings, normalized records, hooks, MCP connectors, or Obsidian.
Markdown plus YAML frontmatter is the v1 contract.
Add heavier indexing only after manual archive use exposes a real retrieval problem.
