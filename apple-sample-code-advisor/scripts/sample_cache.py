#!/usr/bin/env python3
"""Manage the apple-sample-code-advisor skill's local cache."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import fcntl
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import urllib.request
import uuid
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterator, Optional


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = Path(os.environ.get("APPLE_SAMPLE_CODE_CACHE", SKILL_ROOT / "cache"))
MANIFEST_NAME = "manifest.json"
SAMPLE_METADATA_NAME = "metadata.json"
LOCK_NAME = ".sample-cache.lock"
SAFE_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
IGNORED_SOURCE_NAMES = {
    ".build",
    ".git",
    ".swiftpm",
    ".venv",
    "Carthage",
    "DerivedData",
    "Pods",
    "build",
    "node_modules",
}
MAX_DOWNLOAD_BYTES = 2 * 1024 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 20_000
MAX_ARCHIVE_MEMBER_BYTES = 512 * 1024 * 1024
MAX_ARCHIVE_UNCOMPRESSED_BYTES = 2 * 1024 * 1024 * 1024
MAX_ARCHIVE_COMPRESSION_RATIO = 200
DOWNLOAD_TIMEOUT_SECONDS = 60


class CacheError(RuntimeError):
    """Raised when a cache operation cannot complete safely."""


@dataclass(frozen=True)
class DownloadedSource:
    path: Path
    owned_temp: bool


def utc_now() -> str:
    return (
        dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "sample"


def validate_slug(slug: str) -> str:
    if not SAFE_SLUG_PATTERN.fullmatch(slug):
        raise CacheError(f"Unsafe sample slug: {slug!r}")
    return slug


def cache_root(args: argparse.Namespace) -> Path:
    return Path(args.cache_root).expanduser().resolve()


def manifest_path(root: Path) -> Path:
    return root / MANIFEST_NAME


def sample_dir(root: Path, slug: str) -> Path:
    return root / "samples" / validate_slug(slug)


def source_dir(root: Path, slug: str) -> Path:
    return sample_dir(root, slug) / "source"


def sample_metadata_path(root: Path, slug: str) -> Path:
    return sample_dir(root, slug) / SAMPLE_METADATA_NAME


def ensure_samples_root(root: Path) -> Path:
    samples_root = root / "samples"
    if samples_root.is_symlink() or (
        samples_root.exists() and not samples_root.is_dir()
    ):
        raise CacheError(f"Unsafe cache samples directory: {samples_root}")
    samples_root.mkdir(parents=True, exist_ok=True)
    return samples_root


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        file = os.fdopen(descriptor, "w", encoding="utf-8")
        descriptor = -1
        with file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, path)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        temporary_path.unlink(missing_ok=True)


def atomic_write_json(path: Path, payload: dict) -> None:
    atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def remove_file_verified(path: Path) -> None:
    path.unlink(missing_ok=True)
    if path.exists() or path.is_symlink():
        raise CacheError(f"Temporary file still exists after deletion: {path}")


def load_manifest(root: Path) -> dict:
    path = manifest_path(root)
    if not path.exists():
        return {"version": 1, "samples": {}}
    if path.is_symlink() or not path.is_file():
        raise CacheError(f"Unsafe cache manifest: {path}")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CacheError(f"Failed to read cache manifest {path}: {error}") from error
    if not isinstance(manifest, dict) or not isinstance(manifest.get("samples"), dict):
        raise CacheError(f"Invalid cache manifest shape: {path}")
    for slug, metadata in manifest["samples"].items():
        validate_slug(slug)
        if not isinstance(metadata, dict):
            raise CacheError(f"Invalid metadata for sample {slug!r} in {path}")
    return manifest


def save_manifest(root: Path, manifest: dict) -> None:
    atomic_write_json(manifest_path(root), manifest)


def save_sample_metadata(path: Path, metadata: dict) -> None:
    atomic_write_json(path, metadata)


@contextmanager
def cache_lock(root: Path) -> Iterator[None]:
    root.mkdir(parents=True, exist_ok=True)
    lock_path = root / LOCK_NAME
    if lock_path.is_symlink():
        raise CacheError(f"Unsafe cache lock path: {lock_path}")
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(lock_path, flags, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "a+") as lock_file:
            descriptor = -1
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def path_size(path: Path) -> int:
    if not path.exists() or path.is_symlink():
        return 0
    if path.is_file():
        return path.stat().st_size

    total = 0
    for current_root, directories, file_names in os.walk(path, topdown=True):
        current_path = Path(current_root)
        directories[:] = [
            name
            for name in directories
            if not (current_path / name).is_symlink()
        ]
        for file_name in file_names:
            file_path = current_path / file_name
            if file_path.is_symlink() or not file_path.is_file():
                continue
            total += file_path.stat().st_size
    return total


def human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size} B"


def validate_directory_source(source: Path) -> None:
    for path in source.rglob("*"):
        if path.is_symlink():
            raise CacheError(f"Refusing to cache a source tree containing a symlink: {path}")


def archive_member_parts(info: zipfile.ZipInfo) -> tuple[str, ...]:
    name = info.filename
    if not name or "\x00" in name or "\\" in name:
        raise CacheError(f"Unsafe zip member path: {name!r}")
    pure_path = PurePosixPath(name)
    parts = pure_path.parts
    if (
        pure_path.is_absolute()
        or not parts
        or any(part in {"", ".", ".."} for part in parts)
        or re.match(r"^[A-Za-z]:", parts[0])
    ):
        raise CacheError(f"Unsafe zip member path: {name!r}")
    return parts


def validated_archive_members(
    archive: zipfile.ZipFile,
) -> list[tuple[zipfile.ZipInfo, tuple[str, ...]]]:
    infos = archive.infolist()
    if len(infos) > MAX_ARCHIVE_MEMBERS:
        raise CacheError(
            f"Archive contains too many members: {len(infos)} > {MAX_ARCHIVE_MEMBERS}"
        )

    members: list[tuple[zipfile.ZipInfo, tuple[str, ...]]] = []
    seen: set[str] = set()
    file_paths: set[str] = set()
    total_size = 0
    for info in infos:
        parts = archive_member_parts(info)
        if parts[0] == "__MACOSX":
            continue

        unix_mode = (info.external_attr >> 16) & 0xFFFF
        file_type = stat.S_IFMT(unix_mode)
        if stat.S_ISLNK(unix_mode):
            raise CacheError(f"Archive contains a symbolic link: {info.filename}")
        if file_type not in {0, stat.S_IFREG, stat.S_IFDIR}:
            raise CacheError(f"Archive contains a special file: {info.filename}")
        if info.flag_bits & 0x1:
            raise CacheError(f"Archive contains an encrypted member: {info.filename}")
        if info.file_size > MAX_ARCHIVE_MEMBER_BYTES:
            raise CacheError(f"Archive member is too large: {info.filename}")
        total_size += info.file_size
        if total_size > MAX_ARCHIVE_UNCOMPRESSED_BYTES:
            raise CacheError("Archive expands beyond the cache safety limit")
        if (
            info.file_size > 1024 * 1024
            and info.compress_size > 0
            and info.file_size > info.compress_size * MAX_ARCHIVE_COMPRESSION_RATIO
        ):
            raise CacheError(f"Archive member has an unsafe compression ratio: {info.filename}")

        normalized = "/".join(parts).casefold()
        if normalized in seen:
            raise CacheError(
                "Archive contains a duplicate or case-colliding path: "
                f"{info.filename}"
            )
        seen.add(normalized)
        if not info.is_dir():
            file_paths.add(normalized)
        members.append((info, parts))

    for _, parts in members:
        for index in range(1, len(parts)):
            parent = "/".join(parts[:index]).casefold()
            if parent in file_paths:
                raise CacheError(f"Archive file/directory path conflict: {'/'.join(parts)}")
    return members


def safe_extract_zip(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    destination_root = destination.resolve()
    try:
        with zipfile.ZipFile(source) as archive:
            members = validated_archive_members(archive)
            for info, parts in members:
                target = destination.joinpath(*parts)
                resolved_target = target.resolve()
                if (
                    destination_root not in resolved_target.parents
                    and resolved_target != destination_root
                ):
                    raise CacheError(f"Archive member escapes destination: {info.filename}")
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue

                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source_file, target.open("xb") as target_file:
                    shutil.copyfileobj(source_file, target_file)
                if target.stat().st_size != info.file_size:
                    raise CacheError(f"Archive member size mismatch: {info.filename}")
                unix_mode = (info.external_attr >> 16) & 0xFFFF
                target.chmod(0o755 if unix_mode & 0o111 else 0o644)
    except zipfile.BadZipFile as error:
        raise CacheError(f"Invalid zip archive {source}: {error}") from error


def flatten_single_root(destination: Path) -> None:
    children = [child for child in destination.iterdir() if child.name != "__MACOSX"]
    if len(children) != 1 or not children[0].is_dir() or children[0].is_symlink():
        return
    root_child = children[0]
    temporary = destination.with_name(f".{destination.name}.flatten-{uuid.uuid4().hex}")
    os.replace(root_child, temporary)
    shutil.rmtree(destination)
    os.replace(temporary, destination)


def copy_source(source: Path, destination: Path) -> None:
    if source.is_dir():
        validate_directory_source(source)
        shutil.copytree(
            source,
            destination,
            symlinks=True,
            ignore=shutil.ignore_patterns(*sorted(IGNORED_SOURCE_NAMES)),
        )
        validate_directory_source(destination)
        return
    if source.is_file() and zipfile.is_zipfile(source):
        safe_extract_zip(source, destination)
        flatten_single_root(destination)
        return
    raise CacheError(f"Unsupported source. Provide a directory or zip archive: {source}")


def download_to_temp(url: str) -> DownloadedSource:
    local_path = Path(url).expanduser()
    if local_path.exists():
        return DownloadedSource(path=local_path.resolve(), owned_temp=False)

    suffix = ".zip" if ".zip" in url.lower() else ""
    descriptor, temporary_name = tempfile.mkstemp(prefix="apple-sample-", suffix=suffix)
    temporary_path = Path(temporary_name)
    try:
        os.close(descriptor)
        descriptor = -1
        with urllib.request.urlopen(url, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_DOWNLOAD_BYTES:
                raise CacheError(f"Download exceeds cache safety limit: {content_length} bytes")
            total = 0
            with temporary_path.open("wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_DOWNLOAD_BYTES:
                        raise CacheError("Download exceeds cache safety limit")
                    output.write(chunk)
        return DownloadedSource(path=temporary_path, owned_temp=True)
    except BaseException as error:
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except OSError:
                pass
        remove_file_verified(temporary_path)
        if isinstance(error, CacheError):
            raise
        if not isinstance(error, Exception):
            raise
        raise CacheError(f"Failed to download {url}: {error}") from error


def metadata_from_args(
    args: argparse.Namespace,
    root: Path,
    slug: str,
    staged_source: Path,
) -> dict:
    return {
        "slug": slug,
        "title": args.title,
        "apple_url": args.apple_url,
        "source_url": getattr(args, "url", "") or str(getattr(args, "source", "")),
        "frameworks": args.frameworks or [],
        "notes": args.notes or "",
        "fetched_at": utc_now(),
        "cache_path": str(sample_dir(root, slug)),
        "size_bytes": path_size(staged_source),
    }


def unique_sibling(path: Path, label: str) -> Path:
    return path.with_name(f".{path.name}.{label}-{uuid.uuid4().hex}")


def remove_tree_verified(path: Path) -> None:
    if path.is_symlink() or not path.is_dir():
        raise CacheError(f"Refusing to remove unsafe cache path: {path}")
    shutil.rmtree(path)
    if path.exists() or path.is_symlink():
        raise CacheError(f"Cache path still exists after deletion: {path}")


def swap_staged_sample(
    root: Path,
    destination: Path,
    staged_sample: Path,
    updated_manifest: dict,
) -> None:
    backup: Optional[Path] = None
    if destination.is_symlink() or (destination.exists() and not destination.is_dir()):
        raise CacheError(f"Unsafe existing cache entry: {destination}")

    try:
        if destination.exists():
            backup = unique_sibling(destination, "backup")
            os.replace(destination, backup)
        try:
            os.replace(staged_sample, destination)
        except Exception:
            if backup is not None and not destination.exists():
                os.replace(backup, destination)
                backup = None
            raise

        try:
            save_manifest(root, updated_manifest)
        except Exception as manifest_error:
            failed_sample = unique_sibling(destination, "failed")
            try:
                os.replace(destination, failed_sample)
                if backup is not None:
                    os.replace(backup, destination)
                    backup = None
                remove_tree_verified(failed_sample)
            except Exception as rollback_error:
                raise CacheError(
                    "Cache manifest update failed and rollback was incomplete; "
                    f"inspect {destination} and {backup or failed_sample}"
                ) from rollback_error
            raise CacheError(
                "Cache manifest update failed; previous entry restored: "
                f"{manifest_error}"
            ) from manifest_error

        if backup is not None:
            remove_tree_verified(backup)
    except CacheError:
        raise
    except Exception as error:
        raise CacheError(f"Failed to install cache entry {destination}: {error}") from error


def install_source(args: argparse.Namespace, source: Path) -> tuple[Path, dict]:
    root = cache_root(args)
    slug = validate_slug(slugify(args.slug or args.title))
    source = source.expanduser().resolve()
    if not source.exists():
        raise CacheError(f"Source does not exist: {source}")
    if root == source or root.is_relative_to(source):
        raise CacheError(f"Source must not contain the cache root: {source}")

    with cache_lock(root):
        manifest = load_manifest(root)
        destination = sample_dir(root, slug)
        manifest_has_entry = slug in manifest.get("samples", {})
        entry_exists = destination.exists() or destination.is_symlink() or manifest_has_entry
        if entry_exists and not args.replace:
            raise CacheError(
                f"Cache entry already exists: {destination}. Use --replace to refresh it."
            )

        samples_root = ensure_samples_root(root)
        staged_sample = Path(tempfile.mkdtemp(dir=samples_root, prefix=f".{slug}.staging-"))
        try:
            staged_source = staged_sample / "source"
            copy_source(source, staged_source)
            metadata = metadata_from_args(args, root, slug, staged_source)
            save_sample_metadata(staged_sample / SAMPLE_METADATA_NAME, metadata)

            updated_manifest = copy.deepcopy(manifest)
            updated_manifest.setdefault("samples", {})[slug] = metadata
            swap_staged_sample(root, destination, staged_sample, updated_manifest)
        finally:
            if staged_sample.exists():
                remove_tree_verified(staged_sample)
    return destination, metadata


def cmd_list(args: argparse.Namespace) -> int:
    root = cache_root(args)
    manifest = load_manifest(root)
    samples = manifest.get("samples", {})
    if not samples:
        print(f"No cached samples in {root}")
        return 0
    for slug, item in sorted(samples.items()):
        size = human_size(int(item.get("size_bytes", 0)))
        fetched = item.get("fetched_at", "unknown")
        title = item.get("title", slug)
        print(f"{slug}\t{size}\t{fetched}\t{title}")
    return 0


def cmd_add_local(args: argparse.Namespace) -> int:
    source = Path(args.source).expanduser()
    destination, metadata = install_source(args, source)
    print(f"Cached {metadata['slug']} at {destination}")
    return 0


def cmd_fetch_archive(args: argparse.Namespace) -> int:
    downloaded = download_to_temp(args.url)
    try:
        destination, metadata = install_source(args, downloaded.path)
    finally:
        if downloaded.owned_temp:
            remove_file_verified(downloaded.path)
    print(f"Fetched {metadata['slug']} at {destination}")
    return 0


def tree_lines(path: Path, max_depth: int, prefix: str = "") -> list[str]:
    if max_depth < 0 or not path.exists():
        return []
    entries = sorted(path.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
    lines: list[str] = []
    for entry in entries[:80]:
        if entry.is_symlink():
            lines.append(f"{prefix}{entry.name}@")
            continue
        marker = "/" if entry.is_dir() else ""
        lines.append(f"{prefix}{entry.name}{marker}")
        if entry.is_dir():
            lines.extend(tree_lines(entry, max_depth - 1, prefix + "  "))
    if len(entries) > 80:
        lines.append(f"{prefix}... {len(entries) - 80} more")
    return lines


def cmd_inspect(args: argparse.Namespace) -> int:
    root = cache_root(args)
    slug = validate_slug(slugify(args.slug))
    manifest = load_manifest(root)
    item = manifest.get("samples", {}).get(slug)
    if not item:
        raise CacheError(f"Sample not found: {slug}")
    print(json.dumps(item, indent=2, sort_keys=True))
    print("\nsource tree:")
    source = source_dir(root, slug)
    for line in tree_lines(source, args.max_depth):
        print(line)
    return 0


def parse_time(value: object) -> Optional[dt.datetime]:
    if not isinstance(value, str) or not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def classify_stale_samples(
    manifest: dict,
    max_age_days: int,
) -> tuple[list[tuple[str, dict, int]], list[str]]:
    now = dt.datetime.now(dt.timezone.utc)
    stale: list[tuple[str, dict, int]] = []
    invalid: list[str] = []
    for slug, item in manifest.get("samples", {}).items():
        fetched = parse_time(item.get("fetched_at"))
        if fetched is None:
            invalid.append(slug)
            continue
        age = (now - fetched).days
        if age >= max_age_days:
            stale.append((slug, item, age))
    return stale, invalid


def cmd_refresh_plan(args: argparse.Namespace) -> int:
    if args.max_age_days < 0:
        raise CacheError("--max-age-days must be non-negative")
    root = cache_root(args)
    manifest = load_manifest(root)
    stale, invalid = classify_stale_samples(manifest, args.max_age_days)
    for slug in invalid:
        print(f"invalid\t{slug}\tmissing or invalid fetched_at", file=sys.stderr)
    if invalid:
        print("Refusing to classify invalid cache metadata as stale.", file=sys.stderr)
        return 2
    if not stale:
        print(f"No samples older than {args.max_age_days} days in {root}")
        return 0
    for slug, item, age in stale:
        print(f"{slug}\t{age} days\t{item.get('apple_url', '')}")
    return 0


def rollback_moved_directories(moved: list[tuple[Path, Path]]) -> None:
    errors: list[str] = []
    for original, temporary in reversed(moved):
        if not temporary.exists():
            continue
        try:
            os.replace(temporary, original)
        except OSError as error:
            errors.append(f"{temporary} -> {original}: {error}")
    if errors:
        raise CacheError("Failed to roll back cache prune: " + "; ".join(errors))


def apply_prune(root: Path, manifest: dict, stale: list[tuple[str, dict, int]]) -> None:
    moved: list[tuple[Path, Path]] = []
    updated_manifest = copy.deepcopy(manifest)
    try:
        for slug, _, _ in stale:
            target = sample_dir(root, slug)
            if target.is_symlink() or not target.is_dir():
                raise CacheError(f"Cannot safely prune missing or invalid cache entry: {target}")
            temporary = unique_sibling(target, "prune")
            os.replace(target, temporary)
            moved.append((target, temporary))
            updated_manifest.get("samples", {}).pop(slug, None)
        save_manifest(root, updated_manifest)
    except Exception as error:
        rollback_moved_directories(moved)
        if isinstance(error, CacheError):
            raise
        raise CacheError(f"Failed to stage cache prune: {error}") from error

    for _, temporary in moved:
        remove_tree_verified(temporary)


def cmd_prune(args: argparse.Namespace) -> int:
    if args.max_age_days < 0:
        raise CacheError("--max-age-days must be non-negative")
    root = cache_root(args)
    with cache_lock(root):
        manifest = load_manifest(root)
        stale, invalid = classify_stale_samples(manifest, args.max_age_days)
        if invalid:
            names = ", ".join(invalid)
            raise CacheError(
                "Refusing to prune because fetched_at is missing or invalid for: " + names
            )
        if not stale:
            print(f"No prune candidates older than {args.max_age_days} days in {root}")
            return 0
        for slug, _, age in stale:
            target = sample_dir(root, slug)
            action = "delete" if args.apply else "dry-run"
            print(f"{action}\t{slug}\t{age} days\t{target}")
        if args.apply:
            apply_prune(root, manifest, stale)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-root", default=str(DEFAULT_ROOT), help="Cache root directory")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list").set_defaults(func=cmd_list)

    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("slug")
    inspect_parser.add_argument("--max-depth", type=int, default=2)
    inspect_parser.set_defaults(func=cmd_inspect)

    add_parser = subparsers.add_parser("add-local")
    add_parser.add_argument("--source", required=True)
    add_parser.add_argument("--title", required=True)
    add_parser.add_argument("--slug", default="")
    add_parser.add_argument("--apple-url", required=True)
    add_parser.add_argument("--frameworks", nargs="*", default=[])
    add_parser.add_argument("--notes", default="")
    add_parser.add_argument("--replace", action="store_true")
    add_parser.set_defaults(func=cmd_add_local)

    fetch_parser = subparsers.add_parser("fetch-archive")
    fetch_parser.add_argument("--url", required=True)
    fetch_parser.add_argument("--title", required=True)
    fetch_parser.add_argument("--slug", default="")
    fetch_parser.add_argument("--apple-url", required=True)
    fetch_parser.add_argument("--frameworks", nargs="*", default=[])
    fetch_parser.add_argument("--notes", default="")
    fetch_parser.add_argument("--replace", action="store_true")
    fetch_parser.set_defaults(func=cmd_fetch_archive)

    refresh_parser = subparsers.add_parser("refresh-plan")
    refresh_parser.add_argument("--max-age-days", type=int, default=30)
    refresh_parser.set_defaults(func=cmd_refresh_plan)

    prune_parser = subparsers.add_parser("prune")
    prune_parser.add_argument("--max-age-days", type=int, default=90)
    prune_parser.add_argument("--apply", action="store_true")
    prune_parser.set_defaults(func=cmd_prune)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (CacheError, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
