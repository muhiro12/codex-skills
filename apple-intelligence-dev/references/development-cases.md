# Development Cases

These are independent observations from Incomes and Cookle development, not
Apple-confirmed bugs or designs every app must copy. Dates and environments
scope the evidence; later model/OS versions require another check. Examples
below describe input shapes without publishing private source pages or logs.
A successful application workaround is distinct from fixing model behavior.

## Source omissions and rewritten fields

**Conditions:** Cookle recipe extraction with `SystemLanguageModel.default`,
guided Swift output, and greedy sampling on macOS 27, reviewed 2026-09-16.
Inputs included structured metadata and dynamically rendered recipe text.

**Observed:** Generated output summarized ordered steps and lost machine
operations or warnings. Ingredient preparation wording could move into the amount
field. Numeric yield or a serving range could become a misleading serving count.
Some required notes were absent from the acquired text; others were lost during
generation. These are separate acquisition and interpretation failures.

**Attempt and result:** Explicit extraction instructions and greedy sampling did
not eliminate the observed field errors. The application retained recognized
source instructions, ingredient pairs, and supplemental facts alongside model
input, then used those facts to correct the corresponding generated fields.
The correction applied only while the imported text still matched its source
snapshot. Visible serving labels qualified otherwise ambiguous metadata.

The bounded real-model reruns retained the previously omitted equipment operations
and warnings. Synthetic regression tests exercised deliberately summarized model
output. A subsequent deterministic replay corrected the affected ingredient
splits; that replay did not demonstrate better raw model output. Evidence and
limits were recorded in [Cookle #115](https://github.com/muhiro12/Cookle/issues/115).

**Limits and applicability:** This is a workaround for source-faithful extraction
where the application can recognize the original fields. It does not cover
arbitrary HTML, facts absent from the source, or edited input that no longer
matches it. It does not establish that the source's own advice is correct. If a
feature requires exact reproduction, the tested prompt alone did not satisfy
that requirement. Source validation is a candidate to evaluate, not a requirement
for creative generation or every Foundation Models app.

## Missing values and a lost one-period boundary

**Conditions:** An Incomes extraction experiment on macOS 27 using Apple's `fm`
CLI, the system model, structured JSON output, fresh sessions, and greedy
sampling, observed 2026-09-13. The prompt supplied a fixed reference date/time
zone, explicit unknown representations, and the meaning of a one-month change.
The synthetic input set included omitted targets/dates and a change for only
the next month.

**Observed:** Structurally valid output sometimes supplied an unstated target or
start month, or omitted the explicit end month. The prompt already addressed
these cases; providing that instruction was insufficient in the recorded runs.
This was a CLI experiment, not proof about the shipping app's Swift adapter.

**Attempt and result:** Repeated evaluation exposed the remaining extraction
errors. A separately selected target/date/amount and deterministic comparison
allowed the app experiment to proceed without depending on those outputs. That
was a product-level bypass, not a repair to the model or a demonstrated prompt
workaround. No successful correction for these model failures was established
in that experiment. Evidence came from the retained synthetic harness and local
probe results reviewed on 2026-09-16; those raw results are not published here.
[Incomes #366](https://github.com/muhiro12/Incomes/issues/366) tracks the
investigation, not a successful model fix.

**Limits and applicability:** Use missing-field and bounded-date cases when
qualifying a similar extractor. Other prompts, schemas, models, or validation
may perform differently; they were not ruled out. The result does not justify
requiring manual selection or confirmation in unrelated apps. It does mean that
accepting every schema-valid result would not meet this experiment's extraction
requirements without further work.

## PCC availability without execution entitlement

**Conditions:** An Incomes investigation using a temporary Swift command-line
probe on macOS 27, observed 2026-09-13. The capability probe reported PCC as
available.

**Observed:** Execution terminated with a fatal missing-entitlement diagnostic
for `com.apple.developer.private-cloud-compute`. Availability and execution access
were different in this probe. The recorded process terminated rather than
returning a recoverable request error.

**Attempt and result:** The diagnostic identified an entitlement boundary. No
successful PCC execution or entitlement workaround was demonstrated by this
probe. Checking Apple's managed-access requirements and testing a correctly
provisioned supported target are next steps, not recorded successes.

**Limits and applicability:** Do not conclude that PCC is unusable in the app,
Simulator, or all development environments from this command-line failure. Do
not assume adding an entitlement string grants access. Consult the current
[Apple access requirements](https://developer.apple.com/private-cloud-compute/)
and test the actual signed target. The observation supports checking execution
access independently; it does not require switching the product to another model.

## Model errors hidden by a fallback parser

**Conditions:** Cookle's existing Foundation Models adapter, inspected and changed
in September 2026. A broad error handler led into deterministic fallback parsing.

**Observed:** The code path could return a simplified parsed result after a thrown
model error, making it difficult for the caller to distinguish recovery from
successful inference. This was an adapter behavior found by code inspection,
not evidence that every framework error had been reproduced at runtime.

**Attempt and result:** The adapter propagated cancellation and mapped generation
errors separately rather than returning fallback success from that catch path.
The separate model-unavailable fallback remained. The
[adapter correction](https://github.com/muhiro12/Cookle/commit/0a822d27)
passed native build and repository checks. This establishes the code-path
correction, not recovery from every live model service or guardrail error.

**Limits and applicability:** If a fallback is part of another feature, it can
remain. Preserve enough outcome information to diagnose the original failure
and evaluate fallback quality independently. This case does not prescribe error
copy, a manual workflow, or a ban on automatic fallback.
