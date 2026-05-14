# Archive Query Policy

## Scope Boundaries

The default archive layout is:

```text
~/context-archives/
  private/
  work/
  shared-safe/
```

Search only the authorized physical scope.
Treat `private`, `work`, and `shared-safe` as separate policy domains even if their metadata schema is the same.

## Evidence Priority

1. Raw records with direct source text.
2. Derived records that cite raw records.
3. Derived-only records, clearly labeled as such.

Prefer raw records for responsibility boundaries, commitments, dates, and exact wording.
Use derived records for orientation and retrieval hints.

## Search Heuristics

- Start with frontmatter terms: people, projects, topics, source, scope, sensitivity, dates.
- Add raw text searches for distinctive phrases, issue ids, PR numbers, names, and aliases.
- Search by month directories when the timeframe is known.
- If the query is person-centric, include project-neutral searches inside the authorized scope.

## Limits

Local evidence is a near-raw copy, not the source of truth.
If a decision requires current external state, ask the user to provide fresh source material or use a connector/MCP only when available and authorized.
