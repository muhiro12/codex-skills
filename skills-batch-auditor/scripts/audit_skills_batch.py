#!/usr/bin/env python3
"""Audit custom Codex skills for maintenance or refresh workflows."""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

GENERATED_DIRECTORIES = [
    ".build",
    "build",
    "DerivedData",
    ".git",
    ".swiftpm",
    "Pods",
    "Carthage",
]

STATUS_LABELS = {
    "aligned": "✅ aligned",
    "drift": "⚠ drift",
    "risky": "❌ risky",
}

STATUS_ORDER = {
    "risky": 0,
    "drift": 1,
    "aligned": 2,
}

ACTION_ORDER = {
    "retire": 0,
    "improve next": 1,
    "merge with another skill": 2,
    "keep as-is": 3,
}

ACTION_PRIORITY_BASE = {
    "retire": 80,
    "improve next": 60,
    "merge with another skill": 45,
    "keep as-is": 10,
}

REUSE_CUES = {
    "analyze",
    "audit",
    "develop",
    "inspect",
    "localize",
    "maintain",
    "review",
    "summarize",
    "sync",
    "verify",
    "write",
}

SCOPE_CUES = {
    "across",
    "all skills",
    "batch",
    "custom skills",
    "local skills",
    "multiple",
    "one-shot",
    "portfolio",
    "subset",
    "weekly",
}

NARROW_SCOPE_CUES = {
    "deprecated",
    "judgment required",
    "legacy",
    "one-off",
    "refresh only",
    "temporary",
}

MERGE_STOPWORDS = {
    "across",
    "agent",
    "agents",
    "all",
    "and",
    "any",
    "are",
    "artifact",
    "artifacts",
    "audit",
    "batch",
    "before",
    "build",
    "check",
    "checks",
    "coherent",
    "commit",
    "compatibility",
    "compatible",
    "condition",
    "conditions",
    "config",
    "configs",
    "contract",
    "contracts",
    "codex",
    "concise",
    "convention",
    "conventions",
    "coverage",
    "custom",
    "default",
    "drift",
    "entrypoint",
    "entrypoints",
    "existing",
    "fixture",
    "for",
    "from",
    "guidance",
    "hook",
    "hooks",
    "implement",
    "implementation",
    "improve",
    "internal",
    "japanese",
    "local",
    "lint",
    "maintenance",
    "multiple",
    "naming",
    "newest",
    "older",
    "only",
    "output",
    "polite",
    "prompt",
    "push",
    "read",
    "repo",
    "report",
    "repository",
    "return",
    "refresh",
    "reports",
    "reuse",
    "risk",
    "role",
    "roles",
    "run",
    "runs",
    "safe",
    "safely",
    "scan",
    "script",
    "scripts",
    "shell",
    "skill",
    "skills",
    "standard",
    "state",
    "such",
    "summaries",
    "summary",
    "sync",
    "task",
    "tasks",
    "that",
    "the",
    "their",
    "them",
    "there",
    "these",
    "this",
    "test",
    "tests",
    "trigger",
    "under",
    "update",
    "updates",
    "use",
    "verify",
    "verification",
    "when",
    "while",
    "with",
    "without",
    "workflow",
    "wrapper",
    "wrappers",
    "workflow",
}

MERGE_KEYWORD_MAX_DOCUMENT_FREQUENCY = 3
MERGE_MIN_SHARED_KEYWORDS = 2
MERGE_MIN_SIMILARITY = 0.18

FALLBACK_REQUIRED_INPUTS = [
    "全 Skill 名の一覧",
    "各 Skill の current config/instructions",
]

OPENAI_INTERFACE_FIELDS = (
    "display_name",
    "short_description",
    "default_prompt",
)
DEFAULT_VISIBILITY = "public"
VALID_VISIBILITIES = {"public", "internal"}
XCODE_SKILL_PREFIX = "xcode-skill-"
XCODE_SKILL_MARKER = ".xcode-skill-sync.json"
XCODE_SYNC_MANAGER = "sync-xcode-skills"

INSTRUCTION_MAINTENANCE_FIX_CODES = {
    "ci_entrypoint_not_aligned",
    "ci_policy_not_dynamic",
    "ci_artifact_root_not_aligned",
    "ci_artifacts_latest_rule_missing",
    "ci_artifacts_no_old_scan_rule_missing",
}

OPENAI_MAINTENANCE_FIX_CODES = {
    "display_name_snake_case",
    "default_prompt_missing_skill_reference",
}

MAINTENANCE_FIX_CODES = INSTRUCTION_MAINTENANCE_FIX_CODES | OPENAI_MAINTENANCE_FIX_CODES


@dataclass
class SkillRecord:
    name: str
    directory: Path
    is_system: bool
    classification: str
    visibility: str
    description: str
    instructions: str
    skill_text: str
    openai_text: str
    script_texts: dict[str, str]


@dataclass(frozen=True)
class SkillCompatibilityProfile:
    execution_family: str
    output_family: str
    scope_family: str
    mutability_posture: str


