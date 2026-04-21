---
name: internal-fixture-repo-specific-dev-skill
description: Develop `ClientPortal/` while treating `../DesignSystem` and `../SharedKit` as read-only references. Use when repo-specific implementation work must stay inside one product repository.
---

# Internal Fixture Repo Specific Dev Skill

Return output in Japanese.

## Trigger Conditions

- Develop `ClientPortal/`.
- Reuse patterns from `../DesignSystem` and `../SharedKit`.

## Workflow

1. Modify only `ClientPortal/`.
2. Treat `../DesignSystem` and `../SharedKit` as read-only references.
