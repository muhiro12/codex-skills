---
name: skills-batch-auditor
description: Maintain or refresh custom Codex Skills in batch by comparing repository ground truth, current Skill definitions, available tools/plugins, and stored developer principles. Use when you need automatic consistency maintenance or proposal-only evolution review across multiple local Skills.
---

# Skills Batch Auditor

## Overview

Use this skill to run one of two modes across custom skills:

- `maintenance`: automatically preserve consistency when the correct fix is nearly unique and does not need user judgment.
- `refresh`: propose how skills should evolve against the current Codex / AI agent environment, available tools/plugins/skills, repository practice, and the user's current development principles.

Treat bundled script output as a baseline. Add manual fit checks when the task depends on current tool availability, plugin overlap, repository changes, or stored cross-repository principles.
Default explanation language is concise, polite Japanese.

## Trigger Conditions

Use this skill when the user asks to:

- run recurring weekly custom skill maintenance
- repair broken references, renamed paths, stale file names, or obvious consistency drift across skills
- check multiple custom skills against `AGENTS.md`, repository contracts, and `agents/openai.yaml` structure
- refresh one or more skills for current Codex / AI agent capabilities and current repository operations
- propose portfolio-level role adjustments, merges, separations, or retirement candidates across skills
- review only a named subset of skills without broad rewrites

## Mode Selection

Choose exactly one mode per run.

### maintenance

Use `maintenance` when the requested work is consistency preservation and every applied fix can be made without user judgment.

Allowed maintenance fixes include:

- broken references
- references to nonexistent skills, files, or paths
- following already-decided name or path changes
- obvious typos
- clear contradictions inside one Skill
- clear mismatch with `AGENTS.md` or repository contracts
- structural or formatting inconsistencies in files such as `agents/openai.yaml`
- minor consistency edits that do not change a Skill's philosophy, role, or external interface

In `maintenance`:

- apply eligible fixes automatically
- make only existing-file edits unless a missing file's exact contents are mechanically derivable from existing canonical metadata
- preserve skill names, folder names, trigger phrases, CLI flags, default scope, and external behavior unless a safety issue requires otherwise
- rerun the audit after edits and report what was applied
- move anything ambiguous or judgment-heavy to `refresh`

### refresh

Use `refresh` when the requested work is a proposal about how skills should evolve.

Review each target against:

- the current Codex / AI agent environment
- currently available tools, plugins, and skills
- the user's current developer principles and operating policy
- changes in repository contracts or global `AGENTS.md`
- whether the Skill's old assumptions are still good mature design or have become stale ceremony
- whether neighboring skills should be merged, split, narrowed, or left intentionally separate

In `refresh`:

- do not apply changes automatically
- provide proposals only
- make clear that more than one valid answer may exist
- respect the intent and background of each target Skill
- avoid uniform standardization when local variation is intentional
- provide priority, rationale, and adoption decision material

## Workflow

1. Extract repository ground truth.
- Read `AGENTS.md` first and resolve canonical Build/Test entrypoints dynamically.
- Fall back to existing `ci_scripts/**/*.sh` paths when AGENTS guidance is absent.
- Read `.pre-commit-config.yaml` when present.
- Read a current overview doc such as `docs/current-overview.md` only when doc-related checks require it.
- When skill quality depends on user-specific development philosophy, consult a local principle archive skill such as `$track-developer-principles`.
- When skill quality depends on current tool availability, use the active tool/plugin/skill context first and `tool_search` only for deferred tools that are relevant to the audited skill.

2. Discover audit targets.
- Classify each skill directory under the local skills root:
  - `custom`: ordinary user-managed skills
  - `managed-external`: Xcode-provided skills with `.xcode-skill-sync.json`
  - `unmanaged-xcode-prefix`: `xcode-skill-*` directories without `.xcode-skill-sync.json`
  - `system`: skills under `.system`
