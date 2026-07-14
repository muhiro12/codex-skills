#!/usr/bin/env python3
"""Export Xcode-provided skills and install Codex-compatible copies."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
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
SAFE_SLUG_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
IGNORED_EXPORT_TREE_NAMES = {
    ".DS_Store",
    "__pycache__",
    ".build",
    "build",
    "DerivedData",
    ".git",
    ".swiftpm",
    "Pods",
    "Carthage",
}


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


def validate_safe_slug(value: str, *, label: str) -> str:
    normalized = value.strip()
    if not normalized or not SAFE_SLUG_PATTERN.fullmatch(normalized):
        raise SyncError(
            f"Invalid {label} {value!r}; expected a filesystem-safe slug containing only "
            "letters, numbers, '.', '_', and '-'."
        )
    return normalized


def resolved_install_target(skills_root: Path, installed_name: str) -> Path:
    try:
        root = skills_root.resolve()
    except OSError as error:
        raise SyncError(f"Could not resolve skills root {skills_root}: {error}") from error
    target = root / installed_name
    if target.is_symlink():
        raise SyncError(f"Install target must not be a symbolic link: {target}")
    try:
        resolved_target = target.resolve(strict=False)
    except OSError as error:
        raise SyncError(f"Could not resolve install target {target}: {error}") from error
    if resolved_target.parent != root:
        raise SyncError(f"Install target escapes the skills root: {target} -> {resolved_target}")
    return target


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def move_path(source: Path, target: Path) -> None:
    source.rename(target)


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


def write_marker(
    skill_dir: Path,
    original_name: str,
    installed_name: str,
    *,
    xcode_version: str,
) -> None:
    marker = {
        "managed_by": MANAGED_BY,
        "original_name": original_name,
        "installed_name": installed_name,
        "synced_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "xcode_version": xcode_version,
    }
    (skill_dir / MARKER_FILE).write_text(json.dumps(marker, indent=2) + "\n", encoding="utf-8")


def is_managed_skill(skill_dir: Path) -> bool:
    if skill_dir.is_symlink() or not skill_dir.is_dir():
        return False
    marker_path = skill_dir / MARKER_FILE
    if marker_path.is_symlink() or not marker_path.is_file():
        return False
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(marker, dict):
        return False
    original_name = marker.get("original_name")
    installed_name = marker.get("installed_name")
    return (
        marker.get("managed_by") == MANAGED_BY
        and isinstance(original_name, str)
        and SAFE_SLUG_PATTERN.fullmatch(original_name) is not None
        and installed_name == skill_dir.name
        and SAFE_SLUG_PATTERN.fullmatch(installed_name) is not None
    )


def short_text(value: str, limit: int = 160) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def copy_skill_tree(source: Path, target: Path) -> None:
    if source.is_symlink():
        raise SyncError(f"Exported skill directory must not be a symbolic link: {source}")
    for path in source.rglob("*"):
        if path.is_symlink():
            raise SyncError(f"Exported skill tree must not contain symbolic links: {path}")

    def ignore(_: str, names: list[str]) -> set[str]:
        return {name for name in names if name in IGNORED_EXPORT_TREE_NAMES}

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
    validated_prefix = validate_safe_slug(name_prefix, label="name prefix")
    installed_names: dict[str, str] = {}
    for source_skill in sorted(export_dir.iterdir()):
        if source_skill.is_symlink():
            raise SyncError(
                f"Exported skill directory must not be a symbolic link: {source_skill}"
            )
        if not source_skill.is_dir() or not (source_skill / "SKILL.md").exists():
            continue
        metadata, _ = parse_frontmatter(source_skill / "SKILL.md")
        original_name = validate_safe_slug(
            metadata.get("name", source_skill.name).strip() or source_skill.name,
            label=f"exported skill name from {source_skill}",
        )
        installed_name = validate_safe_slug(
            f"{validated_prefix}{original_name}",
            label=f"installed skill name for {original_name}",
        )
        duplicate_key = installed_name.casefold()
        if duplicate_key in installed_names:
            raise SyncError(
                "Duplicate installed skill name in export: "
                f"{installed_names[duplicate_key]} and {installed_name}"
            )
        installed_names[duplicate_key] = installed_name
        if installed_name == MANAGED_BY:
            skipped.append(f"{original_name} -> {installed_name} (reserved name)")
            continue
        target = resolved_install_target(skills_root, installed_name)
        entries.append(
            {
                "original_name": original_name,
                "installed_name": installed_name,
                "source_path": str(source_skill),
                "target_path": str(target),
            }
        )
    return entries, skipped


def unmanaged_reserved_skills(skills_root: Path, *, name_prefix: str) -> list[Path]:
    return [
        target
        for target in sorted(skills_root.glob(f"{name_prefix}*"))
        if target.is_symlink() or not target.is_dir() or not is_managed_skill(target)
    ]


def format_unmanaged_reserved_skills(paths: list[Path], name_prefix: str) -> str:
    lines = [
        f"Refusing to sync because {name_prefix}* is reserved for Xcode-provided managed skills.",
        "The following paths are not managed by sync-xcode-skills:",
    ]
    for path in paths:
        lines.append(f"  - {path}")
    lines.append("Resolve these directories manually before syncing.")
    return "\n".join(lines)


def stale_managed_skills(
    skills_root: Path,
    *,
    name_prefix: str,
    current_installed_names: set[str],
) -> list[Path]:
    stale: list[Path] = []
    for target in sorted(skills_root.glob(f"{name_prefix}*")):
        if target.is_symlink() or not target.is_dir() or not is_managed_skill(target):
            continue
        if target.name in current_installed_names:
            continue
        stale.append(target)
    return stale


def validate_staged_skill(
    skill_dir: Path,
    *,
    original_name: str,
    installed_name: str,
    xcode_version: str,
) -> None:
    skill_md = skill_dir / "SKILL.md"
    openai_yaml = skill_dir / "agents" / "openai.yaml"
    marker_path = skill_dir / MARKER_FILE
    if not skill_md.is_file() or not openai_yaml.is_file() or not marker_path.is_file():
        raise SyncError(f"Staged skill is incomplete: {installed_name}")

    metadata, _ = parse_frontmatter(skill_md)
    if metadata.get("name") != installed_name:
        raise SyncError(f"Staged SKILL.md name mismatch for {installed_name}")
    if not normalize_description(metadata):
        raise SyncError(f"Staged SKILL.md description is empty for {installed_name}")

    openai_text = openai_yaml.read_text(encoding="utf-8")
    if f"${installed_name}" not in openai_text:
        raise SyncError(f"Staged agents/openai.yaml prompt mismatch for {installed_name}")

    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SyncError(f"Staged marker is unreadable for {installed_name}: {error}") from error
    expected_marker_values = {
        "managed_by": MANAGED_BY,
        "original_name": original_name,
        "installed_name": installed_name,
        "xcode_version": xcode_version,
    }
    for key, expected_value in expected_marker_values.items():
        if marker.get(key) != expected_value:
            raise SyncError(f"Staged marker {key} mismatch for {installed_name}")


def rollback_installation(
    swapped: list[tuple[Path, Path, bool]],
    pruned: list[tuple[Path, Path]],
) -> list[str]:
    errors: list[str] = []
    for target, backup in reversed(pruned):
        try:
            if backup.exists():
                if target.exists() or target.is_symlink():
                    remove_path(target)
                move_path(backup, target)
            elif not target.exists() and not target.is_symlink():
                errors.append(f"restore pruned {target}: backup is missing")
        except OSError as error:
            errors.append(f"restore pruned {target}: {error}")

    for target, backup, had_existing in reversed(swapped):
        try:
            if had_existing:
                if backup.exists():
                    if target.exists() or target.is_symlink():
                        remove_path(target)
                    move_path(backup, target)
                elif not target.exists() and not target.is_symlink():
                    errors.append(f"restore installed {target}: backup is missing")
            elif target.exists() or target.is_symlink():
                remove_path(target)
        except OSError as error:
            errors.append(f"restore installed {target}: {error}")
    return errors


def synchronize_exported_skills(
    export_dir: Path,
    skills_root: Path,
    *,
    state_dir: Path,
    developer_dir: Path | None,
    name_prefix: str,
    xcode_version: str,
) -> tuple[list[dict[str, str]], list[str], list[str]]:
    try:
        skills_root = skills_root.resolve()
        skills_root.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise SyncError(f"Could not prepare skills root {skills_root}: {error}") from error
    installed: list[dict[str, str]] = []
    entries, skipped = exported_skill_entries(export_dir, skills_root, name_prefix=name_prefix)
    if not entries:
        raise SyncError(f"No Xcode skills were exported into {export_dir}; refusing to prune installed skills.")

    unmanaged_reserved = unmanaged_reserved_skills(skills_root, name_prefix=name_prefix)
    if unmanaged_reserved:
        raise SyncError(format_unmanaged_reserved_skills(unmanaged_reserved, name_prefix))

    current_installed_names = {entry["installed_name"] for entry in entries}
    stale_targets = stale_managed_skills(
        skills_root,
        name_prefix=name_prefix,
        current_installed_names=current_installed_names,
    )

    staging_root = Path(
        tempfile.mkdtemp(prefix=".sync-xcode-skills-stage-", dir=skills_root)
    )
    try:
        for entry in entries:
            original_name = entry["original_name"]
            installed_name = entry["installed_name"]
            source_skill = Path(entry["source_path"])
            staged_target = staging_root / installed_name
            copy_skill_tree(source_skill, staged_target)
            description = normalize_skill(staged_target, installed_name, original_name)
            write_openai_yaml(staged_target, installed_name, description)
            write_marker(
                staged_target,
                original_name,
                installed_name,
                xcode_version=xcode_version,
            )
            validate_staged_skill(
                staged_target,
                original_name=original_name,
                installed_name=installed_name,
                xcode_version=xcode_version,
            )
            installed.append(
                {
                    "original_name": original_name,
                    "installed_name": installed_name,
                    "path": str(Path(entry["target_path"])),
                    "source_path": str(source_skill),
                    "description": description,
                }
            )
    except BaseException as error:
        shutil.rmtree(staging_root, ignore_errors=True)
        if isinstance(error, (SyncError, KeyboardInterrupt, SystemExit)):
            raise
        raise SyncError(f"Failed to stage Xcode skills: {error}") from error

    backup_root: Path | None = None
    swapped: list[tuple[Path, Path, bool]] = []
    pruned_backups: list[tuple[Path, Path]] = []
    pruned_names: list[str] = []

    try:
        unmanaged_reserved = unmanaged_reserved_skills(skills_root, name_prefix=name_prefix)
        if unmanaged_reserved:
            raise SyncError(format_unmanaged_reserved_skills(unmanaged_reserved, name_prefix))

        backup_root = Path(
            tempfile.mkdtemp(prefix=".sync-xcode-skills-backup-", dir=skills_root)
        )
        installed_backup_root = backup_root / "installed"
        pruned_backup_root = backup_root / "pruned"
        installed_backup_root.mkdir()
        pruned_backup_root.mkdir()

        for entry in entries:
            installed_name = entry["installed_name"]
            target = Path(entry["target_path"])
            staged_target = staging_root / installed_name
            backup_target = installed_backup_root / installed_name
            had_existing = target.exists() or target.is_symlink()
            swapped.append((target, backup_target, had_existing))
            if had_existing:
                if not target.is_dir() or not is_managed_skill(target):
                    raise SyncError(
                        f"Reserved install target stopped being managed before swap: {target}"
                    )
                move_path(target, backup_target)
            move_path(staged_target, target)

        for stale_target in stale_targets:
            if not stale_target.is_dir() or not is_managed_skill(stale_target):
                raise SyncError(
                    f"Stale reserved target stopped being managed before prune: {stale_target}"
            )
            backup_target = pruned_backup_root / stale_target.name
            pruned_backups.append((stale_target, backup_target))
            move_path(stale_target, backup_target)
            pruned_names.append(stale_target.name)

        write_catalog(
            state_dir,
            developer_dir=developer_dir,
            export_dir=export_dir,
            skills_root=skills_root,
            name_prefix=name_prefix,
            xcode_version=xcode_version,
            installed=installed,
            skipped=skipped,
            pruned=pruned_names,
        )
    except BaseException as error:
        rollback_errors = rollback_installation(swapped, pruned_backups)
        shutil.rmtree(staging_root, ignore_errors=True)
        if backup_root is not None and not rollback_errors:
            shutil.rmtree(backup_root, ignore_errors=True)
        if isinstance(error, (KeyboardInterrupt, SystemExit)) and not rollback_errors:
            raise
        message = f"Xcode skill install transaction failed: {error}"
        if rollback_errors:
            message += "\nRollback was incomplete; backups were preserved at "
            message += str(backup_root)
            message += "\n" + "\n".join(f"  - {item}" for item in rollback_errors)
        raise SyncError(message) from error

    shutil.rmtree(staging_root, ignore_errors=True)
    assert backup_root is not None
    shutil.rmtree(backup_root, ignore_errors=True)
    return installed, skipped, pruned_names


def write_catalog_files_atomically(
    state_dir: Path,
    *,
    catalog_json: str,
    catalog_markdown: str,
) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    transaction_root = Path(
        tempfile.mkdtemp(prefix=".catalog-transaction-", dir=state_dir)
    )
    preserve_transaction = False
    replaced: list[str] = []
    original_exists: dict[str, bool] = {}
    try:
        new_root = transaction_root / "new"
        backup_root = transaction_root / "backup"
        new_root.mkdir()
        backup_root.mkdir()
        contents = {
            "catalog.json": catalog_json,
            "catalog.md": catalog_markdown,
        }
        for name, content in contents.items():
            (new_root / name).write_text(content, encoding="utf-8")

        for name in contents:
            destination = state_dir / name
            original_exists[name] = destination.exists() or destination.is_symlink()
            if original_exists[name]:
                if destination.is_symlink() or not destination.is_file():
                    raise SyncError(f"Catalog destination is not a regular file: {destination}")
                shutil.copy2(destination, backup_root / name)

        for name in contents:
            replaced.append(name)
            os.replace(new_root / name, state_dir / name)
    except BaseException as error:
        rollback_errors: list[str] = []
        for name in reversed(replaced):
            destination = state_dir / name
            try:
                if (new_root / name).exists():
                    continue
                if original_exists[name]:
                    os.replace(backup_root / name, destination)
                elif destination.exists() or destination.is_symlink():
                    remove_path(destination)
            except OSError as rollback_error:
                rollback_errors.append(f"restore {destination}: {rollback_error}")
        message = str(error) if isinstance(error, SyncError) else (
            f"Could not atomically update Xcode skill catalogs: {error}"
        )
        if rollback_errors:
            preserve_transaction = True
            message += "\nCatalog rollback was incomplete; transaction files remain at "
            message += str(transaction_root)
            message += "\n" + "\n".join(f"  - {item}" for item in rollback_errors)
        if isinstance(error, (KeyboardInterrupt, SystemExit)) and not rollback_errors:
            raise
        raise SyncError(message) from error
    finally:
        if not preserve_transaction:
            shutil.rmtree(transaction_root, ignore_errors=True)


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
    catalog_json = json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"

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
            escaped_description = short_text(skill["description"]).replace("|", "\\|")
            lines.append(
                "| "
                f"`{skill['installed_name']}` | "
                f"`{skill['original_name']}` | "
                f"{escaped_description} |"
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
    catalog_markdown = "\n".join(lines)
    write_catalog_files_atomically(
        state_dir,
        catalog_json=catalog_json,
        catalog_markdown=catalog_markdown,
    )


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
    try:
        validate_safe_slug(args.name_prefix, label="name prefix")
    except SyncError as error:
        print(str(error))
        return 2
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
        installed, skipped, pruned = synchronize_exported_skills(
            args.export_dir,
            args.skills_root,
            state_dir=args.state_dir,
            developer_dir=developer_dir,
            name_prefix=args.name_prefix,
            xcode_version=xcode_version,
        )
    except SyncError as error:
        print(str(error))
        return 2
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
