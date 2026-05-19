---
name: track-developer-principles
description: "Capture, maintain, harvest, and consult Hiromu's cross-repository developer principles, including product, architecture, implementation, code quality, business heuristics, and workflow judgment. Use when the user explicitly wants to record or revise a durable developer principle; when ordinary repository conversation reveals reusable development judgment, quality bars, tradeoff preferences, architecture heuristics, or workflow rules even without an explicit recording request; when a plausible but not yet settled developer judgment should be kept as a weighted signal; when the user's thinking has changed; or when current work should load stored principles before judgment-heavy repository work."
---

# Track Developer Principles

## Overview

Use this skill as a cross-repository memory for Hiromu's developer judgment.
This skill is intentionally scoped to development-adjacent judgment: product decisions, architecture, implementation, code quality, business heuristics that affect products, repository workflow, and collaboration with coding agents.
Do not use it as a general archive for life philosophy, personality modeling, broad communication style, or non-development personal beliefs; those belong in a separate future skill if Hiromu asks for one.
Keep the current stance easy to consult, keep the change history explicit, and avoid polluting product repositories with personal operating notes unless the user asks for a different storage location.
Treat this skill as a loop between daily repository work and a shared developer-principle archive: harvest reusable thinking from normal work, weight it honestly, then feed the stored judgment back into future repository decisions.

## Trigger Policy

Trigger this skill proactively when development work depends on judgment, tradeoffs, prioritization, maintainability, UX direction, business intent, architecture, code quality, or repository workflow.
Separate read and write behavior:

- `consult`: trigger frequently without explicit user invocation for judgment-heavy repository work; reading relevant current principles is the default.
- `harvest` / `signal`: trigger during ordinary repository conversation when reusable developer judgment appears; record provisional thoughts as weighted signals when they have likely future value.
- `capture` / `revise`: write `settled` or `strong-default` current principles only when the user explicitly states or clearly endorses a reusable stance.
- Do not treat every invocation as permission to write; pure consultation should stay read-only.
- Do not trigger for purely mechanical edits, one-off local choices, temporary debugging, or repository facts with no reusable judgment.

## Storage Files

- `records/principles/<domain>/current.md`
  - Treat these domain files as the source of truth for current active principles.
  - Keep only the latest active stance for that domain.
  - Use `settled` for confirmed principles and `strong-default` only when the stance is active but not absolute.
- `records/principles/<domain>/signals.md`
  - Store plausible, reusable, not-yet-settled thoughts as weighted signals.
  - Use this for ideas that are too useful to lose but too provisional to become doctrine.
  - Review signals later for promotion, revision, or discard.
- `records/current-principles.md`
  - Keep as a compatibility entrypoint and index for older workflows.
  - It should point to the domain files rather than becoming the only source of truth again.
- `records/evolution-log.md`
  - Treat this as the timeline of additions, revisions, deprecations, promotions, and structural changes.
  - Append a dated entry whenever a current stance changes, a new principle is introduced, a signal is promoted, or an important signal is discarded.

Keep `references/` for static skill documentation only. Keep mutable user-specific principle records under `records/`, which is skill-owned local data and should stay ignored by git. If legacy records still exist under `references/`, migrate them to the same relative paths under `records/` before writing new records, and leave unrelated static reference files in place.

Migration check:

- After this skill is installed or updated from GitHub, run `python3 scripts/migrate_skill_data.py --only principles` from the skills root when `records/` is missing or when legacy ignored files may still exist under `references/`.
- If the dry-run reports copyable legacy files, run `python3 scripts/migrate_skill_data.py --only principles --apply` before reading or writing principle records.
- The migration copies only missing targets and never overwrites conflicting files. Resolve conflicts manually before treating `records/` as complete.

Initial domains:

