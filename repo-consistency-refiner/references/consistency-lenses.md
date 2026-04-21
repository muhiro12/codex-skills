# Consistency Lenses

Use this reference to keep the audit focused on high-signal repository drift.
Do not try to exhaustively catalog every style difference.

## Structural Lens

Inspect:

- top-level directories and whether similar concerns live in consistent places
- module or feature folder shape
- source and test co-location strategy
- filename, suffix, and target naming conventions
- duplicate helper or utility areas with overlapping ownership

Look for:

- one feature organized by layer while another equivalent feature is organized by screen or route
- similar modules using different singular/plural or suffix rules
- tests living beside code in one area but in detached buckets elsewhere without a clear reason
- docs, fixtures, or resources stored in inconsistent locations across equivalent modules

Useful targets:

- `Sources/`, `Tests/`, `apps/`, `packages/`, `modules/`, `features/`, `docs/`, `scripts/`
- root manifests such as `Package.swift`, `package.json`, `pyproject.toml`, `Cargo.toml`

## Architectural Lens

Inspect:

- domain logic placement
- persistence and routing ownership
- service, client, repository, adapter, and gateway naming
- shared library boundaries and imports
- feature-to-feature dependency shape

Look for:

- views or controllers performing persistence or heavy business rules directly
- similar integrations wrapped by different abstractions without a clear boundary reason
- one feature using a service layer while another equivalent feature reaches storage or transport directly
- duplicated architectural concepts under different names

Useful targets:

- files containing `View`, `Screen`, `Controller`, `Route`, `Router`, `Store`, `Repository`, `Service`, `Client`, `Adapter`
- dependency registration points and shared library entry modules

## Workflow Lens

Inspect:

- CI entry points and wrapper scripts
- `verify.sh` and related verification orchestration
- `.pre-commit-config.yaml`
- `.build/` artifact conventions, especially CI run directories
- repository-specific rules documented in `AGENTS.md`

Look for:

- multiple scripts that appear to do the same verification with slightly different scope
- workflow docs calling commands that no longer exist
- CI writing artifacts into inconsistent locations or names
- `AGENTS.md` rules that are not reflected in scripts, hooks, or repository layout

Useful targets:

- `.github/workflows/`, `ci_scripts/`, `scripts/`, `Makefile`, `Taskfile.yml`, `justfile`, `verify.sh`, `.build/`

## Documentation Lens

Inspect:

- `README*`
- architecture or overview docs
- ADR directories such as `adr/` or `docs/adr/`
- contributor and setup instructions

Look for:

- removed or renamed modules still described as active
- setup or verification commands that drifted from current scripts
- architectural diagrams or narratives that no longer match module boundaries
- ADRs whose decision is clearly contradicted by the current implementation

Useful targets:

- `README.md`, `docs/`, `architecture/`, `overview*.md`, `adr/`, `docs/adr/`

## Reporting Heuristics

- Prefer three strong findings over ten weak observations.
- Preserve intentional differences when framework or product constraints explain them.
- Call out healthy aligned patterns when they help justify a recommendation.
- Escalate to `高` risk only when a proposed refinement affects many files, shared contracts, or public APIs.
