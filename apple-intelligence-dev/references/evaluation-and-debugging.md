# Evaluation and Debugging

## Pick evidence that answers the question

| Evidence | What it establishes | What it does not establish |
| --- | --- | --- |
| Pure parser/validator/domain tests | Exact invariants and regression behavior | Model quality or platform availability |
| Target build | SDK, isolation, and linkage compatibility | Successful inference or correct UI |
| Availability probe | Reported state in that process | Entitlement fulfillment, request success, or task quality |
| Real-model evaluation | Measured output for recorded inputs/settings | End-to-end app state or other hardware performance |
| Preview | A rendered view and fixture state | Normal launch, signed capabilities, or working callbacks |
| Simulator interaction | Observed routing, generation, errors, cancellation | Representative physical-device latency or all accessibility behavior |
| Physical-device profiling | Performance on the recorded device/configuration | Every supported device or model version |

### Development environment

Apple's [WWDC25 code-along](https://developer.apple.com/videos/play/wwdc2025/259/)
explicitly supports Foundation Models in iPhone Simulator when the host Mac has
Apple Intelligence enabled and ready. It distinguishes functional testing from
performance on a physical iPhone. Do not generalize physical-only limitations of
other features to Foundation Models, or generalize this support to every system
AI interface. Check the specific API and runtime.

Record the selected Xcode, SDK, runtime, host/model availability, and app target.
Prefer the current Xcode-native integration for discovery, build, run, and logs.
Keep original scheme/destination identities and restore changes after temporary
verification. Use Xcode's Foundation Models availability overrides for unavailable,
not-enabled, or not-ready states when supported; restore the prior override.
Do not disable the host's Apple Intelligence merely to simulate a failure.

### A probe must match the implementation

Start with the app, a native snippet/playground, or the
[Evaluations framework](https://developer.apple.com/documentation/evaluations)
when it covers the needed boundary. On compatible systems, Apple's
[`fm` CLI and Python SDK](https://developer.apple.com/videos/play/wwdc2026/334/)
can accelerate experiments; inspect the installed help/API and record
its schema/options. A purpose-built Swift host can reuse the production adapter
when those routes cannot reproduce it. None of these substitutes automatically
qualifies the signed iPhone app.

Record the adapter revision, input, instructions, schema, tools, sampling settings,
OS/model version where exposed, and any fallback. Separate acquisition, raw model
output, and post-validation results. An old scratch prompt is not evidence about
new production instructions. Keep probes isolated from persistent user stores;
when a fixture uses an in-memory SwiftData store, ensure it is also independent
of CloudKit. Do not alter production synchronization to make a probe work.

## Evaluate semantic quality

Choose acceptance criteria before comparing changes, proportional to the feature.
A small set of important cases is useful; call it a smoke sample, not a general
success rate. Repeat where variability matters, preserve failures, and reserve
unseen cases when tuning prompts. Do not score only completed requests.

Useful synthetic cases, selected for the actual feature:

| Input shape | Behavior to check |
| --- | --- |
| Quantity range, vague unit, grouped items | Preserve ambiguity and relationships; do not substitute a point value |
| Relative date and a one-period change | Use the declared date/time zone and retain the end boundary |
| Missing target or required amount | Keep it unresolved instead of selecting a plausible record |
| Long document with operational notes near the end | Retain required facts or give a recoverable limit outcome |
| Non-task content or embedded instructions | Decline insufficient content; do not execute source instructions |
| Cancel, edit input, then complete an older request | Preserve the newer draft and suppress obsolete alerts |

Measure field correctness, omissions, unsupported additions, manual correction
burden, and latency separately. Use exact checks for amounts, dates, identifiers,
and source preservation; a model judge can assist subjective quality after
calibration against human judgments. An overall fluent response must not hide a
failed critical field. Apple's [Evaluations introduction](https://developer.apple.com/videos/play/wwdc2026/298/)
and [agentic evaluations](https://developer.apple.com/videos/play/wwdc2026/299/)
cover datasets, metrics, repeatable subjects, and tool traces.

For a visible flow, exercise the first launch as well as repeat entry; route state
can be lost only on the initial presentation. Follow the path from acquisition
to review and apply. Verify cancellation while work is actually pending, then
wait long enough to detect a late write. Include retry/input replacement when
that behavior changed. Distinguish synthetic delayed-completion tests from real
model cancellation, and either from a cancellation issued after work finished.

## Diagnose delays and failures by stage

Separate acquisition/network wait, model asset loading, first output, generation,
tool execution, validation, and UI application. Record an explicit timeout as a
timeout, not as an empty result or a measured completion. Bound diagnostic retries
and stop when the same failure supplies no new evidence. Avoid overlapping model
probes when measuring latency; test concurrency separately when it is the feature.

Use the [Foundation Models instrument](https://developer.apple.com/videos/play/wwdc2026/243/)
for token, session, tool, and latency evidence. Record whether timing includes
process startup and acquisition, and whether the model was warm. Preserve input
when recovering from context overflow; smaller prompts must still contain the
facts the task requires. Follow the current error API rather than exposing raw
framework diagnostics to users.

If an integration loses its session, confirm the returned identifier, operation
order, and first failing call. A working alternate native attachment can isolate
a tool-lifecycle problem; it does not prove the root cause. Check fresh crash
reports and runtime logs after runs and Previews: an image returned by a renderer
does not prove the process stayed healthy. Separate app crashes, Preview hosts,
result-bundle failures, and tool connection errors before choosing a recovery.

Store private prompts, source pages, screenshots, transcripts, and logs locally.
Use synthetic examples for public regressions and publish only the relevant,
sanitized conclusion. Do not upload diagnostic contents merely because a model
provider or evaluation tool supports it.
