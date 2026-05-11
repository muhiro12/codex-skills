---
name: xcode-ui-smoke-auditor
description: Run a safe, audit-only live Simulator UI smoke review for Apple-platform app repositories using XcodeBuildMCP. Use when the user asks for release UI smoke, Simulator screenshot audit, visual check, Apple-platform visual review, iPad landscape UI check, Apple Watch/companion target coverage, Xcode MCPでUI確認, 実アプリを起動して画面崩れを確認, or similar requests to build/run the current app, inspect live UI, capture screenshots, navigate key screens, and report audit findings. This is for live Simulator app auditing with current repo/session settings, not SwiftUI #Preview inspection, unit tests, UI tests, snapshot tests, code fixes, destructive simulator setup, release-environment manipulation, or forcing Release configuration.
---

# Xcode UI Smoke Auditor

## Overview

Run a pre-release or change-time UI smoke audit against the real app running in Simulator through XcodeBuildMCP.
Keep the workflow evidence-backed and non-mutating: inspect repository truth, run the current app with current repo/session settings, capture UI hierarchy and screenshots, navigate core reachable screens, and report what was covered and what remains unknown.

## When To Use

Use this skill for audit-first requests that ask Codex to inspect a live Apple app UI before release or before shipping a change.
Treat this as a lightweight manual smoke audit with tool support, not as release-environment validation and not as a replacement for CI, unit tests, UI tests, snapshot tests, or SwiftUI `#Preview` review.

Do not use this skill for SwiftUI Preview capture or preview coverage audits; use a Preview-specific workflow for that.

## Non-Mutating First Pass

Before asking questions or running the app, discover the repository's own instructions and available surfaces:

- Read relevant `AGENTS.md`, README, docs, and `ci_scripts` guidance.
- Identify Xcode projects/workspaces, schemes, test plans, launch arguments, debug/sample-data entrypoints, deep links, route names, and supported platforms or device families.
- Use repository files, build settings, scheme names, test plans, and app metadata to infer supported targets before choosing simulators.
- Treat discovered companion app targets such as watchOS apps/extensions as coverage candidates. Every discovered supported platform/device family must end as `audited`, `skipped`, or `coverage gap` with a reason.
- Prefer repo-provided sample data or debug seed flows when they are clearly safe and non-destructive.
- If setup would erase data, write persistent state, hit production services, alter release settings, or otherwise be destructive, ask before doing it.
- If authentication, network services, purchases, permissions, or account state are required, use only clearly safe local/test flows; otherwise report the coverage limit or ask for explicit direction.
- Ask the user only after this pass, and only for product-scope choices that repository evidence cannot answer.

## Simulator Selection

Respect the current XcodeBuildMCP session defaults first.
Do not force a Release configuration, release-like scheme, or iPhone/iPad-only matrix unless the user or repository instructions explicitly require it.

Select representative simulator coverage from the app's discovered supported targets and the XcodeBuildMCP tools available in the current session:

- Prefer the currently configured simulator when it matches the app target.
- When defaults are incomplete, choose a safe representative simulator for each supported platform/device family that XcodeBuildMCP can actually build/run and inspect.
- For iPadOS-capable apps, treat landscape as the preferred representative iPad smoke case because split views, sidebars, and wide layouts are common shipping surfaces.
- Attempt iPad landscape only when a supported XcodeBuildMCP orientation/device-control tool or safe user/environment state makes it possible. Do not imply landscape is guaranteed until it is verified.
- If orientation cannot be changed or verified because the tool is missing, MCP/macOS accessibility blocks it, or the user has not manually rotated the Simulator, continue with the available iPad orientation and record `iPad landscape not confirmed` as a coverage gap with the concrete reason.
- If the user manually rotates the Simulator, re-check orientation from screenshot dimensions, UI hierarchy, or other visible evidence, then continue the landscape audit only after verification.
- Probe the available XcodeBuildMCP tool surface before promising coverage. If only iOS Simulator tools are available, audit the supported iOS/iPadOS surface and report non-iOS targets as coverage gaps instead of pretending they were checked.
- If a target is unsupported, unavailable, not configured, or unsafe to run, record the reason in the report.

## Build And Launch Workflow

