---
name: internal-fixture-release-risk-skill
description: Assess release-blocking risk for the current repository before shipping. Use when a reviewer needs a block or proceed decision from the latest tag range.
---

# Internal Fixture Release Risk Skill

Return output in Japanese.

## Trigger Conditions

- Review release-blocking risk before shipping.
- Check whether the latest tag range looks safe to release.

## Workflow

1. Resolve the latest release range.
2. Review durable release risk and summarize a block or proceed decision.
