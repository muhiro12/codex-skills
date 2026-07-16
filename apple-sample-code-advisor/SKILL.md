---
name: apple-sample-code-advisor
description: Find, cache, inspect, and apply Apple Developer sample code projects as strong official implementation guidance for Apple-platform architecture, framework adoption, SwiftUI app structure, SwiftData, App Intents, StoreKit, WidgetKit, AVFoundation, Liquid Glass, concurrency, cross-surface data flow, and modern iOS/iPadOS/macOS app patterns. Use when a related Apple sample may provide concrete implementation shape for an Apple-platform task, especially after matching Xcode-provided skills and before relying only on prose documentation, HIG/Swift rule checks, current repository convention, or sibling repositories. Use when Codex is adopting or revising Apple frameworks, app shell/lifecycle, target boundaries, entitlements, multi-surface features, data/model wiring, SwiftUI app composition, App Intents, widgets, StoreKit, AVFoundation, SwiftData, or cached Apple sample code itself.
---

# Apple Sample Code Advisor

## Overview

Use this skill when Apple sample projects can clarify the implementation shape. Treat Apple sample code as strong official implementation evidence, especially for app structure, framework integration, target layout, entitlements, data flow, and cross-surface examples.

When a cached or current Apple sample appears directly related to the implementation area, use it early as concrete code evidence after matching Xcode-provided skill guidance. Do not wait until prose documentation, HIG/Swift rule checks, or current repository conventions leave the approach ambiguous. Prefer a focused sample inspection over broad web research when the sample shows the same framework or system surface in a working project.

Sample code is still sample code, not a specification. Prefer HIG for user-interface requirements, Swift.org and Swift documentation for language/API/concurrency requirements, and Apple framework documentation for API contracts. Use samples to understand how Apple composes those pieces in a working project.

## Xcode Skill Catalog

When `sync-xcode-skills/state/catalog.md` exists under the active Codex skills root, scan it for task-relevant Xcode-provided `xcode-skill-*` guidance before applying this skill's local sample-code heuristics. Do not hardcode individual Xcode-provided skill names. If the catalog is missing or no listed skill matches, continue with this skill normally.

## Cache Policy

Use a skill-owned, repo-external cache by default:

`<active-skills-root>/apple-sample-code-advisor/cache`

Resolve `<active-skills-root>` from the parent directory of this loaded skill. If only the Codex home is available, use `${CODEX_HOME:-$HOME/.codex}/skills`. Prefer the loaded skill path when available so custom Codex homes, worktrees, and alternate installations do not accidentally read or mutate the default home cache.

Never place downloaded sample projects inside the target product repository unless the user explicitly asks. Keep cached samples disposable and refreshable; they are local evidence, not vendored source.
Treat legacy `~/.codex/cache/apple-sample-code` contents as a migration source only. Copy or move them into this skill's `cache/` before relying on them, and do not delete the legacy cache unless the user explicitly asks.

Migration check:

- After this skill is installed or updated from GitHub, run `python3 scripts/migrate_skill_data.py --only apple-sample-cache` from the skills root when `cache/` is missing or empty.
- If the dry-run reports legacy cached samples, run `python3 scripts/migrate_skill_data.py --only apple-sample-cache --apply` before relying on the cache, unless the reported copy size is large enough to require confirmation.
- The migration copies only missing targets and never overwrites conflicting files. Resolve conflicts manually before trusting the migrated sample metadata.
- During an applied cache migration, transactionally rebase manifest and per-sample metadata `cache_path` values to the active skill cache root; never retain a legacy absolute cache path in migrated metadata.

Do not pre-seed samples just because this skill exists. Fetch lazily when a concrete implementation, review, or architecture decision has a plausibly related Apple sample, or when the user explicitly asks to cache or refresh a named sample.

Use `scripts/sample_cache.py` for cache operations:

- `list`: show cached samples and staleness.
- `inspect <slug>`: show metadata and a shallow project tree.
- `fetch-archive`: download and extract a known archive URL.
- `add-local`: register an already downloaded archive or directory.
- `mark-checked`: record a completed official-source check without downloading unchanged source again.
- `refresh-plan`: identify stale samples that should be rechecked.
- `prune`: dry-run cache cleanup by default; require `--apply` to delete.

Each cached sample lives under `samples/<slug>/source` with metadata recorded in both the cache manifest and `samples/<slug>/metadata.json`. `fetched_at` records when source was installed, while `checked_at` records the latest successful comparison with the official source. Existing metadata without `checked_at` remains valid and falls back to `fetched_at`.

Cache mutations follow these safety rules:

