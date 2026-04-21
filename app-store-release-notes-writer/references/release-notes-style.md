# App Store "What's New" Style Guide

## Goals

- Explain user-visible improvements clearly.
- Keep text concise and easy to scan.
- Keep meaning consistent across all locales.

## Preferred Style

Use this structure for each locale:

1. Intro sentence (one short paragraph)
2. Bullet list (2-5 items)
3. Optional closing sentence

Example tone (Japanese):

- Intro: `<AppName> <Version>では、操作性と安定性を改善しました。`
- Bullets: concrete user-facing improvements
- Outro: `日々の入力がさらにスムーズになるアップデートです。`

## Writing Rules

- Start bullets with action-oriented phrasing.
- Keep one change per bullet.
- Focus on outcomes and behavior changes.
- Avoid internal terms (class names, refactors, file paths).
- Mention migration actions when behavior changed.

## Localization Rules

- Keep semantic meaning equivalent across locales.
- Use natural wording for each locale (not literal word-for-word translation).
- Preserve product names and proper nouns.
- Keep bullet count roughly aligned across locales.

## Commit Filtering Guidance

- Exclude internal-only commits such as docs/agent updates or pure version bump labels.
- Keep changes that users can notice in app behavior, UX, stability, or performance.

## Final Checklist

- Confirm git range is correct.
- Confirm version and release date are correct.
- Confirm all app-supported locales are present.
- Confirm no duplicate bullets.
- Confirm no internal-only implementation noise.
