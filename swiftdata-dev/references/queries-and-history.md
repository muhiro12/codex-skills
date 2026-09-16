# Fetching, observation, and history

## Choose the read mechanism by its consumer

| Need | Starting point |
| --- | --- |
| Live collection in a SwiftUI view | `@Query` with a bounded predicate and sort |
| One operation or a snapshot | `ModelContext.fetch` and `FetchDescriptor` |
| Count only | `fetchCount` without loading complete models |
| Observable results outside a SwiftUI view, supported OS | `ResultsObserver` |
| Changes since a checkpoint | Persistent history and a stored history token |
| Notification that relevant history is available, supported OS | `HistoryObserver`, followed by history processing |

Apple presents `@Query` for SwiftUI view collections and `ResultsObserver` for
observation outside views. Choose the API for the actual consumer and supported
OS; neither requires a particular application layering scheme.
See [filtering and sorting](https://developer.apple.com/documentation/swiftdata/filtering-and-sorting-persistent-data)
and [ResultsObserver](https://developer.apple.com/documentation/swiftdata/resultsobserver).

## Predicates and performance

Compile predicates and execute them against the intended store. Macro acceptance
does not prove every expression translates to a supported store query. Keep
capture values simple, handle optional relationships explicitly, and avoid
arbitrary helper calls or computed properties in store predicates. When a
predicate is unsupported, reduce it to the smallest failing expression before
choosing a bounded post-fetch transformation.

Distinguish macro/type-check failures, store translation errors, runtime key-path
lookup failures, and incorrect results. Record the expression, captures, optional
paths, concrete model, store, and optimization mode. `Predicate.evaluate` can
succeed even when a persistent fetch fails. Do not maintain a timeless syntax
blacklist: Apple's [iOS 17 release notes](https://developer.apple.com/documentation/ios-ipados-release-notes/ios-ipados-17-release-notes)
list fixes for UUID/Date/URL predicates (109539652) and some `flatMap` and
nil-coalescing behavior (109723704). The [WWDC26 group lab, 34:24](https://developer.apple.com/videos/play/wwdc2026/8017/)
describes new predicate support for `RawRepresentable` enums; that does not make
arbitrary Codable payloads queryable on every deployment target.

If the failure involves an implicit model ID or a predicate over a
protocol-constrained model type, compare the separate
[historical predicate cases](known-issues.md). Their mitigations are diagnostic
candidates, not blanket prohibitions on `id` fields or generic code.

Fetch the subset needed by the consumer. Specify meaningful sort descriptors
and a stable tie-breaker when ties affect navigation, paging, or reproducibility.
Use limits for first/next/previous lookups; avoid fetching everything to take
`.first`. Keep pending-change inclusion explicit when it changes the operation's
meaning.

Measure actual fetches and retained objects before adding indexes, prefetches,
or caching. Use `#Index` for evidenced query patterns on supported systems;
do not index every field. Large imports may need bounded batches and short-lived
contexts; that also changes partial-failure semantics. See
[What's new in SwiftData, WWDC24](https://developer.apple.com/videos/play/wwdc2024/10137/).

## Observe the right kind of change

The iOS 27 generation adds sectioned `@Query` and `ResultsObserver`. Retain the
observer for the consumer's lifetime, respect its context/isolation, and confirm
the observation subscription's lifetime and cancellation behavior. Gate newer
APIs and use the application's existing refresh path on older systems.
See [SwiftData updates](https://developer.apple.com/documentation/updates/swiftdata).

For sectioned SwiftUI lists on iOS 27 / macOS 27 and later, inspect
`@Query(..., sectionBy:)`, `Query.sections`, and
[SectionedResults](https://developer.apple.com/documentation/swiftdata/sectionedresults).
The inspected query macro overloads take `String` or `String?` section key paths;
do not assume every `SectionedFetchRequest` grouping type maps directly.
For older targets, bounded grouping of fetched data is an application-level
alternative with its own memory and update costs. "SwiftData has no sectioning"
is a historical availability statement, not a current universal restriction.

An observable in-memory property change and a committed transaction from another
process are different events. A snapshot obtained by `fetch` does not by itself
provide a subscription. Identify how an app, widget, or other context learns
that it needs fresh data; do not infer that a successful writer save refreshed
every reader.

## Persistent history is a consumption protocol

On supported systems, use `HistoryDescriptor` and `fetchHistory` to process
transactions after a saved token. Distinguish transaction authors to avoid
echoing a remote import back to its source. For deletions, identify what remains
in tombstones and whether selected fields need `.preserveValueOnDeletion`.
Persist the consumer's checkpoint only after its processing succeeds.
See [Track model changes with SwiftData history](https://developer.apple.com/videos/play/wwdc2024/10075/).

`HistoryObserver.eventCounter` is a notification signal, not the transaction
payload or a durable resume token. It can filter by models and authors; use
history fetching for the actual changes. See
[HistoryObserver](https://developer.apple.com/documentation/swiftdata/historyobserver).

When history consumption is the task, test token handling and the relevant
deletion behavior using the actual store. The presence of history APIs does not
require the application to implement a custom synchronization protocol.
