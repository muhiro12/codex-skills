---
name: respect-incomes-architecture
description: Compare the current repository's architecture with a resolved read-only Incomes checkout when that comparison is requested or materially useful. Preserve app-local behavior and avoid copying incidental tooling or product complexity.
---

# Respect Incomes Architecture

## Overview

Use this skill to improve the current repository's outer architecture and development workflow by learning from a resolved local Incomes checkout without copying its product behavior.
Treat the current repository as the only writable target and treat `<incomes-root>` as a read-only reference for reusable architectural intent.
When the user has durable cross-repository architectural or workflow principles, consult `$track-developer-principles` before deciding how much Incomes alignment is actually desirable.
If stored principles identify a maintained platform foundation such as a local MHPlatform checkout as the portfolio source of truth for shared stack, reusable plumbing, or cross-app implementation direction, treat that principle as a higher-level constraint than superficial Incomes similarity.

## Reference Resolution

Resolve `<incomes-root>` once before reading it, in this order:

1. An explicit path supplied by the user or the current repository contract.
2. An `Incomes` sibling of the current repository root, after resolving that root from Git rather than assuming the process working directory.
3. `$HOME/Repositories/Incomes` when it exists.

Require the selected path to be an existing, readable directory distinct from the current writable repository. Canonicalize it before enforcing the read-only boundary. If no candidate is valid, report that the reference checkout is unavailable and continue only with repository evidence and stored principles; do not guess another path.

## Scope

Focus on reusable outer-architecture patterns such as:

- Repository structure
- Package, library, and app boundary design
- Shared-library boundaries justified by demonstrated reuse
- App-side adapter boundaries
- `ci_scripts` organization
- `verify.sh`, hook strategy, and build/test entrypoint philosophy
- `.build` artifact layout and run logging
- `AGENTS.md` conventions
- Overview, architecture, and ADR documentation patterns
- Naming and responsibility boundaries
- Reuse patterns that avoid over-generalization

Do not copy blindly:

- Domain-specific product logic
- App-specific UX decisions
- Finance-specific data models
- Accidental complexity
- Outdated or obviously app-specific conventions

## Workflow

1. Inspect the current repository first.
- Identify the actual writable target from the current working directory.
- Read the current repository's `AGENTS.md`, root layout, `Package.swift`, Xcode project structure, `ci_scripts`, docs, and verification entrypoints when relevant.
- Understand what problem the user is solving before using `<incomes-root>` as a reference.

2. Inspect `$track-developer-principles` second when the request depends on judgment.
- Use it to recover the user's stored cross-repository preferences about boundaries, maintainability, workflow philosophy, naming, reviewability, or abstraction strategy.
- Treat explicit task instructions and clear repository constraints as higher priority than older archived principles when they conflict.

3. Inspect platform-foundation context when relevant.
- If stored principles or the current request point to a maintained platform foundation such as MHPlatform, resolve its checkout from that evidence and inspect only the relevant files there as a read-only reference before comparing Incomes.
- Use this to understand current cross-app source-of-truth decisions, not to copy platform implementation into the target repository.
- Skip this step when the request is specifically about an Incomes-only pattern and no platform-foundation principle applies.

4. Resolve and inspect `<incomes-root>` as a read-only reference.
- Compare only the parts relevant to the user request.
- Prefer concrete files and directories such as `<incomes-root>/AGENTS.md`, `<incomes-root>/ci_scripts`, `<incomes-root>/.build`, docs folders, package boundaries, and app/library split points.
- Never modify files under `<incomes-root>`.

5. Extract intent, not surface similarity.
- Ask what architectural problem the Incomes pattern is solving.
- Separate reusable philosophy from app-specific implementation details.
- Call out explicitly when a pattern should be adapted rather than copied.

6. Compare from an outer-architecture perspective.
- Identify where the current repository diverges from good reusable parts of Incomes.
- Distinguish acceptable divergence from harmful inconsistency.
- Highlight where alignment would improve maintainability, reviewability, or workflow consistency.
- Preserve the current repository's better solution when it is clearly more appropriate.

