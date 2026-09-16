---
name: apple-intelligence-dev
description: Build, modernize, and debug Apple Intelligence features using Foundation Models, Image Playground, and related system integrations. Use for model selection, prompts, structured generation, tool calling, request lifecycle, availability, and evaluation; not for general SwiftUI styling or custom model training.
---

# Apple Intelligence Development

Build the requested intelligent feature around its actual inputs, output quality,
and application behavior. This is independent guidance informed by Apple sources,
not an Apple-authored skill. Platform references were reviewed on 2026-09-16;
recheck version-sensitive details for the selected SDK and runtime.

## Establish the relevant baseline

- Identify the feature's job: extract source facts, generate creative content,
  retrieve app data, propose changes, or execute an authorized action. These jobs
  have different correctness and confirmation requirements.
- Inspect the existing manual flow, inference adapter, prompts, model options,
  input acquisition, validation, and save/apply boundary. Preserve the user's
  chosen deployment targets, privacy model, and automation semantics.
- Check the selected Xcode and supported OS versions. Prefer matching guidance
  from current Xcode-exported skills when available. If `sync-xcode-skills` is
  installed, its generated catalog identifies those skills; otherwise use the
  current Apple documentation and SDK directly. This skill has no required
  sibling skills or tool-server dependency.
- Validate unfamiliar symbols and availability in public SDK declarations or
  current documentation. A WWDC announcement, sample, or successful import of a
  framework does not prove a capability works in the app's signed target.

## Read only the relevant references

| Work | Reference |
| --- | --- |
| Choose models, adopt a new OS capability, diagnose eligibility or quotas | [Models and availability](references/models-and-availability.md) |
| Refine prompts, ground extraction, manage sessions, tools, cancellation, or saving | [Generation and application state](references/generation-and-state.md) |
| Measure quality, test in Simulator, investigate delays or crashes | [Evaluation and debugging](references/evaluation-and-debugging.md) |
| Integrate Image Playground, Writing Tools, OCR, Siri, or app search | [System integrations](references/system-integrations.md) |

## Apply the smallest useful improvement

For new behavior, establish a representative baseline before choosing a more
capable model or expanding the architecture. For existing defects, reproduce the
failing boundary and fix it directly. Prompt changes, input extraction,
deterministic validation, and UI ownership are separate possible causes.

Keep these distinctions explicit:

- A generated Swift value can satisfy its schema while containing invented facts.
  For extraction, preserve unknowns, original units, ranges, ordering, and source
  relationships; validate consequential fields in application code.
- A model may propose an operation or its arguments. The app still resolves real
  records, validates current state, calculates domain results, and enforces the
  existing authorization and confirmation policy.
- A successful model response must belong to the current request and input
  revision before it changes UI state. Cancelling, replacing input, editing a
  draft, and switching documents can invalidate an otherwise valid result.
- Compilation, availability, successful inference, semantic quality, UI behavior,
  and physical-device performance are different evidence. Report the layers
  actually checked rather than calling all of them verified.

Use the repository's verification contract and the available Xcode integration
by capability. A temporary probe can isolate a failure; reuse the production
adapter, schema, prompts, and model settings, or state the differences. Do not
turn a probe's local paths, fixtures, or runtime identifiers into product code.

## Finish with actionable evidence

Summarize what changed, the representative checks and their environment, and any
remaining defect with an input shape and expected behavior. If blocked, identify
whether the missing requirement is an SDK/runtime, model asset, entitlement,
network/quota, tool integration, or app bug. Try a documented alternative when
it supplies the needed evidence; request user action only for the part that
actually requires it.

Keep public examples synthetic and portable. Private source corpora, transcripts,
account details, crash reports, and unreleased product plans are not skill
content. Link to primary sources instead of copying their manuals or samples.

The compact entrypoint and topic references follow the organization used by
Xcode-exported skills. [d-date/iphone-duo-skill](https://github.com/d-date/iphone-duo-skill)
also informed the separation of confirmed SDK behavior from announced APIs;
its platform-specific instructions are not incorporated here.