- Treat local paths as caller-owned input and never delete them. Remove only temporary downloads created by the cache script.
- Validate and fully stage source before replacement. Reject unsafe ZIP members, keep the previous entry until staging succeeds, and roll it back if the manifest update fails.
- Write manifest and per-sample metadata atomically, and serialize mutating operations with the cache lock.
- Fail closed when `fetched_at` is missing or invalid. `refresh-plan` also fails closed when a present `checked_at` is invalid. `prune --apply` continues to use `fetched_at`, must not delete any entry when that value is invalid, and must verify each requested removal.

Before fetching or replacing a cached sample, state the sample title, Apple documentation URL, source/download URL, cache path, and whether this is a refresh. A task may proceed with an on-demand fetch when the sample is clearly needed, but do not silently fetch large archives or replace cached source.

## Required References

Read `references/rubric.md` before applying a sample to a repository decision.

Read `references/source-map.md` when finding samples, resolving frequent samples, or deciding whether a cached sample may be stale.

## Workflow Decision Tree

### Find Candidate Samples

1. Start from the user's framework, feature, platform, or architecture question.
2. Search Apple Developer Documentation and the Sample Code Library first.
3. Prefer recent samples tied to current SDKs, WWDC sessions, or current documentation pages.
4. Check the local cache and `references/source-map.md` for frequent samples such as Wishlist and Landmarks before treating prose documentation as enough.
5. Report candidate samples with what each can and cannot teach.

### Inspect Cached Samples

1. Run `scripts/sample_cache.py list` when a related sample may exist.
2. If cached, run `scripts/sample_cache.py inspect <slug>` and read only the relevant files first: app entry point, scene/root view, model/data source, package manifest, entitlements, framework-specific files, tests, and sample fixtures.
3. If the cached copy is stale or predates the relevant SDK/API, check the Apple page before relying on it. If the official source is unchanged, run `scripts/sample_cache.py mark-checked <slug>` to record the completed check without replacing source.
4. Summarize project-level patterns separately from sample-specific shortcuts.

### Fetch Or Refresh Samples

1. Resolve the official Apple documentation page and download/archive URL.
2. Use the cache script to fetch into `cache/samples/<slug>/source` under the loaded skill directory.
3. Store metadata: title, Apple URL, source URL, fetched time, checked time, size, frameworks, and notes.
4. If an existing cache entry would be replaced, require explicit user approval or an explicit user request.
5. After fetching, inspect the shallow tree and key files before using the sample as evidence.

### Lazy Fetch Policy

- Fetch only when a task has a plausibly related Apple sample whose source would materially clarify implementation, or the user asks for a specific sample to be cached.
- Prefer using an already cached current sample when it is fresh enough for the task.
- If the sample is missing and related sample source would materially clarify the implementation, resolve the Apple page and perform an on-demand fetch before making strong architecture claims.
- If a sample is large, stale, or would replace an existing cache entry, pause for explicit approval unless the user already requested that fetch or refresh.

### Apply Sample Guidance

1. Compare the sample's architecture to the current repository's actual constraints.
2. Extract patterns, not code: target boundaries, data flow, framework setup, lifecycle handling, state ownership, file grouping, entitlement/capability wiring, and verification expectations.
3. Keep product-specific models, sample fixtures, placeholder data, and demo shortcuts out of the target repository unless they express a reusable architecture decision.
4. Combine sample evidence with `$apple-hig-ui-guardian` for UI choices and `$swift-code-guardian` for Swift API/concurrency/package choices.
5. Explain whether the recommendation follows the sample directly, adapts it, or deliberately diverges from it.

## Evidence Strength

Use this order when evidence conflicts:

1. Explicit user/product constraints and hard repository constraints.
2. HIG, Swift official guidance, and Apple framework API documentation.
3. Current Apple sample code projects.
4. Current repository conventions.
5. Local sibling repositories as read-only fallback examples.

Apple samples should usually beat local sibling repositories for framework adoption and modern app structure, but they should not override HIG, Swift language rules, API contracts, or product-specific requirements.

## Guardrails

- Do not copy sample code wholesale into a product repository.
- Do not treat old tutorials or samples as current without checking the Apple page.
- Do not rely on sample fixtures, fake services, simplified error handling, or demo data as production architecture.
- Do not scan every file in a large sample when a focused file set answers the question.
- Do not recursively scan generated directories: `.build`, `build`, `DerivedData`, `.git`, `.swiftpm`, `Pods`, or `Carthage`.
- Do not delete cached samples unless the user asked or `prune --apply` is explicitly chosen.
- Do not claim a sample proves a universal rule; say what project context it demonstrates.

## Output Contract

Return concise Japanese with:

1. `参照したサンプル`
2. `Appleサンプルから見た判断`
3. `現在のrepoへの適用`
4. `検証`
5. `残る判断`

For cache operations, include the cache path, command used, sample slug, fetched/refreshed date, and whether any cleanup was dry-run or applied.
