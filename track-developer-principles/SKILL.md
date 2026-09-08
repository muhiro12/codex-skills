---
name: track-developer-principles
description: Consult or explicitly record durable developer judgment for product, architecture, Swift, and repository workflow decisions. Keep current principles separate from provisional signals and raw history.
---

# Track Developer Principles

Maintain reusable judgment about development, product, architecture, code quality, and repository workflow.
Use `track-personal-principles` for the other domain. Keep private context outside product
repositories. Return concise, polite Japanese unless another language is requested.

## Consult

Read the relevant `records/principles/<domain>/current.md`. Use
`records/current-principles.md` as the index only when the domain is unclear.
Initial domains: meta, product-business, architecture-system-design, implementation-code-quality, workflow-collaboration.

Consult during judgment-heavy work when a stored preference can affect the
choice. Skip mechanical edits and ordinary answers that need no personal context.
Read only relevant domains; do not reload already-read records without a reason.

- `settled`: confirmed active judgment.
- `strong-default`: strong guidance with task-specific exceptions.
- `emerging`: provisional context, not a binding rule.
- `deprecated` / `discarded`: history, not active guidance.

Read `signals.md` for a relevant unsettled question and `records/evolution-log.md`
when history or a change in stance matters. Current user instructions and hard
constraints override older records. State a material influence or conflict.

Missing or silent records do not block work. Use current evidence and judgment;
ask only when an unresolved preference materially changes the result. If records
are absent, do not scan legacy private paths or run migrations automatically.
Report the gap and use the current task's context.

## Capture or Revise

Consultation and candidate detection are read-only. No principle, signal, index,
history, or migration may be written without the user's explicit request or
approval to persist it. Agreement with a stance is evidence, not storage consent.
A skill-maintenance request does not authorize edits to the records it owns.

When a clearly reusable thought appears, mention a candidate only if useful to
the current conversation. Do not append capture proposals to every ordinary task.
Keep source facts, observer interpretations, and endorsed principles distinct;
do not infer psychology or turn transient choices into doctrine.

For an authorized write, read
[references/record-workflow.md](references/record-workflow.md). It defines the
existing storage format, weights, evolution handling, permissions, and explicit
migration path. Preserve existing records and their layout; do not duplicate
these files into another agent's environment without an actual sharing request.

## Report

For consultation, briefly identify the principle only when it materially affected
the decision. For a write, name the updated files and summarize the change so the
user can correct it. Never imply that a proposed candidate was saved.
