---
name: apple-ios-dev-flow
description: Implement or refine Apple-platform app changes with a default workflow that uses current-repository evidence first, Apple official guidance second, and a locally available sibling reference repository as a read-only fallback before running the repository's standard verification shell.
---

# Apple iOS Dev Flow

## Overview

Use this skill as the default workflow for ordinary Apple-platform implementation requests.
Keep the workflow core in this file portable across agent runtimes where practical; platform-specific metadata can live beside the skill.
Return user-facing explanations in concise, practical Japanese.
Keep code, commands, file names, identifiers, and repository documents in English unless the target repository already uses another convention.
When implementation depends on recurring cross-repository judgment, consult a local principle archive skill when available (for example `$track-developer-principles`) before settling the approach.

## Trigger Conditions

Use this skill when the user asks to implement, fix, refactor, review, or continue work in an Apple-platform repository and no more specific sidecar skill is a better fit.

Prefer specialized skills instead for:

- string catalog maintenance
- SwiftUI preview audits
- SwiftData schema audits
- release-risk reviews
- release notes
- repository verification bootstrap or repair

## Decision Order

1. Start from current repository evidence.
- Read the affected code, tests, diagnostics, `AGENTS.md`, and `ci_scripts` first.
- Preserve the repository's better Apple-appropriate pattern when it is already clear.

2. Use a local principle archive skill second when judgment matters.
- Consult it when the task depends on tradeoffs such as maintainability, architecture direction, product intent, workflow philosophy, naming heuristics, or quality bars that may repeat across repositories.
- Treat explicit current-task instructions and hard repository constraints as higher priority than older archived principles when they conflict.

3. Use Apple official guidance third.
- When the implementation shape is still unclear, prefer Apple documentation, sample code, Human Interface Guidelines, WWDC material, and Swift guidelines.
- Prefer Apple or Swift official guidance over general web advice.

4. Use a locally available sibling reference repository fourth as a read-only fallback.
- If a locally available sibling reference repository is available and relevant, inspect it only after current-repo evidence plus Apple official guidance still do not settle the approach.
- Borrow reusable workflow or architecture intent, not app-specific UX, domain models, or naming.

## Workflow

1. Confirm repository workflow prerequisites.
- Resolve the repository's standard verification entrypoint from `AGENTS.md` first, then `ci_scripts/**/*.sh`, then repo-native aggregate commands.
- If the repository provides an explicit repo-managed autofix step for edited files such as `format_swift.sh`, treat it as part of the main implementation flow before the final verification gate.
- If the repository does not have a coherent standard shell for build/test/lint verification, switch to `$apple-repo-verify-bootstrapper` or tell the user that the repo needs that scaffolding first.

2. Implement with local evidence first.
- Inspect the target files, adjacent tests, and current diagnostics before editing.
- Keep the patch as small and local as the task allows.

3. Make implementation decisions in this order.
- current repository evidence
- a local principle archive skill when available and the decision is judgment-heavy
- Apple official guidance
- a locally available sibling reference repository read-only fallback
- State the deciding source when it materially influenced the implementation.

4. Harvest newly explicit durable judgment when appropriate.
- If the repository conversation reveals a clearly reusable cross-repository principle and a local principle archive skill such as `$track-developer-principles` is available, update it after the implementation is stable.
- Do not promote one-off local implementation details into archived principles.

5. Run the final gate before replying.
- If the repository provides an explicit autofix command, run it before the final gate so the last verification pass stays non-destructive.
- Review the actual diff for regressions, missing tests, and architecture drift.
- Run the repository's standard verification entrypoint.
- Treat current-change or clearly introduced build/test/lint/warning failures as blocking.
- If warnings or errors are clearly pre-existing or come from external packages, say so explicitly instead of attributing them to the current change.

6. Report clearly.
- Explain what changed, what decided the approach, what verification ran, and what remains unresolved.

## Guardrails

- Never start with a sibling reference repository.
- Never let archived principles override explicit user instructions or hard repository constraints.
- Never use non-Apple sources as the primary guidance when Apple official material is available.
- Never report success while current-change or clearly introduced verification issues remain unresolved.
- Never rely on `pre-commit` as the first place that auto-fixes SwiftLint issues; keep autofix in the main flow and leave the final gate non-destructive.
- Never rewrite repository artifacts into Japanese unless the task explicitly asks for that.

## Output Contract

Return concise Japanese with:

1. `変更内容`
2. `判断根拠`
3. `検証`
4. `保留事項`
