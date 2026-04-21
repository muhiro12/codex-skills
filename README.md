# Curated Codex Skills

This repository contains custom Codex skills from my local development environment.
It intentionally excludes system-managed skills, runtime/vendor-managed assets, and a small amount of private local state.

## Included Skills

- `app-store-release-notes-writer`: Generates App Store Connect-ready release notes across supported locales from a git range and project localization settings.
- `apple-ios-dev-flow`: Uses current-repository evidence first, Apple guidance second, and an optional local sibling reference repository as a fallback for Apple-platform implementation work.
- `apple-repo-verify-bootstrapper`: Establishes a predictable Apple repository verification flow around `ci_scripts`, `AGENTS.md`, and repo-specific build/test/lint entrypoints.
- `ci-verify-and-summarize`: Runs the repository's standard verify flow, reviews only the newest CI run artifacts, and summarizes push readiness from the current diff.
- `match-user-language`: Matches Codex user-facing replies to the user's conversation language without translating code or repository artifacts by default.
- `product-overview-syncer`: Conservatively syncs an existing product or architecture overview Markdown document with the current codebase reality.
- `release-risk-analyzer`: Assesses whether the range from the latest release tag to `HEAD` contains release-blocking changes on durable-risk surfaces.
- `repo-and-app-footprint-inspector`: Diagnoses repository and app size, concentration, maintenance burden, and structural hotspots without modifying source code.
- `repo-consistency-refiner`: Audits one repository at a time for structural, architectural, workflow, and documentation drift, then proposes low-risk refinements.
- `repo-momentum-driver`: Turns vague "keep going" requests into exactly one bounded next task backed by repository evidence.
- `respect-incomes-architecture`: Uses a sibling `../Incomes` checkout as a read-only architectural reference for repository and tooling alignment.
- `skills-batch-auditor`: Audits multiple custom skills together, scores drift and maintenance burden, and proposes bounded refresh work.
- `string-catalog-maintainer`: Audits and repairs Xcode string catalogs such as `Localizable.xcstrings` and related localization assets.
- `swiftdata-schema-auditor`: Reviews SwiftData schema definitions and explains entities, relationships, persistence, and migration risk.
- `track-developer-principles`: Maintains a personal cross-repository principle system; the private record files themselves are intentionally not tracked here.
- `verify-contract-maintainer`: Bootstraps and normalizes a minimal `ci_scripts`-based verify contract so repository verification entrypoints stay consistent.
- `xcode-preview-auditor`: Audits SwiftUI `#Preview` coverage and capture results screen-by-screen, with audit-first reporting.

## Layout

Each skill lives in its own directory and typically includes:

- `SKILL.md`: the main instructions
- `agents/openai.yaml`: skill-facing metadata
- optional `scripts/` or `references/` directories when the skill needs helpers or supporting guidance

## Intentionally Untracked

- `.system/` and `codex-primary-runtime/` are not part of this repository because they are system/runtime-managed rather than my own custom skills.
- `track-developer-principles/references/current-principles.md` and `track-developer-principles/references/evolution-log.md` are kept out of git because they hold private local principle history.
