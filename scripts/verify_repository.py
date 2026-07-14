#!/usr/bin/env python3
"""Validate tracked skill metadata and the public README inventory."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Sequence, Set


SKILL_NAME_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
README_ENTRY_PATTERN = re.compile(r"^- `([^`]+)`: .+", re.MULTILINE)


def tracked_files(repo_root: Path) -> Set[str]:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "-z"],
        check=True,
        stdout=subprocess.PIPE,
    )
    return {
        item.decode("utf-8", errors="surrogateescape")
        for item in completed.stdout.split(b"\0")
        if item
    }


def tracked_skill_names(files: Iterable[str]) -> List[str]:
    names = []
    for path in files:
        parts = Path(path).parts
        if len(parts) == 2 and parts[1] == "SKILL.md":
            names.append(parts[0])
    return sorted(names)


def frontmatter(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[1:index])
    return ""


def scalar_value(block: str, key: str) -> str:
    lines = block.splitlines()
    prefix = key + ":"
    for index, line in enumerate(lines):
        if not line.startswith(prefix):
            continue
        raw_value = line[len(prefix) :].strip()
        if raw_value not in {"|", ">", "|-", ">-", "|+", ">+"}:
            return raw_value.strip("\"'").strip()

        continuation = []
        for following in lines[index + 1 :]:
            if following and not following[0].isspace():
                break
            stripped = following.strip()
            if stripped:
                continuation.append(stripped)
        return " ".join(continuation)
    return ""


def metadata_value(text: str, key: str) -> str:
    pattern = re.compile(
        r"^(?P<indent>[ \t]{2})"
        + re.escape(key)
        + r":\s*(?P<value>.*?)\s*$",
        re.MULTILINE,
    )
    match = pattern.search(text)
    if match is None:
        return ""
    raw_value = match.group("value").strip()
    if raw_value not in {"|", ">", "|-", ">-", "|+", ">+"}:
        return raw_value.strip("\"'").strip()

    continuation = []
    base_indent = len(match.group("indent").expandtabs())
    for following in text[match.end() :].splitlines():
        if not following.strip():
            continue
        expanded = following.expandtabs()
        indentation = len(expanded) - len(expanded.lstrip())
        if indentation <= base_indent:
            break
        continuation.append(following.strip())
    return " ".join(continuation)


def readme_inventory(text: str) -> List[str]:
    start_marker = "## Included Skills"
    start = text.find(start_marker)
    if start < 0:
        return []
    section_start = start + len(start_marker)
    next_heading = text.find("\n## ", section_start)
    section = text[section_start:] if next_heading < 0 else text[section_start:next_heading]
    return README_ENTRY_PATTERN.findall(section)


def verify_repository(repo_root: Path) -> List[str]:
    issues = []
    files = tracked_files(repo_root)
    skill_names = tracked_skill_names(files)

    for required_path in ("AGENTS.md", "README.md", "scripts/verify_repository.sh"):
        if required_path not in files:
            issues.append(f"required repository contract is not tracked: {required_path}")

    if not skill_names:
        issues.append("no tracked top-level skills were found")

    for skill_name in skill_names:
        if SKILL_NAME_PATTERN.fullmatch(skill_name) is None:
            issues.append(f"{skill_name}: directory name is not a canonical skill name")

        skill_path = repo_root / skill_name / "SKILL.md"
        skill_text = skill_path.read_text(encoding="utf-8")
        header = frontmatter(skill_text)
        if not header:
            issues.append(f"{skill_name}: SKILL.md has no closed frontmatter block")
        else:
            declared_name = scalar_value(header, "name")
            description = scalar_value(header, "description")
            if declared_name != skill_name:
                issues.append(
                    f"{skill_name}: frontmatter name is {declared_name!r}, expected {skill_name!r}"
                )
            if not description:
                issues.append(f"{skill_name}: frontmatter description is empty")

        metadata_relative = f"{skill_name}/agents/openai.yaml"
        if metadata_relative not in files:
            issues.append(f"{skill_name}: tracked agents/openai.yaml is missing")
            continue

        metadata_text = (repo_root / metadata_relative).read_text(encoding="utf-8")
        for key in ("display_name", "short_description", "default_prompt"):
            if not metadata_value(metadata_text, key):
                issues.append(f"{skill_name}: agents/openai.yaml has no {key}")
        if f"${skill_name}" not in metadata_value(metadata_text, "default_prompt"):
            issues.append(
                f"{skill_name}: default_prompt does not invoke ${skill_name}"
            )

    readme_relative = "README.md"
    if readme_relative not in files:
        issues.append("tracked README.md is missing")
    else:
        inventory = readme_inventory(
            (repo_root / readme_relative).read_text(encoding="utf-8")
        )
        if inventory != sorted(inventory):
            issues.append("README Included Skills entries are not sorted")
        duplicates = sorted({name for name in inventory if inventory.count(name) > 1})
        if duplicates:
            issues.append(
                "README Included Skills contains duplicates: " + ", ".join(duplicates)
            )
        missing = sorted(set(skill_names) - set(inventory))
        extra = sorted(set(inventory) - set(skill_names))
        if missing:
            issues.append("README Included Skills is missing: " + ", ".join(missing))
        if extra:
            issues.append("README Included Skills has untracked entries: " + ", ".join(extra))

    agents_relative = "AGENTS.md"
    if agents_relative in files:
        agents_text = (repo_root / agents_relative).read_text(encoding="utf-8")
        if "bash scripts/verify_repository.sh" not in agents_text:
            issues.append("AGENTS.md does not document the standard verification command")

    return issues


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "repo_root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] = ()) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    if sys.version_info < (3, 9):
        print("error: Python 3.9 or later is required", file=sys.stderr)
        return 2

    try:
        issues = verify_repository(repo_root)
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"error: could not inspect repository: {error}", file=sys.stderr)
        return 2

    if issues:
        for issue in issues:
            print(f"error: {issue}", file=sys.stderr)
        return 1

    count = len(tracked_skill_names(tracked_files(repo_root)))
    print(f"metadata and README inventory: ok ({count} tracked skills)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
