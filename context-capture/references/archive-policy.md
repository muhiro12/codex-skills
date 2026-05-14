# Context Archive Policy

## Purpose

Maintain a local evidence archive that future AI agents can read as decision context.
This is not a human-first note system and not a replacement for Slack, Backlog, GitHub, ChatGPT, or any other original source.

## Storage Boundaries

Use the same logical schema across domains, but keep physical roots separate:

```text
~/context-archives/
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

Do not create a cross-domain root that mixes private and work raw data.
Ask before moving or copying work material into `shared-safe`.

## Raw vs Derived

- `raw` is the near-original evidence copy.
- `derived` is an agent-created interpretation, summary, timeline, or decision memo.
- Derived records must cite raw records through `source_refs`.
- Raw records should not be edited for meaning after capture; add a new raw record or derived note instead.

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
- `record_type`: `derived-summary`, `derived-timeline`, `derived-decision`, or `derived-note`.
- `source_refs`: array of raw or derived file paths.
- `created_at`: ISO timestamp with timezone.

## Redaction

Prefer user-approved masking before writing sensitive content.
Use explicit inline redaction markers so later agents know the copy is not fully raw.
Do not silently remove names, obligations, dates, or responsibility boundaries.

## Not in v1

Do not require SQLite, embeddings, normalized records, hooks, MCP connectors, or Obsidian.
Markdown plus YAML frontmatter is the v1 contract.
Add heavier indexing only after manual archive use exposes a real retrieval problem.