@dataclass
class Issue:
    code: str
    severity: str
    summary_ja: str
    fix_ja: str


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit local skills for maintenance or refresh workflows.",
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        help="Repository root used as workflow ground truth.",
    )
    parser.add_argument(
        "--skills-root",
        help="Skills root. Defaults to $CODEX_HOME/skills, then ~/.codex/skills.",
    )
    parser.add_argument(
        "--scope",
        choices=("custom", "all"),
        default="custom",
        help="Audit target scope.",
    )
    parser.add_argument(
        "--include-system",
        action="store_true",
        help="When scope=custom, include .system skills too.",
    )
    parser.add_argument(
        "--include-self",
        action="store_true",
        help="When scope=custom, include skills-batch-auditor itself in the audit targets.",
    )
    parser.add_argument(
        "--skill",
        action="append",
        default=[],
        help="Limit the run to a named skill. May be passed more than once.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )
    parser.add_argument(
        "--bundle-mode",
        choices=("full", "patch"),
        default="full",
        help="Applied-fix detail output mode. Use patch to include diffs.",
    )
    parser.add_argument(
        "--mode",
        choices=("maintenance", "refresh"),
        default="refresh",
        help="Workflow mode: maintenance applies deterministic consistency fixes; refresh proposes evolution only.",
    )
    return parser.parse_args()


def resolve_default_skills_root() -> Path:
    code_home = os.environ.get("CODEX_HOME")
    candidates: list[Path] = []

    if code_home:
        candidates.append((Path(code_home).expanduser() / "skills").resolve())

    candidates.append((Path("~/.codex/skills").expanduser()).resolve())

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_text_if_exists(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return read_text(path)


def parse_frontmatter(raw_frontmatter: str) -> dict[str, Any]:
    frontmatter: dict[str, Any] = {}
    current_mapping_key: str | None = None
    current_mapping_indent: int | None = None

    for line in raw_frontmatter.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if ":" not in stripped:
            continue

        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()

        if indent == 0:
            current_mapping_key = None
            current_mapping_indent = None
            if raw_value:
                frontmatter[key] = parse_simple_yaml_scalar(raw_value)
            else:
                frontmatter[key] = {}
                current_mapping_key = key
                current_mapping_indent = indent
            continue

        if current_mapping_key is None or current_mapping_indent is None or indent <= current_mapping_indent:
            continue

        nested_mapping = frontmatter.get(current_mapping_key)
        if not isinstance(nested_mapping, dict):
            continue

        nested_key, nested_raw_value = stripped.split(":", 1)
        nested_mapping[nested_key.strip()] = parse_simple_yaml_scalar(nested_raw_value.strip())

    return frontmatter


def parse_skill_markdown(skill_text: str) -> tuple[str, str, str, str]:
    match = re.match(r"^---\n(.*?)\n---\n?(.*)$", skill_text, re.DOTALL)
    if not match:
        return "", "", skill_text.strip(), DEFAULT_VISIBILITY

    raw_frontmatter, body = match.groups()
    frontmatter = parse_frontmatter(raw_frontmatter)

    metadata = frontmatter.get("metadata", {})
    visibility = DEFAULT_VISIBILITY
    if isinstance(metadata, dict):
        raw_visibility = metadata.get("visibility")
        if isinstance(raw_visibility, str):
            normalized_visibility = raw_visibility.strip().lower()
            if normalized_visibility in VALID_VISIBILITIES:
                visibility = normalized_visibility

    name = frontmatter.get("name", "")
    if not isinstance(name, str):
        name = ""

    description = frontmatter.get("description", "")
    if not isinstance(description, str):
        description = ""

    return (
        name,
        description,
        body.strip(),
        visibility,
    )


def parse_simple_yaml_scalar(raw_value: str) -> str:
    raw_value = raw_value.strip()
    if not raw_value:
        return ""

    if raw_value[0] == '"':
        characters: list[str] = []
        index = 1
        while index < len(raw_value):
            character = raw_value[index]
            if character == "\\" and index + 1 < len(raw_value):
                index += 1
                escaped = raw_value[index]
                characters.append(
                    {
                        '"': '"',
                        "\\": "\\",
                        "n": "\n",
                        "r": "\r",
                        "t": "\t",
                    }.get(escaped, escaped)
                )
                index += 1
                continue
            if character == '"':
                return "".join(characters)
            characters.append(character)
            index += 1
        return "".join(characters)

    if raw_value[0] == "'":
        characters = []
        index = 1
        while index < len(raw_value):
            character = raw_value[index]
            if character == "'":
                if index + 1 < len(raw_value) and raw_value[index + 1] == "'":
                    characters.append("'")
                    index += 2
                    continue
                return "".join(characters)
            characters.append(character)
            index += 1
        return "".join(characters)

    comment_index = raw_value.find(" #")
    if comment_index >= 0:
        return raw_value[:comment_index].rstrip()

    return raw_value


def parse_openai_interface_fields(openai_text: str) -> dict[str, str]:
    interface_fields: dict[str, str] = {}
    interface_indent: int | None = None
    inside_interface = False

    for line in openai_text.splitlines():
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip(" "))
        if not inside_interface:
            if stripped_line == "interface:":
                inside_interface = True
                interface_indent = indent
            continue

        if interface_indent is not None and indent <= interface_indent and not line.startswith(" "):
            break

        field_match = re.match(r"^\s*([A-Za-z0-9_]+)\s*:\s*(.*)$", line)
        if not field_match:
            continue

        field_name, raw_value = field_match.groups()
        if field_name not in OPENAI_INTERFACE_FIELDS:
            continue

        interface_fields[field_name] = parse_simple_yaml_scalar(raw_value)

    return interface_fields


def yaml_double_quoted(value: str) -> str:
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def title_case_skill_name(skill_name: str) -> str:
    words = [word for word in re.split(r"[-_]+", skill_name) if word]
    return " ".join(word[:1].upper() + word[1:] for word in words)


def replace_interface_field(openai_text: str, field_name: str, value: str) -> str:
    lines = openai_text.splitlines()
    output_newline = "\n" if openai_text.endswith("\n") else ""
    interface_indent: int | None = None
    interface_index: int | None = None
    inside_interface = False
    replacement = yaml_double_quoted(value)

    for index, line in enumerate(lines):
        stripped_line = line.strip()
        indent = len(line) - len(line.lstrip(" "))

        if not inside_interface:
            if stripped_line == "interface:":
                inside_interface = True
                interface_indent = indent
                interface_index = index
            continue

        if interface_indent is not None and indent <= interface_indent and stripped_line:
            break

        field_match = re.match(r"^(\s*)([A-Za-z0-9_]+)\s*:\s*(.*)$", line)
        if field_match and field_match.group(2) == field_name:
            lines[index] = f"{field_match.group(1)}{field_name}: {replacement}"
            return "\n".join(lines) + output_newline

    if interface_index is None:
        lines.extend(["interface:", f"  {field_name}: {replacement}"])
    else:
        lines.insert(interface_index + 1, f"  {field_name}: {replacement}")

    return "\n".join(lines) + "\n"


def replace_skill_markdown_body(skill_text: str, updated_instructions: str) -> str:
    match = re.match(r"^---\n(.*?)\n---\n?(.*)$", skill_text, re.DOTALL)
    if not match:
        return updated_instructions.rstrip() + "\n"

    raw_frontmatter = match.group(1)
    return f"---\n{raw_frontmatter}\n---\n\n{updated_instructions.rstrip()}\n"


def iter_skill_directories(
    skills_root: Path,
    scope: str,
    include_system: bool,
) -> list[Path]:
    directories: list[Path] = []

    for child in sorted(path for path in skills_root.iterdir() if path.is_dir()):
        if child.name == ".system":
            if scope == "all" or include_system:
                directories.extend(
                    sorted(
                        system_child
                        for system_child in child.iterdir()
                        if system_child.is_dir() and (system_child / "SKILL.md").is_file()
                    )
                )
            continue

        if (child / "SKILL.md").is_file():
            directories.append(child)

    return directories


def classify_skill_directory(skill_directory: Path) -> str:
    if ".system" in skill_directory.parts:
        return "system"
    if (skill_directory / XCODE_SKILL_MARKER).exists():
        return "managed-external"
    if skill_directory.name.startswith(XCODE_SKILL_PREFIX):
        return "unmanaged-xcode-prefix"
    return "custom"


def discover_skill_records(
    skills_root: Path,
    scope: str,
    include_system: bool,
    include_self: bool,
) -> list[SkillRecord]:
    records: list[SkillRecord] = []

    for skill_directory in iter_skill_directories(skills_root, scope, include_system):
        if skill_directory.name == "skills-batch-auditor" and not include_self:
            continue

        classification = classify_skill_directory(skill_directory)
        is_system = classification == "system"

        skill_file = skill_directory / "SKILL.md"
        skill_text = read_text_if_exists(skill_file)
        skill_name, description, instructions, visibility = parse_skill_markdown(skill_text)

        if not skill_name:
            skill_name = skill_directory.name

        openai_path = skill_directory / "agents" / "openai.yaml"
        openai_text = read_text_if_exists(openai_path)

        script_texts: dict[str, str] = {}
        scripts_directory = skill_directory / "scripts"
        if scripts_directory.exists() and scripts_directory.is_dir():
            for script_path in sorted(scripts_directory.rglob("*")):
                if not script_path.is_file():
                    continue
                if script_path.suffix not in {".py", ".sh", ".md", ".txt"}:
                    continue
                relative_script_path = str(script_path.relative_to(skill_directory))
                script_texts[relative_script_path] = read_text_if_exists(script_path)

        records.append(
            SkillRecord(
                name=skill_name,
                directory=skill_directory,
                is_system=is_system,
                classification=classification,
                visibility=visibility,
                description=description,
                instructions=instructions,
                skill_text=skill_text,
                openai_text=openai_text,
                script_texts=script_texts,
            )
        )

    return records


def choose_canonical_entrypoint(agents_text: str, ci_script_rel_paths: list[str]) -> str | None:
    agents_commands = re.findall(r"bash\s+ci_scripts/[A-Za-z0-9_./-]+\.sh", agents_text)
    if agents_commands:
        for command in agents_commands:
            if command.endswith("verify_task_completion.sh"):
                return command
        for command in agents_commands:
            if command.endswith("verify.sh"):
                return command
        for command in agents_commands:
            if command.endswith("verify_repository_state.sh"):
                return command
        return agents_commands[0]

    priority_rel_paths = [
        "ci_scripts/tasks/verify_task_completion.sh",
        "ci_scripts/tasks/verify.sh",
        "ci_scripts/verify.sh",
        "ci_scripts/tasks/verify_repository_state.sh",
        "ci_scripts/tasks/run_required_builds.sh",
        "ci_scripts/run_required_builds.sh",
    ]
    for rel_path in priority_rel_paths:
        if rel_path in ci_script_rel_paths:
            return f"bash {rel_path}"

    if ci_script_rel_paths:
        return f"bash {sorted(ci_script_rel_paths)[0]}"

    return None


def choose_run_required_entrypoint(
    ci_script_rel_paths: list[str],
    canonical_entrypoint: str | None,
) -> str | None:
    preferred = [
        "ci_scripts/tasks/verify_repository_state.sh",
        "ci_scripts/tasks/run_required_builds.sh",
        "ci_scripts/run_required_builds.sh",
    ]
    for rel_path in preferred:
        if rel_path in ci_script_rel_paths:
            return f"bash {rel_path}"

    if canonical_entrypoint and "run_required_builds.sh" in canonical_entrypoint:
        return canonical_entrypoint

    return None


def resolve_overview_doc_path(repo_root: Path) -> Path:
    docs_dir = repo_root / "docs"
    default_path = docs_dir / "current-overview.md"
    if default_path.exists():
        return default_path

    if docs_dir.exists() and docs_dir.is_dir():
        overview_matches = sorted(
            path for path in docs_dir.glob("*current-overview.md") if path.is_file()
        )
        if overview_matches:
            return overview_matches[0]

    return default_path


def extract_ground_truth(repo_root: Path, include_doc_source: bool) -> dict[str, Any]:
    agents_path = repo_root / "AGENTS.md"
    pre_commit_path = repo_root / ".pre-commit-config.yaml"
    docs_path = resolve_overview_doc_path(repo_root)

    ci_script_files: list[Path] = []
    ci_root = repo_root / "ci_scripts"
    if ci_root.exists() and ci_root.is_dir():
        ci_script_files = sorted(path for path in ci_root.rglob("*.sh") if path.is_file())

    ci_script_rel_paths = [str(path.relative_to(repo_root)) for path in ci_script_files]

    agents_text = read_text_if_exists(agents_path)
    canonical_entrypoint = choose_canonical_entrypoint(agents_text, ci_script_rel_paths)
    run_required_entrypoint = choose_run_required_entrypoint(ci_script_rel_paths, canonical_entrypoint)
    ci_ground_truth_available = canonical_entrypoint is not None

    artifact_root = ".build/ci/runs/<RUN_ID>/"
    artifact_match = re.search(r"`(\.build/ci/runs/<RUN_ID>/)`", agents_text)
    if artifact_match:
        artifact_root = artifact_match.group(1)

    retention_count = 5
    retention_match = re.search(r"newest\s+(\d+)\s+run", agents_text, re.IGNORECASE)
    if retention_match:
        retention_count = int(retention_match.group(1))

    environment_variables: set[str] = set()
    for script_path in ci_script_files:
        script_text = read_text_if_exists(script_path)
        environment_variables.update(re.findall(r"\bAI_RUN_[A-Z_]+\b", script_text))

    optional_doc_source_used = include_doc_source and docs_path.exists()

    sources_read: list[str] = []
    if agents_path.exists():
        sources_read.append(str(agents_path.relative_to(repo_root)))
    sources_read.extend(ci_script_rel_paths)
    if pre_commit_path.exists():
        sources_read.append(str(pre_commit_path.relative_to(repo_root)))
    if optional_doc_source_used:
        sources_read.append(str(docs_path.relative_to(repo_root)))

    return {
        "repo_root": str(repo_root),
        "canonical_entrypoint": canonical_entrypoint or "",
        "run_required_entrypoint": run_required_entrypoint or "",
        "ci_ground_truth_available": ci_ground_truth_available,
        "artifact_root": artifact_root,
        "retention_count": retention_count,
        "environment_variables": sorted(environment_variables),
        "generated_directories": GENERATED_DIRECTORIES,
        "response_language_expectation": "Japanese concise polite",
        "sources_read": sources_read,
        "optional_doc_source_used": optional_doc_source_used,
    }


def first_sentence(text: str) -> str:
    compact = " ".join(text.split())
    if not compact:
        return "(intent unavailable)"

    sentence_match = re.split(r"(?<=[.!?])\s+", compact)
    if sentence_match:
        return sentence_match[0]
    return compact


def needs_doc_source(records: list[SkillRecord]) -> bool:
    markers = ["doc", "documentation", "overview", "architecture"]
    for record in records:
        haystack = f"{record.name} {record.description}".lower()
        if any(marker in haystack for marker in markers):
            return True
    return False


def has_generated_directory_guard(script_texts: dict[str, str]) -> bool:
    if not script_texts:
        return False

    combined_script_text = "\n".join(script_texts.values()).lower()
    return all(directory.lower() in combined_script_text for directory in GENERATED_DIRECTORIES)


def add_issue(issues: list[Issue], code: str, severity: str, summary_ja: str, fix_ja: str) -> None:
    issues.append(
        Issue(
            code=code,
            severity=severity,
            summary_ja=summary_ja,
            fix_ja=fix_ja,
        )
    )


def clamp_score(value: int) -> int:
    return max(1, min(5, value))


def text_contains_any(text: str, markers: set[str]) -> bool:
    return any(marker in text for marker in markers)


def build_skill_corpus(skill: SkillRecord) -> str:
    return "\n".join(
        [
            skill.name,
            skill.description,
            skill.instructions,
            skill.openai_text,
            "\n".join(skill.script_texts.values()),
        ]
    ).lower()


def text_contains_marker(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def has_concrete_repository_reference(text: str) -> bool:
    sibling_path_match = re.search(
        r"(?<![\w./-])\.\./[a-z0-9][a-z0-9_-]*(?=(?:/|`|'|\"|\s|[.,:)\]]|$))",
        text,
    )
    if sibling_path_match:
        return True

    scoped_work_match = re.search(
        r"\b(?:develop|modify only|work inside|stay inside)\s+`?[a-z][a-z0-9_-]+/`?",
        text,
    )
    return scoped_work_match is not None


def infer_execution_family(text: str) -> str:
    if text_contains_marker(
        text,
        (
            "app store connect",
            "what's new in this version",
            "what's new text",
            "release notes",
            "release-note bodies",
        ),
    ):
        return "release_copywriting"

    if text_contains_marker(
        text,
        (
            "swiftdata",
            "@model",
            "@relationship",
            "versionedschema",
            "schemamigrationplan",
            "schema definitions",
        ),
    ):
        return "schema_inspection"

    if text_contains_marker(
        text,
        (
            "footprint",
            "measure_footprint.py",
            "meaningful loc",
            "healthy structure",
            "architectural concentration",
            "maintenance risk",
        ),
    ):
        return "footprint_diagnosis"

    if text_contains_marker(
        text,
        (
            "custom codex skills",
            "custom skills",
            "agents/openai.yaml",
            "batch update bundle",
            "portfolio classification",
            "portfolio prioritization",
            "local skills root",
        ),
    ):
        return "portfolio_audit"

    if text_contains_marker(
        text,
        (
            "ci/runs/<run_id>",
            "push-readiness",
            "push risk",
            "current git diff",
            "verify-oriented repository ci",
            "latest ci run",
        ),
    ):
        return "ci_verification"

    if has_concrete_repository_reference(text):
        return "repo_specific_development"

    if text_contains_marker(
        text,
        (
            "look at recent changes and keep developing",
            "exactly one safe next task",
            "continue development",
            "execute with minimal scope",
            "implement it",
        ),
    ):
        return "code_mutation"

    if text_contains_marker(
        text,
        (
            "overview notes",
            "overview report",
            "overview wording",
            "overview markdown",
        ),
    ):
        return "overview_maintenance"

    return "general_analysis"


def infer_output_family(text: str) -> str:
    if text_contains_marker(
        text,
        (
            "block` / `proceed with caution` / `proceed`",
            "release-blocking risk",
            "manual inspection is complete",
            "主要リスク",
        ),
    ):
        return "risk_decision"

    if text_contains_marker(
        text,
        (
            "what's new in this version",
            "each supported locale",
            "app store connect-ready",
            "各ロケール本文",
        ),
    ):
        return "localized_release_text"

    if text_contains_marker(
        text,
        (
            "pushリスク",
            "push-ready",
            "push readiness",
            "current git diff",
            "最新run",
        ),
    ):
        return "push_readiness_judgment"

    if text_contains_marker(
        text,
        (
            "規模要点",
            "保守リスク top 3",
            "健全構造シグナル top 3",
            "footprint diagnosis",
        ),
    ):
        return "footprint_diagnosis"

    if text_contains_marker(
        text,
        (
            "エンティティ一覧",
            "relationshipレビュー",
            "schema review",
            "migration hotspots",
        ),
    ):
        return "schema_review"

    if text_contains_marker(
        text,
        (
            "更新バンドル（一括提案）",
            "batch update bundle",
            "skill definitions",
            "portfolio classification",
        ),
    ):
        return "skill_audit_report"

    if text_contains_marker(
        text,
        (
            "overview report",
            "overview wording",
            "overview notes",
        ),
    ):
        return "overview_report"

    if text_contains_marker(
        text,
        (
            "変更概要",
            "変更ファイル",
            "選んだタスク",
            "changes made",
            "implementation task",
        ),
    ):
        return "implementation_work"

    return "general_report"


def infer_scope_family(text: str) -> str:
    if has_concrete_repository_reference(text):
        return "repo_specific"

    return "repo_agnostic"


def infer_mutability_posture(text: str) -> str:
    write_capable = text_contains_marker(
        text,
        (
            "implement",
            "modify ",
            "refactor",
            "write operations",
            "apply minimal safe scope",
            "execute with minimal scope",
            "--apply",
            "apply maintenance updates",
            "modifying source files",
        ),
    )
    read_only = text_contains_marker(
        text,
        (
            "read-only",
            "never edit",
            "do not edit",
            "without changing code",
            "never modify source files",
            "stay read-only",
        ),
    )

    if write_capable and not read_only:
        return "write_capable"
    if read_only and not write_capable:
        return "read_only"
    if write_capable:
        return "write_capable"
    return "read_only"


def build_skill_compatibility_profile(skill: SkillRecord) -> SkillCompatibilityProfile:
    text = build_skill_corpus(skill)
    return SkillCompatibilityProfile(
        execution_family=infer_execution_family(text),
        output_family=infer_output_family(text),
        scope_family=infer_scope_family(text),
        mutability_posture=infer_mutability_posture(text),
    )


def score_skill_dimensions(
    skill: SkillRecord,
    interface_fields: dict[str, str],
    issue_codes: list[str],
    refresh_issue_codes: list[str],
    status: str,
) -> dict[str, int]:
    lower_description = skill.description.lower()
    lower_instructions = skill.instructions.lower()
    lower_text = f"{lower_description}\n{lower_instructions}"
    issue_code_set = set(issue_codes)

    reuse_value = 1
    if 30 <= len(skill.description.strip()) <= 220:
        reuse_value += 1
    if text_contains_any(lower_text, REUSE_CUES):
        reuse_value += 1
    if text_contains_any(lower_text, SCOPE_CUES):
        reuse_value += 1
    if skill.script_texts or "## workflow" in lower_instructions or "## trigger conditions" in lower_instructions:
        reuse_value += 1
    if text_contains_any(lower_text, NARROW_SCOPE_CUES):
        reuse_value -= 1

    clarity_of_invocation = 1
    if (
        "use when" in lower_description
        or "use for" in lower_description
        or "## trigger conditions" in lower_instructions
    ):
        clarity_of_invocation += 1
    if interface_fields.get("default_prompt") and f"${skill.name}" in interface_fields["default_prompt"]:
        clarity_of_invocation += 1
    if re.search(r"japanese|日本語", skill.skill_text, re.IGNORECASE) or "## response contract" in lower_instructions:
        clarity_of_invocation += 1
    if 40 <= len(skill.description.strip()) <= 200:
        clarity_of_invocation += 1
    if "## workflow" in lower_instructions:
        clarity_of_invocation += 1
    if not skill.openai_text.strip() and skill.visibility != "internal":
        clarity_of_invocation -= 1

    safety = 5
    if status == "risky":
        safety -= 3
    if issue_code_set.intersection(
        {
            "ci_entrypoint_not_aligned",
            "ci_policy_not_dynamic",
            "ci_artifacts_latest_rule_missing",
            "ci_artifacts_no_old_scan_rule_missing",
            "generated_directory_guard_missing",
        }
    ):
        safety -= 1
    if "recursive_generated_scan" in issue_code_set:
        safety -= 1

    maintenance_burden = 1
    if skill.script_texts:
        maintenance_burden += 1
    if issue_codes:
        maintenance_burden += 1
    if len(issue_codes) >= 3:
        maintenance_burden += 1
    if refresh_issue_codes:
        maintenance_burden += 1
    if len(skill.script_texts) > 1 or len(skill.instructions.splitlines()) > 120:
        maintenance_burden += 1

    return {
        "reuse value": clamp_score(reuse_value),
        "clarity of invocation": clamp_score(clarity_of_invocation),
        "safety": clamp_score(safety),
        "maintenance burden": clamp_score(maintenance_burden),
    }


def classify_skill(scores: dict[str, int], status: str) -> str:
    reuse_value = scores["reuse value"]
    clarity_of_invocation = scores["clarity of invocation"]
    safety = scores["safety"]
    maintenance_burden = scores["maintenance burden"]

    if (reuse_value <= 2 and (safety <= 2 or maintenance_burden >= 4)) or (
        safety <= 2 and maintenance_burden >= 4
    ):
        return "retire candidate"

    if (
        status == "aligned"
        and reuse_value >= 4
        and clarity_of_invocation >= 4
        and safety >= 4
        and maintenance_burden <= 2
    ):
        return "core"

    if reuse_value >= 3 and clarity_of_invocation >= 3 and safety >= 3:
        return "useful"

    return "optional"


def extract_skill_keywords(skill: SkillRecord) -> set[str]:
    raw_tokens = re.findall(
        r"[a-z0-9][a-z0-9-]{2,}",
        f"{skill.name} {skill.description} {skill.instructions}".lower(),
    )

    keywords: set[str] = set()
    for token in raw_tokens:
        for part in token.split("-"):
            if len(part) < 3 or part in MERGE_STOPWORDS:
                continue
            keywords.add(part)

    return keywords


def build_keyword_document_frequency(keyword_map: dict[str, set[str]]) -> dict[str, int]:
    document_frequency: dict[str, int] = {}
    for keywords in keyword_map.values():
        for keyword in keywords:
            document_frequency[keyword] = document_frequency.get(keyword, 0) + 1
    return document_frequency


def filter_distinctive_keywords(
    keywords: set[str],
    document_frequency: dict[str, int],
) -> set[str]:
    return {
        keyword
        for keyword in keywords
        if document_frequency.get(keyword, 0) <= MERGE_KEYWORD_MAX_DOCUMENT_FREQUENCY
    }


def portfolio_strength(item: dict[str, Any]) -> int:
    scores = item["scores"]
    strength = (
        scores["reuse value"] * 3
        + scores["clarity of invocation"] * 2
        + scores["safety"] * 3
        - scores["maintenance burden"] * 2
    )
    if item["status"] == "aligned":
        strength += 2
    if item["portfolio_classification"] == "core":
        strength += 2
    return strength


def choose_merge_target(
    item: dict[str, Any],
    report_items: list[dict[str, Any]],
    keyword_map: dict[str, set[str]],
    keyword_document_frequency: dict[str, int],
    compatibility_profiles: dict[str, SkillCompatibilityProfile],
) -> tuple[str, list[str]]:
    if item["portfolio_classification"] in {"core", "retire candidate"}:
        return "", []

    current_keywords = filter_distinctive_keywords(
        keyword_map.get(item["name"], set()),
        keyword_document_frequency,
    )
    if len(current_keywords) < MERGE_MIN_SHARED_KEYWORDS:
        return "", []

    current_profile = compatibility_profiles.get(item["name"])
    if current_profile is None:
        return "", []

    current_strength = portfolio_strength(item)
    best_target = ""
    best_overlap: list[str] = []
    best_similarity = 0.0

    for other in report_items:
        if other["name"] == item["name"]:
            continue
        if other["portfolio_classification"] == "retire candidate":
            continue
        other_profile = compatibility_profiles.get(other["name"])
        if other_profile is None:
            continue
        if other_profile != current_profile:
            continue

        other_keywords = filter_distinctive_keywords(
            keyword_map.get(other["name"], set()),
            keyword_document_frequency,
        )
        overlap = sorted(current_keywords & other_keywords)
        if len(overlap) < MERGE_MIN_SHARED_KEYWORDS:
            continue

        union = current_keywords | other_keywords
        similarity = len(overlap) / max(1, len(union))
        if similarity < MERGE_MIN_SIMILARITY:
            continue

        other_strength = portfolio_strength(other)
        if other_strength <= current_strength:
            continue

        if similarity > best_similarity or (
            similarity == best_similarity and other_strength > current_strength
        ):
            best_target = other["name"]
            best_overlap = overlap
            best_similarity = similarity

    return best_target, best_overlap


def choose_recommended_action(item: dict[str, Any]) -> str:
    if item["portfolio_classification"] == "retire candidate":
        return "retire"

    if item.get("merge_target") and item["scores"]["reuse value"] <= 3:
        return "merge with another skill"

    if (
        item["status"] == "aligned"
        and item["scores"]["safety"] >= 4
        and not item.get("merge_target")
        and not item["issue_codes"]
        and not item["refresh_issue_codes"]
    ):
        return "keep as-is"

    return "improve next"


def build_priority_note(item: dict[str, Any]) -> str:
    action = item["recommended_action"]
    if action == "retire":
        return "安全性または再利用価値が低く、保守負債に対して維持価値が見合っていません。"
    if action == "merge with another skill":
        merge_target = item.get("merge_target", "")
        if merge_target:
            return f"`{merge_target}` と用途が近く、統合した方が保守負荷を下げやすい状態です。"
        return "用途重複が見込まれるため、統合候補として扱うのが妥当です。"
    if action == "improve next":
        return "再利用価値はあるため、現役のまま次の保守対象として改善を進めるべきです。"
    return "現状の定義で安定しており、直近の追加保守は不要です。"


def calculate_priority_score(item: dict[str, Any]) -> int:
    scores = item["scores"]
    priority = ACTION_PRIORITY_BASE[item["recommended_action"]]
    priority += (5 - scores["safety"]) * 6
    priority += scores["maintenance burden"] * 5
    priority += scores["reuse value"] * 4
    priority += (5 - scores["clarity of invocation"]) * 3
    priority += len(item["issue_codes"]) * 2
    return min(100, priority)


def enrich_portfolio_prioritization(
    report_items: list[dict[str, Any]],
    skill_records: dict[str, SkillRecord],
) -> list[dict[str, Any]]:
    keyword_map = {
        name: extract_skill_keywords(skill_records[name])
        for name in skill_records
        if name in {item["name"] for item in report_items}
    }
    keyword_document_frequency = build_keyword_document_frequency(keyword_map)
    compatibility_profiles = {
        name: build_skill_compatibility_profile(skill_records[name])
        for name in skill_records
        if name in {item["name"] for item in report_items}
    }

    for item in report_items:
        merge_target, shared_keywords = choose_merge_target(
            item,
            report_items,
            keyword_map,
            keyword_document_frequency,
            compatibility_profiles,
        )
        item["merge_target"] = merge_target
        item["merge_shared_keywords"] = shared_keywords
        item["recommended_action"] = choose_recommended_action(item)
        if item["recommended_action"] != "merge with another skill":
            item["merge_target"] = ""
            item["merge_shared_keywords"] = []
        item["priority_note_ja"] = build_priority_note(item)
        item["maintenance_priority_score"] = calculate_priority_score(item)

    return report_items


def analyze_skill(skill: SkillRecord, ground_truth: dict[str, Any]) -> dict[str, Any]:
    if skill.classification == "unmanaged-xcode-prefix":
        return analyze_unmanaged_xcode_prefix_skill(skill)

    issues: list[Issue] = []
    interface_fields: dict[str, str] = {}

    combined_text = "\n".join(
        [
            skill.skill_text,
            skill.openai_text,
            "\n".join(skill.script_texts.values()),
        ]
    )
    lower_text = combined_text.lower()

    has_japanese_output_rule = bool(re.search(r"japanese|日本語", skill.skill_text, re.IGNORECASE))
    if not has_japanese_output_rule:
        add_issue(
            issues,
            code="missing_japanese_output_rule",
            severity="drift",
            summary_ja="出力言語の既定が日本語で明示されていません。",
            fix_ja="出力は日本語で簡潔・丁寧に返す規則を明記してください。",
        )

    if not skill.openai_text.strip():
        if skill.visibility != "internal":
            add_issue(
                issues,
                code="missing_openai_yaml",
                severity="drift",
                summary_ja="`agents/openai.yaml` が不足しています。",
                fix_ja="UIメタデータ用に `agents/openai.yaml` を追加してください。",
            )
    else:
        interface_fields = parse_openai_interface_fields(skill.openai_text)
        display_name = interface_fields.get("display_name", "")
        short_description = interface_fields.get("short_description", "")
        default_prompt = interface_fields.get("default_prompt", "")

        if display_name and re.fullmatch(r"[a-z0-9_]+", display_name):
            add_issue(
                issues,
                code="display_name_snake_case",
                severity="drift",
                summary_ja="`display_name` が人間向け表示名として読みづらい形式です。",
                fix_ja="`display_name` は Title Case などの人間可読形式にしてください。",
            )

        if short_description and not (25 <= len(short_description) <= 64):
            add_issue(
                issues,
                code="short_description_length_invalid",
                severity="drift",
                summary_ja="`short_description` の長さが推奨範囲(25-64)外です。",
                fix_ja="`short_description` を 25〜64 文字に調整してください。",
            )

        required_prompt_token = f"${skill.name}"
        if default_prompt and required_prompt_token not in default_prompt:
            add_issue(
                issues,
                code="default_prompt_missing_skill_reference",
                severity="drift",
                summary_ja="`default_prompt` に `$<skill-name>` 参照が含まれていません。",
                fix_ja=f"`default_prompt` に `{required_prompt_token}` を含めてください。",
            )

    hardcoded_ci_commands = sorted(
        set(re.findall(r"bash\s+ci_scripts/[A-Za-z0-9_./-]+\.sh", combined_text))
    )
    mentions_dynamic_ci_policy = (
        "AGENTS.md" in combined_text
        and (
            "entrypoint" in lower_text
            or "build and test entry point" in lower_text
            or "標準エントリポイント" in lower_text
            or "fallback" in lower_text
            or "フォールバック" in skill.skill_text
        )
    )

    canonical_entrypoint = ground_truth.get("canonical_entrypoint", "")
    ci_ground_truth_available = ground_truth.get(
        "ci_ground_truth_available",
        bool(canonical_entrypoint),
    )
    artifact_root = ground_truth.get("artifact_root", "")
    expected_artifact_prefix = artifact_root.replace("/<RUN_ID>/", "").rstrip("/")
    if skill.name != "ci-verify-and-summarize" and hardcoded_ci_commands and ci_ground_truth_available:
        if canonical_entrypoint and canonical_entrypoint not in hardcoded_ci_commands:
            add_issue(
                issues,
                code="ci_entrypoint_not_aligned",
                severity="drift",
                summary_ja="ハードコードされたCI実行コマンドがリポジトリ標準と一致していません。",
                fix_ja=(
                    "`AGENTS.md` を優先し、未定義時は `ci_scripts/**/*.sh` を検出して、"
                    "必要時のみ標準CIコマンドを使用してください。"
                ),
            )

        if not mentions_dynamic_ci_policy:
            add_issue(
                issues,
                code="ci_policy_not_dynamic",
                severity="drift",
                summary_ja="CIエントリポイントの動的解決ポリシーが明記されていません。",
                fix_ja=(
                    "`AGENTS.md` を先に確認し、未定義時は `ci_scripts/**/*.sh` へ"
                    "フォールバックする方針を明記してください。"
                ),
            )

    artifact_reference_match = re.search(
        r"\.build/ci(?:/[^`/\s\"']*run[^`/\s\"']*|_[^`/\s\"']*run[^`/\s\"']*)",
        combined_text,
    )
    artifact_reference_prefix = artifact_reference_match.group(0) if artifact_reference_match else ""
    if (
        ci_ground_truth_available
        and artifact_reference_prefix
        and expected_artifact_prefix
        and artifact_reference_prefix != expected_artifact_prefix
    ):
        add_issue(
            issues,
            code="ci_artifact_root_not_aligned",
            severity="drift",
            summary_ja="CI成果物パスがリポジトリ標準と一致していません。",
            fix_ja=f"`{expected_artifact_prefix}/<RUN_ID>/` を標準のCI成果物パスとして参照してください。",
        )

    if artifact_reference_prefix:
        has_latest_rule = bool(
            re.search(r"latest|newest|lexicographically greatest|最新", lower_text)
        )
        if not has_latest_rule:
            add_issue(
                issues,
                code="ci_artifacts_latest_rule_missing",
                severity="drift",
                summary_ja="CI成果物参照時の最新RUN限定ルールが不足しています。",
                fix_ja=f"`{artifact_reference_prefix}` は最新RUNのみ参照する規則を追加してください。",
            )

        has_no_old_scan_rule = bool(
            re.search(r"do not scan older|do not inspect older|no older runs|older runs|古いrun.*参照しない", lower_text)
        )
        if not has_no_old_scan_rule:
            add_issue(
                issues,
                code="ci_artifacts_no_old_scan_rule_missing",
                severity="drift",
                summary_ja="古いRUNを走査しない明示ルールが不足しています。",
                fix_ja=f"`{artifact_reference_prefix}` 配下では古いRUNを走査しないことを明記してください。",
            )

    risky_generated_scan_pattern = bool(
        re.search(r"find\s+\.build(?!/ci/runs)|rglob\([^\n]*\.build|os\.walk\([^\n]*\.build", lower_text)
    )
    if risky_generated_scan_pattern:
        add_issue(
            issues,
            code="recursive_generated_scan",
            severity="risky",
            summary_ja="生成ディレクトリの再帰走査リスクがあります。",
            fix_ja="`.build` など生成ディレクトリは最新RUNの必要範囲以外を再帰走査しないでください。",
        )

    if skill.script_texts and not has_generated_directory_guard(skill.script_texts):
        maybe_repo_scan = any(
            token in lower_text
            for token in [
                "rglob(",
                "os.walk(",
                "find .",
                "rg --files",
            ]
        )
        if maybe_repo_scan:
            add_issue(
                issues,
                code="generated_directory_guard_missing",
                severity="drift",
                summary_ja="生成ディレクトリ除外のガードが読み取りづらい状態です。",
                fix_ja=(
                    "`.build/build/DerivedData/.git/.swiftpm/Pods/Carthage` を"
                    "明示的に除外してください。"
                ),
            )

    if not issues:
        status = "aligned"
    elif any(issue.severity == "risky" for issue in issues):
        status = "risky"
    else:
        status = "drift"

    unique_issue_summaries = list(dict.fromkeys(issue.summary_ja for issue in issues))
    unique_fixes = list(dict.fromkeys(issue.fix_ja for issue in issues))
    issue_codes = list(dict.fromkeys(issue.code for issue in issues))
    maintenance_issue_codes = [code for code in issue_codes if code in MAINTENANCE_FIX_CODES]
    refresh_issue_codes = [code for code in issue_codes if code not in MAINTENANCE_FIX_CODES]
    scores = score_skill_dimensions(
        skill=skill,
        interface_fields=interface_fields,
        issue_codes=issue_codes,
        refresh_issue_codes=refresh_issue_codes,
        status=status,
    )
    portfolio_classification = classify_skill(scores, status)

    return {
        "name": skill.name,
        "intent": first_sentence(skill.description),
        "status": status,
        "status_label": STATUS_LABELS[status],
        "issues": unique_issue_summaries,
        "recommended_fix": unique_fixes,
        "issue_codes": issue_codes,
        "maintenance_issue_codes": maintenance_issue_codes,
        "refresh_issue_codes": refresh_issue_codes,
        "scores": scores,
        "portfolio_classification": portfolio_classification,
        "directory": str(skill.directory),
        "is_system": skill.is_system,
        "classification": skill.classification,
        "visibility": skill.visibility,
    }


def analyze_unmanaged_xcode_prefix_skill(skill: SkillRecord) -> dict[str, Any]:
    issue_codes = ["unmanaged_xcode_prefix"]
    scores = {
        "reuse value": 1,
        "clarity of invocation": 1,
        "safety": 1,
        "maintenance burden": 4,
    }

    return {
        "name": skill.name,
        "intent": first_sentence(skill.description),
        "status": "risky",
        "status_label": STATUS_LABELS["risky"],
        "issues": [
            "`xcode-skill-*` は Xcode 由来 Skill 用の予約 prefix ですが、同期管理メタデータがありません。"
        ],
        "recommended_fix": [
            "`sync-xcode-skills` 管理下に入れるか、Xcode 由来ではないなら別名へ変更してください。"
        ],
        "issue_codes": issue_codes,
        "maintenance_issue_codes": [],
        "refresh_issue_codes": issue_codes,
        "scores": scores,
        "portfolio_classification": "retire candidate",
        "directory": str(skill.directory),
        "is_system": skill.is_system,
        "classification": skill.classification,
        "visibility": skill.visibility,
    }


def load_xcode_skill_catalog(skills_root: Path) -> dict[str, Any]:
    state_dir = skills_root / XCODE_SYNC_MANAGER / "state"
    catalog_json_path = state_dir / "catalog.json"
    catalog_md_path = state_dir / "catalog.md"

    if catalog_json_path.exists():
        try:
            catalog = json.loads(catalog_json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            return {
                "status": "risky",
                "source": str(catalog_json_path),
                "installed_names": [],
                "entries": {},
                "issues": [
                    {
                        "code": "xcode_catalog_json_unreadable",
                        "summary_ja": f"`{catalog_json_path}` を JSON として読めません: {error}",
                        "fix_ja": "`sync-xcode-skills` を再実行して catalog state を再生成してください。",
                    }
                ],
            }

        entries = {
            str(entry.get("installed_name", "")): entry
            for entry in catalog.get("skills", [])
            if isinstance(entry, dict) and entry.get("installed_name")
        }
        return {
            "status": "aligned",
            "source": str(catalog_json_path),
            "installed_names": sorted(entries),
            "entries": entries,
            "issues": [],
        }

    if catalog_md_path.exists():
        catalog_text = catalog_md_path.read_text(encoding="utf-8", errors="replace")
        installed_names = sorted(set(re.findall(r"`(xcode-skill-[^`]+)`", catalog_text)))
        return {
            "status": "drift",
            "source": str(catalog_md_path),
            "installed_names": installed_names,
            "entries": {name: {"installed_name": name} for name in installed_names},
            "issues": [
                {
                    "code": "xcode_catalog_json_missing",
                    "summary_ja": "`catalog.json` がないため `catalog.md` から同期状態を推定しています。",
                    "fix_ja": "`sync-xcode-skills` を再実行して catalog state を再生成してください。",
                }
            ],
        }

    return {
        "status": "risky",
        "source": "",
        "installed_names": [],
        "entries": {},
        "issues": [
            {
                "code": "xcode_catalog_missing",
                "summary_ja": "`sync-xcode-skills/state/catalog.json` または `catalog.md` が見つかりません。",
                "fix_ja": "`sync-xcode-skills` を実行して Xcode Skill catalog を生成してください。",
            }
        ],
    }


def analyze_xcode_sync_integrity(
    skills_root: Path,
    records: list[SkillRecord],
    *,
    check_catalog_missing_directories: bool,
) -> dict[str, Any]:
    managed_records = [record for record in records if record.classification == "managed-external"]
    unmanaged_prefix_records = [
        record for record in records if record.classification == "unmanaged-xcode-prefix"
    ]
    catalog = load_xcode_skill_catalog(skills_root)
    catalog_entries: dict[str, dict[str, Any]] = catalog["entries"]
    actual_managed_names = {record.directory.name for record in managed_records}
    issues: list[dict[str, str]] = list(catalog["issues"])
    managed_external: list[dict[str, Any]] = []

    for record in managed_records:
        marker_path = record.directory / XCODE_SKILL_MARKER
        marker_issues: list[dict[str, str]] = []
        marker: dict[str, Any] = {}

        try:
            marker = json.loads(marker_path.read_text(encoding="utf-8"))
        except OSError as error:
            marker_issues.append(
                {
                    "code": "xcode_marker_unreadable",
                    "summary_ja": f"`{marker_path}` を読めません: {error}",
                    "fix_ja": "`sync-xcode-skills` を再実行するか marker の読み取り権限を確認してください。",
                }
            )
        except json.JSONDecodeError as error:
            marker_issues.append(
                {
                    "code": "xcode_marker_invalid_json",
                    "summary_ja": f"`{marker_path}` を JSON として読めません: {error}",
                    "fix_ja": "`sync-xcode-skills` を再実行して marker を再生成してください。",
                }
            )

        if marker:
            if marker.get("managed_by") != XCODE_SYNC_MANAGER:
                marker_issues.append(
                    {
                        "code": "xcode_marker_wrong_manager",
                        "summary_ja": "`managed_by` が `sync-xcode-skills` ではありません。",
                        "fix_ja": "`sync-xcode-skills` 管理下かどうかを確認してください。",
                    }
                )
            if marker.get("installed_name") != record.directory.name:
                marker_issues.append(
                    {
                        "code": "xcode_marker_installed_name_mismatch",
                        "summary_ja": "`installed_name` が実ディレクトリ名と一致していません。",
                        "fix_ja": "`sync-xcode-skills` を再実行して marker とディレクトリを揃えてください。",
                    }
                )
            if not marker.get("original_name"):
                marker_issues.append(
                    {
                        "code": "xcode_marker_missing_original_name",
                        "summary_ja": "`original_name` が marker にありません。",
                        "fix_ja": "`sync-xcode-skills` を再実行して marker を再生成してください。",
                    }
                )

        catalog_entry = catalog_entries.get(record.directory.name)
        if catalog_entry is None:
            marker_issues.append(
                {
                    "code": "xcode_managed_skill_missing_from_catalog",
                    "summary_ja": "managed external Skill が catalog state にありません。",
                    "fix_ja": "`sync-xcode-skills` を再実行して catalog と実ディレクトリを同期してください。",
                }
            )
        else:
            catalog_path = catalog_entry.get("path")
            if catalog_path and Path(str(catalog_path)).resolve() != record.directory.resolve():
                marker_issues.append(
                    {
                        "code": "xcode_catalog_path_mismatch",
                        "summary_ja": "catalog state の `path` が実ディレクトリと一致していません。",
                        "fix_ja": "`sync-xcode-skills` を再実行して catalog path を更新してください。",
                    }
                )
            marker_original_name = marker.get("original_name")
            catalog_original_name = catalog_entry.get("original_name")
            if marker_original_name and catalog_original_name and marker_original_name != catalog_original_name:
                marker_issues.append(
                    {
                        "code": "xcode_original_name_mismatch",
                        "summary_ja": "marker と catalog state の `original_name` が一致していません。",
                        "fix_ja": "`sync-xcode-skills` を再実行して Xcode 由来 Skill を再同期してください。",
                    }
                )

        managed_external.append(
            {
                "name": record.name,
                "directory": str(record.directory),
                "status": "aligned" if not marker_issues else "drift",
                "marker_path": str(marker_path),
                "catalog_source": catalog["source"],
                "issues": marker_issues,
            }
        )
        issues.extend(marker_issues)

    if check_catalog_missing_directories:
        for catalog_name in sorted(set(catalog_entries) - actual_managed_names):
            issues.append(
                {
                    "code": "xcode_catalog_skill_missing_directory",
                    "summary_ja": f"catalog state の `{catalog_name}` に対応する実ディレクトリがありません。",
                    "fix_ja": "`sync-xcode-skills` を再実行して catalog と実ディレクトリを同期してください。",
                }
            )

    status = "aligned"
    if any(issue["code"].endswith("missing") or "unreadable" in issue["code"] for issue in issues):
        status = "risky"
    elif issues:
        status = "drift"

    return {
        "status": status,
        "catalog_source": catalog["source"],
        "managed_external_count": len(managed_records),
        "unmanaged_xcode_prefix_count": len(unmanaged_prefix_records),
        "managed_external": managed_external,
        "catalog_installed_names": catalog["installed_names"],
        "issues": issues,
    }


def strip_existing_alignment_block(instructions: str) -> str:
    pattern = re.compile(
        r"\n## Workflow Alignment \(skills-batch-auditor\)\n(?:.|\n)*$",
        re.MULTILINE,
    )
    return re.sub(pattern, "", instructions).rstrip()


def build_alignment_lines(
    issue_codes: list[str],
    ground_truth: dict[str, Any],
    skill_name: str,
) -> list[str]:
    lines: list[str] = []
    artifact_root = ground_truth.get("artifact_root", "").strip()
    artifact_root_directory = artifact_root.replace("<RUN_ID>/", "").rstrip("/")

    if "missing_japanese_output_rule" in issue_codes:
        lines.append("- Return output in concise, polite Japanese.")

    if "ci_entrypoint_not_aligned" in issue_codes or "ci_policy_not_dynamic" in issue_codes:
        canonical_entrypoint = ground_truth.get("canonical_entrypoint", "")
        if canonical_entrypoint:
            lines.append(
                "- Resolve CI commands from `AGENTS.md` first, fall back to detected "
                f"`ci_scripts/**/*.sh` paths when needed, and use the repository standard entrypoint "
                f"`{canonical_entrypoint}` when CI verification is required."
            )
        else:
            lines.append(
                "- Resolve CI commands from `AGENTS.md` first and fall back to detected "
                "`ci_scripts/**/*.sh` paths when CI verification is required."
            )

    if "ci_artifact_root_not_aligned" in issue_codes and artifact_root:
        lines.append(
            f"- Use `{artifact_root}` as the CI artifact contract when the repository defines it."
        )

    if "ci_artifacts_latest_rule_missing" in issue_codes:
        if artifact_root:
            lines.append(
                f"- Read only the newest `{artifact_root}` artifacts when summarizing CI runs."
            )
        else:
            lines.append("- Read only the newest CI run artifacts when summarizing CI runs.")

    if "ci_artifacts_no_old_scan_rule_missing" in issue_codes:
        if artifact_root_directory:
            lines.append(f"- Do not scan older runs under `{artifact_root_directory}/`.")
        else:
            lines.append("- Do not scan older CI runs.")

    if not lines:
        return []

    lines.append("- Do not invent architecture or product features.")

    return list(dict.fromkeys(lines))


def apply_minimal_instruction_updates(
    original_instructions: str,
    issue_codes: list[str],
    ground_truth: dict[str, Any],
    skill_name: str,
) -> str:
    updated_instructions = strip_existing_alignment_block(original_instructions)
    canonical_entrypoint = ground_truth.get("canonical_entrypoint", "")
    if "ci_entrypoint_not_aligned" in issue_codes and canonical_entrypoint:
        updated_instructions = re.sub(
            r"bash\s+ci_scripts/[A-Za-z0-9_./-]+\.sh",
            canonical_entrypoint,
            updated_instructions,
        )
    alignment_lines = build_alignment_lines(issue_codes, ground_truth, skill_name)

    if not alignment_lines:
        return updated_instructions.strip()

    alignment_section = "\n".join(
        [
            "## Workflow Alignment (skills-batch-auditor)",
            "",
            *alignment_lines,
        ]
    )

    updated_instructions = updated_instructions.strip()
    if updated_instructions:
        return f"{updated_instructions}\n\n{alignment_section}\n"

    return f"{alignment_section}\n"


def build_file_patch(old_text: str, new_text: str, file_path: Path) -> str:
    diff_lines = list(
        difflib.unified_diff(
            old_text.splitlines(),
            new_text.splitlines(),
            fromfile=f"{file_path}/before",
            tofile=f"{file_path}/after",
            lineterm="",
        )
    )
    return "\n".join(diff_lines)


def apply_openai_maintenance_updates(
    skill: SkillRecord,
    issue_codes: list[str],
) -> tuple[str, list[str]]:
    updated_openai_text = skill.openai_text
    applied_codes: list[str] = []
    interface_fields = parse_openai_interface_fields(skill.openai_text)

    if "display_name_snake_case" in issue_codes and skill.openai_text.strip():
        updated_openai_text = replace_interface_field(
            updated_openai_text,
            "display_name",
            title_case_skill_name(skill.name),
        )
        applied_codes.append("display_name_snake_case")

    if "default_prompt_missing_skill_reference" in issue_codes and skill.openai_text.strip():
        default_prompt = interface_fields.get("default_prompt", "").strip()
        required_prompt_token = f"${skill.name}"
        if default_prompt and required_prompt_token not in default_prompt:
            updated_openai_text = replace_interface_field(
                updated_openai_text,
                "default_prompt",
                f"Use {required_prompt_token}. {default_prompt}",
            )
            applied_codes.append("default_prompt_missing_skill_reference")

    return updated_openai_text, applied_codes


def apply_maintenance_updates(
    report_items: list[dict[str, Any]],
    skill_records: dict[str, SkillRecord],
    ground_truth: dict[str, Any],
    bundle_mode: str,
) -> list[dict[str, Any]]:
    applied_fixes: list[dict[str, Any]] = []

    for item in report_items:
        if item["recommended_action"] != "improve next":
            continue

        issue_codes = item["maintenance_issue_codes"]
        if not issue_codes:
            continue

        skill = skill_records[item["name"]]
        skill_file = skill.directory / "SKILL.md"
        openai_file = skill.directory / "agents" / "openai.yaml"

        instruction_issue_codes = [
            code for code in issue_codes if code in INSTRUCTION_MAINTENANCE_FIX_CODES
        ]
        if instruction_issue_codes:
            updated_instructions = apply_minimal_instruction_updates(
                original_instructions=skill.instructions,
                issue_codes=instruction_issue_codes,
                ground_truth=ground_truth,
                skill_name=skill.name,
            )
            updated_skill_text = replace_skill_markdown_body(skill.skill_text, updated_instructions)
            if updated_skill_text != skill.skill_text:
                skill_file.write_text(updated_skill_text, encoding="utf-8")
                applied_entry: dict[str, Any] = {
                    "name": skill.name,
                    "file": str(skill_file),
                    "issue_codes": instruction_issue_codes,
                }
                if bundle_mode == "patch":
                    applied_entry["patch"] = build_file_patch(
                        skill.skill_text,
                        updated_skill_text,
                        skill_file,
                    )
                applied_fixes.append(applied_entry)

        openai_issue_codes = [
            code for code in issue_codes if code in OPENAI_MAINTENANCE_FIX_CODES
        ]
        if openai_issue_codes and skill.openai_text.strip():
            updated_openai_text, applied_openai_codes = apply_openai_maintenance_updates(
                skill,
                openai_issue_codes,
            )
            if applied_openai_codes and updated_openai_text != skill.openai_text:
                openai_file.write_text(updated_openai_text, encoding="utf-8")
                applied_entry = {
                    "name": skill.name,
                    "file": str(openai_file),
                    "issue_codes": applied_openai_codes,
                }
                if bundle_mode == "patch":
                    applied_entry["patch"] = build_file_patch(
                        skill.openai_text,
                        updated_openai_text,
                        openai_file,
                    )
                applied_fixes.append(applied_entry)

    return applied_fixes


def prioritize_report(report_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        report_items,
        key=lambda item: (
            ACTION_ORDER[item["recommended_action"]],
            -item["maintenance_priority_score"],
            STATUS_ORDER[item["status"]],
            item["scores"]["safety"],
            -item["scores"]["reuse value"],
            item["name"],
        ),
    )


def build_batch_decisions(report_items: list[dict[str, Any]]) -> dict[str, list[dict[str, str]]]:
    decisions: dict[str, list[dict[str, str]]] = {
        "keep as-is": [],
        "improve next": [],
        "merge with another skill": [],
        "retire": [],
    }

    for item in report_items:
        entry = {
            "name": item["name"],
            "classification": item["portfolio_classification"],
            "priority_note_ja": item["priority_note_ja"],
        }
        if item.get("merge_target"):
            entry["merge_target"] = item["merge_target"]
        decisions[item["recommended_action"]].append(entry)

    return decisions


def build_recommendations(report_items: list[dict[str, Any]]) -> list[str]:
    recommendations: list[str] = []

    if any(item["recommended_action"] == "improve next" for item in report_items):
        recommendations.append(
            "4軸スコアと `improve next` 判定理由を 1 つの保守レジストリに残し、次回監査で差分比較できるようにしてください。"
        )

    if any(
        "ci_policy_not_dynamic" in item.get("issue_codes", [])
        or "ci_entrypoint_not_aligned" in item.get("issue_codes", [])
        for item in report_items
    ):
        recommendations.append(
            "CI を扱う Skill 向けに `AGENTS.md` の標準エントリポイント参照テンプレートを共通化してください。"
        )

    if any("default_prompt_missing_skill_reference" in item.get("issue_codes", []) for item in report_items):
        recommendations.append(
            "`agents/openai.yaml` は `default_prompt` に `$<skill-name>` を必ず含める共通チェックを維持してください。"
        )

    if any(item["recommended_action"] == "merge with another skill" for item in report_items):
        recommendations.append(
            "用途が重なる Skill は代表 Skill を 1 つ決め、呼び出し語彙と `default_prompt` をそこへ寄せてください。"
        )

    if any(item["recommended_action"] == "retire" for item in report_items):
        recommendations.append(
            "`retire candidate` は削除前に参照先と代替 Skill を確認し、退役メモを 1 行残してください。"
        )

    return recommendations[:3]


def determine_mode_disposition(item: dict[str, Any]) -> str:
    if item["recommended_action"] in {"merge with another skill", "retire"}:
        return "refresh"
    if item["refresh_issue_codes"]:
        return "refresh"
    if item["maintenance_issue_codes"]:
        return "maintenance"
    return "no action"


def build_result(
    report_items: list[dict[str, Any]],
    ground_truth: dict[str, Any],
    bundle_mode: str,
    mode: str,
    applied_fixes: list[dict[str, Any]] | None = None,
    xcode_sync_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    applied_maintenance_fixes = applied_fixes or []
    maintenance_candidates: list[str] = []
    refresh_candidates: list[str] = []
    batch_decisions = build_batch_decisions(report_items)

    for item in report_items:
        item["mode_disposition"] = determine_mode_disposition(item)

        if item["mode_disposition"] == "maintenance":
            maintenance_candidates.append(item["name"])

        if item["mode_disposition"] == "refresh":
            refresh_candidates.append(item["name"])

    recommendations = build_recommendations(report_items)

    return {
        "ground_truth": ground_truth,
        "drift_report": report_items,
        "xcode_sync_report": xcode_sync_report
        or {
            "status": "aligned",
            "managed_external_count": 0,
            "unmanaged_xcode_prefix_count": 0,
            "managed_external": [],
            "issues": [],
        },
        "batch_decisions": batch_decisions,
        "mode_result": {
            "mode": mode,
            "maintenance_candidates": maintenance_candidates,
            "refresh_candidates": refresh_candidates,
            "applied_fixes": applied_maintenance_fixes,
        },
        "maintenance_application": {
            "mode": bundle_mode,
            "applied_fixes": applied_maintenance_fixes,
        },
        "one_time_recommendations": recommendations,
    }


def format_markdown(result: dict[str, Any]) -> str:
    lines: list[str] = []
    mode = result["mode_result"]["mode"]

    if mode == "maintenance":
        lines.append("1) maintenance 実施結果")
    else:
        lines.append("1) refresh 提案（優先順）")
    lines.append("")

    for item in result["drift_report"]:
        lines.append(f"- {item['status_label']} {item['name']}")
        lines.append(f"  - 意図: {item['intent']}")
        lines.append(f"  - モード振り分け: {item['mode_disposition']}")
        lines.append(f"  - 分類: {item['portfolio_classification']}")
        lines.append(f"  - 推奨アクション: {item['recommended_action']}")
        lines.append(f"  - 保守優先度スコア: {item['maintenance_priority_score']}/100")
        lines.append(f"  - 優先度メモ: {item['priority_note_ja']}")
        lines.append("  - 評価軸スコア:")
        lines.append(f"    - reuse value: {item['scores']['reuse value']}/5")
        lines.append(
            f"    - clarity of invocation: {item['scores']['clarity of invocation']}/5"
        )
        lines.append(f"    - safety: {item['scores']['safety']}/5")
        lines.append(
            f"    - maintenance burden: {item['scores']['maintenance burden']}/5"
        )
        if item.get("merge_target"):
            lines.append(f"  - 統合候補: {item['merge_target']}")

        if item["issues"]:
            lines.append("  - 課題:")
            for issue in item["issues"]:
                lines.append(f"    - {issue}")
        else:
            lines.append("  - 課題:")
            lines.append("    - 問題は検出されませんでした。")

        if item["recommended_fix"]:
            lines.append("  - 推奨修正:")
            for fix in item["recommended_fix"]:
                lines.append(f"    - {fix}")
        else:
            lines.append("  - 推奨修正:")
            lines.append("    - 変更不要です。")

    lines.append("")
    if mode == "maintenance":
        lines.append("2) 自動適用した整合性修正")
    else:
        lines.append("2) 採用判断材料")
    lines.append("")

    maintenance_application = result["maintenance_application"]
    mode_result = result["mode_result"]
    xcode_sync_report = result["xcode_sync_report"]
    decisions = result["batch_decisions"]
    lines.append(f"- モード: {mode_result['mode']}")
    lines.append(f"- 出力形式: {maintenance_application['mode']}")
    lines.append(f"- Xcode同期状態: {xcode_sync_report['status']}")
    lines.append(f"- managed external: {xcode_sync_report['managed_external_count']}件")
    lines.append(
        f"- unmanaged xcode prefix: {xcode_sync_report['unmanaged_xcode_prefix_count']}件"
    )
    if xcode_sync_report.get("issues"):
        lines.append("- Xcode同期整合性の課題:")
        for issue in xcode_sync_report["issues"]:
            lines.append(f"  - {issue['summary_ja']}")

    applied_fixes = maintenance_application["applied_fixes"]
    if mode == "maintenance":
        if not applied_fixes:
            lines.append("- 自動適用した修正はありません。")
        else:
            for applied_fix in applied_fixes:
                lines.append(
                    f"- {applied_fix['name']}: {applied_fix['file']}"
                )
                lines.append(
                    "  - issue codes: " + ", ".join(applied_fix["issue_codes"])
                )
                if applied_fix.get("patch"):
                    lines.append("  - patch:")
                    lines.append("```diff")
                    lines.append(applied_fix["patch"].rstrip())
                    lines.append("```")

        if mode_result["maintenance_candidates"]:
            lines.append(
                "- 未適用の maintenance 候補: "
                + ", ".join(mode_result["maintenance_candidates"])
            )
            lines.append("- 未適用理由: 自動適用後の再監査でも残ったため、個別確認が必要です。")
        else:
            lines.append("- 未適用の maintenance 候補: ありません。")
    else:
        keep_names = [entry["name"] for entry in decisions["keep as-is"]]
        improve_names = [entry["name"] for entry in decisions["improve next"]]
        retire_names = [entry["name"] for entry in decisions["retire"]]
        merge_entries = decisions["merge with another skill"]

        lines.append("- keep as-is: " + (", ".join(keep_names) if keep_names else "ありません。"))
        lines.append(
            "- improve next: " + (", ".join(improve_names) if improve_names else "ありません。")
        )
        if merge_entries:
            merge_summary = ", ".join(
                f"{entry['name']} -> {entry['merge_target']}"
                for entry in merge_entries
                if entry.get("merge_target")
            )
            lines.append("- merge with another skill: " + (merge_summary or "ありません。"))
        else:
            lines.append("- merge with another skill: ありません。")
        lines.append("- retire: " + (", ".join(retire_names) if retire_names else "ありません。"))
        lines.append("- refresh では自動適用用の更新本文を出力しません。")

    lines.append("")
    if mode == "maintenance":
        lines.append("3) refresh に回した判断事項")
    else:
        lines.append("3) maintenance に回せる整合性候補")
    lines.append("")

    recommendations = result.get("one_time_recommendations", [])
    if mode == "maintenance":
        if mode_result["refresh_candidates"]:
            lines.append("- refresh 判断事項: " + ", ".join(mode_result["refresh_candidates"]))
        else:
            lines.append("- refresh 判断事項: ありません。")
    else:
        if mode_result["maintenance_candidates"]:
            lines.append(
                "- maintenance 候補: " + ", ".join(mode_result["maintenance_candidates"])
            )
        else:
            lines.append("- maintenance 候補: ありません。")

    if not recommendations:
        lines.append("- 追加の提案はありません。")
    else:
        for recommendation in recommendations:
            lines.append(f"- {recommendation}")

    return "\n".join(lines).rstrip() + "\n"


def fallback_payload(
    repo_root: Path,
    skills_root: Path,
    ground_truth: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload_ground_truth: dict[str, Any] = {
        "repo_root": str(repo_root),
        "skills_root": str(skills_root),
    }
    if ground_truth:
        payload_ground_truth.update(ground_truth)

    return {
        "ground_truth": payload_ground_truth,
        "fallback_request": {
            "message_ja": "既存 Skill 定義に直接アクセスできません。次の2点を1メッセージで共有してください。",
            "required_user_input": FALLBACK_REQUIRED_INPUTS,
        },
    }


def format_fallback_markdown(payload: dict[str, Any]) -> str:
    message = payload["fallback_request"]["message_ja"]
    required_inputs = payload["fallback_request"]["required_user_input"]

    lines = [message]
    for required_input in required_inputs:
        lines.append(f"- {required_input}")

    return "\n".join(lines) + "\n"


def main() -> int:
    arguments = parse_arguments()
    requested_skill_names = set(arguments.skill)

    repo_root = Path(arguments.repo_root).expanduser().resolve()
    skills_root = (
        Path(arguments.skills_root).expanduser().resolve()
        if arguments.skills_root
        else resolve_default_skills_root()
    )

    try:
        base_ground_truth = extract_ground_truth(
            repo_root,
            include_doc_source=False,
        )
    except Exception as error:  # pragma: no cover - defensive guard
        print(f"Failed to extract ground truth: {error}", file=sys.stderr)
        return 1

    if not skills_root.exists() or not skills_root.is_dir():
        payload = fallback_payload(repo_root, skills_root, base_ground_truth)
        if arguments.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(format_fallback_markdown(payload), end="")
        return 0

    try:
        records = discover_skill_records(
            skills_root=skills_root,
            scope=arguments.scope,
            include_system=arguments.include_system,
            include_self=arguments.include_self or "skills-batch-auditor" in requested_skill_names,
        )
    except PermissionError:
        payload = fallback_payload(repo_root, skills_root, base_ground_truth)
        if arguments.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(format_fallback_markdown(payload), end="")
        return 0

    if not records:
        payload = fallback_payload(repo_root, skills_root, base_ground_truth)
        if arguments.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(format_fallback_markdown(payload), end="")
        return 0

    if requested_skill_names:
        records = [
            record
            for record in records
            if record.name in requested_skill_names or record.directory.name in requested_skill_names
        ]

    if not records:
        payload = fallback_payload(repo_root, skills_root, base_ground_truth)
        payload["fallback_request"]["message_ja"] = (
            "指定された Skill が見つかりません。次の2点を1メッセージで共有してください。"
        )
        if arguments.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(format_fallback_markdown(payload), end="")
        return 0

    ground_truth = base_ground_truth
    if needs_doc_source(records):
        try:
            ground_truth = extract_ground_truth(
                repo_root,
                include_doc_source=True,
            )
        except Exception:
            ground_truth = base_ground_truth

    xcode_sync_report = analyze_xcode_sync_integrity(
        skills_root,
        records,
        check_catalog_missing_directories=not requested_skill_names,
    )
    audit_records = [
        record for record in records if record.classification != "managed-external"
    ]
    skill_records = {record.name: record for record in audit_records}
    analyses = [analyze_skill(record, ground_truth) for record in audit_records]
    enriched = enrich_portfolio_prioritization(analyses, skill_records)
    prioritized = prioritize_report(enriched)
    applied_fixes: list[dict[str, Any]] = []

    if arguments.mode == "maintenance":
        applied_fixes = apply_maintenance_updates(
            report_items=prioritized,
            skill_records=skill_records,
            ground_truth=ground_truth,
            bundle_mode=arguments.bundle_mode,
        )

        if applied_fixes:
            records = discover_skill_records(
                skills_root=skills_root,
                scope=arguments.scope,
                include_system=arguments.include_system,
                include_self=arguments.include_self or "skills-batch-auditor" in requested_skill_names,
            )
            if requested_skill_names:
                records = [
                    record
                    for record in records
                    if record.name in requested_skill_names or record.directory.name in requested_skill_names
                ]
            if needs_doc_source(records):
                try:
                    ground_truth = extract_ground_truth(
                        repo_root,
                        include_doc_source=True,
                    )
                except Exception:
                    ground_truth = base_ground_truth
            xcode_sync_report = analyze_xcode_sync_integrity(
                skills_root,
                records,
                check_catalog_missing_directories=not requested_skill_names,
            )
            audit_records = [
                record for record in records if record.classification != "managed-external"
            ]
            skill_records = {record.name: record for record in audit_records}
            analyses = [analyze_skill(record, ground_truth) for record in audit_records]
            enriched = enrich_portfolio_prioritization(analyses, skill_records)
            prioritized = prioritize_report(enriched)

    result = build_result(
        report_items=prioritized,
        ground_truth=ground_truth,
        bundle_mode=arguments.bundle_mode,
        mode=arguments.mode,
        applied_fixes=applied_fixes,
        xcode_sync_report=xcode_sync_report,
    )

    if arguments.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_markdown(result), end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
