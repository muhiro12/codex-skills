# Repo And App Footprint Methodology

## Primary Principle

Use footprint as diagnostic evidence, not as a vanity score.
The main question is not "how big is it?" but "what does this size imply for maintenance, change safety, and structural health?"

## What To Measure First

### Repository Footprint

- Use Git tracked files as the default scope.
- Fall back to the working tree only when Git metadata is unavailable.
- Use raw directory size only when the user explicitly wants literal disk usage.

### App Codebase Footprint

- Measure explicit app directories with `--app-path`.
- Treat this as implementation footprint inside the repository, not as built-binary size.
- For multi-surface products, include widget, watch, or extension paths only when they materially affect maintenance decisions.

### Meaningful LOC

- Count non-empty, non-comment-only source lines.
- Separate production LOC from test LOC.
- Treat LOC as a maintenance-shape signal, not as output quality by itself.

## Diagnostic Order

Read the report in this order:

1. `diagnostic_summary`
2. selected app scope if present, otherwise repository code profile
3. top-level breakdown and large files
4. optional scale-band or secondary proxy sections

## Diagnostic Layers

### Biggest Directories Or Modules

- Use the top 3 entries from `diagnostic_summary.largest_entries`.
- These preserve the footprint concept, but should be explained in terms of where maintenance load is likely accumulating.

### Maintenance Risk

- Use the top 3 items from `diagnostic_summary.maintenance_risk.findings`.
- Prioritize regression risk, coordination cost, and likely places where future changes become expensive.

### Test Surface Health

- Use `diagnostic_summary.test_surface_health`.
- Judge only the visible repo signal: meaningful test LOC and test-file presence.
- Never convert this into an implied coverage percentage.

### Architectural Concentration

- Use `diagnostic_summary.architectural_concentration`.
- Top-1 and top-3 source LOC share are the main evidence for whether changes are overly concentrated.

### Likely Complexity Hotspots

- Use `diagnostic_summary.complexity_hotspots`.
- Prefer source-heavy directories or modules first.
- Mention large files only when they are clearly substantial enough to act as local bottlenecks.

### Healthy Structure Signals

- Use the top 3 items from `diagnostic_summary.healthy_structure_signals`.
- Favor signals that materially reduce maintenance cost, such as CI, meaningful tests, shared libraries, docs, and balanced feature spread.

## Optional Secondary Context

### Scale Bands

- Use [scale-bands.md](scale-bands.md) only when rough market-scale context is useful.
- This is secondary to the diagnostic conclusion.

### Quality Or Breadth Proxies

- Use the proxy section only as supporting context.
- If the diagnostic conclusion is already clear, keep proxy discussion short or omit it.

## Practical Summarization Rule

Lead with a decision-oriented conclusion, such as:

- changes look safe to continue with normal discipline
- continue, but concentrate on tests or module boundaries first
- pause feature expansion and reduce concentration or hotspot risk

Then support that conclusion with only the most relevant footprint evidence.
