---
name: product-overview-syncer
description: Maintain product overview documentation by conservatively synchronizing an existing overview Markdown file with current code reality. Use when asked to update, refresh, audit, or sync an existing product or architecture overview after code changes in services, app surfaces, app intents, widgets, or capabilities.
---

# Product Overview Syncer

## Overview

Use this skill to keep an existing product overview document synchronized with repository truth.
The output explanation should be concise, polite Japanese by default, while the overview document itself must keep its existing language and tone.
This skill is audit-first: detect doc drift against code, then apply only the smallest evidence-backed corrections needed to restore accuracy.

## Trigger Conditions

Use this skill when the user asks to:

- update or refresh an existing product overview
- audit architecture or feature summaries against current code
- sync product or architecture docs after implementation changes

## Workflow

1. Read the existing overview first.
- Use the user-provided path when present.
- Otherwise, locate the best existing overview under `docs/`.
- Read the current document before inspecting code changes so its section structure, emphasis, and tone become the baseline.
- Do not create a new overview file unless explicitly requested.

2. Detect drift.
- Compare the existing document against repository-visible facts only.
- Collect concrete evidence for:
  - new services
  - removed surfaces
  - new app intents
  - new widgets
  - new capabilities
- Treat this phase as an audit pass first: identify mismatches, omissions, and stale claims before editing anything.
- Do not edit the document during this phase.
- If a claim cannot be confirmed from code, mark it as uncertain and leave it untouched.

3. Apply minimal updates.
- Limit edits to the drift items confirmed in the detection phase.
- Edit only sections proven to be out of sync.
- Every changed sentence must map to at least one concrete code reference.
- Preserve heading hierarchy, section order, document scope, and writing tone from the existing document.
- Prefer line edits or short paragraph replacements over broad rewrites.
- Do not add new sections unless the existing structure clearly requires a small extension to reflect proven code reality.

4. Re-check the edited document.
- Confirm each update is traceable to evidence gathered during drift detection.
- Confirm unchanged sections remain structurally and tonally intact.
- Keep Markdownlint compatibility.

## Safety / Guardrails

- Never create a brand-new overview document unless the user explicitly asks for it.
- Never rewrite the whole document when targeted edits are sufficient.
- Never speculate about architecture, layering, ownership, intent, or future direction.
- Never introduce architectural changes that are not directly evidenced by code.
- Never remove sections unless code clearly shows the documented surface or capability was removed.
- Keep all edits traceable to concrete repository evidence.
- When uncertainty remains, preserve the existing wording instead of guessing.

## Response Contract

Return a concise Japanese report with:

1. `対象ファイル`
2. `変更セクション`
3. `根拠`: `変更セクション` ごとに、使用したコード上の根拠を短く列挙する
4. `見送り事項`: 不確実または根拠不足のため触れなかった事項を列挙する
5. `検証`

## Verification

- Re-read updated sections and confirm each changed statement maps to current code.
- Confirm unchanged sections preserve prior structure and tone.
- Confirm the diff reflects only detected drift and contains no speculative architectural edits.
