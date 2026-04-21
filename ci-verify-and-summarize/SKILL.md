---
name: ci-verify-and-summarize
description: Run the repository's final verification gate by executing its standard verify-oriented CI shell, summarizing only the newest `.build/ci/runs/<RUN_ID>` artifacts, reviewing the current git diff, and separating current-change issues from clearly external or pre-existing ones in concise polite Japanese. Use for requests such as "verifyして", "CIガード通して", "コミット前チェックして", "push前に見て", and explicit `$ci-verify-and-summarize` invocations even when there are no current diffs.
---

# CI Verify and Summarize

## Overview

Use this skill as the repository's final verification gate before treating implementation work as ready.
Run the standard verify-oriented CI entrypoint, inspect the newest CI artifacts, perform a focused diff review, and classify push readiness from build/test/lint/warning signals plus the current git diff.
When the user explicitly invokes `$ci-verify-and-summarize`, still run the workflow even if staged and unstaged diffs are both empty, and report that the worktree is clean instead of treating the skill as not applicable.
Keep execution thin and deterministic by delegating CI execution to the bundled helper script.

## Trigger Conditions

Use this skill when the user asks to run CI verification and judge whether the current branch looks safe to commit or push.
Typical phrases include:

- `verifyして`
- `CIガード通して`
- `コミット前チェックして`
- `push前に見て`
- `最後に危ない差分がないか見て`
- explicit `$ci-verify-and-summarize` invocation to run the final gate even on a clean worktree

## Workflow

1. Validate prerequisites.
- Assume the current working directory is the repository root.
- Resolve the verify-oriented CI entrypoint from `AGENTS.md` first by reading `bash ci_scripts/...sh` references.
- If `AGENTS.md` does not define one, fall back to detecting a standard script under `ci_scripts/`, preferring `ci_scripts/tasks/verify_task_completion.sh`, then `ci_scripts/tasks/verify.sh`, then `ci_scripts/verify.sh`, then `ci_scripts/tasks/verify_repository_state.sh`, then `run_required_builds.sh`, then another detected `.sh`.
- Confirm the resolved workflow writes artifacts to `.build/ci/runs/`.
- If the repository does not provide this contract, explain that this skill is not applicable and stop.

2. Run the helper script.

```bash
bash "${CODEX_HOME:-$HOME/.codex}/skills/ci-verify-and-summarize/scripts/run_verify_and_summarize.sh"
```

3. Resolve the newest run.
- Determine the latest run by lexicographically greatest directory name under `.build/ci/runs/`.
- Do not inspect older runs.

4. Read artifacts in strict order.
- `summary.md`
- `meta.json`
- `failed_log` only when verify failed
- `commands.txt` only when needed for diagnosis

5. Review the current git diff after verify.
- Inspect both `git diff --stat` / patch and `git diff --cached --stat` / patch.
- Treat this as a lightweight code review of the current diff, not only as a category scan.
- Stay inside current diffs only; do not inspect unrelated history or recursively scan the whole repository.
- If both diffs are empty, treat that as a valid clean-worktree review and state it explicitly in the report.
- Focus on practical push-risk categories such as entitlements, persistence or migration, notifications or background behavior, remote config or force update, monetization, widgets or app intents or watch or deeplinks, warnings still present, suspicious `--no-verify`, unexpectedly broad file changes, and missing tests near behavior changes.
- Treat current-change or clearly introduced build/test/lint/warning failures as non-ready.
- If warnings or errors clearly come from external packages or pre-existing unrelated issues, call that out separately instead of automatically attributing them to the current change.

6. Build the final report.
- Use concise, polite Japanese for the agent explanation.
- Keep the report short and practical; do not append raw command output or verbose diagnostics.
- If verify fails, report that first and do not treat the branch as push-ready.
- If current-change or clearly introduced warnings remain, do not treat the branch as push-ready.
- If push risk is `high`, clearly say that pushing is not recommended yet.

## Safety / Guardrails

- Do not edit repository files.
- Do not re-implement CI logic in ad-hoc commands.
- Resolve the CI entrypoint dynamically from `AGENTS.md` or `ci_scripts/` instead of assuming a single hard-coded script.
- Read only the newest run directory in `.build/ci/runs/`.
- Never recursively scan generated directories outside the newest run scope.
- Review only the current git diff and staged diff; do not broaden into full-repository archaeology.
- Do not skip execution only because the current diff is empty when the user explicitly invoked the skill.
- Treat missing git context, missing latest run, current-change or clearly introduced verify failure, or suspicious `--no-verify` as non-push-ready signals.

## Response Contract

Return a short, polite report in Japanese with this structure:

- `結果`
- `最新RUN: <RUN_ID>`
- `要約:` 3〜6行
- `Pushリスク: low / medium / high`
- `リスク理由:` 2〜4行
- `次の一手:` 1〜3 concrete actions

When there is no current diff, still return the full structure and explicitly note that the worktree is clean.

## Verification

- Confirm the helper script completed and returned an exit code.
- Confirm newest run resolution succeeded.
- Confirm both unstaged diff and staged diff were reviewed.
- Confirm explicit invocation on a clean worktree still returns a full report.
- If current-change or clearly introduced warnings remain, ensure the final judgment is non-ready.
- If warnings look external or pre-existing, ensure the report says so explicitly instead of blaming the current change.
- If artifacts are incomplete, clearly mark the report as non-push-ready and continue with available evidence.
- If `.build/ci/runs/` has no run, report artifact-not-found explicitly and keep push risk high.
