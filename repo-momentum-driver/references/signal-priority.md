# Signal Priority Guide

Use this guide to choose exactly one bounded next task from repository signals.
Stay inside the current repository unless the user explicitly says otherwise.

## 1. Scope Boundary

- Choose one task only.
- Prefer small, adjacent changes that can be implemented and verified in one turn.
- Reject large refactors, architecture rewrites, broad renames, or cross-cutting cleanup unless the user explicitly asks.
- Reject tasks that require touching multiple repositories.
- For Apple-platform repositories, inspect a locally available sibling reference repository such as `../Incomes` only as a read-only tie-breaker after current-repo evidence and Apple official guidance.

## 2. Preflight Blockers

Treat these as blockers before selecting a normal next task:

- Merge conflicts or unmerged paths
- Ambiguous repository choice when the current directory is not clearly the target repo
- No identifiable repo-wide verification entrypoint
- High-risk persistence, migration, permissions, auth, billing, security, or destructive changes with unclear intent

If a blocker applies and no safe small fix is obvious, stop and ask one concise question.

## 3. Deterministic Candidate Order

Evaluate buckets in this order and stop at the first safe actionable item:

1. `TODO` or `FIXME` near recent changes
2. Latest standard verification failure or newest `.build/ci/runs/<RUN_ID>` failure that suggests a narrow fix
3. Missing or obviously weak tests adjacent to recent changes
4. Stale docs directly related to recent changes

Treat "recent changes" as the current worktree or index plus the latest branch commits surfaced by signal collection.

## 4. Candidate Acceptance Rules

Accept a candidate only if all of these are true:

- Direct evidence exists in concrete files, commits, diagnostics, or CI artifacts
- The change is small enough to finish in one focused patch
- Verification is available and proportionate
- The task stays within one repository and one clear objective
- Any sibling reference repository inspection remains secondary evidence and does not broaden the write scope
- The task does not require a large refactor or speculative product decision

## 5. Explain Why It Is Best

In the final answer, explain why the chosen task is the best next step now:

- Cite the concrete evidence that triggered it
- Mention why earlier buckets did not yield a safer actionable task when relevant
- Favor the option with the strongest evidence, smallest scope, and clearest verification path

## 6. Standard Verification Entrypoint

Resolve the repo-wide final verification command in this order:

1. `ci_scripts/tasks/verify_task_completion.sh`
2. `ci_scripts/tasks/verify.sh`
3. `ci_scripts/tasks/verify_repository_state.sh`
4. A root CI or documentation command explicitly named `verify`
5. A root build-tool target named `verify`, then `check`, then `test`
6. A repo-wide package-manager or language entrypoint that CI uses for aggregate verification

Do not treat a narrow targeted test as the final verification when a repo-wide entrypoint exists.

## 7. No-Safe-Task Fallback

If no candidate is both safe and sufficiently scoped:

1. Return blockers with direct evidence
2. Ask one concise clarifying question
3. Propose one provisional next task that starts immediately after clarification

## 8. Output Expectations

Always return:

1. Chosen task and why it is best now
2. Evidence references (files, commits, logs)
3. Changes made
4. Final verification command and result
5. Residual risk or blocker only if needed
