---
name: xcode-preview-auditor
description: Audit SwiftUI `#Preview` screens in Apple app repositories by discovering previews, grouping them by screen and source file, attempting XcodeBuildMCP-backed capture when available, explicitly reporting MCP/fallback failures and blocker ownership, and returning a concise Japanese audit report without auto-fixing by default. Use for audit-first requests such as `#Previewをキャプチャして`, `Preview を見て UI 崩れを監査して`, `画面プレビューを一覧で確認したい`, and `コンポーネントではなく 1 画面単位で見てほしい`. Prefer this skill when the user wants capture coverage, issue classification, or missing-preview reasoning, not default implementation work.
---

# Xcode Preview Auditor

Audit SwiftUI `#Preview` in Apple app repositories. Discover previews, prefer screen-level captures, use XcodeBuildMCP as the first capture surface when it exposes a suitable direct Preview workflow, make capture coverage explicit by file and screen, show captured images back to the user, and return a concise Japanese audit report instead of defaulting to fixes.

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
5. Check available XcodeBuildMCP capture capabilities before attempting capture.
   - Use a dedicated Preview capture path if the current XcodeBuildMCP session exposes one.
   - If only simulator workflow tools are available, record that direct Preview capture is unavailable before considering fallback.
   - Before any XcodeBuildMCP build, run, or test call, call `session_show_defaults` and follow the active project/workspace, scheme, and simulator defaults.
6. Capture with XcodeBuildMCP first when a faithful Preview or screen capture path exists. Treat the first visible viewport as the default audit scope.
7. If MCP capture fails or direct Preview capture is unavailable, record an explicit failure entry before any fallback:
   - what was attempted
   - why it failed
   - whether the blocker is `app-side`, `preview-side`, or `tool-side`
   - whether a faithful fallback exists
8. Use Simulator fallback only when the exact same screen state can be reproduced through existing app flows such as deep links, seeded routes, or normal navigation already present in the repository.
9. For simulator fallback through XcodeBuildMCP, prefer the standard flow: `session_show_defaults`, then `build_run_sim` when defaults are complete, then `screenshot`. Do not use `boot_sim` or `open_sim` as prerequisites for `build_run_sim`.
10. If fallback succeeds after MCP failure or direct Preview capture is unavailable, keep the preview as `captured`, but note `MCP failed/unavailable -> Simulator fallback` and preserve the original failure summary for blocker reporting.
11. Show each obtained capture to the user, not just an inventory line. When local image rendering is supported, embed the image inline with a short caption.
12. Review captures at screen level and classify each problem as:
   - app-side UI issue
   - design-system / shared UI foundation issue
   - data/setup issue
   - tooling blocker
13. Report findings in concise, polite Japanese.
14. Do not implement fixes unless the user explicitly asks.

## Coverage Ledger

Maintain one coverage entry per discovered preview, grouped by likely screen and source file.

`captured`

- an inspectable artifact exists and is exposed to the user
- note the mechanism: `MCP` or `Simulator fallback`

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

## XcodeBuildMCP-First Capture Policy

`#Preview` is the canonical source of truth.

Keep XcodeBuildMCP as the first-choice mechanism for every eligible preview when the available tool surface can render or reproduce that preview faithfully.

Do not pretend a dedicated Preview renderer exists when the current XcodeBuildMCP tools expose only simulator build/run/screenshot workflows. In that case, mark direct Preview capture as a `tool-side` blocker and continue only with an explicitly faithful simulator fallback.

Use Simulator fallback only after an MCP attempt fails or direct Preview capture is recorded as unavailable, and only when the exact same screen state can be reproduced through existing app flows such as deep links, seeded routes, or normal navigation already present in the repository.

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
- examples: MCP timeout, renderer session crash without app-side evidence, tool cannot resolve a preview that otherwise looks correctly defined, or the current MCP tool surface lacks direct Preview capture support

## Triage Rules

Classify findings conservatively.

`app-side UI issue`

- layout breakage, clipping, overlap, truncation, unsafe-area mistakes, navigation or title issues, wrong conditional rendering, or state handling specific to that screen

`design-system / shared UI foundation issue`

- the same spacing, typography, control, token, container, or reusable component problem appears likely to affect multiple screens

`data/setup issue`

- placeholder data, missing fixture wiring, incomplete environment injection, or unrealistic preview state prevents reliable audit

`tooling blocker`

- Xcode MCP render failure, unsupported preview dependency, simulator-only limitation, or other non-product blocker prevents trustworthy capture

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

In `主要なブロッカー`, rank the main reasons coverage was limited. Summarize the affected preview or screen, attempted action, failure reason, blocker ownership, and whether fallback was possible.

End with one short line that the run was audit-only and no fixes were applied by default.

## Notes

If the user narrows scope, prioritize the named screens, device class, or width constraint first.

If the user asks for compact-width issues, prefer previews or preview variants that already express compact layouts before using any fallback.

If the user later asks for fixes, treat the audit report as the handoff and only then move into implementation.

Do not auto-fix preview code, app code, or shared UI code during the audit unless the user explicitly changes the task from auditing to implementation.