Use XcodeBuildMCP tools over shell commands for project discovery, session defaults, build/run, simulator control, screenshots, UI hierarchy, and interactions.

1. Call `session_show_defaults` before the first XcodeBuildMCP build/run action in the session, and keep the original defaults for reporting or restoration.
2. If project/workspace, scheme, or simulator defaults are missing or clearly wrong, use discovery tools such as `discover_projs`, `list_schemes`, and `list_sims` to find valid candidates.
3. Set or correct session defaults with `session_set_defaults` only after discovery. Do not persist defaults unless the user explicitly asks.
4. Use the current session defaults, current app scheme, normal development configuration, and existing launch arguments by default. Use release-like settings only when the user asks or repository instructions clearly require them.
5. Once defaults are complete, call `build_run_sim`; do not call `boot_sim` or `open_sim` as prerequisites for `build_run_sim`.
6. Wait for a stable launch, then verify the app with UI hierarchy inspection and a screenshot before navigating.
7. If runtime logs are available from the build/run response or log tools, keep them as supporting evidence and watch for repeated errors, launch crashes, or obvious runtime failures.
8. If `build_run_sim` times out, do not classify it as a failure immediately. Check `snapshot_ui` and `screenshot` to see whether the app is already running or the Simulator is usable.
9. If the app appears installed but is not foregrounded, and launch defaults or bundle id are available, try `launch_app_sim`, then re-check `snapshot_ui` and `screenshot` before continuing.
10. If session defaults were changed for additional targets, restore the original defaults at the end when it is safe and useful. If not restored, report the final active defaults and why they changed.

## UI Audit Workflow

For each selected target, maintain a small coverage ledger of screens attempted, captured, failed, and skipped.

- Start with the initial screen, then navigate only through safe, user-reachable paths discovered from repository evidence or visible UI.
- Record the current Simulator/app data state before interpreting content: existing data, empty state, repo-provided sample data, or unknown.
- If no sample data was inserted and no data was cleared, state that observations are dependent on the current Simulator state.
- For iPad targets, verify whether the captured UI is landscape or portrait. If landscape was intended but not achieved, do not treat the iPad pass as fully covered.
- Prioritize primary tabs, sidebars, navigation roots, settings, detail screens, editor/create flows, sheets, popovers, and platform-specific layouts that can be reached without destructive actions.
- Inspect the live UI hierarchy with the available tool, especially `snapshot_ui` when present, before tapping or gesturing.
- Use screenshots as the visual evidence source; use UI hierarchy to guide navigation and support findings, not as a substitute for visual inspection.
- Prefer accessibility `id` or `label` targets for `tap`; use coordinates only as a fallback after confirming the visible UI state.
- After any coordinate tap or gesture fallback, immediately verify the result with UI hierarchy and screenshot. If the app leaves the expected screen, goes to the Home screen, opens the wrong surface, or becomes ambiguous, stop that transition and record a failed navigation instead of continuing deeper.
- For Tip popovers, onboarding prompts, permission dialogs, and other transient overlays, capture the covered state first. If a clearly safe Close, Cancel, Dismiss, or Not Now action is available, dismiss it and capture the underlying screen too.
- Use safe gestures such as scrolls or back swipes only when they match visible navigation.
- Capture a screenshot after launch and after each meaningful transition. Expose screenshot paths in the final report, and show images inline when the environment supports local image rendering.
- Prefer screenshots that are visually usable as evidence for a human reviewer. If a screenshot is sideways, cropped, blank, on the wrong surface, obscured, or otherwise hard to review, mention that and attempt a safer alternate capture method when one is available.
- Do not claim visual coverage from screenshots that the user cannot inspect or that are not reviewable enough to support the finding.
- Stop when coverage is enough for a smoke audit or when further navigation would require destructive setup, credentials, production actions, or product decisions.

Flag user-visible problems conservatively:

- blank or frozen screens
- launch crashes or failed relaunches
- failed navigation or unreachable primary controls
- missing primary controls or broken empty states
- clipped, truncated, overlapping, or unreadable text
- broken sheets, popovers, tab bars, sidebars, or split-view behavior
- platform-specific layout collapse
- unlocalized placeholder, debug, or fixture text in shipping-facing surfaces
- repeated runtime errors that correlate with visible UI problems

