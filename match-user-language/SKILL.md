---
name: match-user-language
description: Match Codex chat replies, clarification questions, progress updates, final answers, and Plan Mode user-facing content to the dominant language of the user's conversation in the Codex app. Use when the user is conversing in Japanese, English, or another language and expects Codex-facing prose to follow that language, or when the user explicitly says things like "日本語で" or "English please". This skill controls only Codex's user-facing chat text and plan UI language; it does not translate code, identifiers, CLI commands, file paths, YAML or JSON keys, directives, commit messages, or repository documents unless the task explicitly asks for that.
---

# Match User Language

## Overview

Use this skill to keep Codex's user-facing prose aligned with the language the user is actually using in the Codex app.
Treat language matching as a chat-surface behavior, not as permission to translate code or repository artifacts.
This includes user-facing structured Plan Mode content, not just plain chat text.

## Language Selection

1. Prefer an explicit language instruction in the current turn.
- Examples: `日本語で`, `英語で`, `English please`, `reply in Japanese`.
- If the user explicitly requests a language for the current response, follow that request immediately.

2. Otherwise, infer the dominant language from the user's substantive messages in the current thread.
- Focus on the user's actual prose, not Codex's previous replies.
- Ignore URLs, pasted code, shell commands, file paths, quoted source text, stack traces, and short borrowed words when judging the dominant language.
- Treat "substantive" as messages or message portions that express the user's request, feedback, constraints, or decisions.

3. Break ties with recency.
- If the thread is mixed and no language clearly dominates, use the language of the most recent substantive user message.

4. Keep the tone aligned after choosing the language.
- Default to concise, pragmatic, polite wording in the selected language unless the user asks for another tone.

## Apply To

Apply the selected language to:

- normal chat replies
- clarification questions
- progress updates in commentary-style user-facing text
- final answers
- Plan Mode plan prose inside `<proposed_plan>`
- `update_plan.explanation`
- each `update_plan.plan[].step`
- Plan Mode question UI text such as `request_user_input.questions[].header`
- `request_user_input.questions[].question`
- `request_user_input.questions[].options[].label`
- `request_user_input.questions[].options[].description`

## Do Not Apply To

Do not translate or rewrite these just to match the conversation language:

- code blocks
- identifiers, symbol names, API names, type names, and enum cases
- shell commands, CLI flags, environment variables, and file paths
- YAML, JSON, TOML, and similar keys
- directives such as `<proposed_plan>`, `</proposed_plan>`, `::automation-update{...}`, and `::code-comment{...}`
- commit messages or other fixed tool-facing strings
- existing repository documents, comments, localization files, or user-provided artifacts unless the task explicitly asks to change them
- machine-stable identifiers such as `request_user_input.questions[].id`

## Artifact Guardrails

- When generating code or editing repository files, follow the language required by the file, the surrounding project conventions, or the user's explicit content request.
- When the user asks for translation or for content in a target language, produce the requested artifact language even if the surrounding conversation uses another language.
- Keep surrounding explanation in the conversation language unless the user asks for the whole response in the target language.

## Plan Mode Guardrails

- Treat all user-visible Plan Mode text as part of the conversation surface, even when it is passed through tool arguments rather than emitted as plain chat.
- Do not leave `update_plan.explanation` or `plan[].step` in English when the conversation is clearly Japanese unless the user explicitly asked for English.
- Do not leave Plan Mode question labels or descriptions in English just because the tool schema, wrapper tags, or stable IDs are English.
- Keep wrapper names, tool names, and stable IDs unchanged while localizing only the user-facing prose fields.
- When in doubt, prefer matching the most recent substantive user language over inherited defaults from earlier English tool or system text.

## Formatting Rules

- Preserve markup and machine-readable wrappers exactly.
- Keep `<proposed_plan>` tags unchanged and only localize the prose inside the block.
- Preserve Markdown code fences, inline code, and structured config snippets exactly unless the task explicitly asks to rewrite them.
- For structured tool payloads, localize only the user-visible string values and preserve field names and stable IDs exactly.

## Examples

- If the user mostly writes in Japanese and asks for a plan, write the plan body in Japanese.
- If Plan Mode uses `update_plan`, write `explanation` and each `step` in Japanese for a Japanese conversation.
- If Plan Mode asks follow-up questions through structured UI, write the visible question text, labels, and descriptions in Japanese, but keep IDs like `preferred_language` unchanged.
- If the thread is mainly in English, keep the plan body and normal replies in English.
- If the thread is mainly Japanese but the user says `English please` in the current turn, switch that response to English immediately.
- If the user asks for code changes in a Japanese conversation, explain the changes in Japanese but keep code, paths, and identifiers unchanged unless the task itself requires different text.
