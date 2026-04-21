---
name: track-developer-principles
description: Capture, maintain, harvest, and consult the user's cross-repository design judgments, engineering principles, product or business heuristics, and changes in thinking over time. Use when the user explicitly wants to record a durable idea, tradeoff rule, or rationale; when ordinary repository conversations reveal a durable cross-repository preference even without an explicit recording request; when the user says their thinking has changed and wants that evolution preserved; or when Codex should load the stored principles before proposing or implementing repository-specific work.
---

# Track Developer Principles

## Overview

Use this skill as a cross-repository memory for the user's durable judgment.
Keep the current stance easy to consult, keep the change history explicit, and avoid polluting product repositories with personal operating notes unless the user asks for a different storage location.
Treat this skill as a loop between daily repository work and a shared personal principle archive: harvest durable thinking from normal work, then feed that stored judgment back into future work across repositories.

## Storage Files

- `references/current-principles.md`
  - Treat this as the current source of truth.
  - Keep only the user's current durable views.
  - Group entries by domain and keep wording concise.
- `references/evolution-log.md`
  - Treat this as the timeline of additions, revisions, deprecations, and clarifications.
  - Append a dated entry whenever the current stance changes or a new durable principle is introduced.

## Workflow

1. Determine the mode.
- `capture`: add a new durable principle or rationale.
- `harvest`: derive a candidate durable principle from ordinary repository discussion or decision-making.
- `revise`: update the current stance because the user's thinking changed.
- `consult`: read the stored principles and apply them to the current task without modifying the record.

2. Read the current source of truth before writing.
- Read `references/current-principles.md` first.
- Read `references/evolution-log.md` when the user mentions change over time, prior decisions, or possible tension with an older stance.

3. Scan recent repository conversation when working inside a repo.
- During repository-specific work, watch for statements that sound like reusable judgment rather than local implementation chatter.
- Good harvest candidates include repeated tradeoff preferences, quality bars, naming or architecture heuristics, product prioritization rules, and business reasoning that the user frames as generally applicable.
- If the user only discussed a local tactical choice, do not lift it into the shared archive.

4. Decide whether the thought is durable enough to record.
- Record cross-repository judgments, design heuristics, business rules of thumb, quality bars, tradeoff preferences, collaboration principles, and recurring decision criteria.
- Do not record one-off tasks, repository-local implementation details, temporary debugging notes, or speculative comments that the user did not endorse as a durable stance.

5. Normalize the record.
- Rewrite the idea as a reusable principle, not as conversation residue.
- Capture the rationale and the tradeoff it is meant to optimize.
- Note affected domains such as `product`, `architecture`, `implementation`, `workflow`, or `business`.

6. Update both layers when needed.
- Update `references/current-principles.md` so it reflects only the latest endorsed stance.
- Append to `references/evolution-log.md` with the absolute date in `YYYY-MM-DD` format whenever the principle is added, revised, narrowed, broadened, or deprecated.

7. Reuse the record in later work.
- When helping inside any repository, consult `references/current-principles.md` before making major design suggestions if the task depends on judgment, tradeoffs, prioritization, maintainability, UX direction, or business intent.
- State explicitly when a proposal follows a recorded principle, stretches it, or conflicts with it.
- If the current repository task reveals a new durable principle while work is underway, update the shared archive after the user has clearly stated or endorsed that principle.

## Harvesting From Repository Conversations

- Treat the user's explicit statements as the strongest signal.
- Treat repeated choices with consistent rationale as a weaker but still usable signal when the cross-repository intent is clear.
- If a possible principle is still ambiguous, surface it as a candidate summary instead of silently storing it as a settled rule.
- Prefer short durable formulations such as `prefer X because Y` over chat-shaped notes.
- After harvesting from normal repo work, mention briefly that the archive was updated so the user can correct it if needed.

## Consulting During Repository Work

- Before major design or implementation recommendations, read `references/current-principles.md` if the task turns on judgment rather than pure mechanics.
- Map the relevant stored principles to the concrete repo decision you are making.
- When a repository-local constraint forces a different choice, say so explicitly instead of pretending the archived principle did not exist.
- If no stored principle applies, proceed normally and only create a new principle when the conversation actually establishes one.

## Recording Rules

- Prefer a small number of durable principles over a noisy journal.
- Keep each principle concrete enough to guide action.
- Preserve the user's wording when it carries precise nuance, but compress repetition.
- Separate the current rule from the history of how it changed.
- If the user is unsure, record it as a tension or emerging preference rather than a settled principle.
- If the new statement contradicts an older principle, update the old current entry instead of keeping both active, and explain the shift in `references/evolution-log.md`.
- When harvesting from repo work, do not turn a single implementation accident into a principle.

## Current Principles Format

In `references/current-principles.md`, use this entry shape:

### Short principle title
- Principle: one current rule or preference
- Why: what it optimizes or prevents
- Applies to: domains or common decision surfaces
- Last confirmed: `YYYY-MM-DD`

Add an `Exceptions:` line only when the boundary is important.

## Evolution Log Format

In `references/evolution-log.md`, append entries in reverse chronological order using this shape:

## YYYY-MM-DD
- Change: added, revised, clarified, or deprecated principle title
- Previous stance: short summary or `none`
- New stance: short summary
- Why changed: concrete reason, evidence, or tradeoff shift
- Expected impact: how future repo work or business decisions should change

## Guardrails

- Keep this record outside product repositories unless the user explicitly wants a copy in a repo.
- Do not fabricate principles that the user did not actually express or clearly imply.
- Do not convert every preference into doctrine; favor stable decision criteria.
- Let explicit current-task instructions override older archived principles when they conflict.
- When the stored principles are silent or conflicting, say so plainly and ask the user or record the new clarification if they provide one.

## Verification

- The record reflects a durable cross-repository judgment, not a one-off local note.
- `references/current-principles.md` contains only the latest active stance.
- `references/evolution-log.md` captures the historical change with an absolute date when applicable.
- Future Codex work can understand the principle without re-reading the full chat.

## Workflow Alignment (skills-batch-auditor)

- Return output in concise, polite Japanese.
- Do not invent architecture or product features.