## Evidence And Reporting

Return a concise evidence-backed report in the user's language unless instructed otherwise.
Separate current findings from coverage gaps and tool limitations.

Include:

- exact device, runtime, platform, orientation when relevant, scheme, configuration, and launch arguments used
- XcodeBuildMCP tools and notable commands/actions used
- screenshots captured, grouped by device, orientation, and screen, with absolute paths and inline images when possible
- observed Simulator/app data state for each target, especially when results depend on existing local state
- screens and transitions covered
- failed or skipped screens with concrete reasons
- whether findings came from screenshot inspection, UI hierarchy inspection, runtime logs, or a combination
- remaining coverage gaps, including supported targets that could not be audited
- runtime crash/error summary when available
- any `build_run_sim` timeout recovery attempts, including whether `snapshot_ui`, `screenshot`, or `launch_app_sim` showed the app was usable
- any session defaults changed during the audit, whether the original defaults were restored, and the final active defaults if not restored

Use these finding categories:

- `blocking issues`: likely shipping blockers such as launch crash, blank primary screen, unusable navigation, or severe layout collapse
- `warnings`: visible problems that may be shippable but need review, such as clipping, placeholder text, broken secondary layout, or repeated non-fatal runtime errors
- `notes`: coverage context, minor observations, tool limitations, and non-blocking gaps

Use this final report order unless the user asks for another format:

1. `blocking issues`
2. `warnings`
3. `notes`
4. `coverage gaps`
5. `screenshots`
6. `session defaults`

Keep each section short. For empty finding sections, say `none observed in audited coverage` rather than omitting the section. In `coverage gaps`, include skipped targets, discovered companion targets that were not audited, orientation gaps such as `iPad landscape not confirmed`, unreachable screens, state-dependent coverage, tool-side limitations, and transient overlays that could not be dismissed safely. In `screenshots`, provide a concise gallery or grouped index by device, orientation, and screen; include absolute paths; embed each reviewable image with Markdown image syntax when local image rendering is supported; if inline rendering is unavailable, say so explicitly and provide the compact index. In `session defaults`, include original defaults, changes made during the audit, whether they were restored, and final defaults if they were not restored.

Use screenshots to support both automated smoke judgment and human release review. If screenshot evidence is incomplete or hard to review, say so in `warnings` or `coverage gaps` and avoid claiming complete visual coverage for that screen.

Never silently pass or fail the app. Always state what was actually observed and what was not covered.
When no issues are found, say that no blocking issues were observed in the audited coverage and still list remaining gaps.

## Safety Rules

Keep the audit non-mutating unless the user explicitly changes the task.

Do not:

- modify source files, project settings, entitlements, schemes, tests, snapshots, or localization files
- add XCUITest targets, UI tests, snapshot tests, accessibility identifiers, debug routes, or sample data code
- erase simulators, delete app data, reset keychains, wipe containers, or run destructive seed/setup
- change release configuration, signing, provisioning, bundle identifiers, build numbers, or distribution settings
- persist XcodeBuildMCP defaults or write repository config solely for the audit
- perform production, purchase, send, delete, account, or externally visible actions
- grant sensitive permissions, complete onboarding, create accounts, or sign in unless the user explicitly asks and the environment is known safe
- use shell `xcodebuild`, `simctl`, or app-specific scripts as a replacement for XcodeBuildMCP UI auditing unless the user approves a fallback after a clear tool-side blocker

If the user asks for fixes after the audit, treat the report as the handoff and switch to an implementation workflow.

## Failure Handling

Classify blockers by ownership when coverage fails:

- `app-side`: app build, launch, runtime, routing, or UI behavior prevents inspection
- `repo-setup`: missing instructions, fixtures, credentials, scheme clarity, or safe sample data prevents realistic coverage
- `tool-side`: XcodeBuildMCP, Simulator, Xcode, or current tool-surface limitations prevent trustworthy inspection
- `scope`: the requested screen or platform requires a product decision, destructive setup, login, or unavailable device/runtime

For each failure, report what was attempted, the observed symptom, the likely owner, and the next safe action.
Do not mask tool failures by substituting unrelated screenshots or Preview captures.
Treat a timeout as ambiguous until live state checks prove the app is unusable or unavailable.
