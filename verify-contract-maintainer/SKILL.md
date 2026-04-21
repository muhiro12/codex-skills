---
name: verify-contract-maintainer
description: Define, audit, and maintain a minimal verify contract for repositories that already have or are deliberately adopting `ci_scripts`, so verification entrypoints stay predictable, commit-time hooks stay lightweight, and name drift is reduced without broad rewrites.
---

# Verify Contract Maintainer

## Overview

Define and enforce a small, practical verification contract for repositories that already have `ci_scripts` or have already decided to adopt them.
Keep repository behavior stable by preferring low-risk normalization and explicit reporting over broad rewrites.
Treat this skill as the owner of contract-level maintenance: `AGENTS.md` alignment, entrypoint normalization, push/manual routing for heavy checks, and compatibility-first upkeep.
Do not use this skill to design first-pass Apple-platform verification scaffolding from Xcode project layout, `Package.swift`, or sibling reference repositories. Use `$apple-repo-verify-bootstrapper` for that initial bootstrap work.

## Trigger Conditions

Use this skill when the user asks for topics such as:

- `ci_scripts` 採用後の最小契約を整えたい
- verify系スクリプトの名前揺れを減らしたい
- `AGENTS.md` の検証入口記述と実体を一致させたい
- 重い verify を commit 時ではなく push 前または手動実行へ寄せたい
- 契約を満たしているかだけ監査したい
- 既存 verify 導線を大きく変えずに軽量メンテしたい

## Contract Definition

For repositories in scope, use this contract:

1. Required:
- `AGENTS.md` documents one standard verification entrypoint command.
- The documented command resolves to an executable repository-managed shell.

2. Recommended:
- `ci_scripts/tasks/verify_task_completion.sh` as the aggregate final gate.
- `ci_scripts/tasks/verify_repository_state.sh` as a repo-state check surface.

3. Optional:
- `ci_scripts/tasks/verify_pre_push.sh` as a push-compatible wrapper when local push hooks are desired.
- Hook configs such as `.pre-commit-config.yaml` only when needed for migration away from heavy commit-time checks or for lightweight local checks.
- `.build/ci/runs/<RUN_ID>` artifact conventions when the repository already uses run artifacts.

Do not require optional items when the repository has a different but coherent contract.

## Modes

Use one mode per run:

- `report-only`
  - Detect contract compliance and drift.
  - Propose a minimal bundle; do not modify files.

- `bootstrap`
  - Add missing minimal contract pieces in repositories that already adopted or are adopting `ci_scripts`.
  - Prefer creating only the smallest required set.

- `maintenance`
  - Normalize naming drift and stale wrappers while preserving external behavior.
  - Prefer wrappers or alias-safe transitions over destructive renames.

## Workflow

1. Inspect repository ground truth first.
- Read `AGENTS.md`, `ci_scripts/`, and existing hook config when present.
- Detect current or intentionally planned verify entrypoints before proposing changes.
- If the repository still lacks first-pass Apple-repo scaffolding entirely, hand the work to `$apple-repo-verify-bootstrapper` instead of inventing that structure here.

2. Build a contract map.
- Map current files to contract roles:
  - aggregate gate
  - repo-state check
  - optional push wrapper
- Mark each role as `present`, `missing`, or `non-standard but acceptable`.

3. Decide action set by mode.
- In `report-only`, produce findings and a minimal patch plan only.
- In `bootstrap` or `maintenance`, apply only low-risk minimal-diff updates.

4. Normalize with minimal blast radius.
- Keep existing entrypoint behavior unless broken.
- If standard filenames are absent but an equivalent entrypoint exists, prefer documenting and wrapping before replacing.
- Keep script names, interfaces, and invocation compatibility stable where possible.
- Do not expand scope into Apple-specific build surface discovery or sibling-reference-repo alignment.

5. Verify and summarize.
- Run repository-standard verification command when available.
- Report applied updates, remaining low-risk candidates, and manual-review items separately.

## Low-Risk Rules

Treat an update as low-risk only when all conditions are met:

- It keeps user-facing command behavior compatible.
- It stays within existing repository workflow scope (`ci_scripts`, `AGENTS.md`, related config).
- It avoids destructive moves or broad rewrites.
- It does not introduce new external dependencies.

Treat these as manual review:
- Renaming or removing widely-used entrypoint scripts without compatibility wrappers.
- Replacing repository-specific workflow philosophy with a forced convention.
- Broad hook-policy changes that alter lint/format semantics.

## Safety / Guardrails

- Do not require or introduce sibling reference repositories to define the contract.
- Do not scan historical generated artifacts unless explicitly requested.
- Do not enforce one hard-coded script name when repository-standard entrypoints already exist and are documented.
- Do not reintroduce heavy commit-time verification as the default path unless the user explicitly asks for it.
- Prefer compatibility-first normalization and clear reporting.
- Do not use this skill for first-time Apple-specific verify scaffolding or mixed app-package bootstrap design.

## Response Contract

Always return concise polite Japanese:

1. `契約チェック結果`
2. `適用または提案バンドル`
3. `残課題（手動レビュー）`

For each touched or assessed repository, include:
- resolved standard verification command
- contract role mapping
- applied vs pending items

## Workflow Alignment (skills-batch-auditor)

- Read only the newest `.build/ci/runs/<RUN_ID>/` artifacts when summarizing CI runs.
- Do not scan older runs under `.build/ci/runs/`.
