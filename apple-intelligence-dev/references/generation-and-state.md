# Generation and Application State

## Prompts and structured output

Put application-authored behavior in `Instructions`; pass user text, websites,
OCR output, and retrieved content as data. Delimit source content clearly, but do
not treat delimiters as a security boundary. Tool authorization and deterministic
validation still apply if the model follows a command embedded in the source.
See Apple's [Instructions](https://developer.apple.com/documentation/foundationmodels/instructions)
and [tool calling](https://developer.apple.com/documentation/foundationmodels/expanding-generation-with-tool-calling) guidance.

For structured results, use public `Generable`/`Guide` capabilities appropriate
to the SDK and model. Name fields clearly and add guides for actual ambiguity.
Schema validity establishes shape, not truth. Do not ask a schema to silently
collapse a range, infer an omitted target, or fabricate a required date. Use an
optional value or an explicit unknown representation that fits the existing
model; a new persistent field is a separate design decision. See
[guided generation](https://developer.apple.com/documentation/foundationmodels/generating-swift-data-structures-with-guided-generation).

Use greedy sampling as a candidate baseline for fact extraction, not as a promise
of correct or permanently identical output. Compare prompt/options changes on
the same representative inputs. Creative generation can require other sampling
choices; do not impose extraction rules on a creative feature.

## Preserve meaning when extracting facts

Keep acquisition, model interpretation, and source validation inspectable. When
exact structured data already exists, reuse it rather than asking the model to
recreate it. When both sources contribute, define which fields each owns.

Examples that expose semantic errors:

- A yield of items is not necessarily a serving count; a numeric range is not its
  lower bound. Preparation, cooking, and total duration are distinct facts.
- A reference date and time zone can anchor relative dates. They do not authorize
  inventing a missing date, target record, or end of a repeated change.
- Ingredient group markers, repeated rows, step ordering, and references between
  steps can carry meaning. Flattening text can sever those relationships.
- Warnings, equipment settings, and operational instructions can be lost even
  when the main ingredients or summary look correct. Preserve relevant source
  sections through a reliable path when their omission would matter.
- Name/quantity order varies by language. Accept a field split only when it
  preserves the source meaning; keep uncertain text reviewable instead of
  silently discarding qualifiers or preparation instructions.

Apply source-based correction only while it corresponds to the user's current
input. A later edit must not be overwritten by facts from an older source
snapshot. Keep source references accessible where the product needs review;
metadata availability alone does not grant rights to redistribute source content.

## Request ownership and application boundaries

Use an owner whose lifetime matches the interaction. A fresh session often fits
independent extraction; retain a session for a conversation only when its history
is useful. Avoid accidental request overlap on one session. Follow the SDK's
concurrency contracts rather than adding detached tasks or actor workarounds.

Retain the task or use a structured task with an appropriate cancellation
lifetime. After each asynchronous acquisition/generation step, verify cancellation
and the request/input revision before applying results. If cancellation is
cooperative or delayed, invalidate ownership so a late result cannot update the
new draft. Apply a complete validated result together when partial edits would
leave inconsistent fields. Streaming can update a separate draft display without
committing partial results to persistent records.

Preserve the user's input on failure. Classify unavailable, unsupported-language,
context-limit, refusal/guardrail, service, and cancellation outcomes separately;
use current SDK error types with availability-correct compatibility paths.
Cancellation should not present as a failed generation. If a deterministic
fallback exists, make its reduced capability clear where it affects the user's
decision. A thrown model error is not evidence that fallback parsing succeeded.

For tools that change data, resolve real identifiers and revalidate affected
records in domain code at execution time. Respect the product's existing consent,
confirmation, and undo behavior. Financial arithmetic, date boundaries, and
invariants belong to deterministic operations. A model's prose, confidence, or
well-formed arguments are not authorization. Tool calls can overlap or repeat;
make side effects safe under the execution behavior being used. Keep read-only
retrieval separate when that simplifies the boundary.

## Context and latency

Account for instructions, prompts, schemas, history, tool definitions/results,
and generated output. Use current token-count/context APIs where available;
character limits alone do not measure model capacity. Keep concise instructions
and relevant retrieval. For long input, split along meaningful boundaries with
stable ordering and reconciliation, or use a suitably authorized model. Do not
silently truncate required facts or lower output limits until the failure merely
looks faster. See [context management](https://developer.apple.com/documentation/foundationmodels/managing-the-context-window).

Measure before optimizing. Prewarm when a strong interaction signal predicts
use; avoid loading models for every row or view construction. Excluding the schema
from a prompt needs sufficient schema context already present and validation of
lost guide descriptions. Streaming reduces perceived waiting, not necessarily
completion time. These tradeoffs are demonstrated in Apple's
[Foundation Models code-along](https://developer.apple.com/videos/play/wwdc2025/259/).
