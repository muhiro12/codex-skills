# Evaluation and Debugging

## Match the evidence to the failure

| Check | What it establishes | What remains separate |
| --- | --- | --- |
| Target build | SDK, isolation, and linkage compatibility | Model execution |
| Availability probe | State reported in that process | Signed access, request success, output quality |
| Real-model evaluation | Output for recorded inputs and settings | Other prompts, models, or devices |
| Parser/validator tests | Behavior of application correction code | Improvement to the model itself |
| Simulator interaction | Observed generation, routing, cancellation, errors | Physical-device performance |
| Device profiling | Timing on that device and configuration | Other hardware/model versions |

These are distinctions for diagnosis, not a mandatory test matrix for every
change. Choose the checks that answer the current question.

## Development environment

Apple's [WWDC25 code-along](https://developer.apple.com/videos/play/wwdc2025/259/)
shows Foundation Models in iPhone Simulator when the host Mac has Apple
Intelligence enabled and ready. It separates functional testing from physical
phone performance. Check the specific runtime and API before extending this
support or a different feature's physical-only restriction to another interface.

Record Xcode, runtime, model availability, and the app/probe target. Use the
available native build, run, and diagnostic capabilities. Apple's Foundation
Models availability overrides can exercise ineligible, disabled, and not-ready
states where supported; restore overrides afterward.

Start with the app, a native playground, or the
[Evaluations framework](https://developer.apple.com/documentation/evaluations).
On supported systems, the
[`fm` CLI and Python SDK](https://developer.apple.com/videos/play/wwdc2026/334/)
can accelerate experiments. If a custom Swift host is needed to reproduce the
adapter, record that environment difference; an unsigned host cannot substitute
for a signed target when investigating entitlements.

## Semantic evaluation

Record the instructions, input, schema, tools, sampling settings, adapter revision,
and OS/model version where available. Compare acquired source, raw output, and
post-processing separately. A parser replay verifies a correction without
rerunning generation; label it accordingly.

Choose acceptance criteria appropriate to the task: source fidelity for
extraction, usefulness for creative generation, or correct tool arguments and
execution for an agent. Include missing/ambiguous input and failed requests where
they matter. Use repeated and unseen cases when tuning warrants them; a small
smoke sample is not a population accuracy estimate.

Measure omissions, unsupported additions, correction burden, and latency
separately. Apple's [Evaluations introduction](https://developer.apple.com/videos/play/wwdc2026/298/)
and [agentic evaluations](https://developer.apple.com/videos/play/wwdc2026/299/)
cover datasets, metrics, subjects, and tool traces. Prior bounded extraction
failures and their remedies are in [development cases](development-cases.md).

## Latency, cancellation, and errors

Separate acquisition/network wait, model asset loading, time to first output,
generation, tool execution, and result application. A timed-out probe establishes
a timeout, not an empty model response. Avoid overlapping probes when measuring
single-request latency; exercise concurrency separately when relevant.

Use the [Foundation Models instrument](https://developer.apple.com/videos/play/wwdc2026/243/)
for token, session, tool, and timing evidence. Record warm/cold state and whether
process startup or input acquisition is included.

Test cancellation while work is pending when that lifecycle changed. Distinguish
real generation cancellation from a synthetic delayed completion or cancellation
after work already finished. Check for late output reaching the wrong consumer.

If a run fails, retain the first error and identify the process/stage: model
service, adapter, app, Preview host, or development-tool attachment. A failed
attachment alone says nothing about model eligibility; a returned image says
nothing about whether generation finished. Keep raw diagnostic records private
and report the relevant error and tested recovery without unsupported root-cause
claims.