7. Decide using this rule.
- First satisfy clear current-repository evidence and any relevant principle from `$track-developer-principles`.
- Preserve the maintained platform foundation's direction when a relevant stored principle makes it the current cross-app source of truth.
- If Incomes shows a clearly reusable outer-architecture pattern, prefer alignment.
- If the pattern is domain-specific or app-specific, do not copy it.
- If the current repository already has a better structure, keep it.
- When uncertain, explain both options and recommend the more maintainable one.

8. Implement or propose changes only in the current repository.
- Modify only files in the current repository.
- Keep changes scoped to the user's request.
- Prefer consistency with Incomes when it helps, but do not create fake symmetry.

9. Verify with the target repository's own workflow.
- Use the current repository's standard verification entrypoints, not Incomes commands, unless the user asked only for review.
- If adding or revising CI structure, ensure the resulting entrypoints are coherent for the current repository's actual build and test surfaces.

## Comparison Heuristics

Use `<incomes-root>` mainly to learn patterns like:

- How reusable logic is extracted into shared libraries without premature abstraction
- Which stable shared behavior belongs behind adapters and which product behavior remains app-local
- How `ci_scripts` provide stable entrypoints for humans and automation
- How `.build` artifacts and CI outputs are organized for inspection
- How `AGENTS.md` communicates repo-specific expectations
- How docs explain architecture decisions and responsibility boundaries

Treat these as warning areas where copying is usually wrong unless the user explicitly asks:

- Screens, product flows, and UI behavior
- Domain entities and persistence choices
- Naming tied to finance or app-specific concepts
- Complexity created by legacy compatibility that the current repository does not need

## Guardrails

- Never modify `<incomes-root>`.
- Never use `<incomes-root>` as a writable dependency or patch target.
- Never modify the resolved MHPlatform or any other platform-foundation checkout while using this skill unless that repository is the current writable target.
- Never recommend Incomes alignment that conflicts with an explicitly relevant principle from `$track-developer-principles` without saying so clearly.
- Never treat Incomes as the portfolio-wide source of truth when a stored principle points to a maintained platform foundation for the same concern.
- Never force domain similarity, UI similarity, or feature similarity.
- Never claim alignment is beneficial without pointing to concrete paths and reasoning.
- Say explicitly when an Incomes pattern looks weak, stale, or too app-specific to reuse.
- Ask the user only when the choice would materially affect architecture and cannot be resolved from repository evidence.

## Output Contract

Return explanations in concise, practical Japanese.
Use English for code, commands, file names, and identifiers.
Mention concrete file paths whenever they support a claim.

When reviewing or proposing changes, structure the response as:

1. `結論`
2. `参照箇所`
3. `差分評価`
4. `対応方針`
5. `変更内容` or `提案内容`
6. `検証`
7. `保留事項`

For `差分評価`, classify each major divergence as:

- `揃えるべき`
- `適応して取り入れるべき`
- `現状維持でよい`

## Example Requests

- `Incomesを参考にCI周りを整備して`
- `Incomesの設計方針を尊重してこのrepoを整理して`
- `AGENTS.mdやdocs構成をIncomes寄りにしたい`
- `shared library と app target の責務分離を見直したい`
- `verify.sh や .build の運用を Incomes 風に揃えたい`
- `このrepoの外側の設計を Incomes と比較してレビューして`

## Completion Checklist

- Inspect the current repository before `<incomes-root>`.
- Check relevant stored principles before treating Incomes as a pattern to copy.
- Inspect a resolved MHPlatform or another maintained platform-foundation checkout only when current principles or the task make it relevant.
- Treat `<incomes-root>` as read-only reference material only.
- Justify each alignment suggestion with intent, not imitation.
- Keep all modifications inside the current repository.
- State clearly when adaptation is better than direct copying.
