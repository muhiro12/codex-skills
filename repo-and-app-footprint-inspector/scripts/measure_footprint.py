#!/usr/bin/env python3
"""Measure repository and app codebase footprint without changing source files."""

from __future__ import annotations

import argparse
import heapq
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

DEFAULT_EXCLUDED_DIR_NAMES = {
    ".build",
    ".cache",
    ".git",
    ".gradle",
    ".next",
    ".swiftpm",
    ".venv",
    "__pycache__",
    "Build",
    "Carthage",
    "DerivedData",
    "Pods",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "venv",
}

DISCOVERY_EXCLUDED_DIR_NAMES = DEFAULT_EXCLUDED_DIR_NAMES | {
    ".github",
    ".idea",
    ".vscode",
    "assets",
    "docs",
    "examples",
    "references",
    "samples",
    "scripts",
    "test",
    "tests",
    "tools",
}

SOURCE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".dart",
    ".go",
    ".h",
    ".hpp",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".kts",
    ".m",
    ".mm",
    ".py",
    ".rb",
    ".rs",
    ".swift",
    ".ts",
    ".tsx",
}

RESOURCE_EXTENSIONS = {
    ".aac",
    ".gif",
    ".heic",
    ".ico",
    ".jpeg",
    ".jpg",
    ".json",
    ".mp3",
    ".mp4",
    ".pdf",
    ".png",
    ".svg",
    ".ttf",
    ".wav",
    ".webp",
    ".woff",
    ".woff2",
    ".xcstrings",
}

LOCALIZATION_EXTENSIONS = {
    ".arb",
    ".po",
    ".pot",
    ".strings",
    ".stringsdict",
    ".xcstrings",
}

CONFIG_EXTENSIONS = {
    ".cfg",
    ".entitlements",
    ".gradle",
    ".pbxproj",
    ".plist",
    ".toml",
    ".xcconfig",
    ".xcworkspace",
    ".xml",
    ".yaml",
    ".yml",
}

CONFIG_FILE_NAMES = {
    "AndroidManifest.xml",
    "Cartfile",
    "Gemfile",
    "Info.plist",
    "Package.resolved",
    "Package.swift",
    "Podfile",
    "Podfile.lock",
    "app.json",
    "app.config.js",
    "app.config.ts",
    "build.gradle",
    "build.gradle.kts",
    "package-lock.json",
    "package.json",
    "pnpm-lock.yaml",
    "pubspec.lock",
    "pubspec.yaml",
    "settings.gradle",
    "settings.gradle.kts",
    "turbo.json",
    "yarn.lock",
}

APP_DISCOVERY_FILE_NAMES = {
    "AndroidManifest.xml",
    "App.swift",
    "App.tsx",
    "App.jsx",
    "AppDelegate.swift",
    "Info.plist",
    "MainActivity.java",
    "MainActivity.kt",
    "SceneDelegate.swift",
    "app.json",
    "main.dart",
}

APP_DISCOVERY_DIR_NAMES = {
    "Assets.xcassets",
    "Preview Content",
    "Resources",
    "fastlane",
    "res",
}

C_STYLE_SOURCE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".dart",
    ".go",
    ".h",
    ".hpp",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".kts",
    ".m",
    ".mm",
    ".rs",
    ".swift",
    ".ts",
    ".tsx",
}

HASH_STYLE_SOURCE_EXTENSIONS = {
    ".py",
    ".rb",
}

SCALE_BANDS = [
    {
        "label": "Tiny",
        "min_lines": 0,
        "max_lines": 5000,
        "market_note": "prototype or very focused utility app",
    },
    {
        "label": "Small",
        "min_lines": 5000,
        "max_lines": 20000,
        "market_note": "small shipped app with a limited feature set",
    },
    {
        "label": "Medium",
        "min_lines": 20000,
        "max_lines": 60000,
        "market_note": "mid-size consumer app",
    },
    {
        "label": "Large",
        "min_lines": 60000,
        "max_lines": 150000,
        "market_note": "mature multi-surface product",
    },
    {
        "label": "Very Large",
        "min_lines": 150000,
        "max_lines": 300000,
        "market_note": "large product suite with substantial shared code",
    },
    {
        "label": "Platform-Scale",
        "min_lines": 300000,
        "max_lines": None,
        "market_note": "platform-scale app family",
    },
]

QUALITY_BANDS = [
    {"label": "Early", "min_score": 0, "max_score": 25, "note": "basic implementation signals only"},
    {"label": "Basic", "min_score": 25, "max_score": 45, "note": "usable engineering baseline"},
    {"label": "Solid", "min_score": 45, "max_score": 65, "note": "clear quality investment"},
    {"label": "Strong", "min_score": 65, "max_score": 85, "note": "well-supported and disciplined"},
    {"label": "Mature", "min_score": 85, "max_score": None, "note": "broad quality signals across the repo"},
]

VALUE_BANDS = [
    {"label": "Narrow", "min_score": 0, "max_score": 25, "note": "focused single-purpose product"},
    {"label": "Focused", "min_score": 25, "max_score": 45, "note": "clear use case with some supporting depth"},
    {"label": "Useful", "min_score": 45, "max_score": 65, "note": "meaningful breadth for everyday use"},
    {"label": "Distinct", "min_score": 65, "max_score": 85, "note": "noticeable breadth or differentiation"},
    {"label": "Suite-like", "min_score": 85, "max_score": None, "note": "broad multi-surface product value"},
]

FEATURE_ROOT_NAMES = {"Sources", "Features"}
IGNORED_FEATURE_AREA_NAMES = {
    "App",
    "Common",
    "Components",
    "Configuration",
    "Configurations",
    "Core",
    "Debug",
    "Models",
    "Patterns",
    "Resources",
    "Services",
    "Shared",
    "Support",
    "Theme",
    "UI",
    "Utilities",
    "Utils",
}

TECH_MODULE_LABELS = {
    "ActivityKit": "ActivityKit",
    "AppIntents": "AppIntents",
    "Charts": "Swift Charts",
    "CloudKit": "CloudKit",
    "Combine": "Combine",
    "CoreSpotlight": "CoreSpotlight",
    "Intents": "Intents",
    "MapKit": "MapKit",
    "Observation": "Observation",
    "RealmSwift": "Realm",
    "StoreKit": "StoreKit",
    "SwiftData": "SwiftData",
    "SwiftUI": "SwiftUI",
    "TipKit": "TipKit",
    "UserNotifications": "UserNotifications",
    "VisionKit": "VisionKit",
    "WatchConnectivity": "WatchConnectivity",
    "WidgetKit": "WidgetKit",
}


