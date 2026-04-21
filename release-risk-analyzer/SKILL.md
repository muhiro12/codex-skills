---
name: release-risk-analyzer
description: Assess release-blocking risk between the latest reachable release tag and the current commit, with emphasis on changes that can leave lasting product damage if released unnoticed. Use this skill when you need to decide whether a release should be blocked for manual review, especially for permissions and capabilities, SwiftData or database migration surfaces, persistent settings such as UserDefaults or AppStorage, and other high-risk product surfaces. It can still summarize changes, but risk judgment should come first.
---

# Release Risk Analyzer

## Overview

Use this skill to turn `<latest-tag>..HEAD` into a release-blocking risk assessment.
Keep the core review logic in this file portable across agent runtimes where practical; platform-specific metadata can live beside the skill.
Default explanation language is concise, polite Japanese, and the report must lead with the release decision before detailed summaries.

## Trigger Conditions

Use this skill when the user asks to:

- decide whether a release should be blocked
- assess risk since the latest release tag
- review potentially dangerous changes before shipping

## Workflow

1. Resolve comparison range.
- Default to latest reachable release tag -> `HEAD`.
- Use `--base-ref`, `--head-ref`, or `--tag-pattern` when explicitly needed.

2. Load risk rules.
- Use only the built-in heuristics bundled with the skill.
- Do not load repository-local or external rule files.

3. Generate analysis with the bundled script.

```bash
python3 scripts/review_release_risk.py   --repo /path/to/repository   --format markdown
```

4. Prioritize durable-risk findings.
- Highlight permissions, capabilities, migration paths, persistent storage, and long-lived settings first.
- Distinguish reversible UI changes from potentially lasting product damage.

5. Produce final release posture using this template.
- `Block`: release should stop until manual inspection is complete.
- `Proceed with caution`: release may continue with explicit mitigations or focused validation.
- `Proceed`: no release-blocking surfaces detected from available evidence.

## Safety / Guardrails

- Never bury blocking findings under verbose diff summaries.
- Never claim safety without stating the inspected range and confidence level.
- Keep rule reasoning concrete and actionable.
- Prefer false positives on irreversible-risk surfaces over false negatives.

## Response Contract

Return a concise Japanese report with:

1. `結論` (`Block` / `Proceed with caution` / `Proceed`)
2. `判定理由` (durable-risk first)
3. `対象範囲` (base tag, head commit, git range)
4. `主要リスク` (built-in heuristics and concrete findings)
5. `推奨アクション`

## Verification

- Confirm range resolution is explicit and correct.
- Confirm the conclusion matches the listed evidence.
- Confirm built-in heuristic matches and concrete findings are clearly separated.
- Use `--verbose` only when full file/commit listing is necessary.
