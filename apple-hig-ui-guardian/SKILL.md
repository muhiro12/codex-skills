---
name: apple-hig-ui-guardian
description: Create, audit, and fix Apple-platform user interfaces so they follow Apple's Human Interface Guidelines. Use when building or refactoring SwiftUI, UIKit, AppKit, WatchKit, WidgetKit, App Intents, or other Apple app UI; when checking whether screens, components, navigation, controls, accessibility, layout, typography, Liquid Glass, or platform adaptation align with HIG; or when repairing UI issues by replacing non-native or inconsistent patterns with HIG-aligned Apple platform patterns.
---

# Apple HIG UI Guardian

## Overview

Use this skill as an active HIG gate for Apple-platform UI work. Treat Apple's Human Interface Guidelines as a design constraint, not as a fallback inspiration, while still preserving the app's product intent and repository conventions when they do not conflict with Apple guidance.

Prefer current Apple official material over memory. The HIG changes over time, so verify relevant guidance from Apple before making or judging design decisions that depend on platform behavior, components, accessibility, or visual system direction.

## Source Order

Use this decision order:

1. Explicit user intent, product constraints, and current repository evidence.
2. Current Apple official guidance: HIG, Apple Developer documentation, Apple sample code, WWDC material, and Swift guidance.
3. Existing repository UI conventions, only when they are compatible with current Apple guidance.
4. Local sibling repositories or older app patterns, only as read-only examples after Apple guidance is checked.

If existing app UI conflicts with HIG, identify the conflict and propose a HIG-aligned correction instead of preserving the local pattern by default.

## Required References

Read `references/rubric.md` for every create, audit, or fix task.

Read `references/source-map.md` when choosing which Apple pages to verify or cite. If the HIG page requires JavaScript or a topic page is hard to read directly, use web search restricted to `developer.apple.com` and rely only on official Apple sources.

## Workflow Decision Tree

### Create HIG-Aligned UI

1. Identify the target platform, device classes, screen role, primary user task, and relevant system surfaces.
2. Read the HIG rubric and verify the relevant Apple source pages before settling the UI shape.
3. Prefer native Apple components, navigation containers, controls, presentation styles, system typography, semantic colors, and platform-adaptive layout.
4. Use custom UI only when it serves a real product need that native components cannot express cleanly.
5. Include accessibility, Dynamic Type, localization, keyboard/pointer where relevant, and compact/regular width behavior in the initial design.
6. Implement with the repository's established SwiftUI/UIKit/AppKit patterns when they are HIG-compatible.
7. Add previews or safe runtime inspection hooks when the repository already supports them.
8. Run the repository's normal build, formatting, and verification flow when code changes are made.

### Audit Existing UI

1. Inspect source code, previews, screenshots, simulator captures, UI hierarchy, and affected routes as available.
2. Use the rubric to classify issues as `blocking`, `warning`, or `note`.
3. Tie each finding to concrete evidence: file path, screen, screenshot, UI state, or visible behavior.
4. Cite the relevant Apple official page when the finding depends on a specific HIG rule or platform convention.
5. Distinguish HIG issues from product choices, app-specific design language, implementation bugs, and tool limitations.
6. Do not claim full coverage unless the inspected screens, states, platforms, and device classes support that claim.

### Fix HIG Issues

1. Start from the highest-impact HIG issue that is safe to correct within scope.
2. Prefer replacing custom or inconsistent UI with native components and standard platform behavior.
3. Keep fixes minimal and product-preserving: improve alignment without broad redesign unless the user asks for it.
4. Preserve data flow, accessibility identifiers, localization keys, tests, and public APIs unless a HIG fix requires a deliberate change.
5. Verify the corrected UI through build, previews, screenshots, simulator inspection, or the repository's standard verification gate, depending on risk and available tooling.

## Rubric Summary

Use the detailed rubric in `references/rubric.md`. At minimum, check:

- platform fit and device adaptation
- navigation and information architecture
- native components, controls, and presentation
- visual hierarchy, layout, spacing, and safe areas
- typography, Dynamic Type, semantic color, and contrast
- accessibility labels, hit targets, gesture alternatives, and VoiceOver behavior
- loading, empty, error, destructive, and confirmation states
- localization and official Apple feature terminology
- Liquid Glass or other current Apple visual systems when relevant

## Guardrails

- Do not invent HIG rules. If Apple guidance is ambiguous, say so and present the tradeoff.
- Do not copy long HIG text into the response or repository. Summarize and cite official Apple pages.
- Do not use non-Apple design blogs as primary authority when Apple official guidance exists.
- Do not force a generic Apple look that erases the app's product identity when HIG allows multiple valid expressions.
- Do not treat visual polish as HIG compliance if accessibility, Dynamic Type, layout adaptation, or navigation semantics are weak.
- Do not silently skip platform variants such as iPad, macOS, watchOS, widgets, or App Intents when the changed surface supports them.

## Output Contract

For creation or fixes, return concise Japanese with:

1. `HIG方針`
2. `変更内容`
3. `検証`
4. `残る判断`

For audits or reviews, lead with findings:

1. `blocking`
2. `warnings`
3. `notes`
4. `coverage`
5. `recommended fixes`

When Apple official guidance materially affects a decision, include the source URL.
