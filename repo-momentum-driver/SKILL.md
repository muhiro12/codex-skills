---
name: repo-momentum-driver
description: Choose and complete evidence-backed next work when the user asks to continue developing a repository without specifying the next task. Preserve an existing objective and follow the user's requested scope.
---

# Repo Momentum Driver

Use this skill for ambiguous continuation requests such as "続き対応して" or
"look at recent changes and keep developing". If an objective is already agreed,
continue it before inventing new work. Return concise, practical Japanese.

## Find the Next Useful Work

Read the current repository's `AGENTS.md`, worktree/index changes, recent commits,
and relevant planning notes. `scripts/collect_repo_signals.sh /path/to/repo` can
collect a bounded starting inventory; its output is evidence, not a task order.
Read [references/signal-priority.md](references/signal-priority.md) when choosing
among competing candidates.

Prefer unfinished authorized work and confirmed failures over speculative
cleanup. A TODO near a recent commit is a candidate, not an automatic priority.
Choose work with clear product value, concrete evidence, a manageable change,
and a proportionate verification path. Do not create tests solely to increase
counts or manufacture a task when no useful candidate exists.

Stay in the current repository unless the user expands scope. Preserve unrelated
changes. Do not turn an ambiguous continuation into a broad refactor, new product
policy, dependency migration, or cross-repository cleanup.

## Complete the Agreed Scope

Choose one coherent task at a time, finish it with the relevant tests and docs,
and reassess against the user's objective. One task is a useful default when
scope is otherwise undefined, not a mandatory stopping point for a request to
complete several items or finish a release.

Use `apple-ios-dev-flow` for Apple implementation when available; do not repeat
its specialist routing here. Consult relevant principles only when their
tradeoffs matter. A missing principle or aggregate verify script is not by
itself a reason to stop: use repository evidence and appropriate native checks.
Ask only for a material decision that cannot be inferred responsibly.

Use the documented verification contract. If it intentionally produces
`.build/ci/runs/<RUN_ID>` artifacts, inspect only the newest relevant run; ignore
stale artifact trees from retired workflows. Exclude generated, cached, private,
and runtime-owned trees from recursive discovery.

Report the selected work and its evidence, the result, completed verification,
and any remaining blocker. Do not present a partial task as finished because a
step count was reached.
