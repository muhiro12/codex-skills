# Diagnostic And Proxy Signals

Treat every signal in this skill as heuristic evidence from the repository.
The goal is prioritization, not certification.

## Primary Diagnostic Signals

### Maintenance Risk

Look for signals such as:

- no meaningful automated tests despite notable production LOC
- source LOC concentrated in one module or a very small set of modules
- lack of CI for a repo that is already large enough to need repeatable validation
- lack of docs once architecture size or breadth becomes non-trivial
- very large source files that are likely local maintenance bottlenecks
- feature breadth that is expanding faster than the protection around it

Interpretation question:
"Where are future changes most likely to become expensive or risky?"

### Test Surface Health

Look for:

- meaningful test LOC
- test-file count
- test LOC relative to production LOC

Interpretation question:
"How much visible regression buffer exists in the repo?"

Do not imply real code coverage.

### Architectural Concentration

Look for:

- top-1 source LOC share
- top-3 source LOC share
- whether one module absorbs a disproportionate amount of change load

Interpretation question:
"Are future changes funneled into too few places?"

### Likely Complexity Hotspots

Look for:

- the largest source-heavy modules or directories
- large source files that stand out sharply from the rest

Interpretation question:
"Where will maintenance attention probably cluster?"

### Healthy Structure Signals

Prefer practical positives such as:

- meaningful automated tests
- CI or workflow automation
- shared-library extraction
- architecture or design docs
- balanced feature spread
- multi-surface products with shared foundations
- localization discipline when it reflects maintained product depth

Interpretation question:
"What visibly reduces maintenance cost or coordination risk?"

## Secondary Proxy Signals

These are lower priority than the diagnostic signals above.

### Quality Proxy

Use visible evidence such as tests, CI, docs, modularization, and coherent integrations to estimate whether engineering discipline is being invested.

### Breadth Proxy

Use visible evidence such as feature areas, app surfaces, shared logic, localization, and useful OS integrations to estimate whether the codebase supports a narrow or broader product surface.

## Cautions

- A focused product can be healthy even if it is not broad.
- A broad codebase can still be risky if tests or structure are weak.
- Modern frameworks do not guarantee maintainability.
- Raw size alone is not a decision.
- Use these signals to direct next actions, not to deliver a final verdict on team quality.
