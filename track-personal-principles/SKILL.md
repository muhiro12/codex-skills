---
name: track-personal-principles
description: "Capture, maintain, harvest, and consult Hiromu's personal operating principles, including values, life and work heuristics, communication preferences, collaboration style, environment boundaries, and broader non-development judgment. Use when the user explicitly wants to record or revise a personal principle; when ordinary conversation reveals a reusable personal operating candidate that should be surfaced without being persisted implicitly; when the user's thinking has changed and they ask to update the record; or when current assistance should load stored personal principles before judgment-heavy recommendations or user-facing communication. Do not use for technical developer principles, raw transcript capture, or ordinary one-off preferences."
---

# Track Personal Principles

## Overview

Use this skill as a local, cross-context memory for Hiromu's personal operating judgment.
This skill covers broader personal values, life/work heuristics, communication preferences, collaboration style, environment boundaries, and non-development decision criteria that help Codex work in a way that fits Hiromu.
Keep technical product, architecture, implementation, code quality, and repository workflow principles in `track-developer-principles`.
Use this skill to help Codex align with Hiromu; do not use it to impersonate Hiromu externally, make commitments for Hiromu, or store raw private evidence.

## Trigger Policy

Trigger this skill proactively when assistance depends on personal judgment, communication posture, collaboration norms, values, lifestyle/work constraints, privacy boundaries, or non-development decision criteria.
Separate read and write behavior:

- `consult`: trigger frequently without explicit user invocation for judgment-heavy personal assistance or user-facing communication drafts; reading relevant current principles is the default.
- `harvest` / `signal`: trigger during ordinary conversation when reusable personal operating judgment appears; identify and surface a weighted candidate, but keep the archive read-only unless the user explicitly asks to record it or explicitly approves the proposed write.
- `capture` / `revise`: write current principles only when the user explicitly asks to record or revise them, or explicitly approves a proposed archive change. Endorsing a stance is evidence for its weight, not by itself authorization to persist it.
- Be more cautious than `track-developer-principles` when proposing a write: do not persist sensitive personal facts, third-party details, inferred psychology, or anything that cannot be reduced to a reusable decision criterion without explicit, informed approval.
- Implicit invocation permits consultation and candidate detection only. No mode may create, modify, migrate, or delete personal-principle records without an explicit current-task request or approval for that write.

## Storage Files

- `records/principles/<domain>/current.md`
  - Treat these domain files as the source of truth for current active personal principles.
  - Keep only the latest active stance for that domain.
  - Use `settled` for confirmed principles and `strong-default` only when the stance is active but not absolute.
- `records/principles/<domain>/signals.md`
  - Store plausible, reusable, not-yet-settled thoughts as weighted signals.
  - Use this for ideas that are too useful to lose but too provisional to become doctrine.
- `records/current-principles.md`
  - Keep as a compatibility entrypoint and index.
  - It should point to the domain files rather than becoming the only source of truth.
- `records/evolution-log.md`
  - Treat this as the timeline of additions, revisions, deprecations, promotions, and structural changes.
  - Append a dated entry whenever a current stance changes, a new principle is introduced, a signal is promoted, or an important signal is discarded.

Keep `references/` for static skill documentation only. Keep mutable user-specific personal records under `records/`, which is skill-owned local data and should stay ignored by git. If legacy records still exist under `references/`, migrate them to the same relative paths under `records/` before writing new records.
Keep `records/` directories owner-only (`0700`) and record files owner-readable and owner-writable only (`0600`). Write approved changes through a same-directory temporary file and atomic replacement, and never traverse or replace symbolic links in the record tree.

Migration check:

- After this skill is installed or updated from GitHub, run `python3 scripts/migrate_skill_data.py --only principles` from the skills root when `records/` is missing or when legacy ignored files may still exist under `references/`.
- If the dry-run reports copyable legacy files, apply `python3 scripts/migrate_skill_data.py --only principles --apply` only when the user explicitly requests or approves the migration. Otherwise keep consultation read-only and report the legacy-data gap.
- The migration copies only missing targets and never overwrites conflicting files. Resolve conflicts manually before treating `records/` as complete.

Initial domains:

- `meta`: rules about this archive, evidence boundaries, and skill behavior.
- `values-direction`: personal values, priorities, life direction, identity-level preferences, and durable decision criteria.
- `communication-collaboration`: tone preferences, interaction norms, feedback style, delegation expectations, and collaboration boundaries.
- `work-life-operations`: non-technical work habits, personal operating rhythms, planning heuristics, attention management, and lifestyle constraints.
- `environment-boundaries`: privacy boundaries, local-machine assumptions, private/work separation, safety constraints, and storage rules.

## Weights

- `settled`: an explicitly confirmed durable personal principle. Respect it by default unless direct current instructions, safety, law, or hard context constraints override it.
- `strong-default`: a strong personal preference or recurring pattern. Apply it when the current task is silent, but name material tradeoffs.
- `emerging`: a plausible candidate. Use it as context for suggestions or questions, but do not silently treat it as a rule.
- `deprecated`: a former stance that should not guide new work except as history.
- `discarded`: a captured signal that should not guide new work.

## Workflow

1. Determine the mode.
- `capture`: after explicit write authorization, add a settled or strong-default personal principle that the user clearly endorsed.
- `harvest`: derive and surface a reusable personal-principle candidate from ordinary conversation; do not persist it implicitly.
- `signal`: prepare a plausible but not-yet-settled thought with a weight and review trigger; record it only after explicit write authorization.
- `revise`: after explicit write authorization, update the current stance because the user's thinking changed.
- `consult`: read the stored principles and apply them to the current task without modifying the record.

