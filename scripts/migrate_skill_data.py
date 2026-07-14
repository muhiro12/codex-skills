#!/usr/bin/env python3
"""Migrate legacy local skill data into skill-owned data directories."""

from __future__ import annotations

import argparse
import filecmp
import os
import stat
import shutil
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


GROUPS = ("principles", "context-archives", "apple-sample-cache")
INITIAL_DATA_LAYOUT_VERSION = 1
CURRENT_DATA_LAYOUT_VERSION = 2


@dataclass
class MigrationStats:
    copied: int = 0
    would_copy: int = 0
    same: int = 0
    conflicts: int = 0
    missing_sources: int = 0
    bytes_to_copy: int = 0
    skipped_links: int = 0
    permissions_changed: int = 0
    permissions_would_change: int = 0


@dataclass(frozen=True)
class Migration:
    identifier: str
    from_version: int
    to_version: int
    description: str
    groups: tuple[str, ...]
    run: Callable[[Path, Path, bool, set[str], MigrationStats], None]


def file_size(path: Path) -> int:
    if not path.exists() or not path.is_file():
        return 0
    return path.stat().st_size


def human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size} B"


def list_files(source: Path) -> list[Path]:
    if source.is_symlink():
        return []
    if source.is_file():
        return [source]
    if source.is_dir():
        files: list[Path] = []
        for root, directory_names, file_names in os.walk(source, followlinks=False):
            root_path = Path(root)
            directory_names[:] = [
                name
                for name in directory_names
                if not (root_path / name).is_symlink()
            ]
            files.extend(
                path
                for name in file_names
                if not (path := root_path / name).is_symlink() and path.is_file()
            )
        return sorted(files)
    return []


