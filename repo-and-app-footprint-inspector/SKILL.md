---
name: repo-and-app-footprint-inspector
description: Diagnose repository and app footprint without modifying source code. Use this skill when you need practical conclusions from repository size, app codebase size, meaningful LOC, directory or module concentration, maintenance risk, test surface health, architectural hotspots, or structural health signals, especially for requests about project volume, codebase footprint, biggest modules, maintenance burden, or whether the current structure is healthy enough to keep extending.
---

# Repo And App Footprint Inspector

## Overview

Use this skill for read-only footprint diagnosis.
Keep the core instructions in this file portable across agent runtimes where practical; platform-specific metadata can live beside the skill.
Keep size metrics, but treat them as evidence for maintenance cost, change safety, and structural health.
Default response language is concise, polite Japanese unless the user asks for another language.

## Workflow

1. Resolve the inspection scope.
- Use the user-provided repository path when present.
- Otherwise, use the current workspace root.
- Never edit source files as part of this skill.

2. Run the bundled measurement script in JSON first.

```bash
python3 scripts/measure_footprint.py \
  --repo /path/to/repository \
  --format json \
  --top 20
```

- Default audit scope is Git tracked files.
- If Git metadata is unavailable, the script falls back to the working tree with transient directories excluded.
- Add `--include-storage-footprint` only when the user explicitly wants raw or on-disk size.

3. If app-specific size matters, pass explicit app directories instead of build artifacts.

```bash
python3 scripts/measure_footprint.py \
  --repo /path/to/repository \
  --app-path MyApp \
  --app-path Extensions/MyWidget \
  --format json \
  --top 20
```

4. Read the diagnostic layer before the raw tables.
- Start with `diagnostic_summary`.
- Use `largest_entries` for the top 3 biggest directories or modules.
- Use `maintenance_risk.findings` for the top 3 likely maintenance risks.
- Use `healthy_structure_signals` for the top 3 signals of healthy structure.
- Use `test_surface_health`, `architectural_concentration`, and `complexity_hotspots` to explain why the size matters.

5. If `--app-path` is omitted and the app surface is unclear, inspect repo structure or script candidates before concluding.
- Prefer explicit app paths for multi-app or multi-module repositories.
- When the app remains ambiguous, say so plainly instead of guessing.

6. Summarize for decisions, not for vanity.
- Lead with a short conclusion about whether the current footprint looks easy to extend, manageable with care, or worth restructuring first.
- Mention repository or app size as supporting evidence, not as the headline.
- Prefer practical statements such as "test surface is thin for this amount of change" over descriptive statements such as "the repo is medium-sized."
- Use market-scale or quality/value proxy bands only when the user explicitly asks or when they materially clarify the decision.

## Interpretation Rules

### Maintenance Risk

- Judge risk from a combination of test thinness, source concentration, missing CI/docs, weak modularization, and very large source files.
- Focus on change cost and regression risk, not prestige or product value.

### Test Surface Health

- Use meaningful test LOC and test-file count as proxy evidence only.
- Never imply real coverage percentages.
- Prefer labels such as "薄い", "中程度", "比較的健全" in the final Japanese summary.

### Architectural Concentration

- Use top-1 and top-3 source LOC concentration to explain whether changes are funneling into too few modules.
- Call out the dominant modules explicitly.

### Likely Complexity Hotspots

- Prefer the largest source-heavy directories or modules first.
- Add large source files only when they are clearly substantial enough to be local maintenance hotspots.

### Healthy Structure Signals

- Prefer signals such as CI, meaningful tests, shared-library extraction, architecture docs, healthy feature spread, multi-surface shared foundations, and localization discipline.
- Keep this list practical: each signal should help explain why ongoing maintenance may be safer or cheaper.

## Guardrails

- Never modify source files.
- Never build, archive, or export binaries by default.
- Never discuss binary size unless the user explicitly asks for build-derived metrics.
- Never reduce the answer to raw numbers only.
- Never present heuristics as certainty.
- Avoid long raw metric dumps; default to the top 3 items unless the user asks for more detail.

## Output Contract

Return a concise Japanese report with:

1. `結論`
2. `対象`
3. `規模要点`
4. `診断`
5. `保守リスク Top 3`
6. `健全構造シグナル Top 3`
7. `次の判断`
8. `補足`

For `規模要点`, always include:

- repository/app size as relevant
- top 3 biggest directories or modules

For `診断`, always cover:

- maintenance risk
- test surface health
- architectural concentration
- likely complexity hotspots

## Resources

### `scripts/measure_footprint.py`

- Measures Git-tracked repository/app scope by default, with optional storage-footprint expansion.
- Emits `diagnostic_summary` with top modules, maintenance risks, healthy structure signals, test-surface health, concentration, and hotspots.
- Supports `--format markdown` and `--format json`.

### `references/methodology.md`

- Defines each metric and the diagnostic interpretation order.
- Clarifies when raw size matters and when it should stay secondary.

### `references/quality-and-value-signals.md`

- Explains how to interpret maintenance risk, test surface health, concentration, healthy signals, and secondary quality/breadth proxies.

### `references/scale-bands.md`

- Documents the heuristic LOC bands used only when scale comparison is actually useful.

## Verification

- Confirm the repository path and app paths are explicit in the report.
- Confirm whether the audit scope is Git tracked files or working-tree fallback.
- Confirm the report includes the top 3 biggest directories or modules.
- Confirm the report includes the top 3 maintenance risks.
- Confirm the report includes the top 3 healthy structure signals.
- Confirm the final summary leads with a practical conclusion, not raw metrics.
- Confirm test discussion stays at the proxy-signal level and does not claim real coverage.
- Confirm any limitation from missing Git metadata or ambiguous app paths is stated plainly.
