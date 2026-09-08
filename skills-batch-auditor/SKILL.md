---
name: skills-batch-auditor
description: Review or maintain a custom skill portfolio against current usage, repository contracts, and available tools. Fix deterministic drift or recommend concrete simplification, additions, merges, and retirement.
---

# Skills Batch Auditor

Review skills for the work the user actually does. Prefer specific reusable
knowledge, reliable helpers, and important boundaries over generic prompting,
fixed report ceremonies, and instructions already supplied by Codex. Return
concise, practical Japanese.

## Scope and Authorization

Choose the audit mode from the request:

- `maintenance`: apply small, deterministic consistency fixes that preserve the
  skill's responsibility and public interface.
- `refresh`: evaluate roles, invocation, current tool fit, and portfolio changes.
  Propose changes by default. If the user already asks you to decide and implement
  the review, that authorizes in-scope edits; use `skill-creator` to apply the
  selected design and verify it. Do not ask the user to approve the same scope
  again. The bundled script's refresh mode itself remains read-only.

Honor clean-worktree gates in the current task or automation. Do not infer that
an old automation's gate applies to a separate interactive review. Inventory and
preserve existing tracked and untracked changes; do not stash, commit, or discard
work merely to pass a gate. A request for proposals alone remains read-only.

Read the repository `AGENTS.md` and selected skills' full `SKILL.md` before
judging or editing them. Consult only relevant developer-principle domains when
user-specific tradeoffs matter. Current instructions override older preferences.

## Ownership

Separate maintained custom skills from other installed material:

- Tracked top-level skills are repository-owned custom definitions.
- Untracked custom drafts may be reviewed when the task includes them; identify
  them separately and preserve pre-existing work.
- Git-ignored runtime/workspace skills and `.system` are outside normal custom
  maintenance. Report ownership without rewriting provider-managed content.
- Xcode-managed skills are identified by `.xcode-skill-sync.json`; inspect only
  sync integrity and route changes through `sync-xcode-skills` or upstream Xcode.
- An unmarked `xcode-skill-*` directory is a reserved-prefix conflict.
- Exclude this auditor from its own script targets unless explicitly selected.

Do not scan private `records/`, `archives/`, sample caches, or generated build
history as part of definition review. Usage evidence can come from bounded
recent task summaries and selected skill-read/tool events. Distinguish an
available skill, an actual read, and a successfully completed workflow. A few
recent tasks are not a complete usage census; absence alone does not justify
retirement.

## Static Baseline

Run the bundled script from this skill directory:

```bash
python3 scripts/audit_skills_batch.py \
  --repo-root /path/to/repository \
  --skills-root /path/to/skills \
  --scope custom --mode refresh --format json
```

Use `--skill NAME` for a selected subset, `--format markdown` for a human-readable
baseline, and `--mode maintenance` only for deterministic automatic corrections.
Inspect the script's selected repository entrypoint before trusting CI findings.

The baseline analyzes definitions and lists conventional test paths. It does
not execute those tests, arbitrary skill scripts, or runtime capability probes.
`static-aligned` means only its static checks passed; runtime fit and execution
remain unverified. Heuristic scores and recommendations need human/agent judgment.
Do not add boilerplate merely to silence a keyword-based finding.

## Review What Changes Decisions

Compare each relevant skill against:

- Its distinct purpose and whether the description selects the right requests.
- Actual recent use, costly repetition, stalls, and recurring missing knowledge.
- Current official capabilities and installed specialist tools/skills. Resolve
  volatile action names from the active inventory, not remembered namespaces.
- Instructions that unnecessarily halt authorized work, force new scaffolding,
  repeat global rules, or demand unrelated audits.
- Detail that belongs in a reference loaded only for a particular mode.
- Scripts and data invariants whose reliability justifies precise procedures.

Do not merge skills solely because they share words such as verify, CI, HIG, or
repository. A live UI audit, Preview capture, static risk scan, and distribution
check prove different things. Keep useful boundaries; remove duplicated
routing. Do not build cross-agent compatibility layers without a concrete current
consumer. Portable English definitions and Git history can remain useful alone.

Create a new skill only for a repeated workflow with non-obvious knowledge or a
useful deterministic helper that existing capabilities do not cover. Retire a
skill only after checking callers, unique resources, invocation policy, and data
ownership. Never delete its ignored user data as part of definition retirement.

## Decisions and Verification

Choose a clear recommendation: keep, modernize, narrow, merge, split, or retire.
For a portfolio report, a compact table can record reuse, invocation clarity,
safety, and maintenance burden on a 1–5 scale; higher burden is worse, higher
other scores are better. Treat these as qualitative judgments, not measurements.
Classify roles as core, useful, optional, or retirement candidate when useful.
State confidence, the concrete reason, and any adoption condition for deferred
changes. Do not require a large per-skill template in every user response.

When editing, preserve names and CLI compatibility unless the chosen change
requires otherwise. Keep `SKILL.md`, `agents/openai.yaml`, referenced resources,
callers, and README inventory consistent. Do not reset unrelated policy or tool
dependencies when editing UI metadata.

Re-run static checks after edits and run the repository's documented verification
command. Test changed scripts against meaningful behavior. For a substantial
instruction change, use a realistic independent forward test when available and
authorized, following `skill-creator`; do not test wording alone.

Report the important decisions, applied changes, deliberately retained roles,
and completed versus missing evidence. Put detailed inventory in a reviewable
local artifact when it would overwhelm the answer. Report Xcode sync integrity
separately: managed count, marker/catalog errors, and prefix conflicts. Never
claim current upstream synchronization from local marker consistency alone.
