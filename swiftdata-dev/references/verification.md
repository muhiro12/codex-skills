# Verifying SwiftData behavior

Choose evidence for the framework behavior being changed or investigated.
These are diagnostic methods, not an application architecture or a requirement
to introduce a backup feature, a shared library, or a particular test layout.

| Behavior | Evidence that addresses it |
| --- | --- |
| Predicate translation and matching | Execute the descriptor against the intended store; compiling the macro alone is insufficient |
| Pending inserts, updates, deletes, and rollback | Inspect the graph before and after the exact operation, including unrelated pending changes if the context is shared |
| Disk durability and relationship recovery | Save to a temporary disk store, release its owners, reopen, and inspect required values and links |
| Schema migration | Open synthetic stores made from supported historical definitions through the new migration path |
| External binary storage | Reopen and read the actual payload, not just the parent record or byte-count metadata |
| Another process or CloudKit | Observe the affected reader or device; a local save or in-memory test does not prove propagation |

## Reproduce a failure before generalizing it

Capture the failing operation, error/stack, model declarations, store type,
configuration, and Xcode/OS versions. Reduce the reproduction without removing
the relationships or save sequence that triggers it. Keep suspected causes
separate from facts demonstrated by the reproduction.

Use synthetic data and a disposable store with `cloudKitDatabase: .none` unless
cloud behavior itself is under test. Test the original and changed operation
against equivalent fixtures. A successful run of the changed code alone does
not establish that the old code failed, or why it failed.

The [Cookle rollback case](known-issues.md#rollback-snapshot-crash-in-cookle)
illustrates why a simple graph or an in-memory-only test can miss a failure
found with a populated disk-backed graph. Its record includes a before/after
result; the other cases have weaker evidence and are labeled accordingly.

## Failure injection and reopen checks

Injecting an error at the save boundary can exercise the caller's rollback
path. It is not a simulation of every error inside `save()`, actual disk
exhaustion, process termination, or CloudKit conflict. Name the injected
boundary and avoid claiming those other failures were tested.

When the operation promises to preserve existing data, compare the affected
fields, relationship membership, required ordering, and binary payloads in the
recovered context and a fresh container. Counts alone cannot show that a graph
was restored correctly. Use the application's existing representation for the
comparison; no particular archive format is required.

`@Attribute(.externalStorage)` can place a binary payload outside the main
store file. A SQLite-only copy is therefore not sufficient evidence of a
complete store transfer. Check payload readability after the actual transfer
and reopen. See
[externalStorage](https://developer.apple.com/documentation/swiftdata/schema/attribute/option/externalstorage).

## Record the result and its limits

State which symptom changed, what still fails, and which configurations were
tested. Distinguish a current reproduction from an earlier report or source
inspection. Do not mark an incident fixed for newer SDKs without retesting, or
recommend abandoning a design merely because an old commit reverted it.

Retain the original error and recoverable store when initialization fails.
Separate entitlement/location problems, schema incompatibility, and runtime
failures. A successful preview, fresh empty store, or build cannot substitute
for the failing persistence path.
