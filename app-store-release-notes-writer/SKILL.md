---
name: app-store-release-notes-writer
description: Write iOS App Store "What's New" text for each supported app language from git history and localization settings. Use when asked to draft, update, summarize, localize, or style release notes for App Store Connect, especially for "What's New in This Version" text.
---

# App Store Release Notes Writer

## Overview

Use this skill to generate App Store Connect-ready release notes from git history and localization settings.
Agent-side explanation should be concise, polite Japanese by default, while release-note bodies must be written in each target locale language.

## Trigger Conditions

Use this skill when the user asks to:

- draft or update `What's New in This Version`
- localize release notes across supported locales
- summarize user-visible changes for App Store Connect

## Workflow

1. Confirm release scope.
- Resolve exact git range (`<previous-tag>..<current-tag>` or equivalent).
- Confirm target app version and release date.

2. Resolve locale coverage.
- Read `Localizable.xcstrings` and `*.xcodeproj/project.pbxproj`.
- Exclude `Base` from output locales.
- Preserve stable locale order for reproducible outputs.
- Emit locale blocks in App Store Connect display order for the supported locales shown in the UI: `en`, `es`, `fr`, `zh-Hans`, `ja`.
- Apply the same ordering to regional variants such as `en-US`, `es-ES`, `fr-FR`, `zh-CN`, and `ja-JP`.
- Do not move the source locale to the front if that would break the App Store Connect display order.

3. Generate source draft.
- Run `scripts/generate_release_notes.py` and extract user-visible changes.
- Keep 2 to 5 outcome-focused bullets.

4. Apply App Store style.
- Use `--style app-store` for intro + bullets (+ optional outro).
- Use `--include-outro` only when it improves readability.
- Use `--exclude-subject-regex` to filter noisy commits.

5. Localize per locale.
- Emit one locale block per supported App Store language.
- For uncertain translations, keep explicit placeholders and mark them as review-needed.

6. Final quality checks.
- Validate version/date/range consistency.
- Ensure text emphasizes user benefit and behavior changes.
- Ensure output is directly pasteable to App Store Connect.

## Safety / Guardrails

- Never fabricate user-facing changes that are not grounded in commits.
- Avoid implementation-detail-heavy bullets.
- Keep locale ordering stable and deterministic.
- Match the emitted locale order to App Store Connect display order instead of source-locale-first ordering.
- Preserve placeholders and formatting tokens exactly.

## Response Contract

Return a concise Japanese summary plus locale blocks:

1. `要約` (what changed, source range)
2. `検証` (range/locales/style checks)
3. `各ロケール本文` (paste-ready)
4. `要確認翻訳` (only when placeholders remain)

## Verification

- Confirm all target locales are present exactly once.
- Confirm locale order matches App Store Connect display order for supported locales: `en`, `es`, `fr`, `zh-Hans`, `ja`.
- Confirm unresolved translations are explicitly labeled.
- Confirm generated blocks are plain text and App Store Connect ready.

## Draft Script

Use `scripts/generate_release_notes.py` to create an App Store-ready draft and locale blocks.

```bash
python3 scripts/generate_release_notes.py   --repo /path/to/repository   --from-ref v1.4.0   --to-ref v1.5.0   --app-name ExampleApp   --version 1.5.0   --xcstrings /path/to/App/Resources/Localizable.xcstrings   --project /path/to/App.xcodeproj   --style app-store   --include-outro   --output /tmp/whats-new.md   --output-dir /tmp/whats-new-locales
```

Useful options:

- `--max-items`: Set max bullets per locale.
- `--locales`: Override detected locales (`en,ja,es,fr,zh-Hans`) while still emitting in App Store Connect display order.
- `--source-locale`: Force source locale.
- `--copy-source-to-all-locales`: Fill non-source locales with source text.
- `--translations-json`: Inject finalized localized intro/items/outro.
- `--exclude-subject-regex`: Exclude noisy commit subjects.

## References

- Read `references/release-notes-style.md` for App Store writing rules.
- Read `references/release-notes-template.md` for output structure.