2. Route to the right memory.
- Use this skill for broader personal judgment, communication norms, life/work heuristics, and boundaries.
- Use `track-developer-principles` for technical developer judgment, product decisions, architecture, implementation, code quality, repository workflow, and business heuristics that directly affect products.
- Use `context-capture` for near-raw transcripts, copied conversations, source traces, or evidence archives.
- Use `context-consult` to search local context archives without writing new personal principles.

3. Resolve the domain before writing.
- Choose exactly one primary domain for each principle or signal.
- Add secondary domains only in `Applies to`; do not duplicate the same principle across files.
- If a thought contains third-party personal information, credentials, medical details, legal details, or highly sensitive private facts, store only the reusable decision criterion and omit unnecessary identifying details.
- If the useful record cannot be written without sensitive specifics, ask before saving.

4. Read before writing.
- Read the relevant `records/principles/<domain>/current.md` before adding or revising a current principle.
- Read the relevant `signals.md` before adding a new signal, promoting a signal, or deciding whether a similar candidate already exists.
- Read `records/evolution-log.md` when the user mentions change over time, prior decisions, possible tension with an older stance, or when promoting/deprecating a prior record.
- Use `records/current-principles.md` only as a compatibility index when the relevant domain is unclear.

5. Harvest actively but weight conservatively.
- Watch for reusable personal judgment: repeated preferences, explicitly stated values, durable collaboration norms, life/work heuristics, privacy boundaries, and personal decision rules.
- If a thought is clearly endorsed and reusable, propose it as `settled` or `strong-default`; record it in the domain `current.md` only when the user has explicitly authorized that write.
- If a thought is plausible but not confirmed, surface it as an `emerging` candidate only when it has likely future value; persist it only after explicit authorization.
- Do not record one-off moods, transient preferences, ordinary scheduling details, private facts without a reusable rule, or guesses about the user's psychology.

6. Normalize the record.
- Rewrite the idea as a reusable principle or signal, not as conversation residue.
- Capture the rationale and the tradeoff it is meant to optimize.
- Preserve the user's wording when it carries precise nuance, but compress repetition.
- Include enough context for a future agent to apply the record without re-reading the original chat.

7. Update the right layer.
- For active principles, update only the relevant domain `current.md`.
- For unresolved but useful thoughts, update only the relevant domain `signals.md`.
- Update `records/current-principles.md` when the domain inventory or compatibility index changes.
- Append to `records/evolution-log.md` with the absolute date in `YYYY-MM-DD` format whenever a principle is added, revised, narrowed, broadened, deprecated, or a signal is promoted/discarded.

8. Reuse the record in later work.
- Before judgment-heavy personal assistance, drafting user-facing communication, choosing a collaboration posture, or making lifestyle/workflow recommendations, read the relevant domain `current.md`.
- Read the relevant `signals.md` when the decision has no settled principle or the user is exploring a direction that resembles a recorded signal.
- State explicitly when a proposal follows a recorded principle, stretches it, conflicts with it, or is only informed by an emerging signal.
- Treat explicit current instructions as stronger than older archived principles.

## Recording Rules

- Prefer a small number of useful principles and signals over a noisy journal.
- Keep each record concrete enough to guide action.
- Separate current rules from provisional signals and historical evolution.
- Never write any principle, signal, index, or evolution-log change without an explicit current-task request or approval to persist it.
- If the user is unsure, surface the thought as an `emerging` candidate when it has likely future value and ask before recording it.
- If a signal becomes confirmed, promote it to `current.md`, remove or mark the old signal as promoted, and explain the change in `evolution-log.md`.
- If a new statement contradicts an older principle, update the old current entry instead of keeping both active, and explain the shift in `evolution-log.md`.
- Do not infer personality traits, mental states, relationships, or motives beyond what the user clearly states.
- Do not use this archive to justify sending messages, making purchases, changing accounts, or making commitments without explicit current-task confirmation.

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
- Expected impact: how future personal assistance should change

## Guardrails

- Keep this record inside this skill's `records/` directory and outside product repositories unless the user explicitly wants a copy in a repo.
- Treat implicit invocation as read-only. Do not infer storage authorization from a reusable statement, repeated behavior, or agreement with a proposed principle.
- Do not fabricate principles that the user did not actually express or clearly imply.
- Do not store raw conversations, secrets, credentials, or unnecessary third-party personal details.
- Do not let weighted signals erase the difference between confirmed principles and provisional ideas.
- Do not let personal principles override safety, law, platform policy, or explicit current instructions.
- If the stored principles are silent or conflicting, say so plainly and ask the user. Record any clarification only if the user explicitly requests or approves that archive update.

## Verification

- The record reflects reusable personal operating judgment, not a one-off local note.
- Domain `current.md` files contain only the latest active stance for their domain.
- Domain `signals.md` files contain only weighted candidates or inactive signal history.
- `records/current-principles.md` remains a compatibility index, not the only source of truth.
- `records/evolution-log.md` captures historical changes with absolute dates.
- Future agent work can understand the principle or signal without re-reading the full chat.
- Every record mutation can be traced to an explicit user request or approval in the current task.

## Workflow Alignment

- Return user-facing explanations in concise, polite Japanese by default unless the user explicitly asks for another language.
- Keep stored principles concise and do not rewrite code, identifiers, file paths, schema fields, or quoted source text for language matching.
