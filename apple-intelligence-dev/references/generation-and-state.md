# Generation and Application State

Linked sources describe Apple APIs. The integration checks below explain where
to test application behavior; they do not impose a particular product workflow.

## Prompts and guided generation

Use `Instructions` for the model's role and behavior, and prompts for the current
request and source data. Source delimiters help express that distinction but do
not make embedded commands harmless. See Apple's
[Instructions](https://developer.apple.com/documentation/foundationmodels/instructions)
and [prompt guidance](https://developer.apple.com/videos/play/wwdc2025/248/).

Use `Generable` and `Guide` for the requested output shape and supported
constraints. A guide description is prompting; a well-formed generated object
is not proof that its fields match the source. For extraction, decide how the
schema represents absent or ambiguous information. For creative generation,
unspecified details may be precisely what the model should supply. See
[guided generation](https://developer.apple.com/documentation/foundationmodels/generating-swift-data-structures-with-guided-generation).

Greedy sampling is a useful comparison setting for extraction experiments, not
a factuality guarantee. Evaluate schema, instructions, examples, and sampling
changes against the same inputs. When exact extraction still fails, compare
source-based validation or direct field extraction with further prompt tuning.
The [development cases](development-cases.md) distinguish a successful source
workaround from unresolved model errors. For multilingual prompts and generated
text, use [context and language](context-and-language.md#output-language).

## Session lifetime and cancellation

Choose session lifetime according to the requested interaction. Independent
requests can use fresh sessions; conversations need relevant history. Inspect
the current `LanguageModelSession` concurrency and cancellation contracts before
sharing a session between simultaneous operations. See
[LanguageModelSession](https://developer.apple.com/documentation/foundationmodels/languagemodelsession).

If input can change while generation is pending, associate the result with the
request/input that produced it. Cancellation checks or request revisions can
prevent an older completion from updating the new interaction. This matters
when asynchronous ownership changes; it does not require a review screen or
prohibit automatic application of a result.

Handle cancellation separately from generation errors. Classify availability,
context-limit, language, refusal/guardrail, and service errors using the selected
SDK's types. If the app uses a fallback, distinguish its outcome from model
success so evaluation and recovery do not conceal a failing model request.

For streaming, consume the SDK's partial output representation and accommodate
fields that are not generated yet. Decide which partial fields the feature can
use independently; streamed display, tool execution, and persistence need not
share one lifetime. See Apple's
[streaming code-along](https://developer.apple.com/videos/play/wwdc2025/259/).

## Tool execution

Apple's [tool calling guide](https://developer.apple.com/documentation/foundationmodels/expanding-generation-with-tool-calling)
describes generated arguments and potentially concurrent tool calls. Check the
arguments and concurrency behavior against the tool's actual contract. For
side effects, establish what retries, cancellation, and repeated calls mean;
rolling back a session transcript is not evidence that an external effect was
undone.

Use the app's existing authorization and automation policy. A tool may execute
an authorized action automatically; this skill does not require routing every
call through a confirmation UI or a specific domain-layer architecture.

## Context and latency

For token accounting, SDK differences, oversized source text, and recovery, read
[context limits](context-and-language.md#context-limits). A larger model context
and a faster response are separate properties; measure the relevant one.

Profile before selecting optimizations. Prewarming can reduce asset-loading
latency; excluding schema text can reduce prompt size but requires adequate
schema context and may remove guide descriptions. Streaming affects when output
becomes usable, not necessarily total completion time. Apple's
[code-along](https://developer.apple.com/videos/play/wwdc2025/259/)
demonstrates these tradeoffs.
