# Models and Availability

## Choose a capability for the product task

Use the requested processing boundary. Evaluate an existing on-device path before
replacing it solely because a newer or larger model exists. A feature explicitly
intended for recent Apple devices need not introduce an external provider just
to widen compatibility. Conversely, preserve a requested broader-device strategy.

| Capability | Decision to verify |
| --- | --- |
| `SystemLanguageModel` | Suitability for the task, supported language/modality, asset readiness, and actual output quality |
| `PrivateCloudComputeLanguageModel` | Measured need for more context/reasoning, network dependence, granted entitlement, distribution eligibility, and user quota |
| Other `LanguageModel` providers | Supported integrations, model capabilities, data destination, authentication, cost, and deployment footprint |
| Image Playground or Writing Tools | Whether the system experience already performs the requested user task without a custom inference pipeline |

[Foundation Models updates](https://developer.apple.com/documentation/updates/foundationmodels)
is the starting point for current additions. The iOS 26 generation introduced
on-device structured generation and tools; the iOS 27 generation expands model
providers, image inputs, dynamic profiles, evaluation support, and error APIs.
These are versioned capabilities, not replacements to apply indiscriminately to
older deployment targets. Check each symbol's platform availability.

## Separate the availability layers

1. **Build surface:** the selected SDK declares the API for this target.
2. **Runtime support:** the OS, hardware, region/language, and feature-specific
   settings support the operation; required assets are ready.
3. **App authorization:** signed entitlements, provisioning, permissions, and
   provider configuration allow this app to use it.
4. **Current service state:** connectivity, quota, and transient errors permit
   this request.
5. **Task fitness:** the result is accurate enough for the intended feature.

Check availability before offering or starting an operation, then handle errors
during execution because state may change. A type's existence or an `available`
result alone does not establish all five layers. Use the relevant framework's
check; one Foundation Models result does not describe all Apple Intelligence
features. For each unsupported or unavailable state, retain a useful manual path
or explain the recovery that applies to that state.

## Private Cloud Compute

Consult Apple's current [access requirements](https://developer.apple.com/private-cloud-compute/)
and [PCC integration guide](https://developer.apple.com/documentation/foundationmodels/adding-server-side-intelligence-with-private-cloud-compute).
Developer eligibility, the managed `com.apple.developer.private-cloud-compute`
entitlement, the signed app's provisioning, and user availability are independent
checks. Adding an entitlement key locally is not evidence of a grant. A command
line probe can have different authorization from the signed app; test the actual
supported app/distribution path before declaring PCC unusable.

Keep developer API cost, user daily limits, and third-party provider billing
separate. Query supported runtime quota information and preserve useful drafts
when limits are reached. Do not loop retries at quota exhaustion. An alternative
model can change quality, privacy, and cost; switch only within the product's
approved behavior and explain any meaningful change to the user.

Apple's [WWDC26 PCC session](https://developer.apple.com/videos/play/wwdc2026/319/)
also describes debugging approaching and exhausted limits. Use the available
Xcode simulation controls rather than consuming a real user's allowance to
manufacture the condition.

## Context and evolving models

Read the current model's capabilities and context size instead of embedding an
old presentation's fixed token limit. OS updates can change the system model
without changing app code. Re-evaluate representative prompts when upgrading;
version prompts only when results justify the added maintenance. See
[updating prompts for new model versions](https://developer.apple.com/documentation/foundationmodels/updating-prompts-for-new-model-versions).

Dynamic profiles can change instructions, tools, and the model within a session.
Before a local-to-server transition, inspect which source content and transcript
would cross that boundary. Keep confirmed application state independent of the
transcript and expose only the tools needed for the current stage. See
[dynamic sessions and profiles](https://developer.apple.com/documentation/foundationmodels/composing-dynamic-sessions-with-instructions-and-profiles).
