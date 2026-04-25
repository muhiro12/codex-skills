---
name: release-risk-analyzer
description: Assess scored release-blocking risk between the latest reachable release tag and the current commit, with emphasis on changes that can leave lasting product damage if released unnoticed. Use this skill when you need to decide whether a release should be blocked for manual review by quantifying risk across durable-state compatibility, irreversible or externally registered IDs and configuration values, permissions and capabilities, build/signing/dependency surfaces, persistent settings, API contracts, and other high-risk product surfaces. Platform-specific items such as SwiftData models or Bundle IDs are examples of these broader risk axes, not the scoring axes themselves. It can still summarize changes, but risk scoring and release judgment should come first.
---

# Release Risk Analyzer

## Overview

Use this skill to turn `<latest-tag>..HEAD` into a scored release-blocking risk assessment.
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
- Highlight durable-state compatibility, irreversible/external identifiers and configuration values, permissions, capabilities, migration paths, persistent storage, and long-lived settings first.
- Treat concrete technologies as detection anchors, not as the risk model. For example, SwiftData, Core Data, Realm, SQL, and migration files all map to durable-state compatibility; Bundle ID, App Group, iCloud container, URL schemes, associated domains, StoreKit product IDs, signing team/profile changes, and similar values all map to irreversible/external identity or configuration risk.
- Distinguish reversible UI changes from potentially lasting product damage.

5. Produce final release posture using this template.
- `Block` (`80-100`): release should stop until manual inspection is complete.
- `Hold for review` (`60-79`): release should not proceed automatically; a human should decide whether this blocks release.
- `Proceed with caution` (`40-59`): release may continue only after explicit mitigations or focused validation.
- `Review recommended` (`20-39`): release may continue after a lightweight manual review confirms intent.
- `Proceed` (`0-19`): no release-blocking surfaces detected from available evidence, or only low-risk surfaces were detected.

6. Explain the score.
- Report the total as `risk_score/risk_score_max`.
- Show the highest-scoring findings first.
- Treat the score as an absolute risk estimate: `0` means no meaningful release risk was found, and `100` means the release would likely cause a major product problem if shipped as-is.
- Do not describe score items as additive points. Use the strongest signal per independent risk category, suppress weaker path-only signals already covered by concrete findings on the same files, and only apply small breadth modifiers for independent secondary risks.
- Mention that ordinary heuristic matches are capped below `100`; reserve `100` for evidence strong enough to say a major release problem is highly likely, not merely possible.
- Explain the risk axis behind each score contribution, not only the matched framework, file type, or key name.
- Include short `diff` excerpts for risky findings so the reviewer can inspect the concrete code/config changes without opening every file immediately.
- Do not rely on the old severity label alone when giving the final decision.

## Safety / Guardrails

- Never bury blocking findings under verbose diff summaries.
- Never claim safety without stating the inspected range and confidence level.
- Keep rule reasoning concrete and actionable.
- Prefer false positives on irreversible-risk surfaces over false negatives, especially durable state, unique identifiers, externally registered IDs, and long-lived configuration values.
- Do not down-rank a durable setting or identifier change only because it appears in a plist, project file, generated schema, or config file rather than application code.

## Response Contract

Return a concise Japanese report with:

1. `結論` (`Block` / `Hold for review` / `Proceed with caution` / `Review recommended` / `Proceed`) and `リスクスコア` (`0-100`)
2. `判定理由` (highest score and durable-risk first)
3. `対象範囲` (base tag, head commit, git range)
4. `主要リスク` (built-in heuristics, concrete findings, and score contribution)
5. `リスク差分抜粋` (short diff snippets for findings or medium+ path-rule signals)
6. `推奨アクション`

## Verification

- Confirm range resolution is explicit and correct.
- Confirm the conclusion matches the listed evidence.
- Confirm the score threshold maps to the conclusion: `80-100=Block`, `60-79=Hold for review`, `40-59=Proceed with caution`, `20-39=Review recommended`, `0-19=Proceed`.
- Confirm built-in heuristic matches and concrete findings are clearly separated.
- Confirm risky findings include short diff snippets in markdown and `risk_diff_snippets` in JSON when changed lines are available.
- Use `--verbose` only when full file/commit listing is necessary.
