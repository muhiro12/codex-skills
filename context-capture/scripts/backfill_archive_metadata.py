#!/usr/bin/env python3
"""Backfill v2 context archive frontmatter fields without changing record bodies."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import stat
import sys
import tempfile
from pathlib import Path


GENERATED_DIRECTORIES = {
    ".build",
    "build",
    "DerivedData",
    ".git",
    ".swiftpm",
    "Pods",
    "Carthage",
}


def local_timestamp() -> str:
    return dt.datetime.now().astimezone().replace(microsecond=0).isoformat()


def iter_markdown_files(root: Path) -> list[Path]:
    results: list[Path] = []
    for child in sorted(root.iterdir()):
        if child.is_symlink():
            print(f"skipped  {child} (symbolic link)", file=sys.stderr)
            continue
        if child.is_dir():
            if child.name in GENERATED_DIRECTORIES:
                continue
            results.extend(iter_markdown_files(child))
        elif child.is_file() and child.suffix == ".md":
            results.append(child)
    return results


def find_markdown_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        expanded = path.expanduser().absolute()
        if expanded.is_symlink():
            print(f"skipped  {expanded} (symbolic link)", file=sys.stderr)
        elif expanded.is_file() and expanded.suffix == ".md":
            files.append(expanded)
        elif expanded.is_dir():
            files.extend(iter_markdown_files(expanded))
        elif expanded.is_file():
            print(f"skipped  {expanded} (not Markdown)", file=sys.stderr)
        else:
            print(f"missing  {expanded}", file=sys.stderr)
    return sorted(dict.fromkeys(files))


def atomic_rewrite(path: Path, text: str, expected_stat: os.stat_result) -> None:
    """Replace a regular file atomically without following a late symlink swap."""

    current_stat = path.lstat()
    if stat.S_ISLNK(current_stat.st_mode) or not stat.S_ISREG(current_stat.st_mode):
        raise RuntimeError(f"refusing to replace non-regular file: {path}")
    if (current_stat.st_dev, current_stat.st_ino) != (expected_stat.st_dev, expected_stat.st_ino):
        raise RuntimeError(f"file changed while backfill was running: {path}")

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(text)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)

        os.chmod(temporary_path, stat.S_IMODE(expected_stat.st_mode))
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def split_frontmatter(text: str) -> tuple[str, str] | None:
    match = re.match(r"^---\n(.*?)\n---(\n|$)(.*)$", text, re.DOTALL)
    if not match:
        return None
    frontmatter = match.group(1)
    body = match.group(3)
    return frontmatter, body


def top_level_fields(frontmatter: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if line.startswith((" ", "\t")):
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:\s*(.*))?$", line)
        if match:
            fields[match.group(1)] = (match.group(2) or "").strip()
    return fields


def clean_scalar(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def is_derived_record(record_type: str) -> bool:
    return record_type.startswith("derived-")


def append_array(key: str, values: list[str]) -> str:
    if not values:
        return f"{key}: []"
    lines = [f"{key}:"]
    lines.extend(f"  - {value}" for value in values)
    return "\n".join(lines)


def additions_for(fields: dict[str, str], now: str) -> list[str]:
    record_type = clean_scalar(fields.get("record_type", ""))
    if record_type != "raw" and not is_derived_record(record_type):
        return []

    additions: list[str] = []
    is_derived = is_derived_record(record_type)

    if "observer_perspective" not in fields:
        perspective = "archive-derived-from-cited-records" if is_derived else "user-provided-observer-record"
        additions.append(f"observer_perspective: {perspective}")

    if "coverage_limitations" not in fields:
        additions.append(
            append_array(
                "coverage_limitations",
                ["legacy record created before coverage_limitations field was introduced"],
            )
        )

    if "use_policies" not in fields:
        policies = ["internal-reference-only"] if is_derived else ["unknown"]
        additions.append(append_array("use_policies", policies))

    if is_derived:
        created_at = clean_scalar(fields.get("created_at", ""))
        if "last_updated" not in fields:
            additions.append(f"last_updated: {created_at or now}")
        if "review_due" not in fields:
            additions.append("review_due: null")
        if "supersedes" not in fields:
            additions.append("supersedes: []")
        if "revision_note" not in fields:
            additions.append("revision_note: legacy metadata backfill; content unchanged")

    return additions


def backfill_text(text: str, now: str) -> tuple[str, list[str]]:
    parts = split_frontmatter(text)
    if parts is None:
        return text, []

    frontmatter, body = parts
    fields = top_level_fields(frontmatter)
    additions = additions_for(fields, now)
    if not additions:
        return text, []

    updated_frontmatter = frontmatter.rstrip("\n") + "\n" + "\n".join(additions)
    return f"---\n{updated_frontmatter}\n---\n{body}", additions


def default_archive_root() -> Path:
    return Path(__file__).resolve().parents[1] / "archives"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Archive files or directories to inspect. Defaults to context-capture/archives.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Rewrite files in place. Default is dry-run.",
    )
    args = parser.parse_args()

    paths = args.paths or [default_archive_root()]
    files = find_markdown_files(paths)
    mode = "apply" if args.apply else "dry-run"
    print(f"mode     {mode}")

    changed = 0
    skipped = 0
    now = local_timestamp()
    for path in files:
        initial_stat = path.lstat()
        if stat.S_ISLNK(initial_stat.st_mode) or not stat.S_ISREG(initial_stat.st_mode):
            print(f"skipped  {path} (not a regular file)", file=sys.stderr)
            skipped += 1
            continue
        with path.open("r", encoding="utf-8", newline="") as source:
            text = source.read()
        updated, additions = backfill_text(text, now)
        if not additions:
            skipped += 1
            continue

        changed += 1
        keys = ", ".join(line.split(":", 1)[0] for line in additions)
        if args.apply:
            atomic_rewrite(path, updated, initial_stat)
            print(f"updated  {path} ({keys})")
        else:
            print(f"would-update {path} ({keys})")

    print(f"summary  inspected={len(files)} changed={changed} skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
