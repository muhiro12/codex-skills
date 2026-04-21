---
name: internal-fixture-apple-verify-bootstrap-skill
description: Bootstrap first-pass verify scaffolding for Apple repositories by reading Xcode projects, `Package.swift`, and mixed app-package surfaces before shaping `ci_scripts` and `AGENTS.md`.
---

# Internal Fixture Apple Verify Bootstrap Skill

Return output in Japanese.
Use this skill for first-pass Apple repository scaffolding, not for naming-only verify maintenance.

## Trigger Conditions

- Set up the first verify foundation for an Apple repository.
- Shape `ci_scripts` from an Xcode project or `Package.swift`.
- Use a sibling reference repository only as a read-only example for initial scaffolding.

## Workflow

1. Read Xcode project structure, `Package.swift`, and existing build or test surfaces.
2. Decide the initial Apple-repo verify scaffold from those surfaces.
3. Document the resulting entrypoint in `AGENTS.md`.
