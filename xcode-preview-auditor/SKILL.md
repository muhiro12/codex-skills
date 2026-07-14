---
name: xcode-preview-auditor
description: Audit SwiftUI `#Preview` screens in Apple app repositories by discovering previews, grouping them by screen and source file, capturing them directly with native Xcode MCP `RenderPreview`, explicitly reporting Preview or faithful live-app fallback failures and blocker ownership, and returning a concise Japanese audit report without auto-fixing by default. Use for audit-first requests such as `#Previewをキャプチャして`, `Preview を見て UI 崩れを監査して`, `画面プレビューを一覧で確認したい`, and `コンポーネントではなく 1 画面単位で見てほしい`.
---

# Xcode Preview Auditor

Audit SwiftUI `#Preview` in Apple app repositories. Discover previews, prefer screen-level captures, use native Xcode MCP `RenderPreview` as the direct capture surface, make capture coverage explicit by file and screen, show captured images back to the user, and return a concise Japanese audit report instead of defaulting to fixes.
For screen-level Apple UI previews, use `$apple-hig-ui-guardian` after capture so the audit covers HIG alignment, not only render correctness.

## Xcode Skill Catalog

When `sync-xcode-skills/state/catalog.md` exists under the active Codex skills root, scan it for task-relevant Xcode-provided `xcode-skill-*` guidance before applying this skill's local Preview capture or audit heuristics. Do not hardcode individual Xcode-provided skill names. If the catalog is missing or no listed skill matches, continue with this skill normally.

## Workflow

1. Discover `#Preview` definitions from source and note source file, preview identifier, preview label, and likely target surface.
2. Build a coverage ledger grouped by likely screen and source file. Every discovered preview must end in exactly one state:
   - `captured`
   - `failed`
   - `not attempted`
3. Separate likely screen previews from likely component previews before capture. Keep excluded components in the ledger as `not attempted` with a reason instead of dropping them silently.
4. Audit render prerequisites for each candidate:
   - missing environment objects, model containers, dependencies, or sample data
   - preview-only crashes or compile errors
   - unsupported services or platform/tooling blockers
5. Establish the native Xcode MCP workspace selection before capture.
   - Call `XcodeListWindows` and choose the `tabIdentifier` that matches the repository.
   - Call `XcodeListSchemes` and `XcodeListRunDestinations`, and record the original `activeSchemeName`, the active scheme entry's `disambiguatedName`, and `activeDestinationDisplayTitle`.
   - Keep the current scheme and destination when they can render the candidate. Otherwise switch only to discovered, eligible values with `XcodeSwitchScheme` and `XcodeSwitchRunDestination`.
6. Call `RenderPreview` with the source file path and zero-based preview definition index. Treat the first visible viewport as the default audit scope. Record its `previewSnapshotPath`, `errors`, and `renderedDestination`.
7. Use returned localizations, variants, timeline indexes, or toggle states only when the requested coverage needs them. Run localization overrides sequentially rather than in parallel.
8. If `RenderPreview` fails or is unavailable, record an explicit failure entry before any fallback:
   - what was attempted
   - why it failed
   - whether the blocker is `app-side`, `preview-side`, or `tool-side`
   - whether a faithful fallback exists
9. Use live-app fallback only when the exact same screen state can be reproduced through an existing deep link, seeded route, or normal navigation already present in the repository. Start `DeviceInteractionStartSession` only after deciding fallback is faithful, then call `DeviceInteractionInstallAndRun`, use `DeviceInteractionSynthesize` with no interaction for the initial screenshot and hierarchy, interact only from current hierarchy coordinates when needed, and always call `DeviceInteractionEndSession`.
10. If fallback succeeds after `RenderPreview` failure or unavailability, keep the preview as `captured`, but note `RenderPreview failed/unavailable -> Device Interaction fallback` and preserve the original failure summary.
11. When capture work finishes, end any device-interaction session. If the workflow changed Xcode's active selection, restore the original scheme first, restore its original destination second, and re-list both to confirm. Report any selection that could not be restored.
12. Show each obtained capture to the user, not just an inventory line. When local image rendering is supported, embed the image inline with a short caption.
13. Review captures at screen level. For likely screen previews, apply `$apple-hig-ui-guardian` and classify both visible UI breakage and HIG drift.
14. Classify each problem as:
   - app-side UI issue
   - design-system / shared UI foundation issue
   - HIG / Apple platform guidance issue
   - data/setup issue
   - tooling blocker
15. Report findings in concise, polite Japanese.
16. Do not implement fixes unless the user explicitly asks.

## Coverage Ledger

Maintain one coverage entry per discovered preview, grouped by likely screen and source file.

`captured`

- an inspectable artifact exists and is exposed to the user
- note the mechanism: `RenderPreview` or `Device Interaction fallback`

`failed`

- a capture attempt was made but no trustworthy artifact was obtained
- include the attempted action, failure reason, and blocker ownership

`not attempted`

- no capture was attempted because of scope choice, component filtering, duplicate surface coverage, or lack of a faithful fallback path
- include the concrete reason so coverage gaps stay auditable

## Screen Selection

Default to excluding obvious components unless the user explicitly asks to include them.

Likely screen previews:

