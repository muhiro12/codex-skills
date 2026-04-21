---
name: string-catalog-maintainer
description: Audit, clean up, and repair Xcode string catalogs (.xcstrings) across one or more Apple app targets. Use when Codex needs to remove stale localization keys, identify missing locale coverage, seed missing locale entries, or update translations in Localizable.xcstrings, AppIntents.xcstrings, AppShortcuts.xcstrings, or other string catalog files.
---

# String Catalog Maintainer

## Overview

Use this skill to keep `.xcstrings` catalogs aligned with the current source tree.
Default explanation language is concise, polite Japanese.

## Trigger Conditions

Use this skill when the user asks to:

- remove stale localization keys
- fill missing locale entries
- audit locale coverage across multiple catalogs
- update or fix translations in `.xcstrings` files

## Workflow

1. Discover catalogs and expected locales.
- Find catalogs with `rg --files <repo> | rg '\.xcstrings$'`.
- Derive locale expectations from target behavior, sibling catalogs, or explicit user requirements.

2. Audit before mutation.
- Run `python3 scripts/audit_xcstrings.py --project-root <repo>`.
- Use `--required-locales` when locale policy is explicit.
- Use `--format json` when machine-readable analysis is needed.

3. Protect against dynamic-key false positives.
- Treat unused keys as candidates only.
- Validate call sites for dynamic key construction before deletion.

4. Apply candidate -> verification -> delete flow.
- Candidate: identify deletable keys with zero static references.
- Verification: inspect affected call sites and large diff areas.
- Delete: run `--prune-unused --apply` only after verification.

5. Seed missing locales safely.
- Run `--seed-missing-locales --apply` with required locale list.
- Keep uncertain translations with `state: new` and explicit review-needed labeling.

6. Run repository-standard verification.
- Read `AGENTS.md` and follow its Build and Test entrypoint when defined.
- Re-run catalog audit and confirm intended count changes.

## Safety / Guardrails

- Keep diffs minimal; do not rewrite unrelated tables.
- Preserve placeholders, plural structure, punctuation, and `shouldTranslate: false` semantics.
- Never auto-prune keys known to depend on generated/runtime composition without source verification.
- Avoid scanning generated directories recursively unless explicitly required.

## Response Contract

Return a concise Japanese report with:

1. `対象カタログ`
2. `実施内容`
3. `削除候補の検証結果`
4. `ロケール不足と補完結果`
5. `検証結果` (including AGENTS.md entrypoint usage when applicable)

## Verification

- Re-run `audit_xcstrings.py` after edits.
- Confirm missing-locale and unused-candidate counts changed as intended.
- Confirm no unresolved placeholder handling errors were introduced.

## Script

Use `scripts/audit_xcstrings.py` to audit catalogs, seed missing locales, and prune unused candidates.

```bash
python3 scripts/audit_xcstrings.py   --project-root /path/to/repo   --required-locales en,ja,es,fr,zh-Hans   --format markdown
```

Useful options:

- `--catalog`: Limit the run to specific catalogs.
- `--required-locales`: Override expected locale set for selected catalogs.
- `--seed-missing-locales`: Create missing locale entries from source-locale structure.
- `--prune-unused`: Remove keys with zero static literal matches.
- `--apply`: Write changes in place (without this flag, mutations are dry run).
- `--format json`: Emit machine-readable output.
