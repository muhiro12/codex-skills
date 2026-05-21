---
name: context-capture
description: Save user-provided conversations, copied threads, transcripts, decisions, or manual notes as near-raw Markdown evidence in a local context archive. Use when the user explicitly invokes $context-capture or asks to capture, archive, preserve, or save pasted material as local evidence for later AI consultation; do not use for ordinary summarization, general note taking, or searching an existing archive.
---

# Context Capture

## Overview

Use this skill to create local, AI-readable evidence records from material the user provides.
Treat the original Slack, Backlog, GitHub, ChatGPT, transcript, or manual source as the source of truth; the archive copy is a near-raw local trace.
Treat every archive record as an observer-perspective trace: useful evidence from a specific viewpoint, not an exhaustive or neutral copy of reality.

## Trigger Policy

Trigger this skill only when the user explicitly invokes `$context-capture` or clearly asks to save, capture, archive, preserve, or store provided material as local evidence.
Do not trigger automatically from ordinary conversation, from a request for a summary, or merely because a discussion contains useful context.
Writing archive records requires explicit capture intent, and ambiguous scope, sensitivity, destination, or redaction policy requires confirmation before writing.

## Resources

- Read `references/archive-policy.md` before the first capture in a session or whenever scope, sensitivity, redaction, or storage boundaries are unclear.
- Use `references/archive-frontmatter.schema.json` as the machine-readable v1 frontmatter contract when validating or porting the format.
- Use `references/trigger-prompts.csv` only when auditing whether the skill should trigger.
- Use `assets/raw-capture.md` for raw evidence files.
- Use `assets/derived-summary.md` as the starting template for derived records; change `record_type`, filename suffix, and body sections to match the derived purpose.
- Run `scripts/validate_frontmatter.py <markdown-file>` after writing a raw or derived Markdown record.
- Run `python3 scripts/backfill_archive_metadata.py` from the `context-capture` skill directory after updating this skill on a machine with existing archive files; review the dry-run and use `--apply` only when the metadata additions are acceptable.

## Workflow

1. Confirm the capture intent.
- Proceed only when the user explicitly wants material saved or archived.
- If the user only asks for a summary, answer normally without writing archive files.
- If no source material is present, ask the user to provide the pasted text, transcript, copied thread, or manual note.

2. Resolve the archive boundary before writing.
- Default archive roots are this skill's `archives/private`, `archives/work`, and `archives/shared-safe` directories.
- Resolve those paths relative to the `context-capture` skill directory, not the current repository.
- Use another archive root only when the user or current repository clearly specifies one.
- Treat legacy `~/context-archives/<scope>` roots as read-only migration sources unless the user explicitly asks to keep writing there.
- After this skill is installed or updated from GitHub, run `python3 scripts/migrate_skill_data.py --only context-archives` from the skills root before the first write if `archives/` is missing or empty.
- If the dry-run reports legacy archive files, run `python3 scripts/migrate_skill_data.py --only context-archives --apply` before writing new captures, unless the volume, scope, or sensitivity requires confirmation.
- The migration copies only missing targets and never overwrites conflicting files. Resolve conflicts manually before writing into the same scope.
- If existing archive Markdown files predate `observer_perspective`, `coverage_limitations`, or `use_policies`, run `python3 scripts/backfill_archive_metadata.py` in this skill directory and apply it only after reviewing the planned metadata-only edits.
- Never mix `private` and `work` in the same physical root.
- If scope, sensitivity, destination path, or masking policy is ambiguous, ask before writing.

3. Preserve the raw body.
- Keep the provided text as close to the source as practical.
- Do not rewrite raw dialogue into prose.
- Apply only user-approved masking or minimal formatting needed to preserve readability.
- Mark redactions inline, for example `[redacted: customer name]`, so later agents can see that the raw copy was altered.
- Record known capture limits in `coverage_limitations` when relevant, such as copied excerpts, edited or deleted source messages, lost formatting, missing channels, or offline/phone/context gaps.

4. Build required metadata.
- Use `record_type: raw` for raw evidence.
- Use an id shaped like `YYYY-MM-DD-scope-source-###`, for example `2026-05-15-work-slack-001`.
- Set `captured_at` to the current local timestamp with timezone.
- Set `occurred_at` from the source when known; otherwise use `null`.
- Fill `people`, `projects`, `topics`, and `attachments` as arrays, using `[]` when none are known.
- Fill `observer_perspective` with the viewpoint or source boundary represented by the record, for example `user-provided-observer-record`.
- Fill `coverage_limitations` as an array, using `[]` only when no limitation is known.
- Fill `use_policies` as an array of usage labels such as `internal-reference-only`, `do-not-share-externally`, `rephrase-before-direct-discussion`, `may-share-after-redaction`, or `unknown`.
- Use conservative values; do not invent people, projects, topics, dates, or sensitivity.

5. Preview before saving.
- Show the destination path, scope, sensitivity, use policies, observer perspective, metadata, and any redactions.
- Ask for confirmation before creating or modifying archive files unless the user has already given explicit save instructions for the exact destination and metadata.

6. Write without overwriting.
- Place raw records under `<scope>/raw/YYYY/MM/<id>.md` inside this skill's `archives/` directory.
- If the path already exists, choose the next sequence number or ask the user.
- Treat raw files as immutable-ish: later corrections should become a new raw capture or a derived note rather than an in-place rewrite.

7. Add derived records only when useful.
- Place derived records under `<scope>/derived/YYYY/MM/<id>-<kind>.md` inside this skill's `archives/` directory.
- Include `source_refs` that point to the raw file paths.
- Keep derived notes clearly separate from raw evidence; never let a derived note replace the raw record.
- Use specific derived record types:
  - `derived-summary`, `derived-timeline`, `derived-decision`, and `derived-note` for event-local interpretation.
  - `derived-context` for environment supplements such as affiliations, organization structure, contract shape, tenure, glossary entries, and operating rules.
  - `derived-stance` for durable observer judgment axes or long-running evaluation principles that connect multiple events.
  - `derived-analysis` for cross-raw retrospectives, trend analysis, score/evaluation work, and long-range synthesis.
- Name cross-raw analysis files with an analysis suffix, for example `<id>-analysis.md`, and add `analysis_kind` such as `trend`, `retrospective`, `evaluation`, or `bias-check`.
- For `derived-context` and any long-lived derived record, set `last_updated` and `review_due` when useful so stale people, role, organization, or operating-rule facts can be detected.
- When correcting a derived record, do not silently overwrite the prior claim. Either create a new derived record with `supersedes` or update the record with `revision_note` plus a visible `## Revision History` entry.
- Treat person evaluation and other sensitive interpretation as internal reference unless the user explicitly chooses a wider use policy. Use `rephrase-before-direct-discussion` when a claim should not be repeated verbatim to the person being discussed.

## Output Contract

Return user-facing explanations in concise, polite Japanese by default unless the user explicitly asks for another language.

After saving, report:

- raw file path and optional derived file path
- scope and sensitivity
- observer perspective and use policies
- validation result
- any unresolved metadata or evidence gaps
- whether any material was redacted or masked

If nothing was written, say so explicitly and explain the missing confirmation or missing input.