def humanize_bytes(value: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{value} B"


def classify_extension(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix:
        return suffix
    if path.name.startswith("."):
        return "[dotfile]"
    return "[no extension]"


def top_level_entry_name(relative_path: Path) -> str:
    if len(relative_path.parts) == 1:
        return "[root]"
    return relative_path.parts[0]


def push_largest(heap: list[tuple[int, str]], size: int, path: str, limit: int) -> None:
    item = (size, path)
    if len(heap) < limit:
        heapq.heappush(heap, item)
        return
    if size > heap[0][0]:
        heapq.heapreplace(heap, item)


def sorted_size_map(items: dict[str, int], limit: int | None = None) -> list[dict[str, object]]:
    pairs = sorted(items.items(), key=lambda item: (-item[1], item[0]))
    if limit is not None:
        pairs = pairs[:limit]
    return [{"name": name, "bytes": size} for name, size in pairs]


def sorted_line_map(items: dict[str, int], limit: int | None = None) -> list[dict[str, object]]:
    pairs = sorted(items.items(), key=lambda item: (-item[1], item[0]))
    if limit is not None:
        pairs = pairs[:limit]
    return [{"name": name, "lines": line_count} for name, line_count in pairs]


def display_path(path: Path, root: Path | None = None) -> str:
    if root is not None:
        try:
            return str(path.relative_to(root))
        except ValueError:
            pass
    return str(path.resolve())


def scoped_entry_name(scope_label: str, entry_name: str) -> str:
    if entry_name == "[root]":
        return scope_label
    return f"{scope_label}/{entry_name}"


def is_test_path(relative_path: Path) -> bool:
    for part in relative_path.parts:
        lowered = part.lower()
        if lowered in {"test", "tests", "testing", "__tests__"}:
            return True
        if lowered.endswith("tests"):
            return True
    stem = relative_path.stem.lower()
    return stem.endswith("test") or stem.endswith("tests")


def classify_role(relative_path: Path) -> str:
    if is_test_path(relative_path):
        return "Tests"

    suffix = relative_path.suffix.lower()
    name = relative_path.name
    lowered_parts = {part.lower() for part in relative_path.parts}

    if suffix in LOCALIZATION_EXTENSIONS or ".lproj" in lowered_parts:
        return "Localization"
    if suffix in SOURCE_EXTENSIONS:
        return "Source"
    if name in CONFIG_FILE_NAMES or suffix in CONFIG_EXTENSIONS:
        return "Config"
    if (
        suffix in RESOURCE_EXTENSIONS
        or "resources" in lowered_parts
        or "res" in lowered_parts
        or "assets.xcassets" in lowered_parts
        or "preview content" in lowered_parts
    ):
        return "Resources"
    return "Other"


def strip_c_style_comments(line: str, in_block_comment: bool) -> tuple[str, bool]:
    output = []
    index = 0
    while index < len(line):
        if in_block_comment:
            end_index = line.find("*/", index)
            if end_index == -1:
                return "".join(output), True
            index = end_index + 2
            in_block_comment = False
            continue

        if line.startswith("//", index):
            break
        if line.startswith("/*", index):
            in_block_comment = True
            index += 2
            continue

        output.append(line[index])
        index += 1

    return "".join(output), in_block_comment


def count_meaningful_source_lines(file_path: Path) -> int:
    suffix = file_path.suffix.lower()
    if suffix not in SOURCE_EXTENSIONS:
        return 0

    meaningful_lines = 0
    in_block_comment = False

    try:
        with file_path.open("r", encoding="utf-8", errors="ignore") as handle:
            for raw_line in handle:
                line = raw_line.rstrip("\n")
                if suffix in C_STYLE_SOURCE_EXTENSIONS:
                    line, in_block_comment = strip_c_style_comments(line, in_block_comment)
                    if line.strip():
                        meaningful_lines += 1
                    continue

                if suffix in HASH_STYLE_SOURCE_EXTENSIONS:
                    stripped = line.strip()
                    if not stripped or stripped.startswith("#"):
                        continue
                    code_part = line.split("#", 1)[0]
                    if code_part.strip():
                        meaningful_lines += 1
                    continue

                if line.strip():
                    meaningful_lines += 1
    except OSError:
        return 0

    return meaningful_lines


def parse_source_imports(file_path: Path) -> set[str]:
    suffix = file_path.suffix.lower()
    if suffix not in SOURCE_EXTENSIONS:
        return set()

    imports: set[str] = set()
    try:
        with file_path.open("r", encoding="utf-8", errors="ignore") as handle:
            for raw_line in handle:
                stripped = raw_line.strip()
                if not stripped.startswith("import ") and not stripped.startswith("@testable import "):
                    continue
                parts = stripped.replace("@testable ", "", 1).split()
                if len(parts) >= 2:
                    imports.add(parts[1])
    except OSError:
        return set()
    return imports


def benchmark_for_meaningful_loc(lines: int) -> dict[str, object]:
    for band in SCALE_BANDS:
        max_lines = band["max_lines"]
        if max_lines is None or lines < max_lines:
            return {
                "label": band["label"],
                "range": f"{band['min_lines']:,}+" if max_lines is None else f"{band['min_lines']:,}-{max_lines - 1:,}",
                "market_note": band["market_note"],
            }
    return {
        "label": "Unknown",
        "range": "-",
        "market_note": "comparison unavailable",
    }


def benchmark_for_score(score: int, bands: list[dict[str, object]]) -> dict[str, object]:
    for band in bands:
        max_score = band["max_score"]
        if max_score is None or score < max_score:
            return {
                "label": band["label"],
                "range": f"{band['min_score']}+" if max_score is None else f"{band['min_score']}-{max_score - 1}",
                "note": band["note"],
            }
    return {"label": "Unknown", "range": "-", "note": "comparison unavailable"}


def collect_feature_area(relative_path: Path) -> str | None:
    parts = relative_path.parts
    if len(parts) < 2:
        return None
    if parts[0] not in FEATURE_ROOT_NAMES:
        return None
    candidate = parts[1]
    if Path(candidate).suffix.lower() in SOURCE_EXTENSIONS:
        return None
    if candidate in IGNORED_FEATURE_AREA_NAMES:
        return None
    return candidate


def infer_surface_kind(app_path: Path) -> str:
    lowered = app_path.name.lower()
    if lowered == "tests":
        return "tests"
    if lowered.endswith("library") or lowered == "sources":
        return "library"
    if "widget" in lowered:
        return "widget"
    if "watch" in lowered:
        return "watch"
    return "app"


def collect_repo_relative_paths(repo_path: Path, tracked_paths: list[Path] | None) -> list[Path]:
    if tracked_paths is not None:
        return [path.relative_to(repo_path) for path in tracked_paths if path.is_file()]

    collected: list[Path] = []
    for current_root, dirs, files in os.walk(repo_path, topdown=True):
        current_root_path = Path(current_root)
        filtered_dirs = []
        for directory in dirs:
            if directory in DEFAULT_EXCLUDED_DIR_NAMES:
                continue
            candidate = current_root_path / directory
            if candidate.is_symlink():
                continue
            filtered_dirs.append(directory)
        dirs[:] = filtered_dirs

        for file_name in files:
            file_path = current_root_path / file_name
            if file_path.is_symlink() or not file_path.is_file():
                continue
            collected.append(file_path.relative_to(repo_path))
    return collected


def analyze_scope_signals(
    repo_relative_paths: list[Path],
    apps: list[dict[str, object]],
) -> dict[str, object]:
    lowered_strings = [str(path).lower() for path in repo_relative_paths]
    top_level_names = {path.parts[0] for path in repo_relative_paths if path.parts}
    localization_count = sum(1 for path in repo_relative_paths if path.suffix.lower() in LOCALIZATION_EXTENSIONS)
    feature_areas = sorted({area for app in apps for area in app.get("feature_areas", [])})
    surface_kinds = [app.get("surface_kind") for app in apps if app.get("surface_kind") in {"app", "widget", "watch"}]
    has_ci = any(
        (path.parts and path.parts[0] == ".github" and "workflows" in path.parts)
        or (path.parts and path.parts[0] == "ci_scripts")
        for path in repo_relative_paths
    )
    has_docs = any(name in top_level_names for name in {"Designs", "docs"})
    has_shared_library = any(label.lower().endswith("library") for label in (app["label"] for app in apps)) or any(
        name.endswith("Library") for name in top_level_names
    )
    has_app_intents = any("appintent" in value or "shortcut" in value for value in lowered_strings)
    has_notifications = any("notification" in value for value in lowered_strings)
    has_search = any("/search/" in value or value.endswith("/search") for value in lowered_strings)
    has_deep_links = any("deeplink" in value or "route" in value for value in lowered_strings)
    technologies = sorted({tech for app in apps for tech in app.get("technologies", [])})
    if any(path.name == "Package.swift" for path in repo_relative_paths):
        technologies.append("Swift Package Manager")
    if any(path.suffix == ".xcodeproj" for path in repo_relative_paths):
        technologies.append("Xcode project")
    if has_ci:
        technologies.append("GitHub Actions / CI scripts")
    if any(label.lower().endswith("library") for label in (app["label"] for app in apps)):
        technologies.append("Shared domain package")
    technologies = sorted(set(technologies))

    return {
        "feature_area_count": len(feature_areas),
        "feature_areas": feature_areas,
        "surface_count": len(surface_kinds),
        "surface_kinds": sorted(set(surface_kinds)),
        "has_ci": has_ci,
        "has_docs": has_docs,
        "has_shared_library": has_shared_library,
        "has_localization": localization_count > 0,
        "localization_count": localization_count,
        "has_app_intents": has_app_intents,
        "has_notifications": has_notifications,
        "has_search": has_search,
        "has_deep_links": has_deep_links,
        "technologies": technologies,
    }


def summarize_quality_and_value(
    selected_summary: dict[str, object] | None,
    signals: dict[str, object],
) -> dict[str, object] | None:
    if not selected_summary:
        return None

    production_loc = int(selected_summary["meaningful_source_lines"])
    test_loc = int(selected_summary["meaningful_test_lines"])
    source_files = int(selected_summary["source_file_count"])
    test_files = int(selected_summary["test_source_file_count"])
    feature_area_count = int(signals["feature_area_count"])
    surface_count = int(signals["surface_count"])
    test_ratio = test_loc / max(production_loc, 1)
    technologies = list(signals["technologies"])
    advanced_tech_count = sum(
        1
        for tech in technologies
        if tech in {
            "AppIntents",
            "Swift Charts",
            "SwiftData",
            "StoreKit",
            "TipKit",
            "WatchConnectivity",
            "WidgetKit",
        }
    )

    quality_score = 0
    quality_reasons: list[str] = []
    if source_files >= 40:
        quality_score += 5
    if test_loc > 0:
        quality_score += 10
        quality_reasons.append("automated tests are present")
    if test_ratio >= 0.3:
        quality_score += 10
        quality_reasons.append(f"test LOC ratio is high ({test_ratio:.2f}x)")
    elif test_ratio >= 0.1:
        quality_score += 6
        quality_reasons.append(f"test LOC ratio is healthy ({test_ratio:.2f}x)")
    elif test_ratio >= 0.03:
        quality_score += 2
    if test_files >= 10:
        quality_score += 3
    if signals["has_ci"]:
        quality_score += 8
        quality_reasons.append("CI automation is configured")
    if signals["has_docs"]:
        quality_score += 6
        quality_reasons.append("design or architecture docs exist")
    if signals["has_shared_library"]:
        quality_score += 7
        quality_reasons.append("shared library extraction suggests modularization")
    if signals["has_localization"]:
        quality_score += 4
        quality_reasons.append("localization support is present")
    if surface_count >= 3:
        quality_score += 7
    elif surface_count >= 2:
        quality_score += 4
    if feature_area_count >= 8:
        quality_score += 8
        quality_reasons.append(f"{feature_area_count} feature areas suggest breadth with structure")
    elif feature_area_count >= 4:
        quality_score += 4
    integration_count = sum(
        1
        for key in ["has_app_intents", "has_notifications", "has_search", "has_deep_links"]
        if signals[key]
    )
    if integration_count >= 3:
        quality_score += 8
    elif integration_count >= 2:
        quality_score += 5
    elif integration_count == 1:
        quality_score += 2
    if advanced_tech_count >= 5:
        quality_score += 10
        quality_reasons.append(f"advanced Apple-stack technologies are used ({advanced_tech_count})")
    elif advanced_tech_count >= 3:
        quality_score += 6
        quality_reasons.append(f"multiple advanced Apple-stack technologies are used ({advanced_tech_count})")
    elif advanced_tech_count >= 2:
        quality_score += 3

    quality_score = min(quality_score, 100)
    quality_band = benchmark_for_score(quality_score, QUALITY_BANDS)

    value_score = 0
    value_reasons: list[str] = []
    if production_loc >= 10000:
        value_score += 15
        value_reasons.append("production LOC indicates substantial software depth")
    elif production_loc >= 5000:
        value_score += 10
        value_reasons.append("production LOC indicates meaningful product depth")
    elif production_loc >= 1500:
        value_score += 5
    if feature_area_count >= 10:
        value_score += 20
        value_reasons.append(f"{feature_area_count} feature areas suggest broad utility")
    elif feature_area_count >= 6:
        value_score += 15
        value_reasons.append(f"{feature_area_count} feature areas suggest clear breadth")
    elif feature_area_count >= 3:
        value_score += 10
        value_reasons.append(f"{feature_area_count} feature areas support a focused product")
    if surface_count >= 4:
        value_score += 20
        value_reasons.append(f"{surface_count} product surfaces increase reach")
    elif surface_count >= 3:
        value_score += 15
        value_reasons.append(f"{surface_count} product surfaces increase reach")
    elif surface_count >= 2:
        value_score += 10
        value_reasons.append(f"{surface_count} product surfaces expand usage contexts")
    if signals["has_shared_library"]:
        value_score += 10
        value_reasons.append("shared logic suggests durable domain investment")
    if signals["has_localization"]:
        value_score += 5
        value_reasons.append("localization expands audience potential")
    if signals["has_app_intents"]:
        value_score += 8
        value_reasons.append("App Intents / shortcuts increase OS-level utility")
    if signals["has_notifications"]:
        value_score += 5
    if signals["has_search"]:
        value_score += 5
    if signals["has_deep_links"]:
        value_score += 5

    value_score = min(value_score, 100)
    value_band = benchmark_for_score(value_score, VALUE_BANDS)

    return {
        "quality": {
            "score": quality_score,
            "band": quality_band,
            "reasons": quality_reasons[:5],
        },
        "value": {
            "score": value_score,
            "band": value_band,
            "reasons": value_reasons[:5],
        },
        "signals": signals,
    }


def analyze_walk(root: Path, excluded_dir_names: set[str], largest_limit: int) -> dict[str, object]:
    total_bytes = 0
    total_files = 0
    top_level_bytes: dict[str, int] = defaultdict(int)
    extension_bytes: dict[str, int] = defaultdict(int)
    largest_files: list[tuple[int, str]] = []

    for current_root, dirs, files in os.walk(root, topdown=True):
        current_root_path = Path(current_root)
        filtered_dirs = []
        for directory in dirs:
            if directory in excluded_dir_names:
                continue
            candidate = current_root_path / directory
            if candidate.is_symlink():
                continue
            filtered_dirs.append(directory)
        dirs[:] = filtered_dirs

        for file_name in files:
            file_path = current_root_path / file_name
            if file_path.is_symlink():
                continue
            try:
                if not file_path.is_file():
                    continue
                size = file_path.stat().st_size
            except OSError:
                continue

            relative_path = file_path.relative_to(root)
            total_bytes += size
            total_files += 1
            top_level_bytes[top_level_entry_name(relative_path)] += size
            extension_bytes[classify_extension(file_path)] += size
            push_largest(largest_files, size, str(relative_path), largest_limit)

    return {
        "bytes": total_bytes,
        "files": total_files,
        "top_level": sorted_size_map(top_level_bytes),
        "extensions": sorted_size_map(extension_bytes),
        "largest_files": [
            {"path": path, "bytes": size}
            for size, path in sorted(largest_files, key=lambda item: (-item[0], item[1]))
        ],
    }


def list_git_tracked_files(repo_path: Path) -> tuple[Path | None, list[Path] | None, str | None]:
    try:
        top_level_proc = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        )
        git_root = Path(top_level_proc.stdout.strip()).resolve()
        tracked_proc = subprocess.run(
            ["git", "-C", str(repo_path), "ls-files", "-z"],
            check=True,
            capture_output=True,
        )
    except FileNotFoundError:
        return None, None, "git command not found"
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode(
            "utf-8",
            errors="replace",
        )
        stderr = stderr.strip()
        if "not a git repository" in stderr.lower():
            return None, None, "path is not inside a Git repository"
        return None, None, stderr or "Git metadata is unavailable"

    repo_root = repo_path.resolve()
    tracked_paths: list[Path] = []
    for entry in tracked_proc.stdout.split(b"\0"):
        if not entry:
            continue
        absolute_path = (git_root / entry.decode("utf-8", errors="surrogateescape")).resolve()
        try:
            absolute_path.relative_to(repo_root)
        except ValueError:
            continue
        tracked_paths.append(absolute_path)
    return git_root, tracked_paths, None


def analyze_paths(root: Path, paths: Iterable[Path], largest_limit: int) -> dict[str, object]:
    total_bytes = 0
    total_files = 0
    top_level_bytes: dict[str, int] = defaultdict(int)
    extension_bytes: dict[str, int] = defaultdict(int)
    largest_files: list[tuple[int, str]] = []

    for file_path in paths:
        try:
            if file_path.is_symlink() or not file_path.is_file():
                continue
            size = file_path.stat().st_size
            relative_path = file_path.relative_to(root)
        except (OSError, ValueError):
            continue

        total_bytes += size
        total_files += 1
        top_level_bytes[top_level_entry_name(relative_path)] += size
        extension_bytes[classify_extension(file_path)] += size
        push_largest(largest_files, size, str(relative_path), largest_limit)

    return {
        "bytes": total_bytes,
        "files": total_files,
        "top_level": sorted_size_map(top_level_bytes),
        "extensions": sorted_size_map(extension_bytes),
        "largest_files": [
            {"path": path, "bytes": size}
            for size, path in sorted(largest_files, key=lambda item: (-item[0], item[1]))
        ],
    }


def filter_paths_within(root: Path, paths: Iterable[Path]) -> list[Path]:
    resolved_root = root.resolve()
    filtered_paths: list[Path] = []
    for path in paths:
        try:
            path.relative_to(resolved_root)
        except ValueError:
            continue
        filtered_paths.append(path)
    return filtered_paths


def summarize_repo(
    repo_path: Path,
    largest_limit: int,
    git_root: Path | None,
    tracked_paths: list[Path] | None,
    git_error: str | None,
    include_storage_footprint: bool,
) -> dict[str, object]:
    tracked = None
    if tracked_paths is not None:
        tracked = analyze_paths(repo_path.resolve(), tracked_paths, largest_limit=largest_limit)

    filtered = None
    if tracked is None or include_storage_footprint:
        filtered = analyze_walk(
            repo_path,
            excluded_dir_names=DEFAULT_EXCLUDED_DIR_NAMES,
            largest_limit=largest_limit,
        )

    raw = None
    excluded_bytes = None
    if include_storage_footprint:
        raw = analyze_walk(repo_path, excluded_dir_names=set(), largest_limit=largest_limit)
        if filtered is None:
            filtered = analyze_walk(
                repo_path,
                excluded_dir_names=DEFAULT_EXCLUDED_DIR_NAMES,
                largest_limit=largest_limit,
            )
        excluded_bytes = max(raw["bytes"] - filtered["bytes"], 0)

    primary = tracked or filtered
    audit_scope = "git-tracked" if tracked is not None else "working-tree"
    audit_scope_label = "Git tracked files" if tracked is not None else "Working tree fallback"

    return {
        "path": str(repo_path.resolve()),
        "audit_scope": audit_scope,
        "audit_scope_label": audit_scope_label,
        "primary": primary,
        "raw": raw,
        "filtered": filtered,
        "tracked": tracked,
        "git_root": str(git_root) if git_root else None,
        "git_error": git_error,
        "storage_footprint_included": include_storage_footprint,
        "excluded_dir_names": sorted(DEFAULT_EXCLUDED_DIR_NAMES),
        "excluded_bytes": excluded_bytes,
    }


def iter_app_file_paths(app_path: Path, tracked_paths: list[Path] | None) -> Iterable[Path]:
    if tracked_paths is not None:
        yield from filter_paths_within(app_path, tracked_paths)
        return

    for current_root, dirs, files in os.walk(app_path, topdown=True):
        current_root_path = Path(current_root)
        filtered_dirs = []
        for directory in dirs:
            if directory in DEFAULT_EXCLUDED_DIR_NAMES:
                continue
            candidate = current_root_path / directory
            if candidate.is_symlink():
                continue
            filtered_dirs.append(directory)
        dirs[:] = filtered_dirs

        for file_name in files:
            file_path = current_root_path / file_name
            if file_path.is_symlink():
                continue
            if file_path.is_file():
                yield file_path


def analyze_app_path(
    app_path: Path,
    repo_path: Path,
    largest_limit: int,
    tracked_paths: list[Path] | None,
    audit_scope_label: str,
) -> dict[str, object]:
    result = analyze_code_scope(
        scope_path=app_path,
        repo_path=repo_path,
        largest_limit=largest_limit,
        tracked_paths=tracked_paths,
        audit_scope_label=audit_scope_label,
        label=display_path(app_path, repo_path),
    )
    result["surface_kind"] = infer_surface_kind(app_path)
    return result


def analyze_code_scope(
    scope_path: Path,
    repo_path: Path,
    largest_limit: int,
    tracked_paths: list[Path] | None,
    audit_scope_label: str,
    label: str,
) -> dict[str, object]:
    total_bytes = 0
    total_files = 0
    top_level_bytes: dict[str, int] = defaultdict(int)
    extension_bytes: dict[str, int] = defaultdict(int)
    role_bytes: dict[str, int] = defaultdict(int)
    largest_files: list[tuple[int, str]] = []
    top_level_source_lines: dict[str, int] = defaultdict(int)
    largest_source_files: list[tuple[int, str]] = []
    meaningful_source_lines = 0
    meaningful_test_lines = 0
    source_file_count = 0
    test_source_file_count = 0
    feature_areas: set[str] = set()
    imported_modules: set[str] = set()

    for file_path in iter_app_file_paths(scope_path, tracked_paths):
        try:
            if file_path.is_symlink() or not file_path.is_file():
                continue
            size = file_path.stat().st_size
            relative_path = file_path.relative_to(scope_path)
        except OSError:
            continue

        total_bytes += size
        total_files += 1
        top_level_name = top_level_entry_name(relative_path)
        top_level_bytes[top_level_name] += size
        extension_bytes[classify_extension(file_path)] += size
        role = classify_role(relative_path)
        role_bytes[role] += size
        push_largest(largest_files, size, display_path(file_path, repo_path), largest_limit)
        feature_area = collect_feature_area(relative_path)
        if feature_area is not None:
            feature_areas.add(feature_area)
        imported_modules.update(parse_source_imports(file_path))

        meaningful_lines = count_meaningful_source_lines(file_path)
        if meaningful_lines > 0:
            if role == "Tests":
                meaningful_test_lines += meaningful_lines
                test_source_file_count += 1
            else:
                meaningful_source_lines += meaningful_lines
                source_file_count += 1
                top_level_source_lines[top_level_name] += meaningful_lines
                push_largest(
                    largest_source_files,
                    meaningful_lines,
                    display_path(file_path, repo_path),
                    largest_limit,
                )

    benchmark = benchmark_for_meaningful_loc(meaningful_source_lines)
    return {
        "path": str(scope_path.resolve()),
        "label": label,
        "audit_scope_label": audit_scope_label,
        "bytes": total_bytes,
        "files": total_files,
        "top_level": sorted_size_map(top_level_bytes),
        "top_level_meaningful_source_lines": sorted_line_map(top_level_source_lines),
        "extensions": sorted_size_map(extension_bytes),
        "roles": sorted_size_map(role_bytes),
        "largest_files": [
            {"path": path, "bytes": size}
            for size, path in sorted(largest_files, key=lambda item: (-item[0], item[1]))
        ],
        "largest_source_files": [
            {"path": path, "lines": lines}
            for lines, path in sorted(largest_source_files, key=lambda item: (-item[0], item[1]))
        ],
        "meaningful_source_lines": meaningful_source_lines,
        "meaningful_test_lines": meaningful_test_lines,
        "source_file_count": source_file_count,
        "test_source_file_count": test_source_file_count,
        "benchmark": benchmark,
        "feature_areas": sorted(feature_areas),
        "technologies": sorted(
            TECH_MODULE_LABELS[module]
            for module in imported_modules
            if module in TECH_MODULE_LABELS
        ),
    }


def analyze_repository_code_profile(
    repo_path: Path,
    largest_limit: int,
    tracked_paths: list[Path] | None,
    audit_scope_label: str,
) -> dict[str, object]:
    result = analyze_code_scope(
        scope_path=repo_path,
        repo_path=repo_path,
        largest_limit=largest_limit,
        tracked_paths=tracked_paths,
        audit_scope_label=audit_scope_label,
        label=repo_path.name or str(repo_path),
    )
    result["surface_kind"] = "repository"
    return result


def detect_app_candidate(path: Path, repo_path: Path) -> dict[str, object] | None:
    if not path.is_dir() or path.name in DISCOVERY_EXCLUDED_DIR_NAMES or path.name.startswith("."):
        return None

    lowered_name = path.name.lower()
    score = 0
    reasons: list[str] = []
    source_file_count = 0
    saw_marker = False
    saw_resources = False
    saw_config = False
    saw_name_hint = False

    if any(token in lowered_name for token in {"app", "ios", "android", "watch", "mobile", "client"}):
        score += 1
        saw_name_hint = True
        reasons.append("directory name looks app-oriented")

    for current_root, dirs, files in os.walk(path, topdown=True):
        current_root_path = Path(current_root)
        try:
            relative_root = current_root_path.relative_to(path)
        except ValueError:
            continue
        if len(relative_root.parts) > 2:
            dirs[:] = []
            continue

        filtered_dirs = []
        for directory in dirs:
            if directory in DISCOVERY_EXCLUDED_DIR_NAMES:
                continue
            candidate = current_root_path / directory
            if candidate.is_symlink():
                continue
            filtered_dirs.append(directory)
            if directory in APP_DISCOVERY_DIR_NAMES and not saw_resources:
                score += 1
                saw_resources = True
                reasons.append(f"contains `{directory}`")
        dirs[:] = filtered_dirs

        for file_name in files:
            file_path = current_root_path / file_name
            suffix = file_path.suffix.lower()
            if file_name in APP_DISCOVERY_FILE_NAMES and not saw_marker:
                score += 3
                saw_marker = True
                reasons.append(f"contains `{file_name}`")
            elif suffix == ".entitlements" and not saw_marker:
                score += 3
                saw_marker = True
                reasons.append("contains app entitlement metadata")
            elif suffix in {".storyboard", ".xib"} and not saw_resources:
                score += 1
                saw_resources = True
                reasons.append("contains app UI resources")

            if file_name in CONFIG_FILE_NAMES or suffix in CONFIG_EXTENSIONS:
                saw_config = True
            if suffix in SOURCE_EXTENSIONS:
                source_file_count += 1

    if source_file_count >= 10:
        score += 1
        reasons.append("contains substantial source files")
    elif source_file_count >= 3 and saw_marker:
        score += 1
        reasons.append("contains app entry markers plus source files")

    if saw_config and not saw_name_hint and not saw_marker and source_file_count < 3:
        return None

    if score < 3:
        return None

    return {
        "path": str(path.resolve()),
        "label": display_path(path, repo_path),
        "score": score,
        "reasons": reasons[:3],
    }


def discover_app_paths(repo_path: Path) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    seen: set[Path] = set()
    for depth in range(2):
        roots = [repo_path] if depth == 0 else [child for child in repo_path.iterdir() if child.is_dir()]
        for root in roots:
            if root in seen:
                continue
            seen.add(root)
            try:
                children = sorted(
                    child
                    for child in root.iterdir()
                    if child.is_dir() and child.name not in DISCOVERY_EXCLUDED_DIR_NAMES and not child.name.startswith(".")
                )
            except OSError:
                continue
            for child in children:
                candidate = detect_app_candidate(child, repo_path)
                if candidate is not None:
                    candidates.append(candidate)

    deduped: dict[str, dict[str, object]] = {}
    for candidate in candidates:
        deduped[candidate["path"]] = candidate

    return sorted(deduped.values(), key=lambda item: (-int(item["score"]), str(item["label"])))


def summarize_selected_apps(apps: list[dict[str, object]]) -> dict[str, object] | None:
    if not apps:
        return None

    meaningful_source_lines = sum(int(app["meaningful_source_lines"]) for app in apps)
    meaningful_test_lines = sum(int(app["meaningful_test_lines"]) for app in apps)
    source_file_count = sum(int(app["source_file_count"]) for app in apps)
    test_source_file_count = sum(int(app["test_source_file_count"]) for app in apps)
    total_bytes = sum(int(app["bytes"]) for app in apps)
    total_files = sum(int(app["files"]) for app in apps)
    top_level_bytes: dict[str, int] = defaultdict(int)
    top_level_source_lines: dict[str, int] = defaultdict(int)
    largest_source_files: list[tuple[int, str]] = []
    benchmark = benchmark_for_meaningful_loc(meaningful_source_lines)
    feature_areas = sorted({area for app in apps for area in app.get("feature_areas", [])})
    surface_kinds = sorted({app.get("surface_kind") for app in apps if app.get("surface_kind")})
    technologies = sorted({tech for app in apps for tech in app.get("technologies", [])})

    for app in apps:
        scope_label = str(app["label"])
        for entry in app.get("top_level", []):
            top_level_bytes[scoped_entry_name(scope_label, str(entry["name"]))] += int(entry["bytes"])
        for entry in app.get("top_level_meaningful_source_lines", []):
            top_level_source_lines[scoped_entry_name(scope_label, str(entry["name"]))] += int(entry["lines"])
        for entry in app.get("largest_source_files", []):
            push_largest(
                largest_source_files,
                int(entry["lines"]),
                str(entry["path"]),
                limit=10,
            )

    return {
        "path_count": len(apps),
        "bytes": total_bytes,
        "files": total_files,
        "top_level": sorted_size_map(top_level_bytes),
        "top_level_meaningful_source_lines": sorted_line_map(top_level_source_lines),
        "largest_source_files": [
            {"path": path, "lines": lines}
            for lines, path in sorted(largest_source_files, key=lambda item: (-item[0], item[1]))
        ],
        "meaningful_source_lines": meaningful_source_lines,
        "meaningful_test_lines": meaningful_test_lines,
        "source_file_count": source_file_count,
        "test_source_file_count": test_source_file_count,
        "benchmark": benchmark,
        "feature_area_count": len(feature_areas),
        "feature_areas": feature_areas,
        "surface_kinds": surface_kinds,
        "technologies": technologies,
    }


def format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def summarize_test_surface_health(scope_summary: dict[str, object]) -> dict[str, object]:
    production_loc = int(scope_summary["meaningful_source_lines"])
    test_loc = int(scope_summary["meaningful_test_lines"])
    test_files = int(scope_summary["test_source_file_count"])
    ratio = test_loc / max(production_loc, 1)

    if test_loc == 0:
        return {
            "label": "Absent",
            "ratio": ratio,
            "summary": f"No meaningful automated test LOC was detected against {production_loc:,} production LOC.",
        }
    if ratio >= 0.30:
        label = "Strong"
        summary = f"Test surface is strong at {ratio:.2f}x test LOC across {test_files} test files."
    elif ratio >= 0.15:
        label = "Healthy"
        summary = f"Test surface is healthy at {ratio:.2f}x test LOC across {test_files} test files."
    elif ratio >= 0.05:
        label = "Thin"
        summary = f"Tests exist, but {ratio:.2f}x test LOC is thin for ongoing change safety."
    else:
        label = "Very Thin"
        summary = f"Tests exist, but {ratio:.2f}x test LOC leaves a weak regression buffer."

    return {"label": label, "ratio": ratio, "summary": summary}


def summarize_architectural_concentration(scope_summary: dict[str, object]) -> dict[str, object]:
    entries = list(scope_summary.get("top_level_meaningful_source_lines", []))
    total_source_lines = int(scope_summary["meaningful_source_lines"])
    if total_source_lines <= 0 or not entries:
        return {
            "label": "Unknown",
            "top1_share": 0.0,
            "top3_share": 0.0,
            "dominant_entries": [],
            "summary": "No source-line distribution was available.",
        }

    dominant_entries = []
    for entry in entries[:3]:
        line_count = int(entry["lines"])
        dominant_entries.append(
            {
                "name": str(entry["name"]),
                "lines": line_count,
                "share": line_count / total_source_lines,
            }
        )

    top1_share = dominant_entries[0]["share"]
    top3_share = sum(item["share"] for item in dominant_entries)
    if top1_share >= 0.50 or top3_share >= 0.85:
        label = "High"
    elif top1_share >= 0.35 or top3_share >= 0.70:
        label = "Moderate"
    else:
        label = "Distributed"

    summary = (
        f"Top module holds {format_percent(top1_share)} of source LOC; "
        f"top 3 hold {format_percent(top3_share)}."
    )
    return {
        "label": label,
        "top1_share": top1_share,
        "top3_share": top3_share,
        "dominant_entries": dominant_entries,
        "summary": summary,
    }


def build_largest_entries(scope_summary: dict[str, object]) -> list[dict[str, object]]:
    total_bytes = int(scope_summary["bytes"])
    source_lines_by_name = {
        str(entry["name"]): int(entry["lines"])
        for entry in scope_summary.get("top_level_meaningful_source_lines", [])
    }
    largest_entries = []
    for entry in list(scope_summary.get("top_level", []))[:3]:
        bytes_value = int(entry["bytes"])
        name = str(entry["name"])
        largest_entries.append(
            {
                "name": name,
                "bytes": bytes_value,
                "share": bytes_value / max(total_bytes, 1),
                "source_lines": source_lines_by_name.get(name, 0),
            }
        )
    return largest_entries


def collect_maintenance_risks(
    scope_summary: dict[str, object],
    signals: dict[str, object],
    test_surface_health: dict[str, object],
    concentration: dict[str, object],
) -> list[dict[str, object]]:
    risks: list[dict[str, object]] = []
    production_loc = int(scope_summary["meaningful_source_lines"])
    feature_area_count = int(signals["feature_area_count"])
    top_module_name = (
        str(concentration["dominant_entries"][0]["name"])
        if concentration["dominant_entries"]
        else "the largest module"
    )
    largest_source_file = next(iter(scope_summary.get("largest_source_files", [])), None)

    def add(score: int, title: str, summary: str) -> None:
        risks.append({"score": score, "title": title, "summary": summary})

    if production_loc >= 1500 and int(scope_summary["meaningful_test_lines"]) == 0:
        add(
            100,
            "Test surface is absent",
            f"{production_loc:,} production LOC are present, but no meaningful automated test LOC was found.",
        )
    elif production_loc >= 3000 and float(test_surface_health["ratio"]) < 0.05:
        add(
            88,
            "Test surface is too thin",
            f"Only {float(test_surface_health['ratio']):.2f}x test LOC backs {production_loc:,} production LOC.",
        )
    elif production_loc >= 5000 and float(test_surface_health["ratio"]) < 0.10:
        add(
            72,
            "Test surface may not keep pace with change volume",
            f"{float(test_surface_health['ratio']):.2f}x test LOC is modest for a codebase of this size.",
        )

    if production_loc >= 1000 and float(concentration["top1_share"]) >= 0.50:
        add(
            84,
            "Source complexity is concentrated",
            f"{top_module_name} alone holds {format_percent(float(concentration['top1_share']))} of source LOC.",
        )
    elif production_loc >= 1500 and float(concentration["top3_share"]) >= 0.80:
        add(
            74,
            "A small set of modules carries most of the change load",
            f"The top 3 modules hold {format_percent(float(concentration['top3_share']))} of source LOC.",
        )

    if production_loc >= 8000 and not signals["has_shared_library"]:
        add(
            70,
            "Module boundaries look weak for the current size",
            "Substantial source volume is visible without clear shared-library extraction.",
        )

    if production_loc >= 1500 and not signals["has_ci"]:
        add(
            66,
            "Change safety net is weak",
            "No CI or workflow automation was visible for a repo with ongoing maintenance load.",
        )

    if production_loc >= 5000 and not signals["has_docs"]:
        add(
            58,
            "Architecture knowledge may remain implicit",
            "Design or architecture documentation was not visible despite notable code volume.",
        )

    if largest_source_file is not None and int(largest_source_file["lines"]) >= 700:
        add(
            68,
            "Large source files suggest local hotspots",
            f"{largest_source_file['path']} is {int(largest_source_file['lines']):,} meaningful LOC.",
        )
    elif largest_source_file is not None and int(largest_source_file["lines"]) >= 400:
        add(
            54,
            "Some source files are already heavy",
            f"{largest_source_file['path']} is {int(largest_source_file['lines']):,} meaningful LOC.",
        )

    if feature_area_count >= 8 and float(test_surface_health["ratio"]) < 0.10:
        add(
            62,
            "Feature breadth may be outrunning protection",
            f"{feature_area_count} feature areas are visible, but tests remain relatively thin.",
        )

    return sorted(risks, key=lambda item: (-int(item["score"]), str(item["title"])))[:3]


def collect_healthy_structure_signals(
    scope_summary: dict[str, object],
    signals: dict[str, object],
    test_surface_health: dict[str, object],
    concentration: dict[str, object],
) -> list[dict[str, object]]:
    strengths: list[dict[str, object]] = []
    production_loc = int(scope_summary["meaningful_source_lines"])
    feature_area_count = int(signals["feature_area_count"])
    surface_count = int(signals["surface_count"])
    largest_source_file = next(iter(scope_summary.get("largest_source_files", [])), None)

    def add(score: int, title: str, summary: str) -> None:
        strengths.append({"score": score, "title": title, "summary": summary})

    if int(scope_summary["meaningful_test_lines"]) > 0 and float(test_surface_health["ratio"]) >= 0.15:
        add(
            90,
            "Tests provide meaningful regression support",
            f"Test surface sits at {float(test_surface_health['ratio']):.2f}x test LOC.",
        )
    elif int(scope_summary["meaningful_test_lines"]) > 0:
        add(
            62,
            "Automated tests are present",
            f"Tests exist across {int(scope_summary['test_source_file_count'])} test files.",
        )

    if signals["has_ci"]:
        add(84, "CI or workflow automation is visible", "Change validation is not fully manual.")

    if signals["has_shared_library"]:
        add(80, "Shared logic is extracted", "Common behavior appears to have explicit module boundaries.")

    if signals["has_docs"]:
        add(72, "Architecture knowledge is documented", "Design or architecture docs were visible in the repo.")

    if feature_area_count >= 4 and float(concentration["top1_share"]) < 0.45:
        add(
            76,
            "Feature breadth is spread across multiple areas",
            f"{feature_area_count} feature areas are visible without a single dominant source bucket.",
        )

    if surface_count >= 2 and signals["has_shared_library"]:
        add(
            74,
            "Multiple product surfaces appear to share foundations",
            f"{surface_count} app surfaces are visible alongside shared logic extraction.",
        )

    if signals["has_localization"]:
        add(
            58,
            "Localization is part of the maintained structure",
            f"{int(signals['localization_count'])} localization artifacts were detected.",
        )

    if production_loc > 0 and production_loc <= 3000:
        add(
            54,
            "Source scope is still compact enough for direct review",
            f"{production_loc:,} production LOC remain feasible for end-to-end inspection.",
        )

    if int(scope_summary["source_file_count"]) > 0 and int(scope_summary["source_file_count"]) <= 20:
        add(
            50,
            "Source file count is still reviewable by hand",
            f"{int(scope_summary['source_file_count'])} source files shape the current change surface.",
        )

    if 0 < len(scope_summary.get("top_level", [])) <= 6:
        add(
            48,
            "Top-level layout is still shallow",
            f"{len(scope_summary.get('top_level', []))} top-level entries dominate the current footprint.",
        )

    if (
        production_loc > 0
        and float(concentration["top1_share"]) <= 0.40
        and float(concentration["top3_share"]) <= 0.75
    ):
        add(
            64,
            "No single source bucket dominates the codebase",
            f"Top module holds {format_percent(float(concentration['top1_share']))} of source LOC.",
        )

    if largest_source_file is not None and int(largest_source_file["lines"]) < 400:
        add(
            56,
            "Largest source file is still moderate in size",
            f"{largest_source_file['path']} is {int(largest_source_file['lines']):,} meaningful LOC.",
        )

    return sorted(strengths, key=lambda item: (-int(item["score"]), str(item["title"])))[:3]


def build_complexity_hotspots(
    scope_summary: dict[str, object],
    concentration: dict[str, object],
) -> list[dict[str, object]]:
    hotspots: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for entry in concentration.get("dominant_entries", []):
        key = ("module", str(entry["name"]))
        if key in seen:
            continue
        seen.add(key)
        hotspots.append(
            {
                "kind": "module",
                "name": str(entry["name"]),
                "lines": int(entry["lines"]),
                "summary": f"Holds {format_percent(float(entry['share']))} of source LOC.",
            }
        )

    for entry in scope_summary.get("largest_source_files", []):
        if int(entry["lines"]) < 400:
            continue
        key = ("file", str(entry["path"]))
        if key in seen:
            continue
        seen.add(key)
        hotspots.append(
            {
                "kind": "file",
                "name": str(entry["path"]),
                "lines": int(entry["lines"]),
                "summary": "Single-file source hotspot by meaningful LOC.",
            }
        )
        if len(hotspots) >= 3:
            break

    return hotspots[:3]


def build_diagnostic_summary(
    scope_summary: dict[str, object],
    signals: dict[str, object],
) -> dict[str, object] | None:
    if not scope_summary:
        return None

    test_surface_health = summarize_test_surface_health(scope_summary)
    concentration = summarize_architectural_concentration(scope_summary)
    maintenance_risks = collect_maintenance_risks(
        scope_summary,
        signals,
        test_surface_health,
        concentration,
    )
    healthy_structure_signals = collect_healthy_structure_signals(
        scope_summary,
        signals,
        test_surface_health,
        concentration,
    )
    risk_label = "High" if maintenance_risks and int(maintenance_risks[0]["score"]) >= 80 else "Moderate"
    if not maintenance_risks or int(maintenance_risks[0]["score"]) < 60:
        risk_label = "Contained"

    return {
        "largest_entries": build_largest_entries(scope_summary),
        "maintenance_risk": {
            "label": risk_label,
            "findings": maintenance_risks,
        },
        "test_surface_health": test_surface_health,
        "architectural_concentration": concentration,
        "complexity_hotspots": build_complexity_hotspots(scope_summary, concentration),
        "healthy_structure_signals": healthy_structure_signals,
    }


def markdown_table(rows: list[list[str]], headers: list[str]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def format_share(bytes_value: int, total_bytes: int) -> str:
    if total_bytes <= 0:
        return "-"
    return f"{bytes_value / total_bytes * 100:.1f}%"


def render_size_rows(items: list[dict[str, object]], total_bytes: int, limit: int) -> list[list[str]]:
    rows = []
    for item in items[:limit]:
        bytes_value = int(item["bytes"])
        rows.append([
            str(item["name"]),
            humanize_bytes(bytes_value),
            format_share(bytes_value, total_bytes),
        ])
    return rows


def render_path_rows(items: list[dict[str, object]], limit: int) -> list[list[str]]:
    rows = []
    for item in items[:limit]:
        rows.append([str(item["path"]), humanize_bytes(int(item["bytes"]))])
    return rows


def render_candidate_rows(items: list[dict[str, object]], limit: int) -> list[list[str]]:
    rows = []
    for item in items[:limit]:
        rows.append([
            str(item["label"]),
            str(item["score"]),
            "; ".join(str(reason) for reason in item["reasons"]),
        ])
    return rows


def render_largest_entry_rows(items: list[dict[str, object]]) -> list[list[str]]:
    rows = []
    for item in items:
        rows.append([
            str(item["name"]),
            humanize_bytes(int(item["bytes"])),
            format_percent(float(item["share"])),
            f"{int(item['source_lines']):,}" if int(item["source_lines"]) > 0 else "-",
        ])
    return rows


def render_signal_rows(items: list[dict[str, object]]) -> list[list[str]]:
    rows = []
    for item in items:
        rows.append([str(item["title"]), str(item["summary"])])
    return rows


def render_hotspot_rows(items: list[dict[str, object]]) -> list[list[str]]:
    rows = []
    for item in items:
        rows.append([
            str(item["kind"]),
            str(item["name"]),
            str(item["summary"]),
        ])
    return rows


def render_app_markdown(app: dict[str, object], repo_primary_bytes: int, top_limit: int) -> str:
    lines = [
        f"### {app['label']}",
        f"- Path: `{app['path']}`",
        f"- Audit scope: {app['audit_scope_label']}",
        f"- Codebase footprint: {humanize_bytes(int(app['bytes']))} across {app['files']} files",
        (
            f"- Meaningful production LOC: {int(app['meaningful_source_lines']):,} "
            f"across {int(app['source_file_count'])} source files"
        ),
    ]
    if int(app["meaningful_test_lines"]) > 0:
        lines.append(
            f"- Meaningful test LOC: {int(app['meaningful_test_lines']):,} "
            f"across {int(app['test_source_file_count'])} test files"
        )
    if repo_primary_bytes > 0:
        lines.append(
            f"- Share of primary repository footprint: {format_share(int(app['bytes']), repo_primary_bytes)}"
        )
    lines.append(
        f"- Market scale band: {app['benchmark']['label']} "
        f"({app['benchmark']['range']} LOC, {app['benchmark']['market_note']})"
    )
    if app["technologies"]:
        lines.append(f"- Technologies: {', '.join(app['technologies'][:10])}")
    if app["feature_areas"]:
        lines.append(f"- Feature areas: {', '.join(app['feature_areas'][:8])}")

    lines.extend(
        [
            "",
            markdown_table(
                render_size_rows(app["roles"], int(app["bytes"]), len(app["roles"])),
                headers=["Role", "Size", "Share"],
            )
            if app["roles"]
            else "_No role breakdown available._",
            "",
            markdown_table(
                render_size_rows(app["top_level"], int(app["bytes"]), top_limit),
                headers=["Entry", "Size", "Share"],
            )
            if app["top_level"]
            else "_No top-level entries found._",
            "",
            markdown_table(
                render_size_rows(app["extensions"], int(app["bytes"]), top_limit),
                headers=["Extension", "Size", "Share"],
            )
            if app["extensions"]
            else "_No extensions found._",
            "",
            markdown_table(
                render_path_rows(app["largest_files"], top_limit),
                headers=["Path", "Size"],
            )
            if app["largest_files"]
            else "_No files found._",
        ]
    )
    return "\n".join(lines)


def render_markdown(report: dict[str, object], top_limit: int) -> str:
    repo = report["repository"]
    raw = repo["raw"]
    filtered = repo["filtered"]
    primary = repo["primary"]
    repo_primary_bytes = int(primary["bytes"])
    diagnostic_summary = report.get("diagnostic_summary")
    diagnostic_scope = report.get("diagnostic_scope") or {"label": "Repository"}

    lines = [
        "# Footprint Report",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Repository: `{repo['path']}`",
        "",
        "## Repository Summary",
        f"- Audit scope: {repo['audit_scope_label']}",
        f"- Primary footprint: {humanize_bytes(int(primary['bytes']))} across {primary['files']} files",
    ]
    if repo["tracked"] is not None:
        lines.append(
            f"- Git tracked footprint: {humanize_bytes(int(repo['tracked']['bytes']))} across {repo['tracked']['files']} files"
        )
        if repo.get("git_root") and repo["git_root"] != repo["path"]:
            lines.append(f"- Git root: `{repo['git_root']}`")
    elif repo.get("git_error"):
        lines.append(f"- Git tracked footprint: unavailable ({repo['git_error']})")
    if repo["storage_footprint_included"] and filtered is not None:
        lines.append(
            f"- Working footprint: {humanize_bytes(int(filtered['bytes']))} across {filtered['files']} files"
        )
    if repo["storage_footprint_included"] and raw is not None:
        lines.append(
            f"- Raw directory size: {humanize_bytes(int(raw['bytes']))} across {raw['files']} files"
        )
    if repo["storage_footprint_included"] and repo["excluded_bytes"] is not None:
        lines.append(f"- Excluded transient footprint: {humanize_bytes(int(repo['excluded_bytes']))}")

    if diagnostic_summary:
        lines.extend(
            [
                "",
                "## Diagnostics",
                f"- Diagnostic scope: {diagnostic_scope['label']}",
                f"- Maintenance risk: {diagnostic_summary['maintenance_risk']['label']}",
                (
                    f"- Test surface health: {diagnostic_summary['test_surface_health']['label']} "
                    f"({diagnostic_summary['test_surface_health']['summary']})"
                ),
                (
                    f"- Architectural concentration: {diagnostic_summary['architectural_concentration']['label']} "
                    f"({diagnostic_summary['architectural_concentration']['summary']})"
                ),
                "",
                "### Biggest Directories / Modules",
                markdown_table(
                    render_largest_entry_rows(diagnostic_summary["largest_entries"]),
                    headers=["Entry", "Size", "Share", "Source LOC"],
                )
                if diagnostic_summary["largest_entries"]
                else "_No dominant directories or modules were identified._",
                "",
                "### Top Maintenance Risks",
                markdown_table(
                    render_signal_rows(diagnostic_summary["maintenance_risk"]["findings"]),
                    headers=["Risk", "Why it matters"],
                )
                if diagnostic_summary["maintenance_risk"]["findings"]
                else "_No major maintenance risks were highlighted by the heuristics._",
                "",
                "### Healthy Structure Signals",
                markdown_table(
                    render_signal_rows(diagnostic_summary["healthy_structure_signals"]),
                    headers=["Signal", "Why it helps"],
                )
                if diagnostic_summary["healthy_structure_signals"]
                else "_No strong positive structure signals were highlighted._",
                "",
                "### Likely Complexity Hotspots",
                markdown_table(
                    render_hotspot_rows(diagnostic_summary["complexity_hotspots"]),
                    headers=["Type", "Name", "Signal"],
                )
                if diagnostic_summary["complexity_hotspots"]
                else "_No clear hotspots were highlighted._",
            ]
        )

    lines.extend(
        [
            "",
            "## Top-Level Breakdown",
            markdown_table(
                render_size_rows(primary["top_level"], int(primary["bytes"]), top_limit),
                headers=["Entry", "Size", "Share"],
            )
            if primary["top_level"]
            else "_No entries found._",
            "",
            "## Extension Breakdown",
            markdown_table(
                render_size_rows(primary["extensions"], int(primary["bytes"]), top_limit),
                headers=["Extension", "Size", "Share"],
            )
            if primary["extensions"]
            else "_No extensions found._",
            "",
            "## Largest Files",
            markdown_table(
                render_path_rows(primary["largest_files"], top_limit),
                headers=["Path", "Size"],
            )
            if primary["largest_files"]
            else "_No files found._",
            "",
            "## App Codebases",
        ]
    )

    if report["apps"]:
        selected_summary = report.get("selected_apps_summary")
        quality_and_value = report.get("quality_and_value")
        if selected_summary:
            lines.extend(
                [
                    "### Selected Scope",
                    (
                        f"- Scope size: {humanize_bytes(int(selected_summary['bytes']))} "
                        f"across {selected_summary['files']} files and {selected_summary['path_count']} paths"
                    ),
                    (
                        f"- Meaningful production LOC: {int(selected_summary['meaningful_source_lines']):,} "
                        f"across {int(selected_summary['source_file_count'])} source files"
                    ),
                ]
            )
            if int(selected_summary["meaningful_test_lines"]) > 0:
                lines.append(
                    f"- Meaningful test LOC: {int(selected_summary['meaningful_test_lines']):,} "
                    f"across {int(selected_summary['test_source_file_count'])} test files"
                )
            lines.append(
                f"- Market scale band: {selected_summary['benchmark']['label']} "
                f"({selected_summary['benchmark']['range']} LOC, {selected_summary['benchmark']['market_note']})"
            )
            if selected_summary["technologies"]:
                lines.append(f"- Technologies: {', '.join(selected_summary['technologies'][:12])}")
            if selected_summary["feature_areas"]:
                lines.append(f"- Feature areas: {', '.join(selected_summary['feature_areas'][:10])}")
            if quality_and_value:
                lines.append(
                    f"- Supporting quality proxy: {quality_and_value['quality']['band']['label']} "
                    f"({quality_and_value['quality']['score']}/100, {quality_and_value['quality']['band']['note']})"
                )
                lines.append(
                    f"- Supporting breadth proxy: {quality_and_value['value']['band']['label']} "
                    f"({quality_and_value['value']['score']}/100, {quality_and_value['value']['band']['note']})"
                )
            lines.append("")
            if quality_and_value:
                lines.append("### Supporting Proxies")
                if quality_and_value["quality"]["reasons"]:
                    lines.append(f"- Quality evidence: {'; '.join(quality_and_value['quality']['reasons'])}")
                if quality_and_value["value"]["reasons"]:
                    lines.append(f"- Breadth evidence: {'; '.join(quality_and_value['value']['reasons'])}")
                lines.append("")
        for app in report["apps"]:
            lines.append(
                render_app_markdown(
                    app,
                    repo_primary_bytes=repo_primary_bytes,
                    top_limit=top_limit,
                )
            )
            lines.append("")
    elif report["app_candidates"]:
        lines.append("_No app path was provided. Probable app directories:_")
        lines.append("")
        lines.append(
            markdown_table(
                render_candidate_rows(report["app_candidates"], top_limit),
                headers=["Candidate", "Score", "Signals"],
            )
        )
        lines.append("")
    else:
        lines.append("_No app path was provided and no probable app directory was detected._")
        lines.append("")

    lines.extend(
        [
            "## Notes",
            "- Default audit scope is Git tracked files when available; otherwise the script falls back to the working tree with transient directories excluded.",
            "- Working footprint excludes common transient directories such as `.git`, `DerivedData`, `node_modules`, and build caches.",
            "- App codebase footprint is measured from repository directories, not built binaries.",
            "- Meaningful LOC counts non-empty, non-comment-only lines in source files; treat the market scale band as heuristic rather than empirical truth.",
            "- Diagnostic findings are heuristics derived from concentration, tests, CI, docs, modularization, and source-file shape; use them to prioritize review, not as absolute truth.",
            "- Quality and breadth proxies are supplementary and intentionally lower priority than the diagnostic findings.",
            "- Use `--app-path` for app-specific measurement when the repository contains multiple apps or modules.",
        ]
    )
    return "\n".join(lines).rstrip()


def resolve_app_path(raw_path: str, repo_path: Path) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = repo_path / path
    return path.resolve()


def build_report(args: argparse.Namespace) -> dict[str, object]:
    repo_path = Path(args.repo).expanduser().resolve()
    if not repo_path.exists() or not repo_path.is_dir():
        raise SystemExit(f"Repository path does not exist or is not a directory: {repo_path}")

    git_root, tracked_paths, git_error = list_git_tracked_files(repo_path)
    audit_scope_label = "Git tracked files" if tracked_paths is not None else "Working tree fallback"
    repo_relative_paths = collect_repo_relative_paths(repo_path, tracked_paths)
    repository_code_profile = analyze_repository_code_profile(
        repo_path,
        largest_limit=args.top,
        tracked_paths=tracked_paths,
        audit_scope_label=audit_scope_label,
    )

    app_results = []
    for raw_app_path in args.app_path:
        app_path = resolve_app_path(raw_app_path, repo_path)
        if not app_path.exists() or not app_path.is_dir():
            raise SystemExit(f"App path does not exist or is not a directory: {app_path}")
        app_results.append(
            analyze_app_path(
                app_path,
                repo_path=repo_path,
                largest_limit=args.top,
                tracked_paths=tracked_paths,
                audit_scope_label=audit_scope_label,
            )
        )

    app_candidates = [] if args.skip_app_discovery or args.app_path else discover_app_paths(repo_path)
    selected_apps_summary = summarize_selected_apps(app_results)
    diagnostic_targets = app_results or [repository_code_profile]
    diagnostic_scope_kind = "selected-apps" if app_results else "repository"
    diagnostic_scope_label = "Selected app paths" if app_results else "Repository"
    diagnostic_scope_summary = selected_apps_summary or repository_code_profile
    scope_signals = analyze_scope_signals(repo_relative_paths, diagnostic_targets)
    diagnostic_summary = build_diagnostic_summary(diagnostic_scope_summary, scope_signals)
    quality_and_value = None
    if app_results:
        quality_and_value = summarize_quality_and_value(
            selected_apps_summary,
            scope_signals,
        )

    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "repository": summarize_repo(
            repo_path,
            largest_limit=args.top,
            git_root=git_root,
            tracked_paths=tracked_paths,
            git_error=git_error,
            include_storage_footprint=args.include_storage_footprint,
        ),
        "repository_code_profile": repository_code_profile,
        "apps": app_results,
        "selected_apps_summary": selected_apps_summary,
        "diagnostic_scope": {
            "kind": diagnostic_scope_kind,
            "label": diagnostic_scope_label,
        },
        "diagnostic_summary": diagnostic_summary,
        "quality_and_value": quality_and_value,
        "app_candidates": app_candidates,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Measure repository size and optional app codebase size without modifying source files."
    )
    parser.add_argument("--repo", default=".", help="Repository directory to inspect (default: current directory)")
    parser.add_argument(
        "--app-path",
        action="append",
        default=[],
        help="Optional app directory to inspect as codebase footprint (repeatable, relative paths resolve from --repo)",
    )
    parser.add_argument(
        "--skip-app-discovery",
        action="store_true",
        help="Skip probable app-directory discovery when app paths are not provided",
    )
    parser.add_argument(
        "--include-storage-footprint",
        action="store_true",
        help="Also measure working-tree and raw disk footprint in addition to the primary audit scope",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of rows to include in top-level tables (default: 10)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.top <= 0:
        raise SystemExit("--top must be greater than 0")

    report = build_report(args)
    if args.format == "json":
        json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return

    print(render_markdown(report, top_limit=args.top))


if __name__ == "__main__":
    main()
