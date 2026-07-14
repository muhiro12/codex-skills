---
name: context-consult
description: Search and read local context archives to produce cited context packs from prior near-raw evidence and derived notes. Use only when the user explicitly invokes $context-consult; do not invoke implicitly for natural-language archive searches, saving new evidence, summarizing newly pasted material, or browsing external source systems.
---

# Context Consult

## Overview

Use this skill to answer a current question with evidence from local context archives.
Stay read-only: consult files, cite paths, and surface gaps, but do not create or modify archive records.
Treat archive evidence as observer-perspective evidence: useful but partial records from the authorized observation scope, not proof that uncaptured events did not happen.

## Trigger Policy

Trigger this skill only when the user explicitly invokes `$context-consult`.
Treat a natural-language request to consult, search, retrieve, look up, or use a local context archive without the skill name as insufficient to invoke this privacy-sensitive workflow.
Do not trigger automatically just because prior evidence might be useful, and do not search local archives for ordinary repository or personal-principle tasks unless the user asks to use archived context.
This skill is read-only even when triggered.

## Resources

- Read `references/context-pack-format.md` when shaping the final answer.
- Read `references/archive-query-policy.md` when scope boundaries, sensitivity, or raw-vs-derived weighting are unclear.
- Use `references/trigger-prompts.csv` only when auditing whether the skill should trigger.

## Workflow

1. Resolve the query and allowed archive scope.
- Identify requested people, projects, topics, timeframe, source, and sensitivity filters.
- Identify the evidence mode. Default to archive-grounded mode: use only cited archive records as evidence, and do not let non-archive memory or prior conversation context become hidden evidence.
- For evaluations of people, responsibilities, intent, or performance, separate the archive observer view from neutral caveats. Use memory-aware interpretation only when the user explicitly asks for it.
- Default roots are the sibling `context-capture` skill's `archives/private`, `archives/work`, and `archives/shared-safe` directories, but search only the scope the user requested or clearly authorized.
- Treat legacy `~/context-archives/<scope>` roots as migration or explicitly requested fallback sources only.
- If the skill-owned archive is missing or appears empty, run `python3 scripts/migrate_skill_data.py --only context-archives` from the skills root as a dry-run check. Because this skill is read-only, do not apply the migration unless the user asked to migrate or the current task already authorizes updating local archive files.
- When dry-run finds legacy files and no migration is applied, report that legacy evidence exists and either search the authorized legacy scope read-only or ask before crossing the migration boundary.
- Do not search `private` and `work` together unless the user explicitly asks for both and the boundary is appropriate.
- Ask a concise clarification when the root or scope cannot be inferred safely.

2. Build a targeted search plan.
- Prefer `rg --files` and targeted `rg -n` searches over broad file reads.
- Search frontmatter fields such as `people`, `projects`, `topics`, `source`, `scope`, `sensitivity`, `use_policies`, `observer_perspective`, `record_type`, `analysis_kind`, `occurred_at`, `captured_at`, `last_updated`, and `review_due`.
- Search raw text for exact names, handles, issue keys, PR numbers, project aliases, and distinctive phrases from the user query.

3. Read candidates with source weighting.
- Read raw records before derived records when both match.
- Use derived records for orientation, timelines, environment context, stance notes, and retrieval hints, but verify important claims against raw records where available.
- If only derived evidence is found, label it as derived-only and include the missing raw source gap.
- Treat `derived-context`, `derived-stance`, and `derived-analysis` as interpretation layers. Check their `source_refs`, `last_updated`, `review_due`, `supersedes`, and `revision_note` before relying on them.

4. Keep boundaries intact.
- Do not copy private evidence into a work answer unless the user explicitly authorized that scope crossing.
- Do not assume local archive copies are exhaustive or more authoritative than the original source system.
- Do not infer "not recorded" as "did not happen." Report it as not found in the searched scope.
- Do not treat non-archive memory, loaded principles, or prior chat context as archive evidence unless the user explicitly authorizes a memory-aware answer; if used, label it separately from cited archive evidence.
- Do not infer responsibilities, intent, or commitments beyond the cited evidence.
- Respect `use_policies`. For person evaluation or unconfirmed claims, avoid directly reusable wording when the policy includes `rephrase-before-direct-discussion`.
- If older records lack `observer_perspective`, `coverage_limitations`, or `use_policies`, label those fields as legacy metadata gaps rather than assuming unrestricted use.

5. Produce a context pack.
- Cite every material point with file paths.
- Include source ids or timestamps when present.
- Quote only short, necessary snippets; otherwise paraphrase with citations.
- Separate high-confidence evidence, observer-perspective caveats, usage constraints, stale derived records, and gaps.

## Output Contract

Return a concise context pack in the user's language; for Japanese conversations, use concise, polite Japanese.
Use these sections:

1. `Context Pack`
2. `Scope`
3. `Perspective / Evidence Mode`
4. `High-Confidence Evidence`
5. `Timeline`
6. `People / Projects / Topics`
7. `Use Constraints / Staleness`
8. `Gaps`
9. `Files Consulted`

If no relevant evidence is found, return the searched scope, terms, and what metadata or source material would be needed for a useful capture.