- `meta`: rules about this archive, evidence boundaries, and skill behavior.
- `product-business`: product judgment, localization, naming, pricing, business heuristics, and market-facing tradeoffs.
- `architecture-system-design`: reusable architecture, platform foundations, target boundaries, data modeling, and system shape.
- `implementation-code-quality`: Swift, Apple UI, framework usage, design systems, testing posture, code review, and technical quality bars.
- `workflow-collaboration`: agent workflow, repository verification, collaboration rules, and development process.

## Weights

- `settled`: an explicitly confirmed durable principle. Respect it by default in later work unless direct current instructions or hard repository constraints override it.
- `strong-default`: a strong preference or recurring pattern. Apply it when the current task is silent, but name the tradeoff when it materially affects the recommendation.
- `emerging`: a plausible candidate. Use it as context for suggestions or questions, but do not silently treat it as a rule.
- `deprecated`: a former stance that should not guide new work except as history.
- `discarded`: a captured signal that should not guide new work.

## Workflow

1. Determine the mode.
- `capture`: add a settled or strong-default developer principle that the user clearly endorsed.
- `harvest`: derive a reusable developer-principle candidate from ordinary repository discussion or decision-making.
- `signal`: record a plausible but not-yet-settled thought with a weight and review trigger.
- `revise`: update the current stance because the user's thinking changed.
- `consult`: read the stored principles and apply them to the current task without modifying the record.

2. Resolve the domain before writing.
- Choose exactly one primary domain for each principle or signal.
- Add secondary domains only in `Applies to`; do not duplicate the same principle across files.
- If the thought is mostly about life, personality, broad communication, or non-development self-modeling, do not store it here. Mention that it belongs in a separate personal-principle skill if needed.

3. Read before writing.
- Read the relevant `records/principles/<domain>/current.md` before adding or revising a current principle.
- Read the relevant `signals.md` before adding a new signal, promoting a signal, or deciding whether a similar candidate already exists.
- Read `records/evolution-log.md` when the user mentions change over time, prior decisions, possible tension with an older stance, or when promoting/deprecating a prior record.
- Use `records/current-principles.md` only as a compatibility index when the relevant domain is unclear.

4. Harvest aggressively but weight conservatively.
- During repository-specific work, watch for statements that sound like reusable development judgment rather than local implementation chatter.
- Good harvest candidates include repeated tradeoff preferences, quality bars, naming or architecture heuristics, product prioritization rules, business reasoning that affects product work, verification expectations, and collaboration rules for agents.
- If a thought is clearly endorsed and reusable, record it as `settled` or `strong-default` in the domain `current.md`.
- If a thought is plausible but not confirmed, record it as an `emerging` signal instead of dropping it or promoting it too early.
- If the user only discussed a local tactical choice, temporary workaround, one-off repository detail, or debugging note, do not lift it into this archive.

5. Normalize the record.
- Rewrite the idea as a reusable principle or signal, not as conversation residue.
- Capture the rationale and the tradeoff it is meant to optimize.
- Preserve the user's wording when it carries precise nuance, but compress repetition.
- Include enough context for a future agent to apply the record without re-reading the original chat.

6. Update the right layer.
- For active principles, update only the relevant domain `current.md`.
- For unresolved but useful thoughts, update only the relevant domain `signals.md`.
- Update `records/current-principles.md` when the domain inventory or compatibility index changes.
- Append to `records/evolution-log.md` with the absolute date in `YYYY-MM-DD` format whenever a principle is added, revised, narrowed, broadened, deprecated, or a signal is promoted/discarded.

7. Reuse the record in later work.
- Before major design or implementation recommendations, read the relevant domain `current.md` if the task depends on judgment, tradeoffs, prioritization, maintainability, UX direction, business intent, architecture, code quality, or workflow.
- Read the relevant `signals.md` when the decision has no settled principle or the user is exploring a direction that resembles a recorded signal.
- State explicitly when a proposal follows a recorded principle, stretches it, conflicts with it, or is only informed by an emerging signal.
- If the current repository task reveals a new reusable developer principle while work is underway, update this archive after the user has clearly stated or endorsed that principle.

## Harvesting From Repository Conversations

