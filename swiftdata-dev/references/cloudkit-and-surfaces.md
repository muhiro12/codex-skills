# CloudKit and multiple entrypoints

## Inspect configuration before changing the model

Record the store URL or group-container selection, schema, CloudKit database
selection, relevant entitlements, and target-specific initialization. A capability
can cause automatic CloudKit selection; use `cloudKitDatabase: .none` for
deliberately local test/preview stores. Keep development and production CloudKit
environments distinct.

Automatic CloudKit sync has a narrower model contract than a local store:

| Model feature | CloudKit-backed requirement |
| --- | --- |
| Attributes | Optional, or supplied with a compatible model default; an initializer argument default alone is not schema evidence |
| Relationships | Optional, with resolvable inverses; specify an inverse when inference is ambiguous |
| Uniqueness | Unique constraints are unsupported; `#Unique` does not make them cloud-compatible |
| Delete rules | `.deny` is unsupported |
| Related changes | Synchronization is not atomic; related records may arrive separately |

These storage constraints do not require every scalar property to be optional
or determine the app's validation and editing architecture.
See [Syncing model data across a person's devices](https://developer.apple.com/documentation/swiftdata/syncing-model-data-across-a-persons-devices)
and [Creating a Core Data Model for CloudKit](https://developer.apple.com/documentation/coredata/creating-a-core-data-model-for-cloudkit).
The uniqueness and relationship restrictions predate SwiftData; Apple's
[WWDC22 schema session](https://developer.apple.com/videos/play/wwdc2022/10120/)
describes them for Core Data with CloudKit. That history explains the storage
constraint without establishing how fully early SwiftData materials explained it.
Attribute-default validation also appears in the dated
[CloudKit migration report](known-issues.md#cloudkit-startup-during-migration);
its startup workaround later failed on another runtime.

## Local save and remote convergence

Do not present `save()` returning as proof that another device has the data.
During sync diagnosis, distinguish local fetch results, pending imports, and
partially arrived relationships. A fetch-then-insert check on one device does
not establish distributed uniqueness. Check local save, remote export/import,
and reader refresh separately, including the relevant offline/account state.
Local rollback cannot rewind changes exported by earlier commits.

Once promoted, the CloudKit production schema is additive; local schema migration
alone does not authorize incompatible server-schema changes. Inspect the deployed
schema and release compatibility before planning removals or representation
changes. Renaming a Swift property while retaining its persisted identity through
supported `originalName` metadata is a different operation from renaming a
production CloudKit field. Production record types and fields cannot be renamed
or deleted. Do not claim either that every source rename is forbidden or that a
successful local rename proves cloud compatibility. Check existing local stores,
fresh imports from the deployed cloud schema, and older supported clients.

If product behavior requires uniqueness across devices, define duplicate and
conflict semantics before selecting an application-level strategy. A UUID field
or local fetch-before-insert check alone does not enforce one record per domain
key across offline devices.

Treat development-schema initialization and production deployment as
separate actions with their own authorization. Do not deploy or reset CloudKit
as part of an ordinary local implementation check.

## App Groups, widgets, and App Intents

An App Group provides shared storage access, not a shared `ModelContext`. Each
process needs a compatible schema/configuration and its own context. Verify
entitlements and resolved locations across readers and writers. Decide which
process owns migration and sync; include the case where a widget launches before
the updated main app. Do not assume an extension's execution budget permits
migration, large fetches, or a complete network round trip.
See the [SwiftData group lab](https://developer.apple.com/videos/play/wwdc2026/8017/).

For widget and App Intent lookups, resolve a model in that process's context
and handle deletion since an identifier was selected. Do not pass a live model
instance between processes or assume an identifier from an independent store
resolves locally. Consult current WidgetKit/App Intents guidance for their
execution and refresh behavior; this skill does not prescribe a shared use-case
layer or companion-device transfer strategy.

Build and test affected surfaces separately. App-only compilation does not
establish signed App Group access, extension startup, intent execution, or
two-device CloudKit behavior.
