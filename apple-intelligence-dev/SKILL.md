---
name: apple-intelligence-dev
description: Build, modernize, and debug Apple Intelligence features using Foundation Models, Image Playground, and related system integrations. Use for model selection, prompts, structured generation, tool calling, request lifecycle, availability, and evaluation; not for general app architecture or custom model training.
---

# Apple Intelligence Development

Use Apple documentation, WWDC material, and the selected public SDK to implement
the requested feature. This is an independent skill, not an Apple-authored one.
Platform references were reviewed on 2026-09-16; recheck version-sensitive details.

## Scope and evidence

The references combine linked Apple API guidance with independent integration
checks. Local observations are collected separately as
[development cases](references/development-cases.md): conditions, symptoms,
attempted remedies, observed results, and limits. They are neither Apple-confirmed
framework defects nor universal architecture requirements.

Determine whether the requested task is extraction, creative generation,
conversation, retrieval, or action execution. Apply the relevant API contracts
and evaluate that task. This skill does not prescribe a local-only product,
manual-entry fallback, draft/review screen, confirmation on every action,
persistence technology, or Operations layer. Follow the app's requirements for
these choices; adapt a workaround only when its failure conditions apply.

Check the selected Xcode, target OS, model, and runtime. Prefer matching current
Xcode-exported guidance when available, then public documentation and SDK
signatures. No sibling skill or particular tool server is required.

## Read the relevant reference

| Work | Reference |
| --- | --- |
| Model choice, OS capability, eligibility, entitlement, or quota | [Models and availability](references/models-and-availability.md) |
| Input limits, oversized pages, output language, or per-app locale | [Context and language](references/context-and-language.md) |
| Prompts, guided generation, sessions, tools, streaming, or cancellation | [Generation and application state](references/generation-and-state.md) |
| Model quality, Simulator support, latency, or generation failures | [Evaluation and debugging](references/evaluation-and-debugging.md) |
| Image Playground, Writing Tools, OCR, Siri, or app search | [System integrations](references/system-integrations.md) |
| Similar symptoms in a prior implementation or probe | [Development cases](references/development-cases.md) |

## Use failures to choose the next check

Inspect the actual acquisition result, instructions, schema, model settings,
response/error, and result consumer. Separate a model error from an input/parser
error, an adapter that hides failure, or a stale asynchronous result.

A probe should reuse the relevant production configuration or identify its
differences. Report compilation, model availability, successful generation,
semantic quality, and device performance separately. A workaround that changes
which component produces a field may fix the app without improving the model.

For a development case, retain the input shape and separate the symptom, confirmed
cause, attempted remedy, and outcome. Distinguish a developer's report of
resolution from independently reproduced results. Link applicable current Apple guidance and state which part
of the failure it addresses. General guidance is not a confirmed fix for a
specific incident. When it leaves the problem unresolved, evaluate the recorded
workaround under its original conditions and current requirements. Recheck after
model/OS changes; historical success alone does not make it the preferred method.
Recommend avoiding a design only for the requirements the evidence fails to meet.

Keep public examples synthetic and portable. Exclude private corpora, account
information, raw diagnostics, and unreleased product plans. Summarize relevant
technical observations instead of copying private records or official manuals.

The compact entrypoint and topic references follow Xcode-exported skill
organization. [d-date/iphone-duo-skill](https://github.com/d-date/iphone-duo-skill)
informed the distinction between announced and confirmed APIs; its specific
platform instructions are not incorporated here.
