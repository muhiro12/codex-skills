---
name: string-catalog-maintainer
description: Audit, clean up, and repair Xcode string catalogs (.xcstrings) across one or more Apple app targets. Use this skill when you need to remove stale localization keys, identify missing locale coverage, extract translation tasks, apply reviewed translation patches, seed missing locale entries, or update translations in Localizable.xcstrings, AppIntents.xcstrings, AppShortcuts.xcstrings, or other string catalog files.
---

# String Catalog Maintainer

## Overview

Use this skill to keep `.xcstrings` catalogs aligned with the current source tree.
Keep the core instructions in this file portable across agent runtimes where practical; platform-specific metadata can live beside the skill.
Default operating mode is catalog-only maintenance: audit catalogs, extract translation tasks, apply safe reviewed `.xcstrings` fixes during the skill run, and leave source-code fixes for a separate follow-up unless the user explicitly expands scope.
Default explanation language is concise, polite Japanese.

## Trigger Conditions

Use this skill when the user asks to:

- remove stale localization keys
- fill missing locale entries
- extract or apply translation tasks
- audit locale coverage across multiple catalogs
- update or fix translations in `.xcstrings` files

## Workflow

1. Discover catalogs and expected locales.
- Find catalogs with `rg --files <repo> | rg '\.xcstrings$'`.
- Derive locale expectations from target behavior, sibling catalogs, or explicit user requirements. If the user does not provide a policy, rely on the script's project-wide locale inference from sibling catalogs.

2. Audit before mutation.
- Run the bundled script from this skill directory when the repo does not provide its own catalog audit entrypoint:
  `python3 /path/to/string-catalog-maintainer/scripts/audit_xcstrings.py --project-root <repo> --format json`.
- When catalog ownership is target-specific, pass `--source-root` to scope static-reference analysis to the owning target directories instead of the whole repo.
- Use `--required-locales` when locale policy is explicit.
- Inspect `translation_tasks`, `incomplete_keys`, `stale_key_count`, `raw_stale_marker_count`, `stale_unused_candidates`, `stale_strong_referenced_keys`, and `stale_weak_referenced_keys`.

3. Cross-check stale markers.
- Independently run `rg -n '"extractionState"\\s*:\\s*"stale"' <catalogs-or-repo>` when stale cleanup is requested.
- Confirm the raw `rg` count matches each catalog's `raw_stale_marker_count` and that `raw_stale_marker_count == stale_key_count`.
- Stop and investigate before pruning if the counts disagree.

4. Protect against dynamic-key false positives.
- Treat unused keys as candidates only.
- Validate call sites for dynamic key construction before deletion.
- Treat `stale_weak_referenced_keys` as report-only unless the user explicitly asks for deeper source-code investigation.

5. Apply candidate -> verification -> delete flow.
- Default to applying catalog-only fixes within this skill once verification is complete.
- Candidate: identify deletable keys with zero static references.
- Verification: inspect affected call sites and large diff areas.
- Delete: run `--prune-unused --apply` only after verification.
- For `stale` cleanup, prefer `--prune-stale-unused --apply` so only stale keys with zero scoped references are removed.
- If a key is in `stale_strong_referenced_keys` or `stale_weak_referenced_keys`, do not delete it in this skill. Report it as a code-side follow-up, leave source files untouched, and use `--normalize-stale-referenced --apply` only after the separate code fix when the catalog should keep that key.

6. Repair missing or untranslated locales.
- Do not stop after `--seed-missing-locales`; seeding only copies source-locale structure and marks entries as `new`.
- Use `translation_tasks` as the required worklist for missing locales, `state != translated`, empty values, and source-copy translated values.
- Treat source-copy tasks for intentional proper nouns, product names, symbols, and acronyms as review-only and report them as intentionally unchanged when appropriate.
- Create a translation patch JSON with a top-level `translations` list. Each entry must include `catalog`, `key`, `locale`, `path`, and either `value` for `stringUnit` or `values` for `stringSet`.
- Validate first with `--translation-patch <patch.json>` and no `--apply-translations`.
- Apply only after validation passes: `--translation-patch <patch.json> --apply-translations`.
- Preserve placeholders exactly. The script rejects placeholder mismatches such as missing `%lld`, `%1$@`, `%@`, or `${applicationName}`.

7. Run repository-standard verification.
- Read `AGENTS.md` and follow its Build and Test entrypoint when defined.
- Re-run catalog audit and confirm intended count changes.

## Safety / Guardrails

- Keep diffs minimal; do not rewrite unrelated tables.
- Preserve existing JSON whitespace conventions when rewriting catalogs, including indentation style, line ending style, and whether the file ends with a trailing newline.
- Preserve placeholders, plural structure, punctuation, and `shouldTranslate: false` semantics.
- Never auto-prune keys known to depend on generated/runtime composition without source verification.
- Keep source-code fixes out of scope for this skill unless the user explicitly asks to expand beyond catalog maintenance.
- When a `stale` key still has references, report it for later code-side repair instead of changing source files here.
- When a stale key has only weak interpolation-derived references, report it separately; do not normalize or delete it automatically.
- Avoid scanning generated directories recursively unless explicitly required.

## Response Contract

Return a concise Japanese report with:

1. `対象カタログ`
2. `実施内容`
3. `コード側要修正の stale キー`
4. `削除候補の検証結果`
5. `ロケール不足、translation_tasks、翻訳パッチ適用結果`
6. `検証結果` (including AGENTS.md entrypoint usage when applicable)

## Verification

- Re-run `audit_xcstrings.py` after edits.
- Confirm missing-locale, translation-task, and unused-candidate counts changed as intended.
- Confirm `raw_stale_marker_count` matches `stale_key_count`; if not, report the mismatch and do not prune.
- Confirm referenced `stale` keys were reported separately as code-side follow-ups and were not deleted by catalog cleanup.
- Confirm rewritten catalogs did not gain formatting-only diffs such as indentation changes or trailing newline changes unrelated to the intended content edits.
- Confirm no unresolved placeholder handling errors were introduced.

## Script

Use `scripts/audit_xcstrings.py` to audit catalogs, apply safe catalog-local fixes, and separate code-side stale follow-ups from deletable stale entries.

```bash
python3 scripts/audit_xcstrings.py   --project-root /path/to/repo   --required-locales en,ja,es,fr,zh-Hans   --format markdown
```

Useful options:

- `--catalog`: Limit the run to specific catalogs.
- `--source-root`: Limit static-reference analysis to the owning target directories.
- `--required-locales`: Override expected locale set for selected catalogs.
- `--seed-missing-locales`: Create missing locale entries from source-locale structure.
- `--prune-unused`: Remove keys with zero static literal matches.
- `--prune-stale-unused`: Remove only stale keys with zero static literal matches.
- `--normalize-stale-referenced`: Clear stale markers from keys that still have valid static references.
- `--translation-patch <json>`: Validate a Codex-generated translation patch file or inline JSON.
- `--apply-translations`: Apply a validated translation patch and mark patched payloads translated.
- `--apply`: Write changes in place (without this flag, mutations are dry run).
- `--format json`: Emit machine-readable output.
