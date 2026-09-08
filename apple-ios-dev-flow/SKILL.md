---
name: apple-ios-dev-flow
description: Implement, fix, refactor, or debug Apple-platform apps and Swift packages. Select relevant Apple guidance and the smallest verification evidence for the changed boundary; use a more specific skill for a focused audit.
---

# Apple iOS Dev Flow

Start with the affected code, diagnostics, tests, worktree changes, and repository
`AGENTS.md`. Complete the requested outcome, preserve unrelated work, and explain
results in concise Japanese. Keep repository artifacts in the required language.

## Choose Guidance for the Actual Decision

- Use current Apple and Swift official guidance, native APIs, and official tools
  as the platform baseline. Verify version-sensitive behavior against the app's
  actual SDK and release toolchain. A newer installed beta is not automatically
  the app's release baseline.
- Consult the relevant developer-principle domain when a reusable architectural,
  product, or workflow tradeoff matters. Current user instructions and hard
  repository constraints take precedence over older principles.
- Prefer matching Xcode-provided skills from the active skill inventory. The
  generated `sync-xcode-skills/state/catalog.md` beside the installed skills is
  an additional discovery source. Check it once when useful; do not repeatedly
  reload it through every specialist.
- Load only specialists that change the current decision. HIG, Swift correctness,
  and local style remain constraints without requiring a full portfolio audit
  for a small edit. Reuse guidance already read in this task.

| Need | Guidance |
| --- | --- |
| UI composition, navigation, accessibility, platform fit | `apple-hig-ui-guardian`; matching Xcode SwiftUI guidance |
| Swift API, concurrency, ownership, package boundaries | `swift-code-guardian` |
| Local Swift formatting and naming | `mh-swift-style` |
| Framework adoption, lifecycle, entitlements, unfamiliar data wiring | `apple-sample-code-advisor` when a relevant sample clarifies implementation |
| Preview capture or live screen audit | `xcode-preview-auditor` or `xcode-ui-smoke-auditor` |
| Localization, schema, release risk, release notes | The corresponding focused skill when that is the requested work |
| App Intents, SwiftUI performance, leaks, browser mirroring | A matching installed specialist with the required runtime capabilities |

A plugin's guidance-only skill can remain useful without its execution MCP.
Check dependencies for the selected workflow, rather than rejecting an entire
plugin because one unrelated namespace is absent. Never invent unavailable
APIs or install extra tooling merely because a skill mentions it.

Use Incomes or another relevant sibling as a read-only reference when current
repository evidence and official guidance do not settle a concrete comparison.
Do not turn app-local product behavior into a shared dependency merely to align
repositories. Weigh change cost, tests, release coupling, and demonstrated reuse.

## Implement and Verify

Choose the smallest complete change and verify it against the repository contract.
Run a documented formatter/autofix before the final non-destructive checks.

| Changed boundary | Evidence |
| --- | --- |
| Library/package behavior | Relevant library/package tests and retained repository rules |
| App, widget, watch, extension, or UI adapter | Build the affected surface |
| Public API, persisted schema, wire format, products, adopter wiring | Relevant tests plus an affected consumer/surface build |
| Navigation, lifecycle, persistence, sync, notifications, entitlements, visible UI | Add targeted runtime, logs, Preview, or live UI evidence for the actual risk |

Mixed changes need both relevant test and surface evidence. Do not infer runtime
success from a build, visual acceptance from source, or release approval from a
risk score. Report current-change failures separately from pre-existing failures.

A missing aggregate verify command does not prevent ordinary implementation.
Derive proportionate checks from the real project/package/CI configuration and
state the limits. Use `apple-repo-verify-bootstrapper` only when verification
setup is requested or necessary to unblock the task; do not add scaffolding as
an unrelated prerequisite. `ci-verify-and-summarize` can summarize an existing
shell or Xcode-native contract without creating another wrapper.

## Xcode Execution

1. Resolve workspace, selection, build, tests, Preview, run/log, and device
   interaction capabilities from the current tool schemas. Match the workspace
   to the repository; never guess a runtime handle.
2. Before switching, capture the original scheme, destination, and active test
   plan when relevant. Use discovered eligible values. A scheme switch may
   change the destination; recheck before proceeding.
3. Keep stateful Xcode operations serial for the shared workspace and Simulator.
   Independent source analysis can run alongside them. Do not interrupt another
   task's build or session to obtain your own evidence.
4. Follow the active integration's lifecycle and generated device guidance.
   Inspect current screenshots, hierarchy, and logs for runtime claims. End
   interaction sessions and stop runs started only for verification.
5. Restore the scheme, its test plan if changed, then destination, and confirm
   restoration. Do not overwrite a later user selection; report any unresolved
   final state.

When a capability is absent or fails, record the observed gap and use a relevant
repository fallback or official Apple tool that covers the same evidence within
the user's authorization. Do not invent adapters, weaken approval controls, or
claim equivalent coverage from an unrelated screenshot. Request input only when
an actual missing decision or permission prevents the next necessary action.

## Report

State what changed, the material decision, checks that actually completed, and
remaining limitations. Link reviewable artifacts when useful. Preserve the
user's requested scope through verification instead of ending after an arbitrary
number of steps. Do not persist new principles without an explicit request.
