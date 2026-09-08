---
name: ci-verify-and-summarize
description: Run the repository's documented verification checks and review the current diff. Summarize actual shell or Xcode-native evidence, current-run artifacts, and remaining readiness risks, including on a clean worktree.
---

# CI Verify and Summarize

Run the current repository's verification contract and review staged and unstaged
diffs. Explicit invocation applies even when the worktree is clean. Return concise,
polite Japanese. Verification readiness does not authorize a commit or push.

## Resolve the Real Contract

Read `AGENTS.md`, actual build/test configuration, and relevant repository CI.
Resolve the repository root from Git rather than assuming the current directory.
Prefer the documented checks over filename conventions or obsolete wrappers.
Do not require `ci_scripts`, an aggregate shell, or `.build/ci/runs` when the
repository's current contract uses another coherent workflow.

For Xcode-native contracts, resolve the actual capabilities and required evidence
from the runtime inventory. Follow the repository's project/scheme/destination/
test-plan contract; preserve and restore changed Xcode selection. Use
`apple-ios-dev-flow` when Apple evidence selection needs guidance. A retained
static-rule script is only one part of a mixed contract.

For a supported shell contract, run the bundled helper from the target repository:

```bash
bash /path/to/ci-verify-and-summarize/scripts/run_verify_and_summarize.sh
```

Resolve the helper relative to the loaded skill rather than assuming the default
Codex home. It recognizes documented repository-relative `bash` scripts with
verify/check names, including `scripts/verify_repository.sh`, and falls back to
known `ci_scripts` verification names. It never treats an arbitrary migration,
formatter, or deployment script as a verification command. A broken documented
entrypoint is a failure, not permission to silently choose a different check.

If the repository uses another command form, run the documented command directly
and perform the same evidence/diff review. Do not create a compatibility wrapper
just for this skill. If no reliable verification can be derived, report that
limit and continue the useful diff review instead of inventing a gate.

## Current Execution Evidence

Keep shell exit status/output, Xcode build/test results, and runtime/UI evidence
separate. Report only checks that actually ran; prior results need their exact
revision and context before reuse.

The shell helper compares direct child RUN directories before and after execution.
Only one new regular directory may supply current-run artifacts. Do not select
an old successful run when the current command failed or produced no artifacts.
Multiple new runs or symlinked roots/entries are ambiguous and must be reported.

For a valid current run, read `summary.md`, `meta.json`, the failed log only when
needed, and `commands.txt` only for diagnosis. Artifacts must be regular,
non-symlink files contained in that run. Never follow an artifact path outside it
or scan older `.build/ci/runs/<RUN_ID>` directories. Successful checks need no
artifact directory when output is the contract's evidence.

## Review and Report

Review both current diff and staged diff for introduced failures, unintended
behavior, persistence/identifier changes, missing behavioral checks, and scope
creep. Preserve unrelated edits. The helper's category scan supplements this
review; it does not perform a complete semantic code review.

Report the actual commands/capabilities and result, important diff findings,
current-change versus pre-existing failures, and remaining limitations. Include
current-run paths only when such artifacts exist. A clean worktree is valid
context, not a reason to skip requested verification. Do not claim readiness
while an introduced failure or required unverified boundary remains.

Do not edit source/configuration or run formatting as a side effect of this
verification-only workflow. If a user also asked for fixes, perform that authorized
implementation separately and verify the resulting change.
