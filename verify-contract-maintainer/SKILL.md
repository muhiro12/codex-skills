---
name: verify-contract-maintainer
description: Define, audit, and maintain a minimal verification contract for repositories that already have or are deliberately adopting Xcode-native evidence, `ci_scripts`, or retained repository-rule scripts, so verification expectations stay predictable, Xcode selections are restored after checks, commit-time hooks stay lightweight, and tool-name drift is contained without broad rewrites.
---

# Verify Contract Maintainer

## Overview

Define and enforce a small, practical verification contract for repositories that already have Xcode-native checks, `ci_scripts`, or retained repository-rule scripts.
Keep repository behavior stable by preferring low-risk normalization and explicit reporting over broad rewrites.
Treat this skill as the owner of contract-level maintenance: `AGENTS.md` alignment, entrypoint or MCP-check normalization, push/manual routing for heavy checks, and compatibility-first upkeep.
Do not use this skill to design first-pass Apple-platform verification scaffolding from Xcode project layout, `Package.swift`, or sibling reference repositories. Use `$apple-repo-verify-bootstrapper` for that initial bootstrap work.

## Xcode Skill Catalog

When `sync-xcode-skills/state/catalog.md` exists under the active Codex skills
root, scan it for task-relevant Xcode-provided `xcode-skill-*` guidance before
applying this skill's local Xcode-native or Apple verification-contract
heuristics. Do not hardcode individual Xcode-provided skill names. If the
catalog is missing or no listed skill matches, continue with this skill
normally.

## Trigger Conditions

Use this skill when the user asks for topics such as:

- Xcode-native integration の build/test/run 契約を監査したい
- `AGENTS.md` の scheme、destination、MCP action 記述を揃えたい
- `ci_scripts` 採用後の最小契約を整えたい
- verify系スクリプトの名前揺れを減らしたい
- `AGENTS.md` の検証入口記述と実体を一致させたい
- 重い verify を commit 時ではなく push 前または手動実行へ寄せたい
- 契約を満たしているかだけ監査したい
- 既存 verify 導線を大きく変えずに軽量メンテしたい

## Contract Definition

For repositories in scope, use this contract:

1. Required:
- `AGENTS.md` documents the repository's verification contract.
- Any documented repository-managed shell command resolves to an executable script.
- Any documented Xcode-native check names the project/workspace, scheme,
  intended destination family, test plan or test identifiers when relevant,
  and the evidence capability it requires.
- Repository contracts describe stable capabilities rather than volatile MCP
  namespaces or action names. Runtime agents resolve the current discovery,
  selection, build, test, run/log, Preview, and live UI actions from the
  available tool inventory. Exact names belong only in executable adapters,
  runtime configuration, or narrowly scoped compatibility notes.
- The contract requires an agent to record the original active scheme and destination before switching them, restore the original scheme and then its destination after the check, and report any selection it could not restore.
- The contract distinguishes concrete verification capabilities, such as
  library/package tests, app or surface builds, retained repository-rule checks,
  and targeted runtime/UI evidence, without turning every repository file into a
  full cross-repository decision playbook.

2. Recommended:
- `ci_scripts/tasks/check_repository_rules.sh` for retained static rule checks
  that are not naturally covered by the active Xcode-native integration.
- Workspace/project discovery plus scheme and destination discovery for
  original-selection capture.
- A surface-build capability and an all-tests or targeted-tests capability for
  the selected scheme and test plan.
- A bounded run, runtime-log inspection, and stop lifecycle for non-interactive
  runtime evidence.
- Direct SwiftUI Preview rendering when Preview evidence is required.
- A bounded live UI session that installs/runs, captures hierarchy,
  screenshots, logs, orientation, and interactions, and always ends the
  session.
- Short risk-based selection guardrails, for example when public APIs, persisted
  schema, wire contracts, package products, lifecycle wiring, or visible UI
  behavior require stronger evidence than the narrowest local check.
- `ci_scripts/tasks/verify_task_completion.sh` only when the repository intentionally keeps an aggregate shell gate.

3. Optional:
- `ci_scripts/tasks/verify_repository_state.sh` as a repo-state check surface when run artifacts or broader repository checks are intentionally retained.
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
  - Add missing documentation or compatibility pieces only when the repository
    already has a coherent Xcode-native or deliberately retained `ci_scripts`
    direction.
  - Prefer creating only the smallest required set.
  - This is not first-pass Apple build/test surface discovery; hand that to `$apple-repo-verify-bootstrapper`.

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
  - aggregate shell gate
  - retained repository-rule check
  - Xcode-native build/test/runtime/Preview/device evidence
  - repo-state check
  - optional push wrapper
- Mark each role as `present`, `missing`, or `non-standard but acceptable`.

3. Decide action set by mode.
- In `report-only`, produce findings and a minimal patch plan only.
- In `bootstrap` or `maintenance`, apply only low-risk minimal-diff updates.
- If `bootstrap` would require discovering app/package verification surfaces from scratch, stop and route the task to `$apple-repo-verify-bootstrapper` instead.

4. Normalize with minimal blast radius.
- Keep existing entrypoint behavior unless broken.
- If standard filenames are absent but an equivalent entrypoint exists, prefer documenting and wrapping before replacing.
- Keep script names, interfaces, and invocation compatibility stable where possible.
- Do not expand scope into Apple-specific build surface discovery or sibling-reference-repo alignment.

5. Verify and summarize.
- Resolve and run the documented Xcode-native capabilities plus retained rule
  checks that are available. Record the original active scheme and destination,
  switch only when required, restore the original scheme and then destination
  after the checks, and report any unavailable capability or failed
  restoration.
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
- Do not translate a missing third-party MCP namespace by guesswork. Treat a
  specialist that requires unavailable tools as optional and resolve the
  required evidence through the active Xcode-native tool inventory.

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
- Keep public metadata and prompts clear that this skill maintains an existing or intentionally adopted verify contract; it does not design Apple verification scaffolding from scratch.
