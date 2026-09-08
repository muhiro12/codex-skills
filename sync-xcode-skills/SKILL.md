---
name: sync-xcode-skills
description: Export Xcode-provided agent Skills through `xcrun mcpbridge run-agent skills export`, normalize them into Codex-compatible skill folders, and install them into the local Codex skills root. Use when the user wants to discover, extract, sync, refresh, import, or periodically update built-in Xcode Skills so Codex can use the latest Xcode-provided Apple guidance.
---

# Sync Xcode Skills

## Overview

Use this skill to keep Codex's local skill set aligned with the Skills that Xcode exposes through its agent integration.
Default response language is concise, polite Japanese.

From Codex, run Xcode export as a standalone command first:

```bash
xcrun mcpbridge run-agent skills export --output-dir /tmp/xcode-exported-skills --replace-existing
```

Then run the Python installer from this skill directory:

```bash
python3 scripts/sync_xcode_skills.py --install-only --export-dir /tmp/xcode-exported-skills
```

In this Codex environment, `xcrun mcpbridge ...` must be executed as its own top-level command. Do not wrap it in Python, `bash -c`, command chaining such as `cd ... && xcrun ...`, or `MCP_XCODE_PID=...`; those forms can fail to connect to the running Xcode. Let `mcpbridge` use its own Xcode auto-detection.

## Workflow

1. Confirm the selected Xcode with `xcode-select -p` and `xcodebuild -version` when the user cares which Xcode is used.
2. Run `xcrun mcpbridge run-agent skills export --output-dir /tmp/xcode-exported-skills --replace-existing` as a standalone command.
- If export cannot find a running Xcode while the native integration can list its workspaces, distinguish the shell access boundary from an application failure. Use the current approval mechanism for the same standalone export when additional access is required; do not invent wrappers or persistent permission exceptions. Do not install from an incomplete or failed export.
3. Run `python3 scripts/sync_xcode_skills.py --install-only --export-dir /tmp/xcode-exported-skills` from the `sync-xcode-skills` directory.
4. Report the exported and installed skill names, then mention the catalog path when surrounding Apple skills may need to route to the generated Xcode-provided skills.

The script exports with `xcrun mcpbridge run-agent skills export --replace-existing`, then installs Codex-compatible copies into the skills root. By default, installed skill names are prefixed with `xcode-skill-` to avoid collisions with local custom skills.
Treat the `xcode-skill-*` namespace as reserved for this sync output.

## Design Position

Use the `xcode-skill-` prefix as a low-risk namespace boundary, not as a lower authority level. Xcode-provided guidance remains the preferred Apple/Xcode guidance when it matches the task.

The generated copies need Codex-compatible frontmatter, so the script rewrites installed `SKILL.md` metadata to the prefixed `name` and a Codex-readable `description`; the body and bundled references remain Xcode-provided content. The original Xcode skill name is preserved in each managed skill marker and in the central catalog.

After every install, the script writes a generated catalog under `state/` beside this skill:

```text
state/catalog.md
state/catalog.json
```

Apple-platform orchestrator skills should consult this catalog instead of hardcoding specific Xcode-provided skill names. If the catalog lists a relevant Xcode-provided skill, prefer that guidance before applying local custom-skill heuristics.

## Important Behavior

- Prefer direct `xcrun mcpbridge run-agent skills export`. The older `xcrun agent skills export` wrapper can fail from Codex's embedded shell by trying to launch Xcode instead of connecting to the running instance.
- Run `xcrun mcpbridge ...` as a standalone top-level command in Codex. Python subprocesses, `bash -c`, shell chaining, and explicit `MCP_XCODE_PID` can fail to connect to the running Xcode.
- Xcode-exported frontmatter can contain fields Codex does not need, such as `when_to_use` or `effort`. The script rewrites installed `SKILL.md` frontmatter to `name` and `description`, folding `when_to_use` into the description when present.
- Exported `name` values and `--name-prefix` must be filesystem-safe slugs. The installer rejects traversal-like values, duplicate installed names (including case-only duplicates), symbolic links in exported trees or install targets, and any resolved install target outside the skills root before changing managed skills.
- The script writes `agents/openai.yaml` and `.xcode-skill-sync.json` into each installed managed skill.
- Every exported skill is copied, normalized, and validated in a same-filesystem staging directory under the skills root before any existing managed skill is moved. Existing skills are moved to a transaction backup before staged copies are swapped into place; any staging, swap, prune, or catalog failure rolls the managed set back.
- The script writes a generated central catalog for surrounding skills to discover the current Xcode-provided skill set without depending on stable external Xcode naming.
- Stale managed skills are moved into the transaction backup only after all staged installs have swapped successfully. `state/catalog.json` and `state/catalog.md` are prepared together and installed with atomic file replacements; a failure restores both catalogs and the prior managed skill set before backups are removed.
- The Xcode version is captured once at the start of a run and reused for every managed marker and both catalog representations so one sync cannot report mixed toolchain versions.
- When copying exported skill directories, the script ignores generated or local-only directories and files such as `.build`, `build`, `DerivedData`, `.git`, `.swiftpm`, `Pods`, `Carthage`, `.DS_Store`, and `__pycache__`.
- A successful export is treated as the desired Xcode-provided skill set. Managed `xcode-skill-*` directories that are absent from the current export are pruned so Xcode-side deletions and renames are reflected locally.
- If the export returns no skills, the script exits with an error instead of pruning installed skills.
- Any unmanaged `xcode-skill-*` path, including a directory with a missing, malformed, non-object, symlinked, or identity-mismatched marker, causes an error before install or prune begins. This keeps the reserved namespace easy to reason about: every `xcode-skill-*` directory is either managed by `sync-xcode-skills` or must be resolved manually before syncing.

## Useful Options

```bash
python3 scripts/sync_xcode_skills.py --install-only --export-dir /tmp/xcode-exported-skills
python3 scripts/sync_xcode_skills.py --name-prefix xcode-skill-
python3 scripts/sync_xcode_skills.py --state-dir state
```

Use `--export-only` when diagnosing Xcode's export output without installing anything into Codex.
Use Python-driven export options such as `--export-only` only outside Codex or when specifically diagnosing why Python subprocess export differs from top-level `xcrun mcpbridge`.
