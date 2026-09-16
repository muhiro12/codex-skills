---
name: swiftdata-dev
description: Design, implement, and debug SwiftData using Apple guidance and evidence-scoped issue reports. Use for models, relationships, migrations, ModelContext isolation, queries, CloudKit integration, or persistence failures. For a read-only schema inventory, prefer swiftdata-schema-auditor when available.
---

# SwiftData Development

Implement and troubleshoot SwiftData using current Apple documentation and WWDC
guidance. Separately recorded application incidents provide diagnostic leads
and scoped workarounds. This is a community-authored skill, not an Apple skill.

## Start with the affected boundary

Inspect the current diff, deployment targets, model declarations, container
configuration, and the callers that read or mutate the affected data. Establish
whether the task changes stored meaning, an existing store, a query, or only
presentation. Keep a review request read-only; implement when requested.

Work within the app's chosen architecture and behavior. An incident from another
app does not justify adopting that app's layers, editing model, domain types,
backup format, or synchronization strategy.

For version-sensitive choices, confirm the selected Xcode/SDK and deployment
targets. If `sync-xcode-skills/state/catalog.md` exists under the active skills
root, consult it for matching Xcode-provided guidance. Otherwise use current
Apple documentation directly. No sibling skill, app checkout, or custom
package is required. Use [sources.md](references/sources.md) for official
entrypoints, availability landmarks, and provenance.

## Read the relevant reference

| Task | Reference |
| --- | --- |
| Feature availability, historical limitations, or an option that appears ineffective | [compatibility.md](references/compatibility.md) |
| Model fields, identity, relationships, Codable, inheritance | [modeling.md](references/modeling.md) |
| Context ownership, actors, save failures, editing and cancellation | [contexts-and-mutations.md](references/contexts-and-mutations.md) |
| Existing-store upgrades, versioned schemas, Core Data adoption, store relocation | [migrations.md](references/migrations.md) |
| Predicates, fetch performance, SwiftUI observation, persistent history | [queries-and-history.md](references/queries-and-history.md) |
| CloudKit, App Groups, widgets, App Intents, other processes | [cloudkit-and-surfaces.md](references/cloudkit-and-surfaces.md) |
| Disk durability, rollback, external resources, persistence tests | [verification.md](references/verification.md) |
| Missing data after adoption, rollback crashes, or predicate failures resembling recorded incidents | [known-issues.md](references/known-issues.md) |

Read only the references needed for the task. For example, a rename affecting a
synced model needs modeling, migrations, and CloudKit guidance; a bounded fetch
usually needs only queries. General SwiftUI design and non-SwiftData CloudKit
implementations remain outside this skill's focus.

## Constraints that apply across tasks

- Preserve store identity and existing data. A failed container initialization
  is an error to diagnose, not permission to delete the store or silently
  substitute an empty in-memory database.
- Identify who owns the context and commit. `save()` and `rollback()` act on
  pending context changes, including unrelated edits if they share that context.
  Autosave does not define a user-confirmed transaction boundary.
- Respect model isolation. Pass identifiers or `Sendable` values across actor
  and process boundaries, then resolve models in the receiving context.
- `rollback()` cannot undo an earlier successful save or arbitrary filesystem
  and network operations. Diagnose the actual failing boundary.
- Verify at the boundary that changed. Compilation and in-memory tests do not
  establish old-store migration, disk durability, or CloudKit convergence.

## Apply incident evidence conditionally

Match the symptom, model/query shape, store configuration, and SDK/runtime before
trying a workaround. Reproduce the failing path and compare the narrow change
when possible. Classify the evidence as a documented restriction, a confirmed
historical bug, a current reproduction, or an unconfirmed report. Separate the
observed symptom from the reporter's proposed cause; an Apple-hosted community
post is not automatically an Apple confirmation. A successful check on a newer
runtime does not establish that an earlier failure was an implementation mistake.
Do not infer that all versions
have a bug, that a reverted design is unsupported, or that a workaround succeeds
beyond its tests.

## Finish with reviewable evidence

Explain the changed behavior, any schema or store-configuration impact, and
the checks actually performed. Link the relevant Apple source for a consequential
API claim. Separate source inspection, build, persistent-store tests, UI behavior,
and device/cloud evidence; state missing evidence without claiming readiness.
Use the repository's verification contract and the available Xcode-native
capabilities, resolving tool actions from the current runtime inventory.
