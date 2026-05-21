# Archive Query Policy

## Scope Boundaries

The default archive layout is:

```text
context-capture/
  archives/
    private/
    work/
    shared-safe/
```

Search only the authorized physical scope.
Treat `private`, `work`, and `shared-safe` as separate policy domains even if their metadata schema is the same.
Resolve the default layout relative to the sibling `context-capture` skill directory. Search legacy `~/context-archives/<scope>` only when the user explicitly authorizes that fallback or a migration check.
Use `python3 scripts/migrate_skill_data.py --only context-archives` from the skills root for a read-only dry-run migration check; do not apply it during a consult-only task unless the user authorized archive updates.

## Observer Lens and Absence Rule

Archives are observer-perspective records. They show what was captured from an authorized observation scope, not everything that happened.
Never reason from "no archive/memory record found" to "the event did not occur." Say "not found in the searched scope" and list the searched roots, terms, and timeframe.

In archive-grounded mode, cited archive records are the only evidence. Non-archive memory, loaded personal/developer principles, and prior chat context may help choose search terms, but must not become hidden evidence in findings.
Use memory-aware interpretation only when the user explicitly asks for it, and label it separately from archive evidence.

## Evidence Priority

1. Raw records with direct source text.
2. Derived records that cite raw records.
3. Derived-only records, clearly labeled as such.

Prefer raw records for responsibility boundaries, commitments, dates, and exact wording.
Use derived records for orientation, retrieval hints, and explicitly interpretive layers.

Derived record types:

- `derived-context`: environment supplements such as roles, organization structure, glossary terms, and operating rules. Check `last_updated` and `review_due`.
- `derived-stance`: durable observer judgment axes. Treat as a declared lens, not neutral fact.
- `derived-analysis`: cross-raw analysis such as trend, retrospective, evaluation, or bias-check work. Check `analysis_kind`, `source_refs`, and revision history.
- `derived-summary`, `derived-timeline`, `derived-decision`, `derived-note`: event-local interpretation.

When derived evidence conflicts with raw evidence, show both and give raw wording priority for exact claims.

## Search Heuristics

- Start with frontmatter terms: people, projects, topics, source, scope, sensitivity, dates.
- Include `record_type`, `observer_perspective`, `use_policies`, `analysis_kind`, `last_updated`, `review_due`, `supersedes`, and `revision_note` when the query depends on interpretation, staleness, or handling limits.
- Add raw text searches for distinctive phrases, issue ids, PR numbers, names, and aliases.
- Search by month directories when the timeframe is known.
- If the query is person-centric, include project-neutral searches inside the authorized scope.

## Use and Ethics

Respect `use_policies` in frontmatter.
For person evaluations or unconfirmed claims, default to internal-reference handling and rephrase before direct discussion with the person unless the archive record or user explicitly authorizes direct reuse.
Do not present observer-derived assessment as if the subject confirmed it.
If older records lack `observer_perspective`, `coverage_limitations`, or `use_policies`, treat that as a metadata gap and default to conservative handling; do not assume unrestricted sharing.

## Limits

Local evidence is a near-raw copy, not the source of truth.
If a decision requires current external state, ask the user to provide fresh source material or use a connector/MCP only when available and authorized.
Raw captures may omit edited/deleted source messages, lost formatting, offline conversations, adjacent channels, or material outside the observer's access.
