# Local Principle Archive Reference

This directory is reserved for static reference material used by `track-developer-principles`.

Mutable local principle records live in the skill-owned `records/` directory and
are intentionally not tracked in git:

- `current-principles.md`
- `evolution-log.md`
- `principles/<domain>/current.md`
- `principles/<domain>/signals.md`

`current-principles.md` is a compatibility entrypoint. The domain files under
`principles/` are the actual source of truth for current developer principles
and weighted candidate signals.

If legacy private records still exist in this `references/` directory, move them
to the same relative paths under `records/` before writing new records.
Use `python3 scripts/migrate_skill_data.py --only principles` from the skills
root for the standard dry-run check, then add `--apply` to copy missing targets.
