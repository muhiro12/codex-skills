# Curated Codex Skills

This repository contains a curated public-safe subset of custom Codex skills.
It intentionally excludes private notes, system-managed skills, and runtime/vendor-managed assets from the original local workspace.

## Included Skills

- `match-user-language`: Matches Codex user-facing replies to the user's conversation language without translating code or repository artifacts by default.
- `product-overview-syncer`: Conservatively syncs an existing product or architecture overview Markdown document with the current codebase reality.
- `repo-and-app-footprint-inspector`: Diagnoses repository and app size, concentration, maintenance burden, and structural hotspots without modifying source code.
- `string-catalog-maintainer`: Audits and repairs Xcode string catalogs such as `Localizable.xcstrings` and related localization assets.
- `swiftdata-schema-auditor`: Reviews SwiftData schema definitions and explains entities, relationships, persistence, and migration risk.
- `verify-contract-maintainer`: Bootstraps and normalizes a minimal `ci_scripts`-based verify contract so repository verification entrypoints stay consistent.
- `xcode-preview-auditor`: Audits SwiftUI `#Preview` coverage and capture results screen-by-screen, with audit-first reporting.

## Layout

Each skill lives in its own directory and typically includes:

- `SKILL.md`: the main instructions
- `agents/openai.yaml`: skill-facing metadata
- optional `scripts/` or `references/` directories when the skill needs helpers or supporting guidance
