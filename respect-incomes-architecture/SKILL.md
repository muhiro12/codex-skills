---
name: respect-incomes-architecture
description: Develop, review, refactor, or add repository/tooling structure in the current repository while using `../Incomes` as a read-only architectural reference. Use when requests mention aligning with Incomes for repository structure, package and app boundaries, shared-library-first design, adapter boundaries, `ci_scripts`, `verify.sh`, hook strategy or build/test entrypoints, `.build` run artifacts, `AGENTS.md`, overview or ADR documentation, or maintainability-oriented outer architecture review.
---

# Respect Incomes Architecture

## Overview

Use this skill to improve the current repository's outer architecture and development workflow by learning from `../Incomes` without copying its product behavior.
Treat the current repository as the only writable target and treat `../Incomes` as a read-only reference for reusable architectural intent.
When the user has durable cross-repository architectural or workflow principles, consult `$track-developer-principles` before deciding how much Incomes alignment is actually desirable.

## Scope

Focus on reusable outer-architecture patterns such as:

- Repository structure
- Package, library, and app boundary design
- Shared-library-first extraction strategy
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
- Understand what problem the user is solving before using `../Incomes` as a reference.

2. Inspect `$track-developer-principles` second when the request depends on judgment.
- Use it to recover the user's stored cross-repository preferences about boundaries, maintainability, workflow philosophy, naming, reviewability, or abstraction strategy.
- Treat explicit task instructions and clear repository constraints as higher priority than older archived principles when they conflict.

3. Inspect `../Incomes` third as a read-only reference.
- Compare only the parts relevant to the user request.
- Prefer concrete files and directories such as `../Incomes/AGENTS.md`, `../Incomes/ci_scripts`, `../Incomes/.build`, docs folders, package boundaries, and app/library split points.
- Never modify files under `../Incomes`.

4. Extract intent, not surface similarity.
- Ask what architectural problem the Incomes pattern is solving.
- Separate reusable philosophy from app-specific implementation details.
- Call out explicitly when a pattern should be adapted rather than copied.

5. Compare from an outer-architecture perspective.
- Identify where the current repository diverges from good reusable parts of Incomes.
- Distinguish acceptable divergence from harmful inconsistency.
- Highlight where alignment would improve maintainability, reviewability, or workflow consistency.
- Preserve the current repository's better solution when it is clearly more appropriate.

6. Decide using this rule.
- First satisfy clear current-repository evidence and any relevant principle from `$track-developer-principles`.
- If Incomes shows a clearly reusable outer-architecture pattern, prefer alignment.
- If the pattern is domain-specific or app-specific, do not copy it.
- If the current repository already has a better structure, keep it.
- When uncertain, explain both options and recommend the more maintainable one.

7. Implement or propose changes only in the current repository.
- Modify only files in the current repository.
- Keep changes scoped to the user's request.
- Prefer consistency with Incomes when it helps, but do not create fake symmetry.

8. Verify with the target repository's own workflow.
- Use the current repository's standard verification entrypoints, not Incomes commands, unless the user asked only for review.
- If adding or revising CI structure, ensure the resulting entrypoints are coherent for the current repository's actual build and test surfaces.

## Comparison Heuristics

Use `../Incomes` mainly to learn patterns like:

- How reusable logic is extracted into shared libraries without premature abstraction
- How app targets stay thin and depend on adapters instead of owning core logic
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

- Never modify `../Incomes`.
- Never use `../Incomes` as a writable dependency or patch target.
- Never recommend Incomes alignment that conflicts with an explicitly relevant principle from `$track-developer-principles` without saying so clearly.
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
2. `Incomes 参照箇所`
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

- Inspect the current repository before `../Incomes`.
- Treat `../Incomes` as read-only reference material only.
- Justify each alignment suggestion with intent, not imitation.
- Keep all modifications inside the current repository.
- State clearly when adaptation is better than direct copying.
