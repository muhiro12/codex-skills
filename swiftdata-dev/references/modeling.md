# Models, identity, and relationships

## Inspect persisted fields

For a stored field, inspect its declaration, initializer, defaults, optionality,
and existing values. Constructor defaults do not establish the default for an
existing row during migration. Treat `@Transient`, computed properties, and
stored properties separately. A source review is not a guarantee about the
macro-generated schema. Check it with the actual SDK and store when relevant.

Apple's [modeling session](https://developer.apple.com/videos/play/wwdc2023/10195/)
explains attribute options, relationship rules, and preserving renamed fields.

## Identity is a contract

`PersistentIdentifier` locates a model in its persistence domain; a new model
can have a temporary identifier before its first save. Do not assume its encoded
form is a portable identity across independent stores, restore operations, or
devices. Identify whether a lookup concerns this store's persistent identifier
or an explicitly stored application identifier before changing its predicate.
See [insert(_:)](https://developer.apple.com/documentation/swiftdata/modelcontext/insert(_:)).

Uniqueness constraints can produce upsert behavior, rather than a validation
error suitable for UI. Decide what duplicate input means before adding
`@Attribute(.unique)` or `#Unique`. Local constraints are not distributed
deduplication, and CloudKit-backed models have additional restrictions in
[cloudkit-and-surfaces.md](cloudkit-and-surfaces.md).

For a crash involving the implicit model `id` in a predicate, see the historical
[identifier predicate case](known-issues.md#identifier-predicate-crash-in-incomes).
That case does not prohibit an application's explicitly persisted `id` field.

## Relationship behavior

Choose inverses and delete rules from lifecycle meaning: deleting an owned
component may be appropriate; deleting a shared attachment or category may not.
Check both ends of each relationship and deletion from each user entrypoint.
Only relate model instances resolved into the intended context/store graph.

A bidirectional relationship does not require reciprocal `inverse:` annotations
on both properties. Apple's [relationship example](https://developer.apple.com/documentation/swiftdata/defining-data-relationships-with-enumerations-and-model-classes)
declares the inverse on one end. If annotating both ends produces a macro cycle,
retain one explicit inverse; that does not remove the reverse relationship.
See the [minimal compiler case](compatibility.md#reciprocal-inverse-annotations).
Do not generalize this failure to all uses of `@Relationship` on both ends;
other options such as delete rules have their own meaning.

Verify the required membership and ordering after save/reopen and after a failed
mutation. The array immediately after assignment alone is not persistence
evidence. A recorded cascade/rollback failure and its deletion-order workaround
are described in the [rollback case](known-issues.md#rollback-snapshot-crash-in-cookle);
do not apply that workaround to unrelated graphs without checking the failure.

## Value types and inheritance

Persist enum representations deliberately. Changing cases or raw values can
affect existing records and archives; test decoding historical values instead
of assuming source compatibility implies data compatibility.

The iOS 27 generation adds `@Attribute(.codable)` for encoded values, including
external types SwiftData cannot inspect. Their contents are opaque to queries
and sorting, and internal type changes do not trigger schema migration. Keep
their decoder compatible with stored payloads. Prefer ordinary modeled fields
when filtering or indexing their contents matters.
See [WWDC26](https://developer.apple.com/videos/play/wwdc2026/274/).

Model inheritance is available from the iOS 26 generation. Use it for a real
"is-a" relationship with meaningful base and subtype queries. Shared property
names alone are not sufficient reason to introduce persistent inheritance.
Register the relevant model types and account for existing stores and every
supported runtime before adopting it. See
[inheritance and migration](https://developer.apple.com/videos/play/wwdc2025/291/).

Protocol conformance for shared behavior is a separate question from persistent
inheritance and store-query translation. Neither the existence of inheritance
nor a generic predicate failure establishes that models cannot conform to
protocols. Narrow query-specific failures at the
[concrete predicate boundary](known-issues.md#concrete-predicate-construction-in-cookle).
