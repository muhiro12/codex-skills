---
name: xcode-ui-smoke-auditor
description: Inspect a running Apple app in Simulator, capture reviewable screenshots, and audit reachable screens or release flows. Track coverage and restore Xcode state; use xcode-preview-auditor for SwiftUI Preview captures.
---

# Xcode UI Smoke Auditor

Audit the running app using the active Xcode-native live UI capabilities. Keep
source, project settings, and stored app data unchanged unless the user explicitly
requests changes. Return concise Japanese and reviewable visual evidence.
A smoke audit is scoped runtime evidence, not distribution approval or a
replacement for package tests, builds, or real-device checks.

## Choose Coverage from the Request

- **Targeted:** named screens, devices, flows, or a fix to recheck.
- **Diff-focused:** normal release smoke; use the requested base or latest
  reachable release tag and include affected screens, adjacent transitions, and
  impacted companion surfaces.
- **Gallery:** explicit broad inspection or a navigation/layout foundation review;
  inventory discovered screens and capture safe, reachable representatives.

Read repository `AGENTS.md`, affected code/diff, schemes, routes, launch arguments,
and existing safe fixtures. Do not invent a comparison base or claim every screen
was discovered. Identify supported device families and companion targets before
promising coverage. Keep each relevant target as audited, skipped, or a gap with
its reason. A narrow request need not expand into every supported platform.

Use the current suitable Simulator by default. For broad iPhone/iPad coverage,
choose representative compact and wide cases; prefer iPad landscape when useful,
and confirm orientation from the returned image/hierarchy. Do not count an
unconfirmed landscape capture or an iPhone image as evidence for another target.

## Execute Through Current Capabilities

Read matching Xcode-generated device guidance from the active skill inventory or
`sync-xcode-skills/state/catalog.md`. Resolve current action schemas instead of
assuming namespace names, parameter keys, or platform support.

1. Match the workspace to the repository. Discover and record the original scheme,
   destination, and test plan if changing it; keep a suitable active selection.
2. Switch only to discovered eligible values. Recheck destinations after changing
   scheme. Use the normal development configuration and existing launch arguments
   unless a different release environment is explicitly required.
3. Follow the integration's bounded device-session lifecycle to build/install/run.
   Keep operations that share Xcode selection or a Simulator serial. Do not stop
   another task's build/session to claim ownership of the workspace.
4. Capture the initial screenshot, hierarchy, app state, and available logs before
   navigating. Inspect the actual image; hierarchy alone is not visual evidence.
5. Navigate only through safe discovered routes. Follow the current tool's input
   rules and fresh hierarchy/element coordinates. Inspect resulting state and
   image after each meaningful transition; stop a transition that leaves the app
   on an unexpected screen instead of tapping blindly.
6. Always end sessions and stop runs created only for verification. Restore any
   changed scheme, its test plan, then destination, and confirm the result. If
   another actor changed selection in the meantime, avoid overwriting it and
   report the final state.

Capture transient overlays first. Dismiss only clearly safe Close, Cancel, or
Not Now controls, then capture the underlying screen. Record whether observations
use existing, empty, seeded, or unknown data. Use existing safe fixture routes;
do not add debug code or silently create persistent sample data during an audit.

## Evaluate Screens and Preserve Evidence

Use `apple-hig-ui-guardian` for relevant HIG interpretation after images exist.
Prioritize crashes, blank/frozen primary screens, failed navigation, missing
controls, clipping/overlap, unreadable text, broken presentation, placeholder
content, and runtime errors correlated with visible failures. Separate product
bugs, shared UI issues, fixture problems, and tool limitations.

Maintain a compact ledger: screen/target, captured/failed/skipped/unreachable,
actual state, artifact path, and reason where coverage is missing. Keep unknown
screen coverage explicit. Do not infer hidden behavior from a screenshot.

Preserve original captures and verify the exact images shown in the report.
If a capture is blank, sideways, cropped, obscured, or from the wrong route,
recapture through a suitable supported path or report it as unreviewable.
Do not use generative image edits or reconstructed mockups as audit evidence.
Show reviewable screenshots inline with absolute local paths, or provide a
linked gallery for many captures. Never report visual coverage from unseen or
inaccessible artifacts.

## Failures and Safe Fallbacks

A timeout is ambiguous: inspect current app state, logs, and any screenshot before
calling it an app defect. Separate app-side, repo-setup, tool-side, and scope
blockers. Retry only when a relevant condition or method changes; avoid repeating
an identical failed sequence. Continue independent coverage when possible.

After a concrete native-tool gap, use a documented repository fallback or an
official Apple tool that supplies the needed evidence within the existing task
permissions. Explain the gap and evidence difference. A fallback is not itself
a reason to ask for approval; actual additional permissions, destructive setup,
or a missing product decision may be. Never bypass an approval rejection or
substitute unrelated Preview images for live-app evidence.

Do not erase Simulators, delete app data, reset keychains, change signing or release
settings, perform purchases, send messages, or invoke production/account actions.
Permission grants, sign-in, restore/import, WidgetKit, Siri/Shortcuts, and other
external system flows require a separately authorized safe path. Record gaps
instead of silently performing these actions.

## Report

Lead with observed important findings and distinguish them from unverified gates.
Include the screen/target ledger and a reviewable gallery, actual device/runtime/
orientation/scheme, data state, relevant logs, failed attempts and their owners,
and whether Xcode selection was restored. Keep empty sections out of the answer.

If no defect was observed, say so only for the audited coverage. Name remaining
coverage gaps, including unsupported companion targets or unverified iPad
orientation. A clean smoke pass does not establish purchase/restore success,
privacy declarations, real-device behavior, or App Store distribution readiness.
