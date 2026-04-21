---
name: internal-fixture-verify-contract-maintenance-skill
description: Define, audit, and maintain the verify contract for repositories that already have or are adopting `ci_scripts`, keeping entrypoints predictable without broad rewrites.
---

# Internal Fixture Verify Contract Maintenance Skill

Return output in Japanese.
Use this skill for contract maintenance after `ci_scripts` exists or adoption is already decided.

## Trigger Conditions

- Audit whether `AGENTS.md` and verify shells agree.
- Normalize verify naming drift with compatibility-first wrappers.
- Move heavy verification away from commit time without redesigning the initial scaffold.

## Workflow

1. Read `AGENTS.md`, `ci_scripts`, and current hook config.
2. Map the repository's verify contract roles and note drift.
3. Propose or apply low-risk maintenance without introducing Apple-specific bootstrap design.