def atomic_copy(source: Path, target: Path) -> None:
    temporary_path: Path | None = None
    try:
        with source.open("rb") as source_file, tempfile.NamedTemporaryFile(
            mode="wb",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            shutil.copyfileobj(source_file, temporary)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        shutil.copystat(source, temporary_path, follow_symlinks=False)
        os.replace(temporary_path, target)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def has_symbolic_link_component(path: Path, boundary: Path) -> bool:
    try:
        relative = path.relative_to(boundary)
    except ValueError:
        return True

    current = boundary
    if current.is_symlink():
        return True
    for component in relative.parts:
        current /= component
        if current.is_symlink():
            return True
    return False


def copy_file(
    source: Path,
    target: Path,
    *,
    apply: bool,
    stats: MigrationStats,
    target_boundary: Path | None = None,
) -> None:
    if source.is_symlink():
        stats.skipped_links += 1
        print(f"skip     symbolic link source: {source}")
        return
    boundary = target_boundary or target.parent
    if has_symbolic_link_component(target, boundary):
        stats.conflicts += 1
        print(f"conflict symbolic link in target path: {target}")
        return
    if os.path.lexists(target):
        if not target.is_symlink() and target.is_file() and filecmp.cmp(source, target, shallow=False):
            stats.same += 1
            print(f"same     {source} -> {target}")
            return
        stats.conflicts += 1
        print(f"conflict {source} -> {target}")
        return

    size = file_size(source)
    stats.bytes_to_copy += size
    if apply:
        target.parent.mkdir(parents=True, exist_ok=True)
        atomic_copy(source, target)
        stats.copied += 1
        print(f"copied   {source} -> {target}")
    else:
        stats.would_copy += 1
        print(f"copy     {source} -> {target} ({human_size(size)})")


def migrate_tree(source: Path, target: Path, *, apply: bool, stats: MigrationStats) -> None:
    if source.is_symlink():
        stats.skipped_links += 1
        print(f"skip     symbolic link source: {source}")
        return
    if not source.exists():
        stats.missing_sources += 1
        print(f"missing  {source}")
        return

    if source.is_file():
        copy_file(
            source,
            target,
            apply=apply,
            stats=stats,
            target_boundary=target.parent,
        )
        return

    if not source.is_dir():
        stats.conflicts += 1
        print(f"skip     unsupported source type: {source}")
        return

    files = list_files(source)
    if not files and apply:
        target.mkdir(parents=True, exist_ok=True)
    for file_path in files:
        relative = file_path.relative_to(source)
        copy_file(
            file_path,
            target / relative,
            apply=apply,
            stats=stats,
            target_boundary=target,
        )


def private_data_roots(skills_root: Path, groups: set[str]) -> list[Path]:
    roots: list[Path] = []
    if "principles" in groups:
        roots.extend(
            [
                skills_root / "track-developer-principles" / "records",
                skills_root / "track-personal-principles" / "records",
            ]
        )
    if "context-archives" in groups:
        roots.append(skills_root / "context-capture" / "archives")
    return roots


def enforce_private_permissions(
    roots: list[Path],
    *,
    apply: bool,
    stats: MigrationStats,
) -> None:
    for root in roots:
        if root.is_symlink():
            stats.skipped_links += 1
            print(f"skip     symbolic link private-data root: {root}")
            continue
        if not root.exists():
            continue

        paths = [root]
        for directory, directory_names, file_names in os.walk(root, followlinks=False):
            directory_path = Path(directory)
            directory_names[:] = [
                name
                for name in directory_names
                if not (directory_path / name).is_symlink()
            ]
            paths.extend(directory_path / name for name in directory_names)
            paths.extend(
                path
                for name in file_names
                if not (path := directory_path / name).is_symlink()
            )

        for path in paths:
            desired_mode = 0o700 if path.is_dir() else 0o600
            current_mode = stat.S_IMODE(path.lstat().st_mode)
            if current_mode == desired_mode:
                continue
            if apply:
                os.chmod(path, desired_mode, follow_symlinks=False)
                stats.permissions_changed += 1
                print(f"secured  {path} ({current_mode:04o} -> {desired_mode:04o})")
            else:
                stats.permissions_would_change += 1
                print(f"secure   {path} ({current_mode:04o} -> {desired_mode:04o})")


def migrate_principles(skills_root: Path, *, apply: bool, stats: MigrationStats) -> None:
    mappings = [
        (
            "track-developer-principles",
            ["current-principles.md", "evolution-log.md", "principles"],
        ),
        (
            "track-personal-principles",
            ["current-principles.md", "evolution-log.md", "principles"],
        ),
    ]
    for skill_name, entries in mappings:
        for entry in entries:
            migrate_tree(
                skills_root / skill_name / "references" / entry,
                skills_root / skill_name / "records" / entry,
                apply=apply,
                stats=stats,
            )


def migrate_context_archives(
    skills_root: Path,
    home: Path,
    *,
    apply: bool,
    stats: MigrationStats,
) -> None:
    for scope in ("private", "work", "shared-safe"):
        migrate_tree(
            home / "context-archives" / scope,
            skills_root / "context-capture" / "archives" / scope,
            apply=apply,
            stats=stats,
        )


def migrate_apple_cache(skills_root: Path, home: Path, *, apply: bool, stats: MigrationStats) -> None:
    migrate_tree(
        home / ".codex" / "cache" / "apple-sample-code",
        skills_root / "apple-sample-code-advisor" / "cache",
        apply=apply,
        stats=stats,
    )


def migrate_skill_owned_data_directories(
    skills_root: Path,
    home: Path,
    apply: bool,
    groups: set[str],
    stats: MigrationStats,
) -> None:
    if "principles" in groups:
        migrate_principles(skills_root, apply=apply, stats=stats)
    if "context-archives" in groups:
        migrate_context_archives(skills_root, home, apply=apply, stats=stats)
    if "apple-sample-cache" in groups:
        migrate_apple_cache(skills_root, home, apply=apply, stats=stats)


MIGRATIONS = (
    Migration(
        identifier="v1-to-v2-skill-owned-data-directories",
        from_version=1,
        to_version=2,
        description="Copy legacy local skill data into ignored skill-owned records, archives, and cache directories.",
        groups=GROUPS,
        run=migrate_skill_owned_data_directories,
    ),
)


def validate_migrations() -> None:
    expected_from_version = INITIAL_DATA_LAYOUT_VERSION
    seen: set[str] = set()
    for migration in MIGRATIONS:
        if migration.identifier in seen:
            raise SystemExit(f"Duplicate migration id: {migration.identifier}")
        seen.add(migration.identifier)
        if migration.from_version != expected_from_version:
            raise SystemExit(
                "Migration chain is not contiguous: "
                f"expected v{expected_from_version}, got v{migration.from_version} for {migration.identifier}"
            )
        if migration.to_version <= migration.from_version:
            raise SystemExit(
                f"Migration must advance the data layout version: {migration.identifier}"
            )
        expected_from_version = migration.to_version
    if expected_from_version != CURRENT_DATA_LAYOUT_VERSION:
        raise SystemExit(
            "CURRENT_DATA_LAYOUT_VERSION does not match the registered migration chain: "
            f"expected v{expected_from_version}, got v{CURRENT_DATA_LAYOUT_VERSION}"
        )


def selected_groups(values: list[str]) -> set[str]:
    if not values or "all" in values:
        return set(GROUPS)
    return set(values)


def selected_migrations(values: list[str]) -> tuple[Migration, ...]:
    if not values or "all" in values:
        return MIGRATIONS
    by_id = {migration.identifier: migration for migration in MIGRATIONS}
    selected = {by_id[value].identifier for value in values}
    return tuple(migration for migration in MIGRATIONS if migration.identifier in selected)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--list",
        action="store_true",
        help="List registered migrations and exit.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Copy missing legacy data into the new skill-owned locations. Default is dry-run.",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        choices=("all", *GROUPS),
        default=["all"],
        help="Limit migration groups.",
    )
    parser.add_argument(
        "--migration",
        nargs="+",
        choices=("all", *(migration.identifier for migration in MIGRATIONS)),
        default=["all"],
        help="Limit migration ids.",
    )
    parser.add_argument(
        "--skills-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Path to the skills root. Defaults to the parent of this script directory.",
    )
    parser.add_argument(
        "--home",
        default=str(Path.home()),
        help="Home directory to inspect for legacy external roots.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    validate_migrations()
    args = build_parser().parse_args(argv)
    skills_root = Path(args.skills_root).expanduser().resolve()
    home = Path(args.home).expanduser().resolve()
    groups = selected_groups(args.only)
    migrations = selected_migrations(args.migration)
    stats = MigrationStats()

    if args.list:
        print(f"current-data-layout-version\tv{CURRENT_DATA_LAYOUT_VERSION}")
        for migration in MIGRATIONS:
            print(
                f"{migration.identifier}\t"
                f"v{migration.from_version}->v{migration.to_version}\t"
                f"{','.join(migration.groups)}\t"
                f"{migration.description}"
            )
        return 0

    mode = "apply" if args.apply else "dry-run"
    print(f"mode     {mode}")
    print(f"layout   v{CURRENT_DATA_LAYOUT_VERSION}")
    print(f"skills   {skills_root}")
    print(f"home     {home}")

    for migration in migrations:
        active_groups = groups.intersection(migration.groups)
        if not active_groups:
            continue
        conflicts_before = stats.conflicts
        print(f"migration {migration.identifier}")
        migration.run(skills_root, home, args.apply, active_groups, stats)
        if stats.conflicts > conflicts_before:
            print(f"blocked  stopping after conflicts in {migration.identifier}")
            break

    enforce_private_permissions(
        private_data_roots(skills_root, groups),
        apply=args.apply,
        stats=stats,
    )

    print()
    print(
        "summary  "
        f"copied={stats.copied} "
        f"would_copy={stats.would_copy} "
        f"same={stats.same} "
        f"conflicts={stats.conflicts} "
        f"missing_sources={stats.missing_sources} "
        f"skipped_links={stats.skipped_links} "
        f"permissions_changed={stats.permissions_changed} "
        f"permissions_would_change={stats.permissions_would_change} "
        f"bytes_to_copy={human_size(stats.bytes_to_copy)}"
    )
    if stats.conflicts:
        print("result   conflicts require manual review; existing targets were not overwritten")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
