---
name: apple-repo-verify-bootstrapper
description: Prepare or repair Apple-platform repository verification scaffolding by establishing repo-specific `ci_scripts`, `AGENTS.md` entrypoints, and optional push-hook wiring for build, test, and lint workflows while using a locally available sibling reference repository only as a read-only reference.
---

# Apple Repo Verify Bootstrapper

## Overview

Use this skill when an Apple-platform repository does not yet have a coherent verification workflow, or when its `ci_scripts`, `AGENTS.md`, and local hook strategy need to be brought into a predictable shape.
Return user-facing explanations in concise, practical Japanese.
Keep shell scripts, file names, commands, and repository documents in English unless the target repository already uses another convention.
When the verification philosophy depends on the user's durable cross-repository workflow preferences, consult a local principle archive skill when available (for example `$track-developer-principles`) before deciding the target shape.

## Trigger Conditions

Use this skill when the user asks for things such as:

- `ci_scripts を整備して`
- `verify.sh を用意して`
- `build/test/lint の共通 shell を作って`
- `push 前に verify を走らせたい`
- `参照用の sibling repo を参考に repo の検証フローを整備して`

## Workflow

1. Inspect the current repository first.
- Read the current repository's `AGENTS.md`, top-level layout, Xcode project structure, `Package.swift`, `ci_scripts`, hook config when present, and any existing build/test/lint commands.
- Determine the real verification surfaces the repository needs: build, test, lint, app-only checks, package-only checks, or mixed surfaces.

2. Consult a local principle archive skill second when workflow philosophy matters.
- Use it for recurring preferences around verification entrypoints, non-destructive final gates, documentation expectations in `AGENTS.md`, and the balance between strictness and maintainability.
- Treat explicit repository constraints and direct user instructions as higher priority than older archived principles when they conflict.

3. Inspect a locally available sibling reference repository third only when needed.
- If a locally available sibling reference repository is available and relevant, use it as a read-only reference when the current repository lacks a coherent pattern or the user explicitly wants alignment.
- Learn reusable workflow structure, not finance-specific behavior or app-specific naming.

4. Establish one source of truth for verification.
- Prefer a repo-standard aggregate entrypoint such as `ci_scripts/tasks/verify_task_completion.sh`.
- Add supporting shell scripts only when they represent real repository surfaces that should stay independently runnable.
- When the repository benefits from role-based entrypoints, prefer explicit names such as `verify_task_completion.sh`, `verify_repository_state.sh`, and `verify_pre_push.sh`, and keep wrappers optional for compatibility only.
- Keep repo-managed autofix commands such as `format_swift.sh` explicit and separate from the final non-destructive verification gate.
- Keep build/test/lint execution repo-specific; do not force `SwiftLint` or any other tool unless the target repository already uses it or the user explicitly asks for it.

5. Align surrounding workflow contracts.
- Ensure `AGENTS.md` documents the standard verification entrypoint and any important run-artifact conventions.
- If hook config exists, prefer push-time wrappers for heavy verification and keep commit-time hooks lightweight or absent.
- If `.pre-commit-config.yaml` already carries heavy verification, migrate that responsibility to direct shell execution or an optional push-time wrapper instead of duplicating logic there.
- Prefer `.build/ci/runs/<RUN_ID>` when the repository needs inspectable run artifacts.
- When run artifacts exist, read only the newest `.build/ci/runs/<RUN_ID>` for diagnosis.
- Do not scan older runs under `.build/ci/runs/`.
- If the work exposes a clearly reusable cross-repository verification principle and a local principle archive skill such as `$track-developer-principles` is available, harvest it there after stabilizing the repo-level change.

6. Verify and report.
- Run the repository's new or updated standard verification entrypoint before finishing.
- Treat current-change or clearly introduced build/test/lint/warning failures as blocking.
- If warnings or errors clearly come from pre-existing code or external packages, call them out separately without pretending the current change introduced them.

## Guardrails

- Never modify a sibling reference repository.
- Never invent a large CI matrix when one stable repo-standard shell is sufficient.
- Never let archived principles override hard repository constraints or direct user instructions.
- Never make commit-time hooks the primary enforcement path for heavy verification; the repository must remain verifiable by directly running its standard shell scripts.
- Never hard-code a tool such as `SwiftLint` when the target repository's actual workflow does not require it.
- Ask the user only when the repository surfaces are ambiguous enough that you cannot decide what should be verified.

## Output Contract

Return concise Japanese with:

1. `結論`
2. `現状把握`
3. `整備方針`
4. `変更内容`
5. `検証`
6. `保留事項`
