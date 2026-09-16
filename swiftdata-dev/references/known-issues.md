# Recorded SwiftData incidents and workarounds

These cases come from public application history and first-person reports inspected on
2026-09-16. They are not Apple specifications, a list of bugs in every current
SDK, or recommendations to copy either application's architecture. No new
runtime reproduction of these original application failures was performed while
compiling these records. Separate synthetic checks are described in
[compatibility.md](compatibility.md#synthetic-checks-on-the-review-environment).

| Symptom | Evidence strength | Candidate to investigate |
| --- | --- | --- |
| Existing data appears absent after adopting SwiftData | First-person sample investigation and reported recovery | Compare resolved store URLs before blaming schema migration |
| CloudKit initialization prevents migration | Historical community reports, including a later failed workaround | Separate local migration from cloud initialization; reproduce before changing startup |
| Crash in rollback while replacing a related graph | Historical before/after reproduction and environment recorded | Explicitly delete owned children before parents in that replacement path |
| Crash in a predicate using the implicit model `id` | Historical fix report and source diff; runtime details missing | Compare `persistentModelID` for store-local identifier lookup |
| Tag preview predicate failures through a protocol-constrained type | Fix commit and regression test source; diagnostic/result log missing | Construct the predicate with the concrete model type at the fetch boundary |

## Store selection during Core Data adoption

**Observed problem.** A [2023-08-28 first-person article](https://zenn.dev/muhiro12/articles/swift-coredata-to-swiftdata)
reports that records appeared missing when converting Apple's Trips sample to
SwiftData. Inspection found that Core Data used `Trips.sqlite` while the new
SwiftData configuration used `default.store`.

**Attempt and reported result.** Passing the existing store URL to
`ModelConfiguration(url:)` made the original records available. The article
does not specify the precise SDK/runtime or demonstrate every migration shape.

**Transferable lesson.** Verify which store was opened before diagnosing data
loss or a migration-engine bug. Keep URL correction separate from schema
compatibility and data transformation. An explicit URL is appropriate only after
identifying the intended store; this case does not justify hard-coded paths or
assuming any Core Data store can be opened unchanged by SwiftData. Follow
[Apple's adoption guidance](https://developer.apple.com/videos/play/wwdc2023/10189/)
and verify actual historical data with the target schema.

## CloudKit startup during migration

**Observed problem.** A [January 2024 report](https://developer.apple.com/forums/thread/744491)
describes failure after adding CloudKit when users skipped older app releases.
Validation complained about attributes without optionality or defaults despite
the destination schema supplying them. The proposed startup-order cause was
the reporter's diagnosis, not an Apple-confirmed explanation.

**Attempts and limits.** The author reported that retrying initialization with
CloudKit disabled permitted migration, then enabling sync on the next launch
worked. In March 2024 the same author reported that this workaround crashed
with custom migration on iOS 17.4 (`FB13694972`). Later participants reported
mixed results from migrating locally before creating the synced container.
No current resolution or before/after verification is established here.

**When investigating.** Match the historical schema, skipped upgrade, custom
stage, runtime, and cloud configuration. Treat two-phase startup as a candidate
requiring verification, not standard bootstrap code. Check container lifetimes,
local migration completion, and subsequent sync. Do not swallow migration
errors, silently disable expected sync, or move required data transformation
into a view task merely because a forum workaround did so.

## Rollback snapshot crash in Cookle

**Observed problem and conditions.** A disk-backed backup replacement deleted
existing parent records before fetching and deleting their owned children.
An injected save failure reached `context.rollback()` and crashed with
`Unexpected backing data for snapshot creation`; the diagnostic identified
`_FullFutureBackingData` for a child model. The fixture contained a related
graph and a 1 MiB externally stored photo, with CloudKit and autosave disabled.
The recorded environment was Xcode 27.0 build `27A5252f`, iOS 27 Simulator.

**Attempt and result.** The fix changed only deletion order: owned diary,
photo, and ingredient rows were explicitly deleted before their parent rows.
The accompanying report records an isolated failure before the change and
passing library tests afterward. The added regression verifies the original
content after rollback and after opening a fresh container, as well as two
successful restore paths. No schema or public API change was needed.
See the [fix and tests](https://github.com/muhiro12/Cookle/commit/ac5b2f2f25fe435cbdad14ca13f0c2c97fb10f5c)
and the [recorded result](https://github.com/muhiro12/Cookle/blob/ac5b2f2f25fe435cbdad14ca13f0c2c97fb10f5c/Designs/Plans/september-release-readiness.md#september-9-restore-rollback-fix).

**When to try it.** Match a rollback snapshot failure involving cascades and
explicit deletion of both parents and children. Preserve the graph and failing
sequence in a regression, then compare child-first deletion within the same
pending transaction. If a known affected runtime must be supported and the
parent-first path still reproduces, avoid that path until a tested alternative
is available.

**Limits.** The code comment attributes the problem to cascades invalidating
rollback snapshots; this is an application diagnosis, not an Apple-confirmed
root cause. It does not show that cascade deletion is generally broken, that
every relationship graph needs manual child deletion, or that the issue persists
in later SDKs. The test injects an error before committing; actual disk failures
and CloudKit recovery were not established. Explicit deletion can also load
more models, so check cost before extending it to larger graphs.

## Identifier predicate crash in Incomes

**Recorded problem.** A 2025-05-26 commit reports a crash in SwiftData filters
using the model's implicit `id`. The affected model had no explicitly stored
`id` field; the filter parameters were `PersistentIdentifier` values.

**Attempt and available result.** The equality predicate changed from
`model.id == identifier` to `model.persistentModelID == identifier`; membership
changed from `identifiers.contains(model.id)` to the corresponding
`persistentModelID` expression. The [commit](https://github.com/muhiro12/Incomes/commit/b670882db58023042f087d6c232043da36ed410c)
describes this as a crash fix. It does not retain a before/after execution log,
exact error, OS version, or SDK version. Treat the outcome as a historical fix
report, not a newly verified framework limitation.

**When to try it.** If the same implicit-ID predicate fails, compare the narrow
substitution using the same store and identifier values. Confirm matching and
nonmatching lookups; account for an inserted model's temporary identifier before
its first save. Preserve an explicitly stored application `id` if that is what
the query is meant to compare.

**Limits.** This is not evidence that all `.id` expressions crash or that
application-owned identifiers should be replaced. It concerns store-local
lookup; it does not make `PersistentIdentifier` a cross-device or archive ID.
If the current runtime accepts the original query, do not add a compatibility
workaround solely because this historical commit exists.

## Concrete predicate construction in Cookle

**Recorded problem and shape.** A 2026-03-08 commit identifies tag preview
predicates as needing correction. Fetch descriptors for two concrete models
used a generic `TagPredicate<T: Tag>.value`, whose macro body accessed the
protocol requirement `value` through `T`. The retained commit does not include
the original diagnostic or the exact SDK/runtime.

**Attempt and available result.** The changed fetch-descriptor helpers use
`Predicate<Ingredient>` and `Predicate<Category>` constructed in constrained
extensions. The generic selection abstraction remains; only the expressions
used for fetching are specialized. Regression tests were added for actual
fetches, exact and kana-variant matching, and preview-style repeated creation.
See the [patch and tests](https://github.com/muhiro12/Cookle/commit/6b387e145c88a607f00170b3ae9e2a125aff25f9).
The source records the intended coverage but does not include a test-run result.
It therefore supports a candidate mitigation, not a confirmed version range
or guaranteed fix for every generic predicate.

**Related public reports.** A [Swift Forums thread](https://forums.swift.org/t/swiftdata-predicate-does-not-handle-protocol-witness/68256)
contains a November 2023 preview failure resolving a protocol-derived key path,
a February 2024 concrete-descriptor workaround, and a December 2024 report of
Release-only failure. These are first-person reports, not an Apple-confirmed
root cause for the Cookle incident. They support comparing concrete expressions
and testing the affected execution mode, without banning generic abstractions.

**When to try it.** For a similar failure involving a protocol-constrained
model key path, compare the generic expression with a concrete-model expression
in a minimal fetch. Keep filtering semantics unchanged and check the actual
descriptor used by the caller, not only in-memory predicate evaluation.
Include the failing Preview, Debug, or Release mode when it matters; a small
successful generic equality fetch on a newer runtime does not prove every
historical query shape has been repaired.

**Limits.** The cause is not established as a general Swift generics defect.
Do not remove all generic code or split every query by model. A different
failure may involve unsupported predicate translation or another cause entirely.

## Adding or strengthening a case

Keep the symptom, conditions, environment, attempted change, observed outcome,
remaining failures, and retrievable evidence together. Mark missing evidence
as unknown. Source inspection and a regression's existence do not prove it ran.
Describe an unavoidable limitation only when the applicable official restriction
or unsuccessful alternatives are actually demonstrated; a revert alone does
not establish that a design cannot work.

Publish only relevant technical details and public or synthetic evidence.
Exclude private logs, user records, account/container identifiers, personal
paths, and unrelated release or product decisions.
