---
name: skills-batch-auditor
description: Audit and refresh custom Codex Skills in one batch by comparing repository ground truth workflows with current Skill definitions, detecting drift/risk, and proposing consolidated updates. Use when you need one-shot consistency checks or batch update proposals across multiple local Skills.
---

# Skills Batch Auditor

## Overview

Use this skill to audit custom skills against repository contracts and current skill quality standards.
Prioritize consistency with `AGENTS.md`, UI metadata quality, operational safety, and portfolio-level maintenance order across multiple skills.
Default explanation language is concise, polite Japanese.

## Trigger Conditions

Use this skill when the user asks to:

- audit multiple custom skills in one pass
- detect drift across skill definitions and workflow contracts
- propose consolidated update bundles for skill maintenance
- refresh only a named subset of skills without broad rewrites
- run recurring weekly skill maintenance that may apply only low-risk fixes
- explicitly implement only low-risk auditor proposals

## Workflow

1. Extract repository ground truth.
- Read `AGENTS.md` first and resolve the canonical Build/Test entrypoint dynamically.
- Fallback to existing `ci_scripts/**/*.sh` paths when AGENTS guidance is absent.
- Read `.pre-commit-config.yaml` when present.
- Read a current overview doc such as `docs/current-overview.md` only when doc-related checks require it.

2. Discover audit targets.
- Audit custom skills under local skills root.
- Exclude `.system` by default.
- Exclude `skills-batch-auditor` itself from audit targets by default.
- If the user explicitly names one or more skills, limit the audit report, update bundle, and recommendations to that subset.
- Allow self-audit only when the caller explicitly opts in with `--include-self` or explicitly names `skills-batch-auditor` as a target.

3. Run bundled audit script.

```bash
python3 scripts/audit_skills_batch.py   --repo-root /path/to/repository   --skills-root /path/to/skills   --scope custom   --format markdown
```

Use `--include-self` only when the user explicitly asks to audit `skills-batch-auditor` itself.
Use `--implementation-mode low-risk` only for weekly maintenance runs or when the user explicitly requests low-risk implementation.

4. Analyze drift and risk.
- Check workflow contract alignment, generated-directory scan safety, and CI artifact handling.
- Check public skill `agents/openai.yaml` quality:
  - human-readable `display_name`
  - `short_description` length (25-64)
  - `default_prompt` includes `$<skill-name>`
- Treat skills with `metadata.visibility: internal` as intentionally UI-hidden and allow them to omit `agents/openai.yaml`.
- Distinguish true merge candidates from intentionally split neighboring skills.
- Do not recommend `merge with another skill` when the overlap is mostly broad repository-workflow vocabulary such as `ci_scripts`, `AGENTS.md`, `verify`, `hook`, or `entrypoint`.
- Score every skill explicitly on these four dimensions:
  - `reuse value`
  - `clarity of invocation`
  - `safety`
  - `maintenance burden`
- Use a simple 1-5 scale and keep the scale direction explicit:
  - `reuse value`, `clarity of invocation`, `safety`: higher is better
  - `maintenance burden`: higher means heavier maintenance cost

5. Build a single consolidated update bundle with portfolio prioritization.
- Keep invocation phrases and external interface behavior unless safety requires change.
- Default to minimal-diff updates when the user does not request a broader refresh.
- Prefer practical, implementation-ready updates over vague suggestions.
- Classify every skill into exactly one portfolio class:
  - `core`
  - `useful`
  - `optional`
  - `retire candidate`
- For batch decisions, assign exactly one next action per skill:
  - `keep as-is`
  - `improve next`
  - `merge with another skill`
  - `retire`
- Use the four scores plus detected drift/risk to make the maintenance priority ordering stronger than a simple issue-count sort.

6. Apply low-risk updates only in allowed modes.
- Default mode is `report-only`.
- Switch to `low-risk` only for:
  - weekly recurring maintenance automation
  - an explicit user request to implement low-risk proposals
- In `low-risk` mode, apply only minimal-diff text edits that stay within existing custom skill files and preserve external behavior.
- After applying low-risk updates, rerun the audit and report what was applied vs what still needs manual review.

## Implementation Modes

- `report-only`
  - Audit, classify, and propose updates without mutating files.
- `low-risk`
  - Implement only low-risk proposals and leave everything else as manual review.

Treat a proposal as low-risk only when all of the following are true:

- the edit is a minimal-diff text update to an existing custom skill file such as `SKILL.md` or an existing `agents/openai.yaml`
- no skill name, folder name, CLI flag, default scope, or external invocation phrase changes
- no new dependency, no file creation, no file deletion, and no directory move/rename
- no bundled script rewrite unless the user explicitly asks for it
- no `.system` skill mutation unless the user explicitly names that skill

Treat these as manual review by default:

- adding missing files such as a new `agents/openai.yaml` for a public skill
- changing bundled scripts or execution behavior
- changing public naming, trigger wording, or scope semantics
- any fix that requires judgment beyond the generated minimal diff

## Safety / Guardrails

- Keep analysis read-only unless the mode is weekly maintenance or the user explicitly requests low-risk implementation.
- Keep `report-only` as the default mode unless the user explicitly requests low-risk implementation or a weekly automation is doing scheduled maintenance.
- Never invent repository architecture or product features.
- Never recursively scan generated directories except explicitly scoped newest run artifacts.
- Keep skill names, folder names, CLI flags, and default scope unchanged unless safety requires change.
- In `low-risk` mode, never apply manual-review items automatically.
- Keep output concise, polite Japanese.

## Response Contract

Always return this three-part structure in Japanese:

1. `1) 監査結果（優先順）`
2. `2) 更新バンドル（一括提案）`
3. `3) 任意: 単発の推奨事項`

For each skill in drift report, include:

- name
- intent
- status: `✅ aligned` / `⚠ drift` / `❌ risky`
- scores:
  - `reuse value`
  - `clarity of invocation`
  - `safety`
  - `maintenance burden`
- portfolio classification: `core` / `useful` / `optional` / `retire candidate`
- recommended action: `keep as-is` / `improve next` / `merge with another skill` / `retire`
- issues (short bullets, Japanese labels in Markdown output)
- recommended fix (short bullets, Japanese labels in Markdown output)

For update bundle:

- summarize the batch decision buckets first:
  - `keep as-is`
  - `improve next`
  - `merge with another skill`
  - `retire`
- separate entries with `--- SKILL: <name> ---`
- include:
  - `Description: ...`
  - `Instructions: ...`
- default to full-text definitions
- use patch mode only when explicitly requested
- when the user requested a named subset, include only that subset
- include the implementation mode and distinguish low-risk implementation candidates from manual-review items

## Verification

- Confirm script output is valid in both `--format markdown` and `--format json`.
- Confirm named-skill requests are reported only for the requested subset.
- Confirm custom-scope runs exclude `skills-batch-auditor` itself by default.
- Confirm `--include-self` includes `skills-batch-auditor` when explicitly requested.
- Confirm `--implementation-mode low-risk` marks only low-risk candidates for implementation and leaves manual-review items unapplied.
- Confirm recommendations are bounded (up to 3) and implementation-oriented.
- Confirm `agents/openai.yaml` parsing works with double-quoted, single-quoted, and bare scalar values.
- Confirm `metadata.visibility: internal` allows missing `agents/openai.yaml` without drift.
- Confirm post-implementation reruns report the remaining manual-review items clearly.

## Access Fallback

If current skill definitions are inaccessible, ask the user once for:

1. all skill names
2. each skill's current config/instructions

Do not request additional inputs in fallback mode.
