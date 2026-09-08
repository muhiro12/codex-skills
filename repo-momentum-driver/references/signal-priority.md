# Selecting Repository Work

Preserve an active user objective. For an otherwise open continuation request,
compare a few concrete candidates from current changes and recent repository
activity in this order:

1. Unfinished work already authorized by the user and current documented plans.
2. Confirmed user-visible bugs or current verification failures with a narrow fix.
3. Recent TODO/FIXME markers whose intent is still valid.
4. Missing behavioral checks or stale documentation directly tied to recent work.

This is a default priority, not a rigid queue. Explain a material departure using
impact, confidence, change cost, and the ability to verify the result.

A candidate should have concrete file/commit/diagnostic evidence, fit the user's
scope, and admit proportionate verification. Preserve pre-existing edits and
unmerged work. High-risk persistence, auth, billing, permissions, or destructive
changes need clear intent; choose independent safe work while a required decision
is pending.

Resolve verification from `AGENTS.md`, the project's actual build/test setup,
and current CI. Prefer official Xcode capabilities for Apple evidence and retain
repository rule checks. Do not execute an arbitrary script discovered in a tree,
and do not require a new aggregate wrapper just to continue ordinary work.

Read only the newest contract-owned `.build/ci/runs/<RUN_ID>` when relevant.
Generated or historical artifacts are not current work priorities by default.

When no useful candidate is justified, say what evidence is missing and ask a
concise scope question only if the answer is needed. Do not create speculative
cleanup to keep the agent busy.
