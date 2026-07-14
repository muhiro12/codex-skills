# Curated Codex Skills

This repository contains custom Codex skills from my local development environment.
It intentionally excludes system-managed skills, runtime/vendor-managed assets, and a small amount of private local state.

## Included Skills

- `app-store-release-notes-writer`: Generates App Store Connect-ready release notes across supported locales from a git range and project localization settings.
- `apple-hig-ui-guardian`: Audits and repairs Apple-platform UI work against Apple's Human Interface Guidelines.
- `apple-ios-dev-flow`: Uses current-repository evidence first, Apple guidance second, and an optional local sibling reference repository as a fallback for Apple-platform implementation work.
- `apple-repo-verify-bootstrapper`: Establishes a predictable Apple repository verification flow around `ci_scripts`, `AGENTS.md`, and repo-specific build/test/lint entrypoints.
- `apple-sample-code-advisor`: Finds and applies Apple Developer sample code as official implementation guidance for Apple-platform work.
- `ci-verify-and-summarize`: Runs the repository's standard verify flow, reviews only the newest CI run artifacts, and summarizes push readiness from the current diff.
- `context-capture`: On explicit `$context-capture` invocation, saves user-provided material as near-raw local Markdown evidence.
- `context-consult`: On explicit `$context-consult` invocation, searches local context archives and returns cited context packs.
- `match-user-language`: Matches Codex user-facing replies to the user's conversation language without translating code or repository artifacts by default.
- `mh-swift-style`: Applies this repository owner's established Swift formatting and code-organization preferences to Apple-platform code.
- `product-overview-syncer`: Conservatively syncs an existing product or architecture overview Markdown document with the current codebase reality.
- `release-risk-analyzer`: Assesses whether the range from the latest release tag to `HEAD` contains release-blocking changes on durable-risk surfaces.
- `repo-agent-contract-maintainer`: Maintains concise, clone-ready repository `AGENTS.md` contracts and routes longer guidance to the correct durable layer.
- `repo-and-app-footprint-inspector`: Diagnoses repository and app size, concentration, maintenance burden, and structural hotspots without modifying source code.
- `repo-consistency-refiner`: Audits one repository at a time for structural, architectural, workflow, and documentation drift, then proposes low-risk refinements.
- `repo-momentum-driver`: Turns vague "keep going" requests into exactly one bounded next task backed by repository evidence.
- `respect-incomes-architecture`: Resolves a local Incomes checkout and uses it as a read-only architectural reference for repository and tooling alignment.
- `skills-batch-auditor`: Audits multiple custom skills together, scores drift and maintenance burden, and proposes bounded refresh work.
- `string-catalog-maintainer`: Audits and repairs Xcode string catalogs such as `Localizable.xcstrings` and related localization assets.
- `swift-code-guardian`: Audits and repairs Swift code against official Swift guidance, API design conventions, and concurrency safety expectations.
- `swiftdata-schema-auditor`: Reviews SwiftData schema definitions and explains entities, relationships, persistence, and migration risk.
- `sync-xcode-skills`: Exports Xcode-provided agent Skills and installs Codex-compatible local copies.
- `track-developer-principles`: Maintains a personal cross-repository principle system; the private record files themselves are intentionally not tracked here.
- `track-personal-principles`: Maintains private weighted personal operating principles while keeping the record files out of git.
- `verify-contract-maintainer`: Maintains a minimal verification contract across native Xcode MCP evidence and retained repository-rule scripts.
- `xcode-preview-auditor`: Audits SwiftUI `#Preview` coverage and capture results screen-by-screen, with audit-first reporting.
- `xcode-ui-smoke-auditor`: Runs safe Simulator UI smoke audits for Apple-platform apps and reports visual or interaction risks without auto-fixing by default.

## Layout

Each skill lives in its own directory and typically includes:

- `SKILL.md`: the main instructions
- `agents/openai.yaml`: skill-facing metadata
- optional `scripts/` or `references/` directories when the skill needs helpers or supporting guidance
- optional ignored data directories such as `records/`, `archives/`, or `cache/` when a skill owns mutable local state

After pulling updates on another machine, run `python3 scripts/migrate_skill_data.py`
from this repository to check whether legacy ignored local data should be copied
into the new skill-owned data directories. The script is dry-run by default and
uses `--apply` only to copy missing targets without overwriting conflicts.
It is also the stable entrypoint for future local data migrations: add new
migration ids there instead of creating separate one-off migration commands.
Run `python3 scripts/migrate_skill_data.py --list` to see registered migrations.

Local data layout migrations are a linear version chain. The current layout is
reported by `--list`, and running the script without `--migration` executes every
registered migration in order. Each migration should be idempotent and should
detect its own source and target paths, so a v1 machine can move through later
versions by running the same entrypoint, while an already migrated machine sees
earlier steps as `same`, `missing`, or no-op rather than corruption.
The script does not mark migrations as applied; filesystem state is the source
of truth. If a migration reports conflicts, later migrations are not run until
the conflict is resolved.

General helper scripts can still live under `scripts/` when they are not data
migrations, but local data path or schema changes should go through the migration
entrypoint.

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
- `xcode-skill-*` and `sync-xcode-skills/state/` are generated locally by `sync-xcode-skills`; never edit or commit them directly.
