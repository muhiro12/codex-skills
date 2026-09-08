---
name: xcode-preview-auditor
description: Capture and review SwiftUI Preview screens with explicit per-preview coverage and blocker ownership. Prefer screen-level previews and preserve failures when using a faithful live-app fallback.
---

# Xcode Preview Auditor

Audit SwiftUI `#Preview` without changing app or preview code unless fixes are
requested. Prefer screen-level captures and return concise Japanese with images
that the user can inspect. Use `xcode-ui-smoke-auditor` for a live-app audit.

## Discover and Select

Read repository instructions and discover previews in the requested source scope.
Record source file, label/identifier, preview definition, likely screen, and target.
Separate screens from isolated rows, buttons, cards, and component matrices.
Exclude obvious components by default, but retain them as not attempted with a
reason. Respect named screens, width/device constraints, and requested variants.

Maintain one ledger entry per discovered preview:

- `captured`: an inspectable artifact exists; record direct Preview or faithful
  live-app fallback as the mechanism.
- `failed`: attempted but no trustworthy artifact exists; record the action,
  symptom, and blocker owner.
- `not attempted`: scope exclusion or unsupported/unreachable state, with a reason.

This is discovered-source coverage, not proof that all app states exist as previews.

## Capture

Read relevant generated Xcode guidance when available. Resolve workspace, scheme,
destination, and Preview rendering actions from the active tool inventory and
schemas, including how the current renderer identifies a definition or variant.

Match the workspace to the repository. Record original scheme, destination, and
test plan if changing it. Switch only to discovered eligible values and recheck
destinations after a scheme change. Keep shared Xcode stateful operations serial;
independent source analysis can proceed alongside them.

Use direct native Preview rendering first. Record the requested definition and
actual returned destination, variants, errors, and artifact path. Inspect the
returned image. Default to the first viewport; request additional states or
localizations only when they serve the user's coverage. Run state overrides
sequentially.

When rendering fails, preserve the attempt and classify the owner:

- `app-side`: product code, build, or runtime dependency prevents capture.
- `preview-side`: fixture, environment, or preview-only setup fails.
- `tool-side`: integration, renderer, transport, or missing capability blocks it.

Do not diagnose an app defect from a tool timeout alone. Inspect available state
and logs; retry only after a relevant change rather than repeating identical
attempts indefinitely.

## Faithful Fallback

After recording direct rendering failure or unavailability, a live capture may
stand in only if an existing route, deep link, or fixture reproduces the same
screen state. During capture-only work, do not add seed code, change product data,
or use merely similar screens as substitutes. If fixes are already requested,
repair a confirmed preview/setup defect in the implementation phase and recapture
it; the original failure remains part of the evidence. New persistent live-app
data or destructive setup still needs its own authorized safe path.
Follow the active live-session lifecycle and its input
rules, inspect the screenshot and hierarchy, and always end the session.

A successful fallback can be `captured` in the ledger, but retain the original
direct Preview failure and label the mechanism. Count direct and fallback captures
separately. Preview-only states without a faithful route remain failed or not
attempted; they do not become verified by association.

Restore changed scheme, its test plan, then destination, and confirm restoration.
Avoid overwriting a later user selection; report any unresolved final state.

## Review and Report

Show each useful capture inline with an absolute path or in a linked gallery.
Verify the exact report images; blank, wrong-state, or inaccessible images do not
support coverage. Do not use generative edits or mockups as captured evidence.

Apply relevant `apple-hig-ui-guardian` guidance to screen findings. Separate
app-specific UI, shared UI foundation, HIG, fixture/setup, and tooling issues.
Tie findings to visible evidence and files, citing a specific Apple rule when it
determines the finding. Do not infer runtime, accessibility, or release acceptance
beyond what the capture proves.

Report captured/failed/not-attempted counts, direct-versus-fallback mechanisms,
important findings, and concrete blockers with their attempted actions and owners.
Include coverage exclusions and selection restoration. Keep output concise and
avoid a long inventory without inspectable images. Fixes require an implementation
request, which may already be present in the current task.
