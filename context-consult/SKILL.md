---
name: context-consult
description: Search and read local context archives to produce cited context packs from prior near-raw evidence and derived notes. Use when the user explicitly invokes $context-consult or asks to consult, search, retrieve, or use a local evidence archive for a decision; do not use to save new evidence, summarize newly pasted material, or browse external source systems.
---

# Context Consult

## Overview

Use this skill to answer a current question with evidence from local context archives.
Stay read-only: consult files, cite paths, and surface gaps, but do not create or modify archive records.

## Trigger Policy

Trigger this skill only when the user explicitly invokes `$context-consult` or clearly asks to consult, search, retrieve, look up, or use a local context archive for the current decision.
Do not trigger automatically just because prior evidence might be useful, and do not search local archives for ordinary repository or personal-principle tasks unless the user asks to use archived context.
This skill is read-only even when triggered.

## Resources

- Read `references/context-pack-format.md` when shaping the final answer.
- Read `references/archive-query-policy.md` when scope boundaries, sensitivity, or raw-vs-derived weighting are unclear.
- Use `references/trigger-prompts.csv` only when auditing whether the skill should trigger.

## Workflow

1. Resolve the query and allowed archive scope.
- Identify requested people, projects, topics, timeframe, source, and sensitivity filters.
- Default roots are `~/context-archives/private`, `~/context-archives/work`, and `~/context-archives/shared-safe`, but search only the scope the user requested or clearly authorized.
- Do not search `private` and `work` together unless the user explicitly asks for both and the boundary is appropriate.
- Ask a concise clarification when the root or scope cannot be inferred safely.

2. Build a targeted search plan.
- Prefer `rg --files` and targeted `rg -n` searches over broad file reads.
- Search frontmatter fields such as `people`, `projects`, `topics`, `source`, `scope`, `sensitivity`, `occurred_at`, and `captured_at`.
- Search raw text for exact names, handles, issue keys, PR numbers, project aliases, and distinctive phrases from the user query.

3. Read candidates with source weighting.
- Read raw records before derived records when both match.
- Use derived records for orientation, timelines, and retrieval hints, but verify important claims against raw records where available.
- If only derived evidence is found, label it as derived-only and include the missing raw source gap.

4. Keep boundaries intact.
- Do not copy private evidence into a work answer unless the user explicitly authorized that scope crossing.
- Do not assume local archive copies are exhaustive or more authoritative than the original source system.
- Do not infer responsibilities, intent, or commitments beyond the cited evidence.

5. Produce a context pack.
- Cite every material point with file paths.
- Include source ids or timestamps when present.
- Quote only short, necessary snippets; otherwise paraphrase with citations.
- Separate high-confidence evidence from gaps and uncertainty.

## Output Contract

Return a concise context pack in the user's language; for Japanese conversations, use concise, polite Japanese.
Use these sections:

1. `Context Pack`
2. `Scope`
3. `High-Confidence Evidence`
4. `Timeline`
5. `People / Projects / Topics`
6. `Gaps`
7. `Files Consulted`

If no relevant evidence is found, return the searched scope, terms, and what metadata or source material would be needed for a useful capture.