- Audit `custom` skills under the local skills root.
- Exclude `.system` by default.
- Exclude `managed-external` from normal custom skill drift checks, maintenance edits, and refresh proposals.
- Check `managed-external` only for sync integrity: readable `.xcode-skill-sync.json`, consistency with `sync-xcode-skills/state/catalog.json` or `catalog.md`, and actual directory presence.
- Report `unmanaged-xcode-prefix` as risky because `xcode-skill-*` is reserved for Xcode-provided managed skills.
- Exclude `skills-batch-auditor` itself from batch targets by default.
- If the user explicitly names one or more skills, limit the report, maintenance edits, and refresh proposals to that subset.
- If the user explicitly names a `managed-external` Xcode skill, inspect it read-only and route findings to sync integrity or upstream Xcode/sync updates; never auto-edit it.
- If the user explicitly names `skills-batch-auditor` or passes `--include-self`, treat that as target selection only; do not introduce a separate self-audit mode.

3. Run the bundled audit script.

```bash
python3 scripts/audit_skills_batch.py \
  --repo-root /path/to/repository \
  --skills-root /path/to/skills \
  --scope custom \
  --mode maintenance \
  --format markdown
```

Use `--mode refresh` for proposal-only runs.
Use `--include-self` only when the user explicitly asks to include `skills-batch-auditor` itself.

4. Analyze drift, consistency, and evolution needs.
- Check workflow contract alignment, generated-directory scan safety, and CI artifact handling.
- Check public skill `agents/openai.yaml` quality:
  - human-readable `display_name`
  - `short_description` length (25-64)
  - `default_prompt` includes `$<skill-name>`
- Treat skills with `metadata.visibility: internal` as intentionally UI-hidden and allow them to omit `agents/openai.yaml`.
- Check current Codex environment fit:
  - tool and namespace names still match the active environment
  - plugin-provided skills have not replaced or narrowed the custom skill's role
  - UI directives and structured tool fields are current
  - MCP or simulator workflow assumptions name available capabilities accurately
  - local sibling-repository assumptions still match the user's current platform principles
- Distinguish true merge candidates from intentionally split neighboring skills.
- Do not recommend `merge with another skill` when overlap is mostly broad repository-workflow vocabulary such as `ci_scripts`, `AGENTS.md`, `verify`, `hook`, or `entrypoint`.
- Score every skill explicitly on these four dimensions:
  - `reuse value`
  - `clarity of invocation`
  - `safety`
  - `maintenance burden`
- Use a simple 1-5 scale and keep the scale direction explicit:
  - `reuse value`, `clarity of invocation`, `safety`: higher is better
  - `maintenance burden`: higher means heavier maintenance cost

5. Classify portfolio position and next action.
- Keep invocation phrases and external interface behavior unless safety requires change.
- Prefer practical, implementation-ready recommendations over vague suggestions.
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
- Use the four scores plus detected drift/risk to make ordering stronger than a simple issue-count sort.
- Do not rely on the script's `aligned` result alone when manual environment fit shows stale tool names, outdated directives, or superseded local-reference assumptions.

6. Execute the selected mode.
- In `maintenance`, apply only deterministic consistency fixes, rerun the audit, and summarize applied edits plus anything moved to `refresh`.
- In `refresh`, do not mutate files; provide prioritized evolution proposals and adoption criteria.
- In either mode, do not apply local custom-skill quality rules such as `missing_japanese_output_rule` or `agents/openai.yaml` wording checks to `managed-external` Xcode skills.

## Maintenance Eligibility

Treat a fix as maintenance only when all of the following are true:

- the correction has a nearly unique answer from existing files, repository contracts, or active tool context
- the edit preserves the Skill's purpose, role, trigger surface, and external behavior
- the edit is small enough to review as a consistency correction
- no new dependency, directory move, rename, or broad script behavior change is required
- the target is an existing custom skill file, or a missing metadata file whose exact contents are mechanically derivable
- `.system` skills are untouched unless the user explicitly names the target
- `managed-external` Xcode skills are never maintenance targets; resolve their content through `sync-xcode-skills` or upstream Apple/Xcode updates

Move these to `refresh` by default:

