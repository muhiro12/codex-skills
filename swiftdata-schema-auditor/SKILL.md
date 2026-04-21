---
name: swiftdata-schema-auditor
description: Inspect SwiftData schema definitions in the current repository and turn them into a human-readable Japanese review. Use this skill when you need to explain or audit `@Model` entities, persisted properties, defaults, optionality, `@Relationship`, inverse relationships, delete rules, `@Attribute`, `@Transient`, computed vs persisted fields, schema coupling, or SwiftData migration risk.
---

# SwiftData Schema Auditor

## Overview

Use this skill for read-only inspection and design review of SwiftData model code.
Keep the core instructions in this file portable across agent runtimes where practical; platform-specific metadata can live beside the skill.
Default explanation language is concise, practical Japanese. Keep code identifiers, type names, attributes, and file names in English.

## Trigger Conditions

Use this skill when the user asks to:

- visualize or explain a SwiftData schema
- list entities, stored properties, defaults, optionality, or relationships
- review `Relationship` design, inverse consistency, or delete rules
- find migration hotspots or persistence-modeling risk
- explain how SwiftData models align with the current app architecture

## Workflow

1. Resolve scope.
- Use the user-provided repository path when present.
- Otherwise, inspect the current workspace root.
- Stay read-only unless the user explicitly asks for code changes.

2. Discover SwiftData-related sources.
- Search for schema surfaces first:

```bash
rg -n '@Model|@Relationship|@Attribute|@Transient|VersionedSchema|SchemaMigrationPlan|MigrationPlan|ModelContainer|ModelConfiguration|Schema\\(' /path/to/repo
```

- Then narrow to relevant Swift files:

```bash
rg --files /path/to/repo | rg '\.swift$'
```

- Ignore build artifacts, generated directories, dependency checkouts, and package caches unless the user explicitly asks to include them.

3. Identify entity candidates and persistence hints.
- Treat each type annotated with `@Model` as an entity candidate.
- Inspect stored properties that appear persisted by source code.
- Inspect `@Attribute`, `@Relationship`, `@Transient`, raw-value enums used by stored properties, custom initializers, and versioned schema declarations when present.
- Distinguish source facts from inference. If macro expansion is not visible, describe the result as source-based inference rather than guaranteed storage truth.

4. Build the entity summary.
- For each entity, capture:
  - entity name
  - file path
  - persisted properties
  - property type
  - optional vs non-optional
  - inline default value when visible
  - initializer-only default when visible and clearly constructor-scoped
  - computed / derived / helper / static properties that appear non-persistent
  - relationships, inverse relationships, delete rules, and collection shape when identifiable
  - identity hints such as `id`, `UUID`, `@Attribute(.unique)`, or natural-key assumptions

5. Review relationship design.
- Infer one-to-one, one-to-many, and many-to-many style patterns from scalar vs collection properties and the matching side when present.
- Check whether inverse relationships appear symmetric and intentional.
- Call out collection relationships that may rely on array ordering or unstable graph mutation semantics.
- Flag delete rules that look dangerous for long-lived data, especially wide `cascade`, ambiguous `nullify`, or missing inverse on tightly coupled graphs.
- Call out cyclic references or dense relationship clusters that may complicate maintenance and migration.

6. Review schema quality from an architecture perspective.
- Check naming clarity and whether model names map cleanly to app concepts.
- Check optionality consistency and whether defaults appear to hide invalid states.
- Check for mixed responsibilities inside one model.
- Check for over-denormalization, under-modeling, or business logic leaking into persistence structure.
- Check uniqueness and identity assumptions, including whether duplicates are possible by accident.
- Check migration hotspots such as:
  - non-optional property additions without obvious defaults
  - enum/raw-value persistence that may be brittle if cases evolve
  - relationship cardinality changes
  - delete-rule changes
  - renames that lack versioned schema or migration structure
- If widgets, intents, watch targets, or extensions are present, mention tight coupling that may make cross-target reuse harder.

7. State uncertainty explicitly.
- If an inverse relationship cannot be confirmed from available code, say so.
- If a value is likely persisted but hidden behind helper abstractions, say "ambiguous" rather than inventing details.
- If no SwiftData models are found, report that clearly and list the searched signals.

## Interpretation Rules

### Persisted vs Non-Persistent

- Treat obvious stored properties inside `@Model` types as persisted candidates unless `@Transient`, computed accessors, `static`, or other source evidence suggests otherwise.
- Treat computed properties, helper methods, and formatting/state helpers as non-persistent unless there is explicit evidence otherwise.
- When defaults are only visible in initializers, label them as constructor defaults, not declaration defaults.

### Relationship Review

- Use scalar reference plus matching scalar reference as a likely one-to-one pattern.
- Use scalar reference plus collection reference as a likely one-to-many pattern.
- Use collection on both sides as a likely many-to-many pattern.
- If only one side is visible, describe the intended cardinality as inferred and incomplete.

### Migration Risk

- Prioritize risks that can break existing stores or force destructive migration.
- Treat persisted enum/raw-value changes, uniqueness changes, and required-field additions as high-signal migration hotspots.
- Treat relationship graph churn as a practical risk even when the code still compiles.

## Safety / Guardrails

- Do not edit code unless the user explicitly asks for modifications.
- Do not invent schema facts that cannot be inferred from source.
- Prefer file-path-based evidence over generalized SwiftData advice.
- Do not claim actual database column names when only source-level declarations are visible.
- Keep the report practical; focus on the current repository rather than generic theory.

## Output Contract

Return a structured Japanese report with these exact sections:

1. `1) スキーマ概要`
2. `2) エンティティ一覧`
3. `3) Relationshipレビュー`
4. `4) 設計レビュー`
5. `5) 気になる点`
6. `6) 改善候補`

Use this content contract:

- `1) スキーマ概要`
  - inspected scope or repository path
  - discovered entity count
  - main entities or aggregate roots if inferable
  - whether versioned schema / migration definitions were found
- `2) エンティティ一覧`
  - summarize each entity with entity name and file path
  - list persisted properties with type, optionality, and default visibility
  - list computed / derived / non-persistent properties when relevant
  - list relationships, inverse, delete rule, and collection shape when identifiable
- `3) Relationshipレビュー`
  - summarize one-to-one / one-to-many / many-to-many patterns
  - note inverse consistency, delete-rule risk, cycles, and collection semantics
- `4) 設計レビュー`
  - review naming, optionality, defaults, responsibility split, modeling balance, identity assumptions, migration posture, and architecture fit
- `5) 気になる点`
  - list concrete risks, ambiguities, or suspicious patterns with file-path-based evidence
- `6) 改善候補`
  - list actionable improvements in priority order
  - keep recommendations bounded and tied to observed code

## Response Style

- Use Japanese for explanation.
- Use English for identifiers, type names, attributes, and file names.
- Prefer bullet-style structured summaries over long prose.
- Keep findings concrete and evidence-based.
- If there are no clear issues, say so explicitly and still note residual ambiguity.

## Verification

- Confirm every entity listed is backed by a source file path.
- Confirm persisted vs non-persistent distinctions are marked as inference when necessary.
- Confirm relationship conclusions distinguish confirmed facts from one-sided inference.
- Confirm the report includes at least one migration-focused observation when persistence exists.
- Confirm default mode stayed read-only.