- Treat the user's explicit statements as the strongest signal.
- Treat repeated choices with consistent rationale as weaker but usable evidence when the cross-repository intent is clear.
- Treat a single plausible but unconfirmed statement as a signal, not as doctrine.
- Prefer short durable formulations such as `prefer X because Y` over chat-shaped notes.
- After harvesting from normal repo work, mention briefly that the archive was updated so the user can correct it if needed.
- When uncertain, store a compact `emerging` signal or surface the candidate summary instead of silently creating a settled principle.

## Consulting During Repository Work

- Read the domain files that match the current decision surface.
- Use `settled` principles as default constraints, subject to explicit current instructions and hard repository constraints.
- Use `strong-default` principles as strong guidance, but name material tradeoffs.
- Use `emerging` signals as context for proposals or clarifying questions only.
- Ignore `deprecated` and `discarded` records for active guidance except when explaining history.
- When stored principles are silent or conflicting, say so plainly and ask the user or record the new clarification if they provide one.

## Recording Rules

- Prefer a small number of useful principles and signals over a noisy journal.
- Keep each record concrete enough to guide action.
- Separate current rules from provisional signals and historical evolution.
- If the user is unsure, record the thought as an `emerging` signal only when it has likely future value.
- If a signal becomes confirmed, promote it to `current.md`, remove or mark the old signal as promoted, and explain the change in `evolution-log.md`.
- If a new statement contradicts an older principle, update the old current entry instead of keeping both active, and explain the shift in `evolution-log.md`.
- Do not convert every preference into doctrine; favor reusable decision criteria.
- Let explicit current-task instructions override older archived principles when they conflict.

## Current Principles Format

In `records/principles/<domain>/current.md`, use this entry shape:

### Short principle title
- Weight: `settled` or `strong-default`
- Principle: one current rule or preference
- Why: what it optimizes or prevents
- Applies to: domains or common decision surfaces
- Last confirmed: `YYYY-MM-DD`

Add an `Exceptions:` line only when the boundary is important.

## Signals Format

In `records/principles/<domain>/signals.md`, use this entry shape:

### Short signal title
- Weight: `emerging`, `strong-default`, `deprecated`, or `discarded`
- Signal: reusable thought or candidate rule
- Why it may matter: what future work could gain by remembering it
- Evidence: short source summary, not raw transcript
- Applies to: domains or common decision surfaces
- Captured: `YYYY-MM-DD`
- Review trigger: what would promote, revise, or discard this signal

## Evolution Log Format

In `records/evolution-log.md`, append entries in reverse chronological order using this shape:

## YYYY-MM-DD
- Change: added, revised, clarified, promoted, deprecated, discarded, or restructured principle/signal title
- Previous stance: short summary or `none`
- New stance: short summary
- Why changed: concrete reason, evidence, or tradeoff shift
- Expected impact: how future repo work or business decisions should change

## Guardrails

- Keep this record inside this skill's `records/` directory and outside product repositories unless the user explicitly wants a copy in a repo.
- Do not fabricate principles that the user did not actually express or clearly imply.
- Do not store broad personal philosophy, life policy, personality modeling, or non-development communication preferences in this skill.
- Do not let weighted signals erase the difference between confirmed principles and provisional ideas.
- Do not treat context archives as principles; near-raw evidence belongs in context skills, while this archive stores normalized developer judgment.
- When the stored principles are silent or conflicting, say so plainly and ask the user or record the new clarification if they provide one.

## Verification

- The record reflects reusable developer judgment, not a one-off local note.
- Domain `current.md` files contain only the latest active stance for their domain.
- Domain `signals.md` files contain only weighted candidates or inactive signal history.
- `records/current-principles.md` remains a compatibility index, not the only source of truth.
- `records/evolution-log.md` captures historical changes with absolute dates.
- Future agent work can understand the principle or signal without re-reading the full chat.

## Workflow Alignment (skills-batch-auditor)

- Return output in concise, polite Japanese.
- Do not invent architecture or product features.
