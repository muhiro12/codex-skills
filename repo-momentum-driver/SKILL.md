---
name: repo-momentum-driver
description: Drive bounded autonomous continuation of development from vague "keep going" requests by inspecting recent repository activity, current worktree state, TODO/FIXME markers, latest verification or `.build/ci/runs` failures, nearby test gaps, and directly related docs, then selecting and implementing exactly one safe next task in the current repository. For Apple-platform repositories, prefer current-repo evidence first, Apple official guidance second, and a locally available sibling reference repository only as a read-only fallback. Use when prompts include phrases like "直近の対応や、リポジトリ内の各種情報を見て、続きのどんどん対応を進めて欲しい", "続き対応して", "どんどん進めて", "直近の対応を見て進めて", "look at recent changes and keep developing", or any request to self-direct next steps in an existing repository.
---

# Repo Momentum Driver

## Overview

Use this skill to convert ambiguous continuation requests into exactly one concrete, low-risk, high-signal implementation task per turn.
Default explanation language is concise, practical Japanese.
For Apple-platform repositories, keep the default decision order as current repository evidence first, Apple official guidance second, and a locally available sibling reference repository only as a read-only fallback when implementation shape is still unclear.
When choosing the next task depends on durable cross-repository judgment, consult a local principle archive skill when available (for example `$track-developer-principles`) and let it inform both task selection and implementation shape.

## Trigger Conditions

Use this skill when requests indicate autonomous continuation, such as:

- `続き対応して`
- `どんどん進めて`
- `直近の対応を見て進めて`
- `look at recent changes and keep developing`

## Workflow

1. Set boundaries before exploring.
- Stay inside the current repository by default.
- If multiple repositories are visible, ignore siblings or children unless the user explicitly names another repository.
- For Apple-platform repositories, inspect a locally available sibling reference repository only as a read-only fallback after local evidence plus Apple official guidance still leave the implementation shape unresolved.
- Select and execute exactly one next task per invocation.
- Do not broaden into a roadmap, batch cleanup, or multi-commit plan.
- Do not start large refactors, architecture rewrites, broad renames, or cross-cutting cleanup unless the user explicitly asks.

2. Collect evidence before coding.
- Run `scripts/collect_repo_signals.sh /path/to/current-repo`.
- If unavailable, gather equivalent evidence manually inside the current repository only.
- Consult a local principle archive skill when available when task choice or implementation direction depends on recurring tradeoffs such as maintainability, product priority, workflow philosophy, architecture direction, or quality thresholds.
- For Apple-platform repositories, if the implementation shape is still ambiguous after local inspection, consult Apple official documentation, sample code, or Swift guidelines before looking at a sibling reference repository.
- Resolve CI commands from `AGENTS.md` first and use its standard Build/Test entrypoint when defined.
- If `AGENTS.md` does not define one, fall back to detected `ci_scripts/**/*.sh` paths and prefer `bash ci_scripts/tasks/verify_task_completion.sh`, then `bash ci_scripts/tasks/verify.sh`, then `bash ci_scripts/tasks/verify_repository_state.sh` when CI verification is required.
- Read only the newest `.build/ci/runs/<RUN_ID>` when CI artifacts exist.
- Never scan older runs under `.build/ci/runs/`.
- Exclude generated directories from recursive scans (`.build`, `build`, `DerivedData`, `.git`, `.swiftpm`, `Pods`, `Carthage`).

3. Evaluate candidates in deterministic order.
- Apply [references/signal-priority.md](references/signal-priority.md).
- Check these buckets in order and stop at the first safe, decision-complete task:
  1. `TODO` or `FIXME` near recently changed files
  2. Small, well-scoped fixes suggested by the latest standard verification failure or newest `.build/ci/runs/<RUN_ID>` failure
  3. Missing or weak tests adjacent to recent changes
  4. Stale docs directly related to recent changes
- Reject candidates that require broad or risky changes, unclear product decisions, or touching unrelated areas.

4. Choose the single best next task.
- Explain why the chosen task is the best next step now.
- Cite concrete evidence such as files, commits, diagnostics, or CI artifacts.
- If a local principle archive skill materially influenced task choice or priority, cite that explicitly after current-repo evidence.
- If Apple official guidance or a sibling reference repository materially influenced the task choice or implementation shape, cite that explicitly after the current-repo evidence.
- If the chosen task comes from a lower bucket, briefly state why higher buckets were not safer or actionable.

5. Execute with minimal scope.
- Keep the patch local to the evidence-bearing area.
- Prefer adjacent tests or docs only when they are part of the same single task.
- Do not opportunistically fix unrelated issues.

6. Harvest newly explicit durable judgment when appropriate.
- If the user states or clearly endorses a reusable cross-repository principle during this work, update a local principle archive skill such as `$track-developer-principles` after finishing the selected single task when one is available.
- Do not archive tactical one-off choices, temporary workarounds, or principles inferred only from an accidental local implementation.

7. Run final verification before finishing.
- Run the repository's standard verification entrypoint before the final response.
- Prefer the repo-wide verify or check entrypoint indicated by `AGENTS.md`, CI scripts, or root build files over ad-hoc targeted commands.
- If multiple candidates exist, choose the most standard repo-wide one and state the exact command.
- Treat current-change or clearly introduced build/test/lint/warning failures as incomplete work.
- If warnings or errors clearly come from external packages or pre-existing unrelated issues, call them out separately instead of pretending the current change introduced them.
- If the command cannot complete, report the exact failure and whether the task itself is still locally validated.

8. Report in Japanese.
- Keep the response concise and practical.

## Safety / Guardrails

- Never revert unrelated user edits.
- Never fabricate context; cite concrete files, commits, logs, or diagnostics.
- Stay within the current repository unless the user explicitly broadens scope.
- Never let archived principles broaden the task beyond the single best next step.
- Never use a sibling reference repository as a first source or as a writable target.
- Forbid large refactors, architecture rewrites, sweeping renames, or broad cleanup unless explicitly requested.
- Raise review rigor for persistence, migrations, settings keys, permissions, auth, billing, security-sensitive paths, and destructive behavior.
- Never report success while current-change or clearly introduced build/test/lint failures or warnings remain unresolved.
- Ask the user only when blocked by missing requirements or risky product decisions.

## Response Contract

Use this structure:

1. `選んだタスク`
2. `今これが最善な理由`
3. `変更内容`
4. `検証`
5. `保留事項`

Additionally include checklist status:

- `事前チェック` (evidence collected, single-task scope fixed, current-repo scope respected)
- `事後チェック` (standard verification entrypoint run, residual risk noted)

## Verification

- Ensure all claims in `今これが最善な理由` map to concrete evidence.
- Ensure exactly one task was selected and implemented.
- Ensure the repository's standard verification entrypoint was run before finishing.
- If final verification cannot run to completion, include the exact failed command and a direct next command.
