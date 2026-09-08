# Authorized Record Updates

Read this only when the user has explicitly requested or approved recording,
revision, promotion, or migration. Implicit consultation remains read-only.

## Storage and Update

All paths are relative to this loaded skill directory:

- `records/principles/<domain>/current.md`: latest active stance, using `settled`
  or `strong-default` weights.
- `records/principles/<domain>/signals.md`: provisional or inactive signals.
- `records/current-principles.md`: compatibility index pointing to domain files.
- `records/evolution-log.md`: dated additions, revisions, promotions, deprecations,
  and significant discarded signals, in reverse chronological order.

Choose one primary domain, read its current and relevant signal entries, and
avoid duplicates. Preserve the rationale and applicability, not raw chat text.
A clear endorsement can support a settled principle; uncertain ideas remain
emerging. Do not turn a one-off tactic into a cross-context rule.

Revise a superseded current entry rather than keeping contradictory active rules.
When promoting a signal, update current guidance and mark/remove the old signal.
Update the index when its entries change, and record the previous and new stance
with the reason in the evolution log. Keep raw evidence in an explicitly
requested context archive, not in the principle files.

Keep records Git-ignored and outside product repositories. Use owner-only
permissions (`0700` directories, `0600` files), same-directory temporary files,
and atomic replacement. Do not traverse or replace symbolic links in the record
tree. Preserve unrelated files and confirm the written diff.

## Existing Formats

Current entry:

```markdown
### Short principle title
- Weight: settled or strong-default
- Principle: one current rule or preference
- Why: what it optimizes or prevents
- Applies to: domains or common decision surfaces
- Last confirmed: YYYY-MM-DD
```

Add `Exceptions:` when it changes how the rule should be applied.

Signal entry:

```markdown
### Short signal title
- Weight: emerging, strong-default, deprecated, or discarded
- Signal: reusable candidate
- Why it may matter: future value
- Evidence: short source summary, not a raw transcript
- Applies to: relevant decision surfaces
- Captured: YYYY-MM-DD
- Review trigger: what would promote, revise, or discard it
```

Evolution entry:

```markdown
## YYYY-MM-DD
- Change: added, revised, clarified, promoted, deprecated, discarded, or restructured
- Previous stance: short summary or none
- New stance: short summary
- Why changed: evidence or tradeoff shift
- Expected impact: effect on future decisions
```

## Explicit Migration

Legacy ignored records under `references/` may be migrated only when the user
requests that operation. From the skills repository root, inspect:

```bash
python3 scripts/migrate_skill_data.py --only principles
```

Review the dry run and affected scopes before applying an authorized migration
with `--apply`. The helper covers both principle skills; do not assume the other
archive was authorized merely because the current skill was. It copies missing
targets and preserves conflicts. Never delete old records to make an audit pass.

## Verify

Confirm active entries are current, signals retain their weight, the index points
to the right domains, and the evolution entry has an absolute date. Every write
must be traceable to the user's explicit persistence request. Report the files
and the substance of the update.
