---
name: swift-code-guardian
description: Create, audit, and fix Swift code so it follows official Swift documentation, Swift API Design Guidelines, Swift language semantics, Swift 6 concurrency and data-race safety guidance, SwiftPM package conventions, DocC documentation practices, and idiomatic standard-library usage. Use when building, refactoring, reviewing, or repairing Swift source, public APIs, package manifests, async/await or actor code, Sendable boundaries, value/reference type choices, generics, protocols, error handling, testing seams, or Swift package/module boundaries.
---

# Swift Code Guardian

## Overview

Use this skill as an active Swift-language quality gate. Treat official Swift documentation and Swift.org guidance as the first external authority for Swift semantics, API shape, concurrency, packages, and documentation, while still respecting the repository's established conventions when they do not conflict with Swift guidance.

Prefer current Swift official material over memory. Swift language features, concurrency checking, package tools, and recommended idioms evolve, so verify relevant guidance before making or judging decisions that depend on current Swift behavior.

## Source Order

Use this decision order:

1. Explicit user intent, repository architecture, existing tests, diagnostics, and local style.
2. Current official Swift sources: Swift.org documentation, The Swift Programming Language, API Design Guidelines, Swift Package Manager docs, standard library docs, Swift Evolution, and official migration guides.
3. Apple platform documentation when the Swift code depends on Apple frameworks or platform annotations.
4. Existing repository conventions, only when they remain compatible with current Swift guidance.
5. Local sibling repositories as read-only examples, only after official Swift guidance and current-repo evidence are not enough.

If local style conflicts with Swift API design, concurrency safety, or language semantics, identify the conflict and propose a Swift-aligned correction instead of preserving the local pattern by default.

## Required References

Read `references/rubric.md` for every create, audit, or fix task.

Read `references/source-map.md` when choosing which Swift official pages to verify or cite. If a page requires JavaScript, use web search restricted to `swift.org` or `docs.swift.org` and rely on official Swift sources.

## Workflow Decision Tree

### Create Idiomatic Swift

1. Identify the target surface: app code, shared library, public API, package manifest, test helper, concurrency boundary, persistence model, or interop layer.
2. Read the Swift rubric and verify the relevant official Swift source pages before settling the design.
3. Choose value types, reference types, protocols, generics, async boundaries, and error surfaces deliberately.
4. Design APIs at the call site first. Prefer clarity, role-based names, natural argument labels, and small public surfaces.
5. Prefer standard library and Swift-native constructs over ad hoc helper layers unless the helper removes real repetition or expresses domain meaning.
6. Keep concurrency safe by default: isolate mutable shared state, respect actor boundaries, and address `Sendable` requirements intentionally.
7. Add documentation comments for public or reusable declarations when the summary would clarify behavior, complexity, preconditions, errors, or concurrency expectations.
8. Run the repository's normal formatting, build, test, and verification flow when code changes are made.

### Audit Existing Swift

1. Inspect source, call sites, tests, diagnostics, package manifests, and public API use.
2. Use the rubric to classify issues as `blocking`, `warning`, or `note`.
3. Tie each finding to concrete evidence: file path, call site, compiler diagnostic, test gap, package boundary, or public API surface.
4. Cite the relevant official Swift page when the finding depends on language semantics, API design, concurrency safety, package behavior, or migration guidance.
5. Distinguish Swift issues from app architecture choices, platform UI/HIG issues, repository-local style, and unrelated product decisions.

### Fix Swift Issues

1. Start from the highest-impact Swift issue that is safe to correct within scope.
2. Prefer small corrections that improve type safety, API clarity, concurrency safety, package boundaries, or testability without broad rewrites.
3. Preserve behavior, public API compatibility, persistence schema, localization keys, and app-facing semantics unless the fix explicitly requires changing them.
4. When public API changes are necessary, update call sites, docs, and tests together.
5. Verify with the narrowest useful build/test command first, then the repository's standard verification gate when available.

## Rubric Summary

Use the detailed rubric in `references/rubric.md`. At minimum, check:

- API clarity at the call site and Swift API Design Guidelines
- naming, argument labels, mutating/nonmutating pairs, and terminology
- value/reference semantics, ownership, identity, and mutation
- Swift 6 concurrency, actor isolation, `Sendable`, task lifetime, and cancellation
- error handling, optionality, result modeling, and invalid-state prevention
- generics, protocols, existentials, type erasure, and associated types
- standard library, Foundation/Core Libraries, and platform API fit
- SwiftPM targets, package boundaries, access control, and module layering
- DocC/documentation comments, complexity notes, and public API summaries
- source compatibility, migration risk, tests, and verification coverage

## Guardrails

- Do not invent Swift rules. If official guidance is ambiguous, say so and present the tradeoff.
- Do not copy long Swift documentation passages into the response or repository. Summarize and cite official Swift pages.
- Do not use blog posts, Stack Overflow, or package-specific opinions as primary authority when Swift official guidance exists.
- Do not rewrite a stable repository style merely for aesthetic preference; require a concrete Swift clarity, safety, maintainability, or correctness reason.
- Do not treat compiler success as enough when API clarity, concurrency safety, or package boundaries are weak.
- Do not broaden a local Swift fix into a package architecture rewrite unless the user explicitly asks.

## Output Contract

For creation or fixes, return concise Japanese with:

1. `Swift方針`
2. `変更内容`
3. `検証`
4. `残る判断`

For audits or reviews, lead with findings:

1. `blocking`
2. `warnings`
3. `notes`
4. `coverage`
5. `recommended fixes`

When official Swift guidance materially affects a decision, include the source URL.
