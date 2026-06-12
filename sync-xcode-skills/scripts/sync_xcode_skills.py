#!/usr/bin/env python3
"""Export Xcode-provided skills and install Codex-compatible copies."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


MARKER_FILE = ".xcode-skill-sync.json"
MANAGED_BY = "sync-xcode-skills"
DEFAULT_EXPORT_DIR = Path(tempfile.gettempdir()) / "xcode-exported-skills"
DEFAULT_STATE_DIR = Path(__file__).resolve().parents[1] / "state"


class SyncError(Exception):
    """Raised when syncing would overwrite unmanaged local state."""


class CommandResult:
    def __init__(self, returncode: int, stdout: str, stderr: str) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

    @property
    def combined_output(self) -> str:
        return "\n".join(part for part in [self.stdout, self.stderr] if part)


def run_command(
    command: list[str],
    *,
    env: dict[str, str] | None = None,
    timeout: int | None = None,
) -> CommandResult:
    try:
        completed = subprocess.run(
            command,
            env=env,
            timeout=timeout,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout if isinstance(error.stdout, str) else ""
        stderr = error.stderr if isinstance(error.stderr, str) else ""
        stderr = f"{stderr}\nTimed out after {timeout} seconds".strip()
        return CommandResult(124, stdout, stderr)
    except PermissionError as error:
        return CommandResult(126, "", f"{command[0]}: {error}")


def selected_developer_dir() -> Path | None:
    result = run_command(["xcode-select", "-p"])
    if result.returncode != 0:
        return None
    text = result.stdout.strip()
    return Path(text) if text else None


def xcode_version_text() -> str:
    result = run_command(["xcodebuild", "-version"])
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def export_direct(output_dir: Path, timeout: int) -> CommandResult:
    command = [
        "xcrun",
        "mcpbridge",
        "run-agent",
        "skills",
        "export",
        "--output-dir",
        str(output_dir),
        "--replace-existing",
    ]
    return run_command(command, timeout=timeout)


def parse_frontmatter(skill_md: Path) -> tuple[dict[str, str], str]:
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    frontmatter = text[4:end].splitlines()
    body = text[end + len("\n---") :].lstrip("\n")
    data: dict[str, str] = {}
    index = 0
    while index < len(frontmatter):
        line = frontmatter[index]
        if not line.strip() or line.startswith(" "):
            index += 1
            continue
        if ":" not in line:
            index += 1
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()
        if value in {"|", "|-", "|+"}:
            block_lines: list[str] = []
            index += 1
            while index < len(frontmatter):
                next_line = frontmatter[index]
                if next_line and not next_line.startswith(" ") and ":" in next_line:
                    break
                block_lines.append(next_line[2:] if next_line.startswith("  ") else next_line)
                index += 1
            data[key] = "\n".join(block_lines).strip()
            continue
        data[key] = value.strip('"').strip("'")
        index += 1
    return data, body


def normalize_description(metadata: dict[str, str]) -> str:
    description = metadata.get("description", "").strip()
    when_to_use = metadata.get("when_to_use", "").strip()
    if when_to_use and when_to_use not in description:
        description = f"{description} Use when: {when_to_use}".strip()
    return " ".join(description.split())


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def title_from_name(name: str) -> str:
    words = name.replace("-", " ").split()
    special = {
        "ios": "iOS",
        "uikit": "UIKit",
        "swiftui": "SwiftUI",
        "xcode": "Xcode",
        "sdk": "SDK",
        "c": "C",
    }
    return " ".join(special.get(word.lower(), word.capitalize()) for word in words)


def normalize_skill(skill_dir: Path, installed_name: str, original_name: str) -> str:
    metadata, body = parse_frontmatter(skill_dir / "SKILL.md")
    description = normalize_description(metadata)
    if not description:
        description = f"Xcode-provided skill originally named {original_name}."
    if original_name != installed_name and original_name not in description:
        description = f"{description} Original Xcode skill name: {original_name}."
    normalized = (
        "---\n"
        f"name: {installed_name}\n"
        f"description: {yaml_string(description)}\n"
        "---\n"
        f"{body}"
    )
    (skill_dir / "SKILL.md").write_text(normalized, encoding="utf-8")
    return description


def write_openai_yaml(skill_dir: Path, installed_name: str, description: str) -> None:
    agents_dir = skill_dir / "agents"
    agents_dir.mkdir(exist_ok=True)
    first_sentence = re.split(r"(?<=[.!?])\s+", description, maxsplit=1)[0]
    short = first_sentence[:61].rstrip() + "..." if len(first_sentence) > 64 else first_sentence
    content = (
        "interface:\n"
        f"  display_name: {yaml_string(title_from_name(installed_name))}\n"
        f"  short_description: {yaml_string(short)}\n"
        f"  default_prompt: {yaml_string(f'Use ${installed_name} for the matching Xcode-provided workflow.')}\n"
        "policy:\n"
        "  allow_implicit_invocation: true\n"
    )
    (agents_dir / "openai.yaml").write_text(content, encoding="utf-8")


def write_marker(skill_dir: Path, original_name: str, installed_name: str) -> None:
    marker = {
        "managed_by": MANAGED_BY,
        "original_name": original_name,
        "installed_name": installed_name,
        "synced_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "xcode_version": xcode_version_text(),
    }
    (skill_dir / MARKER_FILE).write_text(json.dumps(marker, indent=2) + "\n", encoding="utf-8")


def is_managed_skill(skill_dir: Path) -> bool:
    marker_path = skill_dir / MARKER_FILE
    if not marker_path.exists():
        return False
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return marker.get("managed_by") == MANAGED_BY


def short_text(value: str, limit: int = 160) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def copy_skill_tree(source: Path, target: Path) -> None:
    def ignore(_: str, names: list[str]) -> set[str]:
        return {name for name in names if name in {".DS_Store", "__pycache__"}}

    shutil.copytree(source, target, ignore=ignore)
    for path in target.rglob("*"):
        if path.is_dir():
            path.chmod(path.stat().st_mode | 0o700)
        else:
            path.chmod(path.stat().st_mode | 0o600)
    target.chmod(target.stat().st_mode | 0o700)


def exported_skill_entries(
    export_dir: Path,
    skills_root: Path,
    *,
    name_prefix: str,
) -> tuple[list[dict[str, str]], list[str]]:
    entries: list[dict[str, str]] = []
    skipped: list[str] = []
    for source_skill in sorted(export_dir.iterdir()):
        if not source_skill.is_dir() or not (source_skill / "SKILL.md").exists():
            continue
        metadata, _ = parse_frontmatter(source_skill / "SKILL.md")
        original_name = metadata.get("name", source_skill.name).strip() or source_skill.name
        installed_name = f"{name_prefix}{original_name}"
        if installed_name == MANAGED_BY:
            skipped.append(f"{original_name} -> {installed_name} (reserved name)")
            continue
        entries.append(
            {
                "original_name": original_name,
                "installed_name": installed_name,
                "source_path": str(source_skill),
                "target_path": str(skills_root / installed_name),
            }
        )
    return entries, skipped


def unmanaged_reserved_skills(skills_root: Path, *, name_prefix: str) -> list[Path]:
    return [
        target
        for target in sorted(skills_root.glob(f"{name_prefix}*"))
        if target.is_dir() and not is_managed_skill(target)
    ]


def format_unmanaged_reserved_skills(paths: list[Path], name_prefix: str) -> str:
    lines = [
        f"Refusing to sync because {name_prefix}* is reserved for Xcode-provided managed skills.",
        "The following directories are not managed by sync-xcode-skills:",
    ]
    for path in paths:
        lines.append(f"  - {path}")
    lines.append("Resolve these directories manually before syncing.")
    return "\n".join(lines)


def prune_stale_managed_skills(
    skills_root: Path,
    *,
    name_prefix: str,
    current_installed_names: set[str],
) -> list[str]:
    pruned: list[str] = []
    for target in sorted(skills_root.glob(f"{name_prefix}*")):
        if not target.is_dir() or not is_managed_skill(target):
            continue
        if target.name in current_installed_names:
            continue
        shutil.rmtree(target)
        pruned.append(target.name)
    return pruned


def install_exported_skills(
    export_dir: Path,
    skills_root: Path,
    *,
    name_prefix: str,
) -> tuple[list[dict[str, str]], list[str], list[str]]:
    installed: list[dict[str, str]] = []
    entries, skipped = exported_skill_entries(export_dir, skills_root, name_prefix=name_prefix)
    if not entries:
        raise SyncError(f"No Xcode skills were exported into {export_dir}; refusing to prune installed skills.")

    unmanaged_reserved = unmanaged_reserved_skills(skills_root, name_prefix=name_prefix)
    if unmanaged_reserved:
        raise SyncError(format_unmanaged_reserved_skills(unmanaged_reserved, name_prefix))

    current_installed_names = {entry["installed_name"] for entry in entries}
    for entry in entries:
        original_name = entry["original_name"]
        installed_name = entry["installed_name"]
        source_skill = Path(entry["source_path"])
        target = Path(entry["target_path"])
        if target.exists():
            shutil.rmtree(target)
        copy_skill_tree(source_skill, target)
        description = normalize_skill(target, installed_name, original_name)
        write_openai_yaml(target, installed_name, description)
        write_marker(target, original_name, installed_name)
        installed.append(
            {
                "original_name": original_name,
                "installed_name": installed_name,
                "path": str(target),
                "source_path": str(source_skill),
                "description": description,
            }
        )
    pruned = prune_stale_managed_skills(
        skills_root,
        name_prefix=name_prefix,
        current_installed_names=current_installed_names,
    )
    return installed, skipped, pruned


def write_catalog(
    state_dir: Path,
    *,
    developer_dir: Path | None,
    export_dir: Path,
    skills_root: Path,
    name_prefix: str,
    xcode_version: str,
    installed: list[dict[str, str]],
    skipped: list[str],
    pruned: list[str],
) -> None:
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat()
    state_dir.mkdir(parents=True, exist_ok=True)
    catalog = {
        "managed_by": MANAGED_BY,
        "generated_at": generated_at,
        "selected_developer_dir": str(developer_dir) if developer_dir else None,
        "xcode_version": xcode_version,
        "export_dir": str(export_dir),
        "skills_root": str(skills_root),
        "name_prefix": name_prefix,
        "skills": installed,
        "skipped": skipped,
        "pruned": pruned,
    }
    (state_dir / "catalog.json").write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Xcode Skill Catalog",
        "",
        "Generated by `sync-xcode-skills` from the selected local Xcode.",
        "",
        f"- Generated at: `{generated_at}`",
        f"- Selected developer directory: `{developer_dir or 'unknown'}`",
        f"- Xcode version: `{short_text(xcode_version)}`",
        f"- Name prefix: `{name_prefix}`",
        "",
        "## Installed Skills",
        "",
    ]
    if installed:
        lines.append("| Installed skill | Original Xcode skill | Summary |")
        lines.append("| --- | --- | --- |")
        for skill in installed:
            lines.append(
                "| "
                f"`{skill['installed_name']}` | "
                f"`{skill['original_name']}` | "
                f"{short_text(skill['description']).replace('|', '\\|')} |"
            )
    else:
        lines.append("No Xcode skills were installed.")

    if skipped:
        lines.extend(["", "## Skipped Skills", ""])
        for item in skipped:
            lines.append(f"- {item}")
    if pruned:
        lines.extend(["", "## Pruned Stale Managed Skills", ""])
        for name in pruned:
            lines.append(f"- `{name}`")
    lines.append("")
    (state_dir / "catalog.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--skills-root", type=Path, default=Path.home() / ".codex" / "skills")
    parser.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR)
    parser.add_argument("--name-prefix", default="xcode-skill-")
    parser.add_argument("--export-only", action="store_true", help="Export but do not install into the skills root.")
    parser.add_argument("--install-only", action="store_true", help="Install from an existing export directory without invoking Xcode.")
    parser.add_argument("--direct-only", action="store_true", help="Compatibility no-op; direct mcpbridge export is always used.")
    parser.add_argument("--timeout", type=int, default=180)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.export_dir.mkdir(parents=True, exist_ok=True)
    developer_dir = selected_developer_dir()
    xcode_version = xcode_version_text()

    print(f"Selected developer directory: {developer_dir or 'unknown'}")
    print(f"Xcode version: {xcode_version}")
    print("Xcode export command: xcrun mcpbridge run-agent skills export")
    print(f"Export directory: {args.export_dir}")

    if not args.install_only:
        export_result = export_direct(args.export_dir, args.timeout)
        if export_result.returncode == 0:
            print("Direct export succeeded.")
        else:
            print("Direct export failed.")
            print(export_result.combined_output.strip())
            return export_result.returncode
    else:
        print("Skipping export; installing from existing export directory.")

    if args.export_only:
        return 0

    try:
        installed, skipped, pruned = install_exported_skills(
            args.export_dir,
            args.skills_root,
            name_prefix=args.name_prefix,
        )
    except SyncError as error:
        print(str(error))
        return 2
    write_catalog(
        args.state_dir,
        developer_dir=developer_dir,
        export_dir=args.export_dir,
        skills_root=args.skills_root,
        name_prefix=args.name_prefix,
        xcode_version=xcode_version,
        installed=installed,
        skipped=skipped,
        pruned=pruned,
    )
    print(f"Installed {len(installed)} Xcode skill(s) into {args.skills_root}:")
    for skill in installed:
        print(f"  - {skill['installed_name']} (Xcode: {skill['original_name']})")
    if pruned:
        print(f"Pruned {len(pruned)} stale managed skill(s):")
        for name in pruned:
            print(f"  - {name}")
    print(f"Wrote catalog to {args.state_dir / 'catalog.md'}")
    if skipped:
        print(f"Skipped {len(skipped)} skill(s):")
        for item in skipped:
            print(f"  - {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