- changing a Skill's philosophy, responsibility, or target audience
- changing public naming, trigger wording, default scope, CLI flags, or external invocation semantics
- adding new workflows, new dependencies, or new broad script behavior
- deciding whether to merge, split, retire, or substantially narrow a Skill
- rewriting `short_description`, documentation tone, or portfolio positioning when multiple valid outcomes exist
- any change where the main question is "should we?" rather than "what is the correct current reference?"

## Safety / Guardrails

- Never create a separate read-only audit mode; use `refresh` for proposal-only review.
- Never auto-apply `refresh` proposals.
- Never invent repository architecture or product features.
- Never claim a skill is fully current solely because the bundled audit script passed.
- Never recursively scan generated directories except explicitly scoped newest run artifacts.
- Keep skill names, folder names, CLI flags, and default scope unchanged unless safety requires change.
- Keep `xcode-skill-*` reserved for `sync-xcode-skills` managed external skills; report unmanaged prefix collisions instead of silently auditing them as custom skills.
- Keep output concise, polite Japanese.

## Response Contract

Always return concise Japanese.

For `maintenance`, use:

1. `1) maintenance 実施結果`
2. `2) 自動適用した整合性修正`
3. `3) refresh に回した判断事項`

For `refresh`, use:

1. `1) refresh 提案（優先順）`
2. `2) 採用判断材料`
3. `3) maintenance に回せる整合性候補`

For each reported skill, include:

- name
- intent
- status: `✅ aligned` / `⚠ drift` / `❌ risky`
- mode disposition: `maintenance` / `refresh` / `no action`
- scores:
  - `reuse value`
  - `clarity of invocation`
  - `safety`
  - `maintenance burden`
- portfolio classification: `core` / `useful` / `optional` / `retire candidate`
- recommended action: `keep as-is` / `improve next` / `merge with another skill` / `retire`
- issues or proposal reasons, using short Japanese labels
- recommended fix or proposal, using short Japanese labels

For Xcode-derived skills, report sync integrity separately from normal skill drift:

- managed external count
- unmanaged `xcode-skill-*` prefix collision count
- marker readability and key mismatches
- catalog source and catalog/directory mismatches
- fixes that point to `sync-xcode-skills` or upstream Apple/Xcode updates, not local custom-skill edits

For `maintenance`, explicitly separate:

- automatically applied fixes
- eligible fixes not applied and why
- items moved to `refresh` because they need user judgment

For `refresh`, explicitly separate:

- proposal priority
- rationale
- adoption tradeoffs
- maintenance-only consistency fixes that can be handled separately

When the user requested a named subset, include only that subset.
Use patch mode only when explicitly requested.

## Verification

- Confirm script output is valid in both `--format markdown` and `--format json`.
- Confirm `--mode maintenance` uses maintenance terminology, applies only deterministic consistency fixes, and reruns the audit afterward.
- Confirm `--mode refresh` uses refresh terminology and does not produce automatic application output.
- Confirm named-skill requests are reported only for the requested subset.
- Confirm custom-scope runs exclude `skills-batch-auditor` itself by default.
- Confirm `--include-self` includes `skills-batch-auditor` when explicitly requested and does not create a separate self-audit mode.
- Confirm managed external `xcode-skill-*` skills with `.xcode-skill-sync.json` are excluded from normal `drift_report` and appear only in Xcode sync integrity reporting.
- Confirm unmanaged `xcode-skill-*` directories without `.xcode-skill-sync.json` are reported as risky reserved-prefix collisions.
- Confirm recommendations are bounded and implementation-oriented.
- Confirm `agents/openai.yaml` parsing works with double-quoted, single-quoted, and bare scalar values.
- Confirm `metadata.visibility: internal` allows missing `agents/openai.yaml` without drift.
- Confirm post-maintenance reruns report remaining `refresh` items clearly.

## Access Fallback

If current skill definitions are inaccessible, ask the user once for:

1. all skill names
2. each skill's current config/instructions

Do not request additional inputs in fallback mode.
