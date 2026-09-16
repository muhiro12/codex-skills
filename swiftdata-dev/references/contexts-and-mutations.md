# Context ownership and mutation boundaries

## Choose the owner before choosing async syntax

A `ModelContainer` describes the schema and storage configuration. A
`ModelContext` owns a working graph and pending changes. The container's
`mainContext` is main-actor isolated. For an isolated persistence worker,
consider `@ModelActor` and its context rather than sharing a UI context inside
`Task.detached`. An unstructured `Task` does not itself make database work run
off the main actor. Actor isolation also does not promise a particular thread.
See [ModelContainer](https://developer.apple.com/documentation/swiftdata/modelcontainer)
and [ModelActor](https://developer.apple.com/documentation/swiftdata/modelactor).

Pass a stable identifier or a `Sendable` snapshot to another actor; fetch the
model there and handle it having disappeared. Do not make live model graphs
`@unchecked Sendable` to bypass diagnostics. After an `await`, recheck assumptions
that concurrent work could have invalidated. Bound long imports and avoid
retaining every imported model in a UI-owned context.

## Editing and cancellation

Inspect the actual context's `autosaveEnabled` value. It defaults to false for
a directly created context, while SwiftData enables it for `mainContext`.
Window and view lifecycle events can trigger autosave. Binding a form directly
to a registered model can therefore persist edits before a Save button is tapped.
See [autosaveEnabled](https://developer.apple.com/documentation/swiftdata/modelcontext/autosaveenabled).

For a reported cancellation problem, inspect whether edits were already saved
and which other changes the same context tracks. A context-wide rollback can
discard unrelated pending edits and cannot restore changes committed by autosave.
Fix the context/save behavior required by the existing UI contract; SwiftData
does not require every app to use a value draft or a dedicated editing context.

## Commit and failure

Trace all saves, including autosave, before interpreting a failed mutation.
Multiple successful saves create multiple committed states; a later error does
not make the whole sequence uncommitted.

`transaction(block:)` runs a closure and saves pending changes. It is not an
isolated child context, and it cannot transactionally include network calls,
files, or notification scheduling. On failure, use the operation's defined
recovery strategy. `rollback()` discards pending context changes and clears
the undo stack; it cannot reverse an earlier successful save.
See [transaction(block:)](https://developer.apple.com/documentation/swiftdata/modelcontext/transaction(block:))
and [rollback()](https://developer.apple.com/documentation/swiftdata/modelcontext/rollback()).

Preserve the original fetch/save error during diagnosis. Distinguish registered,
inserted, deleted, and discarded models before dereferencing them after recovery.
For an error inside `rollback()` rather than the preceding save, compare the
[recorded cascade/snapshot failure](known-issues.md#rollback-snapshot-crash-in-cookle).
The API's intended rollback semantics do not establish that a particular
framework version handles every graph correctly. See
[verification.md](verification.md) for testing the exact failure path.
