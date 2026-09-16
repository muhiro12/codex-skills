# Context and Language

Reviewed 2026-09-16 against Apple guidance, Xcode 27 public declarations, historical
implementation evidence, and bounded macOS 27 probes. Historical reports help
identify hypotheses; they do not establish the cause or current status of a bug.

## Context limits

### Budget tokens for the session

The limit is a token budget, not a GET-response byte limit or a fixed character
count. Instructions, prompts, history, tool definitions/results, generated
schemas, and responses all consume context. A short latest prompt can fail when
prior turns or a large generated response fill the remaining space. Apple's
[context guide](https://developer.apple.com/documentation/foundationmodels/managing-the-context-window)
explains accounting and recovery.

In a [June 2025 forum response](https://developer.apple.com/forums/thread/788847),
Apple DTS identified an over-limit request as expected behavior and cautioned
that character-based estimates are approximate. Another report of a small prompt
led to a request for a fresh-session reproduction, not confirmation of an Apple
bug: [context-length investigation](https://developer.apple.com/forums/thread/791026).
Do not classify either all context errors as bugs or every small-input error as
user error without the actual session contents and error.

### Use the current SDK and model

- Early iOS 26 guidance describes 4,096 tokens. Do not make that a permanent limit
  for every model/OS. Query `SystemLanguageModel.contextSize`; the inspected Xcode
  27 SDK back-deploys this property to iOS 26 and uses a runtime value on iOS 27.
- `tokenCount(for:)` is available from iOS/macOS/visionOS 26.4 in that SDK. It can
  count prompts, instructions, tools, schemas, and transcript entries. Check
  availability when supporting older runtimes; those versions need Instruments
  evidence or a conservative estimate rather than an unavailable API call.
- Reserve output space and request overhead. Counting only the source string is
  not a complete session budget. `maximumResponseTokens` caps output; it does
  not enlarge the input/context capacity.
- Current iOS 27 uses `LanguageModelError.contextSizeExceeded`; older deployment
  paths use `LanguageModelSession.GenerationError.exceededContextWindowSize`.
  Check the selected SDK rather than copying a dated error handler.

The [Foundation Models updates](https://developer.apple.com/documentation/updates/foundationmodels)
record the 26.4 measurement APIs and later model changes. The current synthetic
[case](development-cases.md#whole-page-input-and-context-overflow) observed 8,192
tokens on one macOS 27 configuration; it is not a replacement universal constant.
If capability measurements fail or return unusable values, diagnose that process's
model-service access before drawing conclusions about capacity.

### Reduce or partition the actual source

If one source exceeds the budget even in a fresh session, another empty session
alone will not fix it. Extract relevant content, process meaningful chunks in
separate sessions, or evaluate a model with sufficient context. If accumulated
history causes overflow, rebuild the session with only needed context. These are
different remedies. See Apple's
[TN3193](https://developer.apple.com/documentation/technotes/tn3193-managing-the-on-device-foundation-model-s-context-window).

For HTML, raw scripts/navigation can consume budget while the required content
may depend on rendering. Inspect acquisition separately from generation. Verify
that filtering/chunking preserves required relationships and that recombining
results also fits. Do not silently truncate important source material merely to
make the request complete.

## Output language

Apple's [language and locale guide](https://developer.apple.com/documentation/foundationmodels/supporting-languages-and-locales-with-foundation-models)
supports using different languages for instructions, prompts, and output. For
non-U.S.-English locale context it documents this exact English phrase:

```swift
"The person's locale is \(locale.identifier)."
```

Locale context and output language are separate. Explicitly state the target
language in `Instructions` when needed, for example `You MUST respond in Japanese.`
The model otherwise tends to follow its input languages; mixed-language prompts
can produce mixed-language output. This is steering, not a language guarantee.

Determine the feature's intended output language from its actual app/user
settings. `Locale.current` can reflect per-app settings; a device's top preferred
language need not be the requested output. `supportsLocale(_:)` checks support
and fallbacks; it does not configure the response language. Catch unsupported
input/output-language errors at execution too.

Schemas, property names, and guide descriptions also reach the model. Inspect
them when diagnosing unexpected English output, but do not require translating
Swift identifiers or all prompts: Apple permits different supported languages.
For extraction, distinguish text to translate from source fields or machine
identifiers the feature intends to preserve.

Evaluate mixed-language input, app/device language differences, and structured
output for the actual feature. The [current probe](development-cases.md#locale-based-output-language)
is a small successful sample, not proof that historical language-following
failures are all fixed. Model instruction-following improvements in 26.4 and 27
justify retesting rather than retaining or removing a workaround by assumption.
