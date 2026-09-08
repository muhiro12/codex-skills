# Curated Codex Skills

This repository contains curated Codex skills for development and personal workflows.
System-managed skills, runtime assets, generated artifacts, and private local data are excluded.

## Included Skills

- `app-store-release-notes-writer`: Generates App Store Connect-ready release notes across supported locales from a git range and project localization settings.
- `apple-hig-ui-guardian`: Audits and repairs Apple-platform UI work against Apple's Human Interface Guidelines.
- `apple-ios-dev-flow`: Uses current-repository evidence first, Apple guidance second, and an optional local sibling reference repository as a fallback for Apple-platform implementation work.
- `apple-repo-verify-bootstrapper`: Derives an initial Apple verification contract from actual Xcode and package surfaces, retaining scripts only for uncovered checks.
- `apple-sample-code-advisor`: Finds and applies Apple Developer sample code as official implementation guidance for Apple-platform work.
- `ci-verify-and-summarize`: Runs the repository's standard verify flow, reviews only the newest CI run artifacts, and summarizes push readiness from the current diff.
- `context-capture`: On explicit `$context-capture` invocation, saves user-provided material as near-raw local Markdown evidence.
- `context-consult`: On explicit `$context-consult` invocation, searches local context archives and returns cited context packs.
- `mh-swift-style`: Applies this repository owner's established Swift formatting and code-organization preferences to Apple-platform code.
- `organize-photos-for-line-sharing`: Safely builds outbound LINE-sharing albums from self-captured originals, preserves their dates, actively corrects their orientation, normalizes dates only for confirmed LINE downloads, rotates LINE media conservatively, never deletes media, and produces a visual HTML report.
- `product-overview-syncer`: Conservatively syncs an existing product or architecture overview Markdown document with the current codebase reality.
- `release-risk-analyzer`: Assesses whether the range from the latest release tag to `HEAD` contains release-blocking changes on durable-risk surfaces.
- `repo-agent-contract-maintainer`: Maintains concise, clone-ready repository `AGENTS.md` contracts and routes longer guidance to the correct durable layer.
- `repo-and-app-footprint-inspector`: Diagnoses repository and app size, concentration, maintenance burden, and structural hotspots without modifying source code.
- `repo-consistency-refiner`: Audits one repository at a time for structural, architectural, workflow, and documentation drift, then proposes low-risk refinements.
- `repo-momentum-driver`: Continues the agreed repository objective or chooses bounded next work backed by current evidence.
- `respect-incomes-architecture`: Resolves a local Incomes checkout and uses it as a read-only architectural reference for repository and tooling alignment.
- `skills-batch-auditor`: Reviews custom skills against current usage and tools, fixes deterministic drift, and applies portfolio changes when authorized.
- `string-catalog-maintainer`: Audits and repairs Xcode string catalogs such as `Localizable.xcstrings` and related localization assets.
- `swift-code-guardian`: Audits and repairs Swift code against official Swift guidance, API design conventions, and concurrency safety expectations.
- `swiftdata-schema-auditor`: Reviews SwiftData schema definitions and explains entities, relationships, persistence, and migration risk.
- `sync-xcode-skills`: Exports Xcode-provided agent Skills and installs Codex-compatible local copies.
- `track-developer-principles`: Maintains a personal cross-repository principle system; the private record files themselves are intentionally not tracked here.
- `track-personal-principles`: Maintains private weighted personal operating principles while keeping the record files out of git.
- `verify-contract-maintainer`: Maintains a minimal verification contract across Xcode-native evidence capabilities and retained repository-rule scripts.
- `xcode-preview-auditor`: Audits SwiftUI `#Preview` coverage and capture results screen-by-screen, with audit-first reporting.
- `xcode-ui-smoke-auditor`: Runs safe Simulator UI smoke audits for Apple-platform apps and reports visual or interaction risks without auto-fixing by default.

## Layout

Each skill lives in its own directory and typically includes:

- `SKILL.md`: the main instructions
- `agents/openai.yaml`: skill-facing metadata
- optional `scripts/` or `references/` directories when the skill needs helpers or supporting guidance
- optional ignored data directories such as `records/`, `archives/`, or `cache/` when a skill owns mutable local state

Local data migrations are explicit maintenance operations. Run
`python3 scripts/migrate_skill_data.py --list` to inspect available migrations
when a known legacy layout needs updating. Select the relevant scope, review the
dry run, and use `--apply` only for an authorized migration. The helper copies
missing targets, preserves conflicts, and stops the version chain on conflict;
it is not a required step after every pull or on a fresh installation.

## Verification

The repository requires Python 3.9 or later and a Bash 3.2-compatible shell.
Run the clone-ready verification entrypoint from the repository root:

```sh
bash scripts/verify_repository.sh
```

The command uses the Git index as its inventory. It validates every tracked
skill's frontmatter and `agents/openai.yaml`, checks the Included Skills list,
compiles tracked Python, syntax-checks tracked shell files, runs tracked Python
and shell tests, and checks both staged and unstaged diffs for whitespace errors. Ignored
runtime skills, generated Xcode skills, private records, archives, and caches
are not traversed.

## Intentionally Untracked

- `.system/`, `codex-primary-runtime/`, and `ci_scripts/` are not part of this repository because they are system/runtime/local-workflow managed rather than portable custom skill content.
- `track-developer-principles/records/` and `track-personal-principles/records/` are kept out of git because they hold private local principle history.
- `context-capture/archives/` is kept out of git because it holds private or work-local evidence captures.
- `apple-sample-code-advisor/cache/` is kept out of git because cached Apple sample projects are disposable local evidence.
- `organize-photos-for-line-sharing/work/` is kept out of git because inventories, media exports, contact sheets, and run reports are private task artifacts.
- `xcode-skill-*` and `sync-xcode-skills/state/` are generated locally by `sync-xcode-skills`; never edit or commit them directly.
