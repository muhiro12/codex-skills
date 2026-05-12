#!/usr/bin/env python3
"""Manage repo-external Apple sample code caches."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path


DEFAULT_ROOT = Path(os.environ.get("APPLE_SAMPLE_CODE_CACHE", Path.home() / ".codex/cache/apple-sample-code"))
MANIFEST_NAME = "manifest.json"
SAMPLE_METADATA_NAME = "metadata.json"


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "sample"


def cache_root(args: argparse.Namespace) -> Path:
    return Path(args.cache_root).expanduser().resolve()


def manifest_path(root: Path) -> Path:
    return root / MANIFEST_NAME


def sample_metadata_path(root: Path, slug: str) -> Path:
    return sample_dir(root, slug) / SAMPLE_METADATA_NAME


def load_manifest(root: Path) -> dict:
    path = manifest_path(root)
    if not path.exists():
        return {"version": 1, "samples": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(root: Path, manifest: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    manifest_path(root).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def save_sample_metadata(root: Path, slug: str, metadata: dict) -> None:
    target = sample_metadata_path(root, slug)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sample_dir(root: Path, slug: str) -> Path:
    return root / "samples" / slug


def source_dir(root: Path, slug: str) -> Path:
    return sample_dir(root, slug) / "source"


def path_size(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size} B"


def ensure_replace_ok(destination: Path, replace: bool) -> None:
    if destination.exists():
        if not replace:
            raise SystemExit(f"Cache entry already exists: {destination}. Use --replace to refresh it.")
        shutil.rmtree(destination)


def copy_source(source: Path, destination: Path) -> None:
    if source.is_dir():
        shutil.copytree(
            source,
            destination,
            ignore=shutil.ignore_patterns(".git", ".swiftpm", "DerivedData", ".build", "build", "Pods", "Carthage"),
        )
        return
    if zipfile.is_zipfile(source):
        destination.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(source) as archive:
            archive.extractall(destination)
        flatten_single_root(destination)
        return
    raise SystemExit(f"Unsupported source. Provide a directory or zip archive: {source}")


def flatten_single_root(destination: Path) -> None:
    children = [child for child in destination.iterdir() if not child.name.startswith("__MACOSX")]
    if len(children) != 1 or not children[0].is_dir():
        return
    root_child = children[0]
    tmp = destination.with_name(destination.name + "-flatten")
    if tmp.exists():
        shutil.rmtree(tmp)
    root_child.rename(tmp)
    shutil.rmtree(destination)
    tmp.rename(destination)


def download_to_temp(url: str) -> Path:
    parsed_path = Path(url).expanduser()
    if parsed_path.exists():
        return parsed_path.resolve()
    suffix = ".zip" if ".zip" in url.lower() else ""
    handle, tmp_name = tempfile.mkstemp(prefix="apple-sample-", suffix=suffix)
    os.close(handle)
    tmp_path = Path(tmp_name)
    with urllib.request.urlopen(url) as response, tmp_path.open("wb") as output:
        shutil.copyfileobj(response, output)
    return tmp_path


def metadata_from_args(args: argparse.Namespace, root: Path, slug: str) -> dict:
    source = source_dir(root, slug)
    return {
        "slug": slug,
        "title": args.title,
        "apple_url": args.apple_url,
        "source_url": getattr(args, "url", "") or str(getattr(args, "source", "")),
        "frameworks": args.frameworks or [],
        "notes": args.notes or "",
        "fetched_at": utc_now(),
        "cache_path": str(sample_dir(root, slug)),
        "size_bytes": path_size(source),
    }


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
    root = cache_root(args)
    slug = slugify(args.slug or args.title)
    destination = source_dir(root, slug)
    ensure_replace_ok(sample_dir(root, slug), args.replace)
    source = Path(args.source).expanduser().resolve()
    if not source.exists():
        raise SystemExit(f"Source does not exist: {source}")
    copy_source(source, destination)
    metadata = metadata_from_args(args, root, slug)
    manifest = load_manifest(root)
    manifest.setdefault("samples", {})[slug] = metadata
    save_manifest(root, manifest)
    save_sample_metadata(root, slug, metadata)
    print(f"Cached {slug} at {sample_dir(root, slug)}")
    return 0


def cmd_fetch_archive(args: argparse.Namespace) -> int:
    root = cache_root(args)
    slug = slugify(args.slug or args.title)
    destination = source_dir(root, slug)
    ensure_replace_ok(sample_dir(root, slug), args.replace)
    downloaded = download_to_temp(args.url)
    try:
        copy_source(downloaded, destination)
    finally:
        if downloaded.exists() and downloaded.parent == Path(tempfile.gettempdir()):
            downloaded.unlink(missing_ok=True)
    metadata = metadata_from_args(args, root, slug)
    manifest = load_manifest(root)
    manifest.setdefault("samples", {})[slug] = metadata
    save_manifest(root, manifest)
    save_sample_metadata(root, slug, metadata)
    print(f"Fetched {slug} at {sample_dir(root, slug)}")
    return 0


def tree_lines(path: Path, max_depth: int, prefix: str = "") -> list[str]:
    if max_depth < 0 or not path.exists():
        return []
    entries = sorted(path.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
    lines: list[str] = []
    for entry in entries[:80]:
        marker = "/" if entry.is_dir() else ""
        lines.append(f"{prefix}{entry.name}{marker}")
        if entry.is_dir():
            lines.extend(tree_lines(entry, max_depth - 1, prefix + "  "))
    if len(entries) > 80:
        lines.append(f"{prefix}... {len(entries) - 80} more")
    return lines


def cmd_inspect(args: argparse.Namespace) -> int:
    root = cache_root(args)
    slug = slugify(args.slug)
    manifest = load_manifest(root)
    item = manifest.get("samples", {}).get(slug)
    if not item:
        raise SystemExit(f"Sample not found: {slug}")
    print(json.dumps(item, indent=2, sort_keys=True))
    print("\nsource tree:")
    source = source_dir(root, slug)
    for line in tree_lines(source, args.max_depth):
        print(line)
    return 0


def parse_time(value: str) -> dt.datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = dt.datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt.UTC)
    return parsed.astimezone(dt.UTC)


def stale_samples(root: Path, max_age_days: int) -> list[tuple[str, dict, int]]:
    manifest = load_manifest(root)
    now = dt.datetime.now(dt.UTC)
    stale: list[tuple[str, dict, int]] = []
    for slug, item in manifest.get("samples", {}).items():
        fetched = parse_time(item.get("fetched_at", ""))
        age = 999999 if fetched is None else (now - fetched).days
        if age >= max_age_days:
            stale.append((slug, item, age))
    return stale


def cmd_refresh_plan(args: argparse.Namespace) -> int:
    root = cache_root(args)
    stale = stale_samples(root, args.max_age_days)
    if not stale:
        print(f"No samples older than {args.max_age_days} days in {root}")
        return 0
    for slug, item, age in stale:
        print(f"{slug}\t{age} days\t{item.get('apple_url', '')}")
    return 0


def cmd_prune(args: argparse.Namespace) -> int:
    root = cache_root(args)
    stale = stale_samples(root, args.max_age_days)
    if not stale:
        print(f"No prune candidates older than {args.max_age_days} days in {root}")
        return 0
    manifest = load_manifest(root)
    for slug, item, age in stale:
        target = sample_dir(root, slug)
        action = "delete" if args.apply else "dry-run"
        print(f"{action}\t{slug}\t{age} days\t{target}")
        if args.apply:
            shutil.rmtree(target, ignore_errors=True)
            manifest.get("samples", {}).pop(slug, None)
    if args.apply:
        save_manifest(root, manifest)
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


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