- names or files that suggest app surfaces such as Home, Settings, Detail, List, Editor, Onboarding, Dashboard, or similar
- previews wrapped in `NavigationStack`, `TabView`, split view, or other screen-level containers
- device-sized layouts with multiple content regions or realistic end-user state

Likely component previews:

- isolated rows, cells, buttons, cards, charts, badges, pickers, or small layout experiments
- preview matrices for style variants, color states, or single control permutations
- small fixed frames that do not represent a full user-visible screen

When ambiguous, include the preview only if it reasonably represents one screen the user could recognize as a product surface.

## Native RenderPreview-First Capture Policy

`#Preview` is the canonical source of truth.

Use native Xcode MCP `RenderPreview` as the first-choice mechanism for every eligible preview. It builds and renders the selected Preview definition and returns the snapshot path plus render errors and actual rendered destination.

If `RenderPreview` is absent from the current tool inventory, rejects the source/index, or returns no inspectable snapshot, record the direct capture as a blocker before considering fallback. Do not replace it silently with a screenshot of a merely similar app state.

Use Device Interaction fallback only after `RenderPreview` fails or is recorded as unavailable, and only when the exact same screen state can be reproduced through existing app flows such as deep links, seeded routes, or normal navigation already present in the repository.

Do not claim equivalence for preview-only states that cannot be reproduced faithfully. Keep them in the `failed` or `not attempted` part of `プレビューカバレッジ要約` with a concrete reason.

Do not silently skip missing captures. If capture fails, record:

- what was attempted
- the observable failure or error symptom
- whether the blocker is `app-side`, `preview-side`, or `tool-side`
- whether a faithful fallback was unavailable, attempted, or succeeded

Do not default to stitched or full-scroll capture. Audit only the first visible viewport unless the user explicitly asks for more.

## Blocker Ownership

Use this ownership only for capture failures and blockers.

`app-side`

- app build or runtime behavior prevents rendering even though the preview mechanism itself is behaving as expected
- examples: shared code crash, compile failure from app code, broken app-level dependency wiring

`preview-side`

- the issue is isolated to preview definitions or preview-only setup
- examples: missing preview fixtures, missing environment injection, unsupported preview macro composition, preview-only sample data problems

`tool-side`

- the failure is attributable to Xcode, MCP transport, preview renderer instability, or capture tooling rather than product code
- examples: native Xcode MCP timeout, renderer session crash without app-side evidence, `RenderPreview` cannot resolve a preview that otherwise looks correctly defined, or the current tool surface lacks `RenderPreview`

## Triage Rules

Classify findings conservatively.

`app-side UI issue`

- layout breakage, clipping, overlap, truncation, unsafe-area mistakes, navigation or title issues, wrong conditional rendering, or state handling specific to that screen

`HIG / Apple platform guidance issue`

- non-native navigation, unclear hierarchy or primary action, custom controls that duplicate standard controls poorly, weak Dynamic Type or accessibility behavior, poor contrast, small hit targets, gesture-only interaction, platform adaptation gaps, or other findings from `$apple-hig-ui-guardian`
- cite the relevant Apple official URL when the finding depends on a specific HIG rule or platform convention

`design-system / shared UI foundation issue`

- the same spacing, typography, control, token, container, or reusable component problem appears likely to affect multiple screens

`data/setup issue`

- placeholder data, missing fixture wiring, incomplete environment injection, or unrealistic preview state prevents reliable audit

`tooling blocker`

- native Xcode MCP `RenderPreview` failure, unsupported preview dependency, live-app fallback limitation, or another non-product blocker prevents trustworthy capture

## Output Contract

Return concise, polite Japanese with these sections in this order:

- `プレビューカバレッジ要約`
- `主要な UI 問題`
- `主要なブロッカー`

In `プレビューカバレッジ要約`, include:

- total counts for `captured`, `failed`, and `not attempted`
- grouping by likely screen and source file
- for `captured`: preview identifier, mechanism, artifact path, and the image itself whenever the environment supports local image display
- for `failed`: what was attempted, why it failed, and whether the blocker is `app-side`, `preview-side`, or `tool-side`
- for `not attempted`: the concrete reason

Do not report a capture as obtained unless the user can inspect the artifact from the response.

If local images can be rendered, prefer inline display with absolute filesystem paths. If inline display is not available, still expose the capture path and state that the image could not be rendered inline.

In `主要な UI 問題`, rank only the most important user-visible problems seen in trustworthy captures. Keep it concise and tie each item to the affected screen or file.
Mark HIG-specific findings as `HIG / Apple platform guidance issue` when they come from `$apple-hig-ui-guardian`.

In `主要なブロッカー`, rank the main reasons coverage was limited. Summarize the affected preview or screen, attempted action, failure reason, blocker ownership, and whether fallback was possible.

End with one short line that the run was audit-only and no fixes were applied by default.

## Notes

If the user narrows scope, prioritize the named screens, device class, or width constraint first.

If the user asks for compact-width issues, prefer previews or preview variants that already express compact layouts before using any fallback.

If the user later asks for fixes, treat the audit report as the handoff and only then move into implementation.

Do not auto-fix preview code, app code, or shared UI code during the audit unless the user explicitly changes the task from auditing to implementation.
