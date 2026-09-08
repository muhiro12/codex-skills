---
name: apple-hig-ui-guardian
description: Create, review, or fix Apple UI decisions about navigation, native controls, accessibility, and platform adaptation using current HIG. Keep product intent and review only relevant surfaces.
---

# Apple HIG UI Guardian

Use Apple HIG and official platform documentation as the platform baseline for
navigation, controls, layout, accessibility, and platform adaptation. Preserve the user's product intent and stronger
repository evidence; explain an intentional departure when it matters. Return
concise Japanese, with code and repository artifacts in their required language.

## Scope the Guidance

Start with affected files, call sites, tests, diagnostics, and available runtime
or visual evidence. Read the relevant portions of
[references/rubric.md](references/rubric.md); a focused change does not require
reviewing every rubric category. For an explicit broad audit, use the full rubric.

Prefer matching Xcode-provided guidance from the active skill inventory or its
generated catalog when available. Reuse task-relevant guidance already read.
Use [references/source-map.md](references/source-map.md) to find official pages
when a specific rule or version-sensitive behavior needs verification. Do not
invent rules, rely on outdated samples, or repeatedly fetch the same source.

## Apply and Review

Prefer native containers, controls, system typography, semantic colors, and
adaptive layouts. Check Dynamic Type, localization, VoiceOver semantics, hit
targets, and supported widths when the affected UI makes them relevant. Custom
UI is valid when it serves a concrete product need within platform constraints.
Do not replace product identity with a generic appearance.

For visual audits, inspect actual screenshots or rendered previews. Source and
UI hierarchy support diagnosis but do not prove visible quality. Separate app UI,
shared design-system, fixture/setup, and tool failures. A shared-looking issue
needs evidence before changing a package used by other apps.

Distinguish confirmed bugs, official-guidance conflicts, local style choices,
and uncertainty. Tie findings to concrete files, diagnostics, or inspected UI.
Do not manufacture findings from a checklist or widen a local fix into an
unrequested redesign or architecture migration.

For an audit-only request, report findings without changing code. For creation or
fixes, complete the authorized change, update affected call sites and meaningful
behavioral checks, and use the repository's verification contract. Separate
static, build/test, and runtime/visual evidence. A passing compiler alone does not
prove every quality claim, and missing runtime evidence is not itself a code bug.

## Report

Lead with important findings or the implemented result. Give the evidence,
completed checks, and material limitations; skip empty report sections. Cite the
relevant official URL when a specific official rule decides the finding.
