#!/usr/bin/env python3
"""Audit and repair Xcode string catalogs."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any
import re
import sys

EXCLUDED_DIRS = {
    ".build",
    ".git",
    ".swiftpm",
    "Carthage",
    "DerivedData",
    "Pods",
    "build",
}
SOURCE_SUFFIXES = {
    ".h",
    ".intentdefinition",
    ".m",
    ".mm",
    ".plist",
    ".storyboard",
    ".strings",
    ".stringsdict",
    ".swift",
    ".swiftinterface",
    ".xib",
}
STRING_LITERAL_PATTERN = re.compile(r'"((?:\\.|[^"\\])*)"', re.DOTALL)
GENERIC_INTERPOLATION_PLACEHOLDERS = ("%@", "%lld", "%f")
PLACEHOLDER_HINTS = {
    "applicationname": ("${applicationName}",),
    "int": ("%lld",),
    "integer": ("%lld",),
    "double": ("%f",),
    "float": ("%f",),
    "number": ("%f", "%lld"),
    "decimal": ("%f",),
}


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit xcstrings files, seed missing locales, and prune unused keys.",
    )
    parser.add_argument(
        "--project-root",
        required=True,
        help="Repository or project root that contains source files and xcstrings catalogs.",
    )
    parser.add_argument(
        "--catalog",
        action="append",
        default=[],
        help="Relative or absolute path to a specific xcstrings file. Repeat as needed.",
    )
    parser.add_argument(
        "--source-root",
        action="append",
        default=[],
        help=(
            "Relative or absolute source root to scan for static string references. "
            "Repeat as needed. Defaults to the whole project root."
        ),
    )
    parser.add_argument(
        "--required-locales",
        help="Comma-separated locale list to enforce for selected catalogs.",
    )
    parser.add_argument(
        "--seed-missing-locales",
        action="store_true",
        help="Create missing locale entries by copying the source locale structure.",
    )
    parser.add_argument(
        "--prune-unused",
        action="store_true",
        help="Remove keys that have no static literal matches in project source files.",
    )
    parser.add_argument(
        "--prune-stale-unused",
        action="store_true",
        help="Remove keys that are marked stale and have no static literal matches.",
    )
    parser.add_argument(
        "--normalize-stale-referenced",
        action="store_true",
        help="Clear the stale extraction marker from keys that still have static references.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write catalog changes in place. Without this flag, mutations are a dry run.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format for the audit report.",
    )
    return parser.parse_args()


def should_skip_path(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts)


def resolve_catalog_path(project_root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = (project_root / path).resolve()
    return path.resolve()


def render_report_path(project_root: Path, path: Path) -> str:
    if path.is_relative_to(project_root):
        return str(path.relative_to(project_root))
    return str(path)


def discover_catalogs(project_root: Path, raw_catalogs: list[str]) -> list[Path]:
    if raw_catalogs:
        catalogs = [resolve_catalog_path(project_root, raw_path) for raw_path in raw_catalogs]
    else:
        catalogs = [
            path.resolve()
            for path in project_root.rglob("*.xcstrings")
            if path.is_file() and not should_skip_path(path)
        ]
    catalogs = sorted(dict.fromkeys(catalogs))
    if not catalogs:
        raise ValueError(f"No xcstrings files found under {project_root}")
    return catalogs


def load_catalog(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Failed to parse {path}: {error}") from error


def normalize_string_literal(raw_literal: str) -> str:
    normalized: list[str] = []
    index = 0
    while index < len(raw_literal):
        character = raw_literal[index]
        if character == "\\" and index + 1 < len(raw_literal):
            next_character = raw_literal[index + 1]
            if next_character == '"':
                normalized.append('"')
                index += 2
                continue
            if next_character == "\\":
                normalized.append("\\")
                index += 2
                continue
            if next_character == "n":
                normalized.append("\n")
                index += 2
                continue
            if next_character == "r":
                normalized.append("\r")
                index += 2
                continue
            if next_character == "t":
                normalized.append("\t")
                index += 2
                continue
        normalized.append(character)
        index += 1
    return "".join(normalized)


def split_interpolated_literal(literal: str) -> list[tuple[str, str]]:
    segments: list[tuple[str, str]] = []
    buffer: list[str] = []
    index = 0

    while index < len(literal):
        if literal[index:index + 2] != "\\(":
            buffer.append(literal[index])
            index += 1
            continue

        if buffer:
            segments.append(("text", "".join(buffer)))
            buffer = []

        index += 2
        depth = 1
        interpolation: list[str] = []

        while index < len(literal) and depth > 0:
            character = literal[index]
            if character == "(":
                depth += 1
                interpolation.append(character)
                index += 1
                continue
            if character == ")":
                depth -= 1
                if depth == 0:
                    index += 1
                    break
                interpolation.append(character)
                index += 1
                continue
            interpolation.append(character)
            index += 1

        if depth == 0:
            segments.append(("interpolation", "".join(interpolation)))
            continue

        buffer.append("\\(")
        buffer.extend(interpolation)

    if buffer:
        segments.append(("text", "".join(buffer)))

    return segments


def interpolation_placeholders(expression: str) -> tuple[str, ...]:
    stripped_expression = expression.strip()
    if stripped_expression == ".applicationName" or stripped_expression.endswith(".applicationName"):
        return PLACEHOLDER_HINTS["applicationname"]

    match = re.search(r"placeholder:\s*\.([A-Za-z0-9_]+)", expression)
    if not match:
        return GENERIC_INTERPOLATION_PLACEHOLDERS

    hint = match.group(1).lower()
    return PLACEHOLDER_HINTS.get(hint, ("%@",))


def expand_literal_variants(raw_literal: str) -> set[str]:
    normalized_literal = normalize_string_literal(raw_literal)
    variants = {normalized_literal}
    segments = split_interpolated_literal(normalized_literal)

    if not any(kind == "interpolation" for kind, _ in segments):
        return variants

    expanded_variants = [""]
    for kind, value in segments:
        if kind == "text":
            expanded_variants = [candidate + value for candidate in expanded_variants]
            continue

        placeholders = interpolation_placeholders(value)
        expanded_variants = [
            candidate + placeholder
            for candidate in expanded_variants
            for placeholder in placeholders
        ]

    variants.update(expanded_variants)
    return variants


def collect_catalog_keys(catalogs: dict[Path, dict[str, Any]]) -> set[str]:
    keys: set[str] = set()
    for catalog in catalogs.values():
        keys.update(catalog.get("strings", {}).keys())
    return keys


def resolve_source_roots(project_root: Path, raw_roots: list[str]) -> list[Path] | None:
    if not raw_roots:
        return None

    resolved_roots: list[Path] = []
    for raw_root in raw_roots:
        root = resolve_catalog_path(project_root, raw_root)
        if not root.exists():
            raise ValueError(f"Source root not found: {root}")
        resolved_roots.append(root)
    return sorted(dict.fromkeys(resolved_roots))


def iter_source_candidates(project_root: Path, source_roots: list[Path] | None) -> list[Path]:
    if source_roots is None:
        return [project_root]
    return source_roots


def collect_source_files(
    project_root: Path,
    source_roots: list[Path] | None = None,
) -> list[Path]:
    files: list[Path] = []
    for candidate_root in iter_source_candidates(project_root, source_roots):
        if candidate_root.is_file():
            candidates = [candidate_root]
        else:
            candidates = candidate_root.rglob("*")

        for path in candidates:
            if (
                path.is_file()
                and path.suffix in SOURCE_SUFFIXES
                and not should_skip_path(path)
                and path.suffix != ".xcstrings"
            ):
                files.append(path)
    return sorted(files)


def build_literal_reference_map(
    project_root: Path,
    keys: set[str],
    source_roots: list[Path] | None = None,
) -> dict[str, list[str]]:
    reference_map = {key: [] for key in keys}
    for source_file in collect_source_files(project_root, source_roots):
        try:
            content = source_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        matched_keys: set[str] = set()
        for match in STRING_LITERAL_PATTERN.finditer(content):
            matched_keys.update(expand_literal_variants(match.group(1)))
        relative_path = render_report_path(project_root, source_file)
        for key in matched_keys & keys:
            reference_map[key].append(relative_path)
    return reference_map


def parse_required_locales(raw_locales: str | None) -> list[str] | None:
    if not raw_locales:
        return None
    locales = [locale.strip() for locale in raw_locales.split(",") if locale.strip()]
    if not locales:
        return None
    return list(dict.fromkeys(locales))


def collect_catalog_locales(catalog: dict[str, Any], source_language: str) -> list[str]:
    locales: list[str] = [source_language]
    for entry in catalog.get("strings", {}).values():
        for locale in entry.get("localizations", {}):
            if locale not in locales:
                locales.append(locale)
    return locales


def walk_localization_payloads(node: Any) -> list[tuple[str, dict[str, Any]]]:
    payloads: list[tuple[str, dict[str, Any]]] = []
    if isinstance(node, dict):
        string_unit = node.get("stringUnit")
        if isinstance(string_unit, dict):
            payloads.append(("stringUnit", string_unit))
        string_set = node.get("stringSet")
        if isinstance(string_set, dict):
            payloads.append(("stringSet", string_set))
        for value in node.values():
            payloads.extend(walk_localization_payloads(value))
    elif isinstance(node, list):
        for value in node:
            payloads.extend(walk_localization_payloads(value))
    return payloads


def collect_pending_states(localization: dict[str, Any]) -> list[str]:
    states: list[str] = []
    for payload_kind, payload in walk_localization_payloads(localization):
        if payload_kind == "stringUnit":
            state = payload.get("state", "missing-state")
            if payload.get("value") in (None, ""):
                state = "missing-value"
        else:
            state = payload.get("state", "missing-state")
            if not payload.get("values"):
                state = "missing-value"
        if state != "translated" and state not in states:
            states.append(state)
    return states


def mark_localization_payloads_as_new(node: Any) -> None:
    if isinstance(node, dict):
        string_unit = node.get("stringUnit")
        if isinstance(string_unit, dict):
            string_unit["state"] = "new"
        string_set = node.get("stringSet")
        if isinstance(string_set, dict):
            string_set["state"] = "new"
        for value in node.values():
            mark_localization_payloads_as_new(value)
    elif isinstance(node, list):
        for value in node:
            mark_localization_payloads_as_new(value)


def build_seed_localization(
    key: str,
    entry: dict[str, Any],
    source_language: str,
) -> dict[str, Any] | None:
    localizations = entry.get("localizations", {})
    template = localizations.get(source_language)
    if template is None and localizations:
        template = next(iter(localizations.values()))
    if template is None:
        return {
            "stringUnit": {
                "state": "new",
                "value": key,
            }
        }
    seeded_localization = copy.deepcopy(template)
    mark_localization_payloads_as_new(seeded_localization)
    return seeded_localization


def write_catalog(path: Path, catalog: dict[str, Any]) -> None:
    serialized = json.dumps(catalog, ensure_ascii=False, indent=2)
    path.write_text(serialized + "\n", encoding="utf-8")


def audit_catalog(
    project_root: Path,
    path: Path,
    catalog: dict[str, Any],
    reference_map: dict[str, list[str]],
    required_locales_override: list[str] | None,
    prune_unused: bool,
    prune_stale_unused: bool,
    normalize_stale_referenced: bool,
    seed_missing_locales: bool,
    apply_changes: bool,
    source_roots: list[Path] | None,
) -> dict[str, Any]:
    source_language = catalog.get("sourceLanguage", "en")
    required_locales = required_locales_override or collect_catalog_locales(catalog, source_language)
    if source_language not in required_locales:
        required_locales = [source_language, *required_locales]

    string_table = catalog.get("strings", {})
    incomplete_keys: list[dict[str, Any]] = []
    unused_candidates: list[dict[str, Any]] = []
    seeded_entries: list[dict[str, Any]] = []
    pruned_keys: list[str] = []
    stale_keys: list[str] = []
    stale_unused_candidates: list[dict[str, Any]] = []
    stale_referenced_keys: list[dict[str, Any]] = []
    normalized_stale_keys: list[str] = []

    for key in list(string_table.keys()):
        entry = string_table[key]
        localizations = entry.get("localizations", {})
        is_stale = entry.get("extractionState") == "stale"

        if is_stale:
            stale_keys.append(key)

        if entry.get("shouldTranslate", True):
            missing_locales: list[str] = []
            pending_locales: dict[str, list[str]] = {}
            for locale in required_locales:
                localization = localizations.get(locale)
                if localization is None:
                    if seed_missing_locales:
                        seeded_localization = build_seed_localization(
                            key,
                            entry,
                            source_language,
                        )
                        if seeded_localization is not None:
                            localizations[locale] = seeded_localization
                            seeded_entries.append(
                                {
                                    "key": key,
                                    "locale": locale,
                                }
                            )
                            pending_locales[locale] = ["new"]
                            continue
                    missing_locales.append(locale)
                    if localization is None:
                        continue

                states = collect_pending_states(localization)
                if states:
                    pending_locales[locale] = states

            if missing_locales or pending_locales:
                incomplete_keys.append(
                    {
                        "key": key,
                        "missing_locales": missing_locales,
                        "pending_locales": pending_locales,
                    }
                )

        references = reference_map.get(key, [])
        if is_stale:
            if references:
                stale_referenced_keys.append(
                    {
                        "key": key,
                        "references": references,
                    }
                )
                if normalize_stale_referenced:
                    entry.pop("extractionState", None)
                    normalized_stale_keys.append(key)
            else:
                stale_unused_candidates.append(
                    {
                        "key": key,
                        "references": references,
                    }
                )

        if not references:
            unused_candidates.append(
                {
                    "key": key,
                    "references": references,
                    "is_stale": is_stale,
                }
            )
            if prune_unused or (prune_stale_unused and is_stale):
                pruned_keys.append(key)

    if prune_unused or prune_stale_unused:
        for key in pruned_keys:
            string_table.pop(key, None)

    mutated = bool(seeded_entries or pruned_keys or normalized_stale_keys)
    if mutated and apply_changes:
        write_catalog(path, catalog)

    return {
        "path": render_report_path(project_root, path),
        "source_roots": [
            render_report_path(project_root, root)
            for root in source_roots or [project_root]
        ],
        "source_language": source_language,
        "required_locales": required_locales,
        "key_count": len(string_table),
        "incomplete_keys": incomplete_keys,
        "stale_keys": stale_keys,
        "stale_unused_candidates": stale_unused_candidates,
        "stale_referenced_keys": stale_referenced_keys,
        "unused_candidates": unused_candidates,
        "seeded_entries": seeded_entries,
        "pruned_keys": pruned_keys,
        "normalized_stale_keys": normalized_stale_keys,
        "applied": mutated and apply_changes,
        "dry_run_changes": mutated and not apply_changes,
    }


def format_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# XCStrings Audit",
        "",
        f"- Project root: `{report['project_root']}`",
        f"- Catalog count: {len(report['catalogs'])}",
    ]
    if report["planned_changes"] and not report["apply"]:
        lines.append("- Mutations are a dry run because `--apply` was not set.")
    if report["apply"]:
        lines.append("- Mutations were written in place.")

    for catalog in report["catalogs"]:
        lines.extend(
            [
                "",
                f"## `{catalog['path']}`",
                "",
                f"- Source roots: `{', '.join(catalog['source_roots'])}`",
                f"- Source language: `{catalog['source_language']}`",
                f"- Required locales: `{', '.join(catalog['required_locales'])}`",
                f"- Key count: {catalog['key_count']}",
                f"- Incomplete keys: {len(catalog['incomplete_keys'])}",
                f"- Stale keys: {len(catalog['stale_keys'])}",
                f"- Stale unused candidates: {len(catalog['stale_unused_candidates'])}",
                f"- Stale referenced keys: {len(catalog['stale_referenced_keys'])}",
                f"- Unused candidates: {len(catalog['unused_candidates'])}",
            ]
        )

        if catalog["seeded_entries"]:
            lines.append(f"- Seeded locale entries: {len(catalog['seeded_entries'])}")
            for seeded_entry in catalog["seeded_entries"][:20]:
                lines.append(
                    f"  - `{seeded_entry['key']}` -> `{seeded_entry['locale']}`"
                )
            if len(catalog["seeded_entries"]) > 20:
                lines.append("  - ...")

        if catalog["pruned_keys"]:
            lines.append(f"- Pruned keys: {len(catalog['pruned_keys'])}")
            for key in catalog["pruned_keys"][:20]:
                lines.append(f"  - `{key}`")
            if len(catalog["pruned_keys"]) > 20:
                lines.append("  - ...")

        if catalog["normalized_stale_keys"]:
            lines.append(
                f"- Normalized stale keys: {len(catalog['normalized_stale_keys'])}"
            )
            for key in catalog["normalized_stale_keys"][:20]:
                lines.append(f"  - `{key}`")
            if len(catalog["normalized_stale_keys"]) > 20:
                lines.append("  - ...")

        if catalog["incomplete_keys"]:
            lines.append("")
            lines.append("### Incomplete Keys")
            for entry in catalog["incomplete_keys"][:40]:
                fragments: list[str] = []
                if entry["missing_locales"]:
                    fragments.append(f"missing `{', '.join(entry['missing_locales'])}`")
                if entry["pending_locales"]:
                    pending = ", ".join(
                        f"{locale} ({'/'.join(states)})"
                        for locale, states in entry["pending_locales"].items()
                    )
                    fragments.append(f"pending `{pending}`")
                lines.append(f"- `{entry['key']}`: {', '.join(fragments)}")
            if len(catalog["incomplete_keys"]) > 40:
                lines.append("- ...")

        if catalog["unused_candidates"]:
            lines.append("")
            lines.append("### Unused Candidates")
            for entry in catalog["unused_candidates"][:40]:
                suffix = " (stale)" if entry["is_stale"] else ""
                lines.append(f"- `{entry['key']}`{suffix}")
            if len(catalog["unused_candidates"]) > 40:
                lines.append("- ...")

        if catalog["stale_referenced_keys"]:
            lines.append("")
            lines.append("### Stale Referenced Keys")
            for entry in catalog["stale_referenced_keys"][:40]:
                lines.append(f"- `{entry['key']}`")
                for reference in entry["references"][:10]:
                    lines.append(f"  - `{reference}`")
                if len(entry["references"]) > 10:
                    lines.append("  - ...")
            if len(catalog["stale_referenced_keys"]) > 40:
                lines.append("- ...")

    return "\n".join(lines) + "\n"


def main() -> int:
    arguments = parse_arguments()
    project_root = Path(arguments.project_root).resolve()
    required_locales_override = parse_required_locales(arguments.required_locales)
    try:
        source_roots = resolve_source_roots(project_root, arguments.source_root)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1

    try:
        catalogs = discover_catalogs(project_root, arguments.catalog)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1

    catalog_data: dict[Path, dict[str, Any]] = {}
    for catalog_path in catalogs:
        try:
            catalog_data[catalog_path] = load_catalog(catalog_path)
        except ValueError as error:
            print(str(error), file=sys.stderr)
            return 1

    reference_map = build_literal_reference_map(
        project_root,
        collect_catalog_keys(catalog_data),
        source_roots=source_roots,
    )

    catalog_reports = [
        audit_catalog(
            project_root=project_root,
            path=catalog_path,
            catalog=catalog_data[catalog_path],
            reference_map=reference_map,
            required_locales_override=required_locales_override,
            prune_unused=arguments.prune_unused,
            prune_stale_unused=arguments.prune_stale_unused,
            normalize_stale_referenced=arguments.normalize_stale_referenced,
            seed_missing_locales=arguments.seed_missing_locales,
            apply_changes=arguments.apply,
            source_roots=source_roots,
        )
        for catalog_path in catalogs
    ]

    report = {
        "project_root": str(project_root),
        "source_roots": [
            render_report_path(project_root, root)
            for root in source_roots or [project_root]
        ],
        "apply": arguments.apply,
        "planned_changes": any(
            catalog_report["seeded_entries"]
            or catalog_report["pruned_keys"]
            or catalog_report["normalized_stale_keys"]
            for catalog_report in catalog_reports
        ),
        "catalogs": catalog_reports,
    }

    if arguments.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_markdown(report), end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
