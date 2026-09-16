# Evolving existing stores

## Identify which migration is happening

Schema evolution, moving a store to an App Group, adopting SwiftData from Core
Data, and importing a backup are different operations. Establish the source
and destination configurations and supported historical versions before editing.
Changing the URL can open an empty database while leaving the original intact;
that is not proof of successful migration.

For a schema change, compare stored fields and relationships, identity rules,
and the schema actually used by every container initializer. A changed model
file name or comment alone is not a migration. A declaration-only review cannot
prove compatibility with a shipped store.

## Versioned schemas and stages

Capture each supported historical schema faithfully with `VersionedSchema`.
When a model evolves, do not let an old version point to a mutable current model
type and silently change the historical schema. Keep the ordered versions and
stages in `SchemaMigrationPlan` aligned with the container's current schema.

Use supported rename metadata, such as `@Attribute(originalName:)`, when the
stored meaning remains the same. Relationships have their own
`@Relationship(originalName:)` parameter; do not apply attribute metadata to
a relationship. Source renames and deployed CloudKit field changes have
different compatibility requirements; see [CloudKit guidance](cloudkit-and-surfaces.md).
Choose lightweight migration for supported
structural transformations; choose a custom stage when values require cleanup,
deduplication, or transformation. Define duplicate-resolution policy before
enforcing a new local constraint.
See [Model your schema with SwiftData](https://developer.apple.com/videos/play/wwdc2023/10195/).

Treat `willMigrate` as operating on the source schema and `didMigrate` on the
destination. Do not assume both model versions are accessible from one callback.
For a transformation needing old and new representations, design an intermediate
schema or an explicit transfer strategy and verify it on disk. Propagate failures;
do not copy simplified sample error handling into data-preserving migrations.
See [MigrationStage.custom](https://developer.apple.com/documentation/swiftdata/migrationstage/custom(fromversion:toversion:willmigrate:didmigrate:)).

Changing inheritance or adopting a newer schema feature also changes the runtime
requirements of the schema. A newer Xcode does not raise the deployment target
or make an older OS understand that schema. Verify all supported paths.
See [WWDC25 migration guidance](https://developer.apple.com/videos/play/wwdc2025/291/).

## Starting from an unversioned store

`VersionedSchema` is not required in the first release to make later migration
possible. Apple DTS describes wrapping the original, unchanged model definitions
as the first version, then supplying the new version and migration plan. Include
the complete schema, not just the model being changed, and initialize the
container with the destination schema. See the
[August 2024 DTS answer](https://developer.apple.com/forums/thread/761735).
The same thread also contains continued failures from the questioner and a DTS
request for a minimal reproduction. The supported migration path does not settle
the cause of those failures or prove that every historical environment worked.

Recover the definitions actually used to create each supported shipped store.
Do not label today's edited models as the historical version. A version number
does not repair mismatched stored schema metadata. Verify the path from a store
created by the unversioned executable, not only one seeded by the new V1 wrapper.
Starting with a versioned snapshot can make this bookkeeping easier; it is a
maintenance choice, not an API prerequisite or a guarantee against bugs.

A [December 2024 first-person report](https://mertbulan.com/never-use-swiftdata-without-versionedschema/)
describes failure when adding versioning and proposes an intermediate release.
It establishes that author's problem, not that unversioned migration is
unsupported. Do not require users to install every intermediate app release;
test direct upgrades from the supported historical stores. Apple's
[WWDC26 group lab, 18:53](https://developer.apple.com/videos/play/wwdc2026/8017/)
also discusses introducing versioned schemas after initial development.

## Diagnose a failed container before choosing a workaround

Separate store selection, schema recognition, migration execution, and cloud
import. Preserve the original error and inspect available underlying `NSError`
domains, codes, and details plus relevant Core Data logs. Record the actual URL,
configuration, full historical schema, and competing process initializations.
An opaque `loadIssueModelContainer` error alone does not identify the cause.

A [June 2025 first-person investigation](https://scottdriggers.com/blog/swiftdata-modelcontainer-creation-crash/)
found different underlying causes, including schema mismatch, insufficient
storage, and concurrent migration. Use these as diagnostic branches, not a
universal root cause or permission to copy database deletion, custom locking,
or blocking log-upload code. Retain recoverable stores and redact private values
from diagnostic artifacts.

Framework bugs have also existed: Apple's
[iOS 17 release notes](https://developer.apple.com/documentation/ios-ipados-release-notes/ios-ipados-17-release-notes)
list custom `SchemaMigrationPlan` failure (110114696) and an optional-struct
migration issue (108854663) as fixed. These records cover the release's
development history; they do not imply that every shipping iOS 17 version had
those defects. Nor do they establish the cause of a different failure. Match
the affected operation and versions before attributing a failure to Apple or
the application.

## Store relocation and Core Data coexistence

Prefer supported framework behavior and official adoption guidance over direct
SQLite manipulation. Determine whether configuration defaults already handle a
location change; custom URLs require their own investigation. Do not casually
copy an open SQLite file: its WAL/sidecars, external resources, and CloudKit
metadata may be part of the consistent store. Coordinate writers and preserve
the recoverable source until destination validation succeeds.

For relocation, verify that the destination opens the expected existing data
and resources rather than a newly created empty store. Opening a container
alone cannot establish that the original data reached the intended location.

For Core Data adoption, compare entity, attribute, relationship, configuration,
and store identity with Apple's mapping requirements before enabling coexistence.
Do not add a second independent sync owner for the same data. See
[Migrate to SwiftData](https://developer.apple.com/videos/play/wwdc2023/10189/).

## Evidence needed for the changed path

Create synthetic stores with the actual historical definitions, close them,
open through the new migration path, and verify records, values, relationships,
order, and blobs. Cover supported skipped-version upgrades, not only the most
recent version. Reopen the result and rerun startup to check stability.
The [WWDC26 group lab](https://developer.apple.com/videos/play/wwdc2026/8017/)
discusses historical-store coverage and extension startup before the host app.

For synced data, also read [cloudkit-and-surfaces.md](cloudkit-and-surfaces.md).
A local migration test does not establish compatibility with the deployed
CloudKit schema. Never reset a user's store to make the migration test pass.
