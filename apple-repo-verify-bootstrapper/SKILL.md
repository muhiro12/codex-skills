---
name: apple-repo-verify-bootstrapper
description: Bootstrap first-pass Apple-platform repository verification by deriving an `AGENTS.md` capability-based Xcode-native evidence contract from the real Xcode and Swift package surfaces, then adding repository-local format, lint, static-rule, or otherwise uncovered scripts only when needed. Use sibling repositories only as read-only fallback evidence.
---

# Apple Repo Verify Bootstrapper

## Overview

Use this skill when an Apple-platform repository still needs its first coherent
verification foundation, especially when Xcode project structure,
`Package.swift`, or mixed app-plus-package surfaces must be turned into an
Xcode-native evidence contract.
Return user-facing explanations in concise, practical Japanese.
Keep shell scripts, file names, commands, and repository documents in English unless the target repository already uses another convention.
Treat this skill as the owner of first-pass scaffolding and Apple-repo-specific verification design.
If the repository already has a coherent Xcode-native or deliberately retained
`ci_scripts` contract and only needs auditing, naming cleanup, `AGENTS.md`
alignment, or lightweight maintenance, use `$verify-contract-maintainer`
instead.
When the verification philosophy depends on the user's durable cross-repository workflow preferences, consult a local principle archive skill when available (for example `$track-developer-principles`) before deciding the target shape.

## Xcode Skill Catalog

When `sync-xcode-skills/state/catalog.md` exists under the active Codex skills root, scan it for task-relevant Xcode-provided `xcode-skill-*` guidance before applying this skill's local Apple verification heuristics. Do not hardcode individual Xcode-provided skill names. If the catalog is missing or no listed skill matches, continue with this skill normally.

## Trigger Conditions

Use this skill when the user asks for things such as:

- `Apple repo の verify 基盤を新設して`
- `Xcode project と Package.swift を見て Xcode-native の検証契約を作って`
- `app と package の mixed surface を踏まえて build/test/run の証跡を初期設計して`
- `参照用の sibling repo を参考に Apple repo の検証 scaffolding を揃えて`
- `まだ形になっていない verify 導線を Apple 系 repo 向けに整えて`

## Workflow

1. Inspect the current repository first.
- Read the current repository's `AGENTS.md`, top-level layout, Xcode project structure, `Package.swift`, `ci_scripts`, hook config when present, and any existing build/test/lint commands.
- Determine the real Apple-repo verification surfaces the repository needs: app or extension builds, package or test-plan tests, Preview evidence, runtime logs, live UI evidence, retained lint/static rules, app-only checks, package-only checks, or mixed surfaces.

2. Consult a local principle archive skill second when workflow philosophy matters.
- Use it for recurring preferences around verification entrypoints, non-destructive final gates, documentation expectations in `AGENTS.md`, and the balance between strictness and maintainability.
- Treat explicit repository constraints and direct user instructions as higher priority than older archived principles when they conflict.

3. Inspect a locally available sibling reference repository third only when needed.
- If a locally available sibling reference repository is available and relevant, use it as a read-only reference when the current repository lacks a coherent pattern or the user explicitly wants alignment.
- Learn reusable workflow structure, not finance-specific behavior or app-specific naming.

4. Establish the Xcode-native evidence contract first.
- Inspect the current tool inventory and resolve the available Xcode-native
  discovery, selection, build, test, run/log, Preview, and live UI
  capabilities by their schemas and descriptions. Do not assume a namespace or
  action spelling.
- Use workspace/project discovery to identify the current repository context,
  then discover the real active and available schemes and destinations. Treat
  runtime-only context handles as ephemeral session state; do not write them
  into repository files.
- Document concrete project/workspace paths, schemes, destination families, test plans or targeted tests, and the smallest evidence needed for each repository boundary.
- Map those boundaries to stable evidence capabilities: surface build, all or
  targeted tests, bounded launch/log/stop, direct Preview rendering, or a
  bounded live UI lifecycle with screenshots, hierarchy, logs, orientation,
  and interaction.
