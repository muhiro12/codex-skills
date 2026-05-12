# Apple Sample Code Rubric

Use this rubric when deciding how strongly to apply an Apple sample project to a current repository.

## Severity

- `blocking`: Current implementation conflicts with a current Apple sample and the relevant framework documentation in a way that can break required framework behavior, entitlements, lifecycle, data flow, or system integration.
- `warning`: Current implementation works but diverges from Apple's sample structure enough to risk maintenance drift, missed platform behavior, weaker state ownership, or nonstandard framework adoption.
- `note`: Sample shows a useful pattern, but the current repository has a valid reason to differ.

## Checks

### 1. Currentness

- Check the Apple page, WWDC year, SDK requirement, and deprecation notes before relying on cached source.
- Treat pages that explicitly warn about outdated practices as historical only.
- If cached source is stale, propose refresh before making a strong claim.

### 2. Project Shape

- Inspect app entry points, scenes, root navigation, target layout, package manifests, entitlements, assets, fixtures, previews, and tests.
- Extract architecture-level patterns rather than isolated snippets.
- Note what Apple kept in app targets versus libraries, extensions, widgets, intents, or packages.

### 3. Framework Adoption

- Check how the sample wires framework lifecycle, capabilities, permissions, delegates, async streams, environment values, model containers, stores, or system surfaces.
- Prefer framework setup that matches the sample unless the current repository has a concrete product or architecture reason to differ.

### 4. Data Flow and State Ownership

- Identify the source of truth, observation model, environment injection, persistence boundary, async loading, and mutation paths.
- Distinguish demo data/fixtures from the reusable state-management pattern.

### 5. UI and Platform Adaptation

- Use samples to understand app shell and platform adaptation, then use `$apple-hig-ui-guardian` for HIG compliance.
- Compare iPhone, iPad, macOS, watchOS, widgets, and visionOS coverage only when the sample and target app both support those surfaces.

### 6. Swift and Code Quality

- Use samples to understand Apple framework usage, then use `$swift-code-guardian` for Swift API design, concurrency safety, access control, and package boundaries.
- Do not copy simplified sample error handling, fake services, or demo-only abstractions into production without review.

### 7. Applicability

- Match sample assumptions against the current app: minimum OS, app lifecycle, persistence model, authentication, offline needs, product scale, and target platforms.
- If the sample solves a narrower problem, adopt only the part that fits.

## Review Questions

- Is the sample current enough for the target SDK and feature?
- Which project-level pattern is Apple demonstrating?
- Which files prove the pattern: app entry, root view, model, framework adapter, entitlement, manifest, test, or fixture?
- What is sample-only scaffolding that should not be copied?
- Does HIG, Swift guidance, or framework documentation override the sample?
- How should the current repository adapt the pattern without importing sample-specific product meaning?
