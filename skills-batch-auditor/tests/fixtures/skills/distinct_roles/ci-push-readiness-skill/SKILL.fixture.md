---
name: internal-fixture-ci-push-readiness-skill
description: Run verify CI, read only the newest `.build/ci/runs/<RUN_ID>` artifacts, and judge push readiness from the current git diff. Use when a branch needs a push-readiness judgment.
---

# Internal Fixture CI Push Readiness Skill

Return output in Japanese.

## Trigger Conditions

- Run verify CI before push.
- Judge whether the current branch looks push-ready.

## Workflow

1. Review only the newest `.build/ci/runs/<RUN_ID>` artifacts.
2. Do not inspect older runs.
3. Summarize a push-readiness judgment from the current git diff.
