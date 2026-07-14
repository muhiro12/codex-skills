---
name: repo-agent-contract-maintainer
description: Maintain clone-ready repository AGENTS.md contracts and their boundaries with global AGENTS.md, developer principles, personal principles, skills, and durable architecture documents. Use when creating a new repository AGENTS.md, auditing or updating existing AGENTS.md files, deciding whether policy belongs in global AGENTS.md, a repo AGENTS.md, a skill, developer principles, personal principles, Designs/ADRs, or issues, or aligning Apple repositories to MCP-first verification while preserving repository-specific rules.
---

# Repo Agent Contract Maintainer

## Overview

Use this skill to keep repository agent instructions portable, minimal, and
safe to act on from a fresh clone while still fitting Hiromu's local Codex
environment.

This skill is a routing and judgment workflow, not a universal AGENTS.md
template. Prefer small, evidence-backed edits over broad rewrites, and do not
copy this skill's meta-rationale into every repository.

## Core Rule

Keep each GitHub-facing repository's `AGENTS.md` clone-ready and
action-focused. Do not remove an actionable repository-local instruction only
because it repeats global policy, but also do not add repeated explanations
about why duplication is acceptable. Put that rationale in this skill or the
developer-principle archive.

Move information to the narrowest durable layer that can carry it forward:

- Global `AGENTS.md`: local Codex environment routing, principle lookup,
  skill routing, and cross-repository storage boundaries for this machine.
- Repository `AGENTS.md`: commands, schemes, package names, verification
  entrypoints, language/style rules, and repository-specific boundaries needed
  to work safely from a fresh clone.
- Developer principles: reusable judgment, rationale, priority, exceptions,
  and history.
- Personal principles: private personal operating preferences and environment
  boundaries that should not leak into product repositories.
- Skills: long procedural workflows, specialist routing, reusable checklists,
  and tool-specific operating instructions.
- Durable repository docs: architecture guides, ADRs, public setup docs, and
  product or package contracts.
- Issues or temporary notes: short-term plans, release checklists, and work
  queues that should not become durable doctrine yet.

## Workflow

1. Inspect current evidence.
- Read the current repository `AGENTS.md` when present.
- Read nearby `ci_scripts/`, project or package manifests, and durable
  architecture docs that the existing AGENTS file references.
- Read the global Codex `AGENTS.md` under the active Codex home
  (`$CODEX_HOME/AGENTS.md`, or `~/.codex/AGENTS.md` when `CODEX_HOME` is unset)
  when changing local environment routing or cross-repository boundaries.
- Consult `$track-developer-principles` when the decision depends on durable
  development judgment.

2. Classify each policy before editing.
- Ask whether the item must be available to an agent from a fresh clone.
- Ask whether the item is a reusable principle, a local-machine routing rule, a
  repository-specific contract, a long procedure, or temporary planning.
- Keep repository-specific commands and verification facts in the repository
  even when the same broad policy appears globally.
- Keep private personal context and raw context archives out of product
  repositories unless Hiromu explicitly asks otherwise.

3. Preserve or add clone-ready repository content.
- Keep repository `AGENTS.md` concise, self-contained, and practical.
- Include language and documentation rules when they affect public repository
  quality.
- Include Swift style rules when they are part of the repository's review or
  lint contract.
- Include concrete build/test/run schemes, package workspaces, and retained
  repository rule commands.
- For verification guidance, expose concrete repository capabilities and a few
  risk-based guardrails rather than a full decision tree; long evidence
  selection logic belongs in skills or developer principles.
- Include architecture or package boundary summaries when they prevent unsafe
  edits.
- Point to durable docs such as `Designs/Architecture/` or
  `Designs/Decisions/` when detailed rationale already lives there.
- Avoid explaining cross-repository maintenance history inside each repository
  unless the explanation changes how an agent should work in that repository.

4. Route specialist work instead of duplicating it.
- For Apple implementation flow, route to `$apple-ios-dev-flow`.
- For verification contract naming, retained rule checks, or MCP-vs-shell
  verification alignment, route to `$verify-contract-maintainer`.
- For HIG, Swift language, sample-code, preview, UI smoke, release-risk, or
  localization-specific work, use the relevant specialist skill instead of
  copying its full procedure into `AGENTS.md`.
- Keep `AGENTS.md` focused on entrypoints and durable rules, not exhaustive
  operational playbooks.

5. Apply repository family judgment.
- Treat Incomes as the frontier app reference for Hiromu's Apple app
  architecture and workflow.
- Treat Cookle as the next app-repository baseline after Incomes.
- For Liet, Fluel, and Stally, align where practical with Incomes/Cookle while
  preserving real repository-specific targets, schemes, surfaces, and
  architecture boundaries.
- For MHPlatform and MHUI, preserve package/foundation boundary rules more
  strongly than app-repository symmetry.

6. Verify the contract.
- Confirm documented commands or schemes exist when practical.
- Run `git diff --check` for touched Git repositories.
- Search for stale framing such as a repository AGENTS file calling itself a
  global contract.
- Search for repeated meta-rationale that belongs in this skill or developer
  principles instead of the repository file.
- For MCP-first Apple repositories, confirm `AGENTS.md` names the project or
  workspace, concrete schemes and destination families, native Xcode MCP
  actions such as `BuildProject`, `RunAllTests`/`RunSomeTests`, `RunProject`,
  `RenderPreview`, or the `DeviceInteraction*` lifecycle as appropriate, and
  retained repository-rule scripts separately. Require runtime agents to record
  the original active scheme and destination, restore the scheme and then its
  destination after switching, and report failed restoration.
- Report any global or skill-owned files that are not Git-managed.

## Editing Guardrails

- Do not blank out repository `AGENTS.md` files just because global guidance
  exists.
- Do not force one shared template across app repositories, package
  foundations, and utility repositories.
- Do not store private local paths, context archive contents, or personal
  operating notes in public repository docs unless explicitly requested.
- Do not add team-process artifacts such as contribution guides, PR templates,
  or issue templates unless they are actually useful.
- Do not replace repository-specific architecture documents with AGENTS.md
  summaries; summarize only the boundary needed for safe agent behavior.
- Do not treat shell verification scripts as primary for MCP-first Apple
  repositories when native Xcode MCP covers the evidence; retain scripts for
  SwiftLint, formatting, repository-specific static rules, compatibility, or
  uncovered checks.

## Output

Return concise Japanese with:

1. `契約整理`
2. `配置判断`
3. `変更内容`
4. `検証`
5. `残課題`
