---
name: swift-code-guardian
description: Create, review, or fix Swift APIs, concurrency, ownership, type modeling, and package boundaries using official Swift guidance. Focus on substantive correctness and clarity decisions.
---

# Swift Code Guardian

Use official Swift documentation and API Design Guidelines as the platform baseline for
Swift APIs, concurrency, ownership, type modeling, and package boundaries. Preserve the user's product intent and stronger
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

Design APIs at their call sites, keep public surfaces deliberate, and preserve
source compatibility unless changing it is part of the task. Respect actor
isolation, Sendable boundaries, task lifetime/cancellation, and mutable-state
ownership. Address diagnostics without hiding unsafe behavior behind unchecked
annotations. Check the actual toolchain before adopting version-specific idioms.

Prefer standard library constructs and clear types over unnecessary helper
layers. Documentation should clarify behavior, preconditions, errors, or
concurrency, not restate the declaration. Apply `mh-swift-style` when local source
style matters, subject to language correctness and repository rules.

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