- Require agents to record the original scheme and destination, including the
  current integration's unambiguous restoration handles, before switching
  them. When checks finish, restore the original scheme first and its original
  destination second, then rediscover both to confirm. Report any selection
  that could not be restored.
- Shape the initial contract from observed Apple surfaces rather than starting from a generic verify template or a shell aggregate.

5. Add retained shell checks only for uncovered responsibilities.
- Add or retain shell scripts only for formatting or autofix, lint,
  repository-specific static/policy rules, temporary compatibility, or
  evidence the active Xcode-native integration does not naturally provide.
- Keep repo-managed autofix commands such as `format_swift.sh` explicit and separate from the final non-destructive verification pass.
- Do not force `SwiftLint` or any other tool unless the target repository already uses it or the user explicitly asks for it.
- Add an aggregate shell or push wrapper only when the repository intentionally retains that interface; do not make it the first-pass build/test contract.

6. Document and wire the surrounding workflow.
- Ensure `AGENTS.md` documents stable Xcode-native evidence capabilities and
  boundaries first, with retained shell commands in a separate role. Keep
  volatile action or namespace names out of the repository contract.
- Keep build/test/run verification in the documented Xcode-native contract. If
  hook config exists, reserve optional push-time wrappers for retained
  uncovered checks and keep commit-time hooks lightweight or absent.
- If `.pre-commit-config.yaml` already carries heavy Apple build/test
  verification, migrate that responsibility to the Xcode-native contract. Move
  only retained format/lint/static/uncovered shell checks to direct execution
  or an optional push-time wrapper.
- Do not install user-level hooks or mutate global Git configuration. Keep any hook guidance repository-local and optional unless the user explicitly asks for active hook setup.
- Prefer result artifacts supplied by the active Xcode-native integration,
  such as build logs, test summaries, `xcresult` bundles, Preview snapshots,
  screenshots, hierarchies, and runtime logs. Use
  `.build/ci/runs/<RUN_ID>` only when a retained repository script
  intentionally creates those artifacts.
- When run artifacts exist, read only the newest `.build/ci/runs/<RUN_ID>` for diagnosis.
- Do not scan older runs under `.build/ci/runs/`.
- If the work exposes a clearly reusable cross-repository verification principle and a local principle archive skill such as `$track-developer-principles` is available, surface the candidate after stabilizing the repo-level change. Persist it only when the user explicitly requests or approves that archive write.
- Leave post-bootstrap contract auditing and naming-only maintenance to `$verify-contract-maintainer`.

7. Verify and report.
- Run the repository's new or updated Xcode-native contract before finishing:
  select the intended scheme/destination only when necessary, execute the
  smallest documented build/test/run/Preview/device evidence set, and restore
  the original active selection afterward.
- Run retained format/lint/static-rule scripts when they are part of the contract.
- Treat current-change or clearly introduced build/test/lint/warning failures as blocking.
- If warnings or errors clearly come from pre-existing code or external packages, call them out separately without pretending the current change introduced them.

## Guardrails

- Never modify a sibling reference repository.
- Never invent a large local verification matrix when a small set of
  Xcode-native evidence capabilities proves the repository boundaries.
- Never let archived principles override hard repository constraints or direct user instructions.
- Never make commit-time hooks the primary enforcement path for heavy
  verification; the repository must remain verifiable through its documented
  Xcode-native capabilities plus any retained rule scripts.
- Never present pre-commit wiring or an aggregate shell as the default setup for newly bootstrapped Apple verification.
- Never hard-code a tool such as `SwiftLint` when the target repository's actual workflow does not require it.
- Never translate a missing third-party MCP namespace by guesswork. Treat a
  specialist skill that requires unavailable tools as optional and keep the
  active Xcode-native contract authoritative.
- Do not use this skill for repositories that already have a coherent verify scaffold and only need contract-level maintenance or naming cleanup.
- Ask the user only when the repository surfaces are ambiguous enough that you cannot decide what should be verified.

## Output Contract

Return concise Japanese with:

1. `結論`
2. `現状把握`
3. `整備方針`
4. `変更内容`
5. `検証`
6. `保留事項`
