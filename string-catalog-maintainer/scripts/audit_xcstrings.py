#!/usr/bin/env python3
"""Audit and repair Xcode string catalogs."""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from dataclasses import dataclass
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
PRINTF_PLACEHOLDER_PATTERN = re.compile(
    r"%(?!%)"
    r"(?:\d+\$)?"
    r"[-+#0 ]*"
    r"(?:\d+|\*)?"
    r"(?:\.(?:\d+|\*))?"
    r"(?:hh|h|ll|l|z|t|j)?"
    r"[@aAcCdiouxXfFeEgGsSp]"
)
NAMED_PLACEHOLDER_PATTERN = re.compile(r"\$\{[A-Za-z0-9_.-]+\}")
STALE_MARKER_PATTERN = re.compile(r'"extractionState"\s*:\s*"stale"')
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


@dataclass(frozen=True)
class JSONFormatting:
    indent: int | str | None
    newline: str
    trailing_newline: bool


@dataclass(frozen=True)
class LocalizationPayload:
    kind: str
    path: tuple[str | int, ...]
    payload: dict[str, Any]


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
        "--translation-patch",
        help=(
            "Path to a JSON translation patch, '-' for stdin, or inline JSON. "
            "Accepted shapes are a list of translation entries or an object with "
            "a 'translations' list."
        ),
    )
    parser.add_argument(
        "--apply-translations",
        action="store_true",
        help=(
            "Apply entries from --translation-patch after placeholder validation. "
            "Without this flag, the patch is validated as a dry run."
        ),
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


def read_raw_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", newline="")


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
        return json.loads(read_raw_text(path))
    except json.JSONDecodeError as error:
        raise ValueError(f"Failed to parse {path}: {error}") from error


def detect_indentation(raw_text: str) -> int | str | None:
    if "\n" not in raw_text and "\r" not in raw_text:
        return None

    for line in raw_text.splitlines():
        stripped = line.lstrip(" \t")
        if not stripped:
            continue
        prefix = line[: len(line) - len(stripped)]
        if not prefix:
            continue
        if set(prefix) == {" "}:
            return len(prefix)
        return prefix

    return 2


def detect_json_formatting(raw_text: str) -> JSONFormatting:
    newline = "\r\n" if "\r\n" in raw_text else "\n"
    trailing_newline = raw_text.endswith(("\n", "\r\n"))
    return JSONFormatting(
        indent=detect_indentation(raw_text),
        newline=newline,
        trailing_newline=trailing_newline,
    )


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


def extract_placeholders(text: str) -> list[str]:
    matches: list[tuple[int, str]] = []
    matches.extend((match.start(), match.group(0)) for match in NAMED_PLACEHOLDER_PATTERN.finditer(text))
    matches.extend((match.start(), match.group(0)) for match in PRINTF_PLACEHOLDER_PATTERN.finditer(text))
    return [placeholder for _, placeholder in sorted(matches)]


def placeholder_signature(values: list[str]) -> dict[str, int]:
    placeholders: Counter[str] = Counter()
    for value in values:
        placeholders.update(extract_placeholders(value))
    return dict(sorted(placeholders.items()))


def payload_values(kind: str, payload: dict[str, Any]) -> list[str]:
    if kind == "stringUnit":
        value = payload.get("value")
        return [value] if isinstance(value, str) else []
    values = payload.get("values")
    if isinstance(values, list):
        return [value for value in values if isinstance(value, str)]
    return []


def payload_is_empty(kind: str, payload: dict[str, Any]) -> bool:
    if kind == "stringUnit":
        return payload.get("value") in (None, "")
    values = payload.get("values")
    return not isinstance(values, list) or not values or any(value in (None, "") for value in values)


def serialize_payload_values(kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    if kind == "stringUnit":
        return {"value": payload.get("value")}
    return {"values": copy.deepcopy(payload.get("values", []))}


def format_payload_path(path: tuple[str | int, ...]) -> str:
    rendered = ""
    for part in path:
        if isinstance(part, int):
            rendered += f"[{part}]"
        elif rendered:
            rendered += f".{part}"
        else:
            rendered = part
    return rendered


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


def build_literal_reference_maps(
    project_root: Path,
    keys: set[str],
    source_roots: list[Path] | None = None,
) -> dict[str, dict[str, list[str]]]:
    strong_reference_map = {key: [] for key in keys}
    weak_reference_map = {key: [] for key in keys}
    for source_file in collect_source_files(project_root, source_roots):
        try:
            content = source_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        strong_matches: set[str] = set()
        weak_matches: set[str] = set()
        for match in STRING_LITERAL_PATTERN.finditer(content):
            raw_literal = match.group(1)
            normalized_literal = normalize_string_literal(raw_literal)
            if normalized_literal in keys:
                strong_matches.add(normalized_literal)
            weak_matches.update(expand_literal_variants(raw_literal) - {normalized_literal})
        relative_path = render_report_path(project_root, source_file)
        for key in strong_matches & keys:
            strong_reference_map[key].append(relative_path)
        for key in (weak_matches & keys) - strong_matches:
            weak_reference_map[key].append(relative_path)
    return {
        "strong": strong_reference_map,
        "weak": weak_reference_map,
    }


def build_literal_reference_map(
    project_root: Path,
    keys: set[str],
    source_roots: list[Path] | None = None,
) -> dict[str, list[str]]:
    maps = build_literal_reference_maps(project_root, keys, source_roots)
    return {
        key: sorted(set(maps["strong"].get(key, []) + maps["weak"].get(key, [])))
        for key in keys
    }


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


def collect_project_locales(catalogs: dict[Path, dict[str, Any]]) -> list[str]:
    locales: list[str] = []
    for catalog in catalogs.values():
        source_language = catalog.get("sourceLanguage", "en")
        for locale in collect_catalog_locales(catalog, source_language):
            if locale not in locales:
                locales.append(locale)
    return locales


def walk_localization_payloads(
    node: Any,
    path: tuple[str | int, ...] = (),
) -> list[LocalizationPayload]:
    payloads: list[LocalizationPayload] = []
    if isinstance(node, dict):
        string_unit = node.get("stringUnit")
        if isinstance(string_unit, dict):
            payloads.append(LocalizationPayload("stringUnit", (*path, "stringUnit"), string_unit))
        string_set = node.get("stringSet")
        if isinstance(string_set, dict):
            payloads.append(LocalizationPayload("stringSet", (*path, "stringSet"), string_set))
        for key, value in node.items():
            payloads.extend(walk_localization_payloads(value, (*path, key)))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            payloads.extend(walk_localization_payloads(value, (*path, index)))
    return payloads


def collect_pending_states(localization: dict[str, Any]) -> list[str]:
    states: list[str] = []
    for localization_payload in walk_localization_payloads(localization):
        if localization_payload.kind == "stringUnit":
            state = localization_payload.payload.get("state", "missing-state")
            if localization_payload.payload.get("value") in (None, ""):
                state = "missing-value"
        else:
            state = localization_payload.payload.get("state", "missing-state")
            if not localization_payload.payload.get("values"):
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


def get_node_at_path(root: Any, path: tuple[str | int, ...]) -> Any | None:
    node = root
    for part in path:
        if isinstance(part, int):
            if not isinstance(node, list) or part >= len(node):
                return None
            node = node[part]
            continue
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def normalize_patch_path(raw_path: Any) -> tuple[str | int, ...] | None:
    if isinstance(raw_path, list):
        normalized: list[str | int] = []
        for part in raw_path:
            if isinstance(part, (str, int)):
                normalized.append(part)
            else:
                return None
        return tuple(normalized)
    if isinstance(raw_path, str) and raw_path:
        return tuple(part for part in raw_path.split(".") if part)
    return None


def source_localization_for_entry(
    key: str,
    entry: dict[str, Any],
    source_language: str,
) -> dict[str, Any]:
    localizations = entry.get("localizations", {})
    if source_language in localizations:
        return localizations[source_language]
    if localizations:
        return next(iter(localizations.values()))
    return {
        "stringUnit": {
            "state": "translated",
            "value": key,
        }
    }


def matching_source_payload(
    key: str,
    entry: dict[str, Any],
    source_language: str,
    path: tuple[str | int, ...],
) -> LocalizationPayload | None:
    source_localization = source_localization_for_entry(key, entry, source_language)
    source_payload = get_node_at_path(source_localization, path)
    if isinstance(source_payload, dict):
        kind = "stringSet" if path and path[-1] == "stringSet" else "stringUnit"
        if "values" in source_payload:
            kind = "stringSet"
        return LocalizationPayload(kind, path, source_payload)
    return None


def build_translation_task(
    catalog_path: str,
    key: str,
    locale: str,
    source_language: str,
    payload: LocalizationPayload,
    source_payload: LocalizationPayload | None,
    reasons: list[str],
) -> dict[str, Any] | None:
    if not reasons:
        return None
    source_payload_data = source_payload.payload if source_payload else {}
    source_values = payload_values(payload.kind, source_payload_data)
    current_values = payload_values(payload.kind, payload.payload)
    return {
        "catalog": catalog_path,
        "key": key,
        "locale": locale,
        "path": list(payload.path),
        "path_string": format_payload_path(payload.path),
        "kind": payload.kind,
        "reasons": reasons,
        "state": payload.payload.get("state", "missing-state"),
        "source_language": source_language,
        "source": serialize_payload_values(payload.kind, source_payload_data),
        "current": serialize_payload_values(payload.kind, payload.payload),
        "required_placeholders": placeholder_signature(source_values),
        "current_placeholders": placeholder_signature(current_values),
    }


def collect_translation_tasks_for_localization(
    catalog_path: str,
    key: str,
    entry: dict[str, Any],
    locale: str,
    localization: dict[str, Any],
    source_language: str,
    extra_reasons: list[str] | None = None,
) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for payload in walk_localization_payloads(localization):
        source_payload = matching_source_payload(key, entry, source_language, payload.path)
        reasons = list(extra_reasons or [])
        state = payload.payload.get("state", "missing-state")
        if state != "translated":
            reasons.append(f"state-{state}")
        if payload_is_empty(payload.kind, payload.payload):
            reasons.append("missing-value")
        if locale != source_language and source_payload is not None:
            source_values = payload_values(payload.kind, source_payload.payload)
            current_values = payload_values(payload.kind, payload.payload)
            if source_values and source_values == current_values:
                reasons.append("source-copy")
        task = build_translation_task(
            catalog_path=catalog_path,
            key=key,
            locale=locale,
            source_language=source_language,
            payload=payload,
            source_payload=source_payload,
            reasons=list(dict.fromkeys(reasons)),
        )
        if task is not None:
            tasks.append(task)
    return tasks


def collect_missing_locale_translation_tasks(
    catalog_path: str,
    key: str,
    entry: dict[str, Any],
    locale: str,
    source_language: str,
) -> list[dict[str, Any]]:
    source_localization = source_localization_for_entry(key, entry, source_language)
    source_payloads = walk_localization_payloads(source_localization)
    if not source_payloads:
        source_payloads = [
            LocalizationPayload(
                "stringUnit",
                ("stringUnit",),
                {
                    "state": "translated",
                    "value": key,
                },
            )
        ]
    tasks: list[dict[str, Any]] = []
    for source_payload in source_payloads:
        missing_payload = copy.deepcopy(source_payload.payload)
        missing_payload["state"] = "new"
        task = build_translation_task(
            catalog_path=catalog_path,
            key=key,
            locale=locale,
            source_language=source_language,
            payload=LocalizationPayload(source_payload.kind, source_payload.path, missing_payload),
            source_payload=source_payload,
            reasons=["missing-locale"],
        )
        if task is not None:
            tasks.append(task)
    return tasks


def load_translation_patch(raw_patch: str | None) -> list[dict[str, Any]]:
    if raw_patch is None:
        return []
    if raw_patch == "-":
        raw_content = sys.stdin.read()
    else:
        patch_path = Path(raw_patch)
        if patch_path.exists():
            raw_content = patch_path.read_text(encoding="utf-8")
        else:
            raw_content = raw_patch
    data = json.loads(raw_content)
    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict):
        entries = data.get("translations", data.get("translation_tasks", []))
    else:
        raise ValueError("Translation patch must be a list or an object with a translations list.")
    if not isinstance(entries, list):
        raise ValueError("Translation patch entries must be a list.")
    return [entry for entry in entries if isinstance(entry, dict)]


def group_translation_patches(
    project_root: Path,
    catalogs: list[Path],
    patches: list[dict[str, Any]],
) -> tuple[dict[Path, list[dict[str, Any]]], list[str]]:
    grouped = {catalog: [] for catalog in catalogs}
    errors: list[str] = []
    catalog_set = set(catalogs)
    for index, patch in enumerate(patches):
        raw_catalog = patch.get("catalog")
        if raw_catalog is None and len(catalogs) == 1:
            catalog_path = catalogs[0]
        elif isinstance(raw_catalog, str):
            catalog_path = resolve_catalog_path(project_root, raw_catalog)
        else:
            errors.append(f"patch[{index}] missing catalog")
            continue
        if catalog_path not in catalog_set:
            errors.append(f"patch[{index}] catalog is not selected: {catalog_path}")
            continue
        grouped[catalog_path].append(patch)
    return grouped, errors


def proposed_patch_values(kind: str, patch: dict[str, Any]) -> tuple[list[str], str | None]:
    if kind == "stringUnit":
        value = patch.get("value")
        if not isinstance(value, str) or value == "":
            return [], "stringUnit patches require a non-empty string 'value'"
        return [value], None
    values = patch.get("values")
    if not isinstance(values, list) or not values or not all(isinstance(value, str) and value for value in values):
        return [], "stringSet patches require a non-empty string list 'values'"
    return values, None


def validate_placeholder_compatibility(source_values: list[str], target_values: list[str]) -> str | None:
    source_signature = placeholder_signature(source_values)
    target_signature = placeholder_signature(target_values)
    if source_signature != target_signature:
        return (
            "placeholder mismatch: "
            f"expected {source_signature or '{}'}, got {target_signature or '{}'}"
        )
    return None


def apply_translation_patches(
    project_root: Path,
    catalog_path: Path,
    catalog: dict[str, Any],
    patches: list[dict[str, Any]],
    apply_changes: bool,
) -> dict[str, Any]:
    string_table = catalog.get("strings", {})
    source_language = catalog.get("sourceLanguage", "en")
    errors: list[str] = []
    operations: list[dict[str, Any]] = []

    for index, patch in enumerate(patches):
        key = patch.get("key")
        locale = patch.get("locale")
        path = normalize_patch_path(patch.get("path"))
        if not isinstance(key, str) or key not in string_table:
            errors.append(f"patch[{index}] key not found: {key!r}")
            continue
        if not isinstance(locale, str) or not locale:
            errors.append(f"patch[{index}] missing locale")
            continue
        if path is None:
            errors.append(f"patch[{index}] missing or invalid path")
            continue

        entry = string_table[key]
        localizations = entry.get("localizations", {})
        target_localization = localizations.get(locale)
        created_locale = target_localization is None
        if created_locale:
            target_localization = build_seed_localization(key, entry, source_language)
        if target_localization is None:
            errors.append(f"patch[{index}] could not build localization for {key!r} {locale!r}")
            continue

        target_payload = get_node_at_path(target_localization, path)
        if not isinstance(target_payload, dict):
            errors.append(f"patch[{index}] payload path not found: {format_payload_path(path)}")
            continue
        kind = "stringSet" if "values" in target_payload else "stringUnit"

        source_payload = matching_source_payload(key, entry, source_language, path)
        if source_payload is None:
            errors.append(f"patch[{index}] source payload path not found: {format_payload_path(path)}")
            continue
        source_values = payload_values(kind, source_payload.payload)
        target_values, value_error = proposed_patch_values(kind, patch)
        if value_error is not None:
            errors.append(f"patch[{index}] {value_error}")
            continue
        placeholder_error = validate_placeholder_compatibility(source_values, target_values)
        if placeholder_error is not None:
            errors.append(f"patch[{index}] {placeholder_error}")
            continue

        operations.append(
            {
                "index": index,
                "key": key,
                "locale": locale,
                "path": path,
                "kind": kind,
                "values": target_values,
                "created_locale": created_locale,
            }
        )

    applied_entries: list[dict[str, Any]] = []
    if not errors and apply_changes:
        for operation in operations:
            entry = string_table[operation["key"]]
            localizations = entry.setdefault("localizations", {})
            target_localization = localizations.get(operation["locale"])
            if target_localization is None:
                target_localization = build_seed_localization(
                    operation["key"],
                    entry,
                    source_language,
                )
                localizations[operation["locale"]] = target_localization
            target_payload = get_node_at_path(target_localization, operation["path"])
            if not isinstance(target_payload, dict):
                errors.append(
                    f"patch[{operation['index']}] payload disappeared before apply: "
                    f"{format_payload_path(operation['path'])}"
                )
                break
            if operation["kind"] == "stringUnit":
                target_payload["value"] = operation["values"][0]
            else:
                target_payload["values"] = operation["values"]
            target_payload["state"] = "translated"
            applied_entries.append(
                {
                    "key": operation["key"],
                    "locale": operation["locale"],
                    "path": list(operation["path"]),
                    "path_string": format_payload_path(operation["path"]),
                    "kind": operation["kind"],
                    "created_locale": operation["created_locale"],
                }
            )

    validated_entries = [
        {
            "key": operation["key"],
            "locale": operation["locale"],
            "path": list(operation["path"]),
            "path_string": format_payload_path(operation["path"]),
            "kind": operation["kind"],
            "created_locale": operation["created_locale"],
        }
        for operation in operations
    ]

    return {
        "validated_entries": validated_entries,
        "applied_entries": applied_entries,
        "errors": errors,
        "applied": bool(applied_entries),
        "dry_run_changes": bool(operations) and not apply_changes and not errors,
        "patch_count": len(patches),
    }


def write_catalog(path: Path, catalog: dict[str, Any]) -> None:
    formatting = detect_json_formatting(read_raw_text(path))
    serialized = json.dumps(
        catalog,
        ensure_ascii=False,
        indent=formatting.indent,
    )
    if formatting.newline != "\n":
        serialized = serialized.replace("\n", formatting.newline)
    if formatting.trailing_newline:
        serialized += formatting.newline
    path.write_text(serialized, encoding="utf-8", newline="")


def audit_catalog(
    project_root: Path,
    path: Path,
    catalog: dict[str, Any],
    reference_maps: dict[str, dict[str, list[str]]],
    required_locales_override: list[str] | None,
    inferred_required_locales: list[str] | None,
    prune_unused: bool,
    prune_stale_unused: bool,
    normalize_stale_referenced: bool,
    seed_missing_locales: bool,
    apply_changes: bool,
    translation_patches: list[dict[str, Any]],
    apply_translations: bool,
    source_roots: list[Path] | None,
    raw_stale_marker_count: int,
) -> dict[str, Any]:
    catalog_report_path = render_report_path(project_root, path)
    source_language = catalog.get("sourceLanguage", "en")
    required_locales = (
        required_locales_override
        or inferred_required_locales
        or collect_catalog_locales(catalog, source_language)
    )
    if source_language not in required_locales:
        required_locales = [source_language, *required_locales]

    translation_patch_result = apply_translation_patches(
        project_root=project_root,
        catalog_path=path,
        catalog=catalog,
        patches=translation_patches,
        apply_changes=apply_translations,
    )

    string_table = catalog.get("strings", {})
    incomplete_keys: list[dict[str, Any]] = []
    translation_tasks: list[dict[str, Any]] = []
    unused_candidates: list[dict[str, Any]] = []
    seeded_entries: list[dict[str, Any]] = []
    pruned_keys: list[str] = []
    stale_keys: list[str] = []
    stale_unused_candidates: list[dict[str, Any]] = []
    stale_referenced_keys: list[dict[str, Any]] = []
    stale_strong_referenced_keys: list[dict[str, Any]] = []
    stale_weak_referenced_keys: list[dict[str, Any]] = []
    normalized_stale_keys: list[str] = []
    strong_reference_map = reference_maps.get("strong", {})
    weak_reference_map = reference_maps.get("weak", {})

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
                            seeded_entries.append(
                                {
                                    "key": key,
                                    "locale": locale,
                                }
                            )
                            pending_locales[locale] = ["new"]
                            if apply_changes:
                                localizations[locale] = seeded_localization
                                localization = seeded_localization
                            else:
                                translation_tasks.extend(
                                    collect_translation_tasks_for_localization(
                                        catalog_path=catalog_report_path,
                                        key=key,
                                        entry=entry,
                                        locale=locale,
                                        localization=seeded_localization,
                                        source_language=source_language,
                                        extra_reasons=["seeded-locale"],
                                    )
                                )
                                continue
                    else:
                        translation_tasks.extend(
                            collect_missing_locale_translation_tasks(
                                catalog_path=catalog_report_path,
                                key=key,
                                entry=entry,
                                locale=locale,
                                source_language=source_language,
                            )
                        )
                    missing_locales.append(locale)
                    if localization is None:
                        continue

                states = collect_pending_states(localization)
                if states:
                    pending_locales[locale] = states
                translation_tasks.extend(
                    collect_translation_tasks_for_localization(
                        catalog_path=catalog_report_path,
                        key=key,
                        entry=entry,
                        locale=locale,
                        localization=localization,
                        source_language=source_language,
                    )
                )

            if missing_locales or pending_locales:
                incomplete_keys.append(
                    {
                        "key": key,
                        "missing_locales": missing_locales,
                        "pending_locales": pending_locales,
                    }
                )

        strong_references = strong_reference_map.get(key, [])
        weak_references = weak_reference_map.get(key, [])
        references = sorted(set(strong_references + weak_references))
        if is_stale:
            if strong_references:
                stale_strong_referenced_keys.append(
                    {
                        "key": key,
                        "references": strong_references,
                    }
                )
                stale_referenced_keys.append(
                    {
                        "key": key,
                        "references": references,
                        "reference_strength": "strong",
                    }
                )
                if normalize_stale_referenced:
                    normalized_stale_keys.append(key)
                    if apply_changes:
                        entry.pop("extractionState", None)
            elif weak_references:
                stale_weak_referenced_keys.append(
                    {
                        "key": key,
                        "references": weak_references,
                    }
                )
                stale_referenced_keys.append(
                    {
                        "key": key,
                        "references": references,
                        "reference_strength": "weak",
                    }
                )
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

    if (prune_unused or prune_stale_unused) and apply_changes:
        for key in pruned_keys:
            string_table.pop(key, None)

    catalog_mutated = bool(
        (seeded_entries or pruned_keys or normalized_stale_keys) and apply_changes
    )
    translation_mutated = bool(translation_patch_result["applied_entries"])
    mutated = catalog_mutated or translation_mutated
    if mutated and not translation_patch_result["errors"] and (apply_changes or translation_mutated):
        write_catalog(path, catalog)

    return {
        "path": catalog_report_path,
        "source_roots": [
            render_report_path(project_root, root)
            for root in source_roots or [project_root]
        ],
        "source_language": source_language,
        "required_locales": required_locales,
        "key_count": len(string_table),
        "incomplete_keys": incomplete_keys,
        "translation_tasks": translation_tasks,
        "stale_keys": stale_keys,
        "stale_key_count": len(stale_keys),
        "raw_stale_marker_count": raw_stale_marker_count,
        "stale_marker_count_matches": raw_stale_marker_count == len(stale_keys),
        "stale_unused_candidates": stale_unused_candidates,
        "stale_referenced_keys": stale_referenced_keys,
        "stale_strong_referenced_keys": stale_strong_referenced_keys,
        "stale_weak_referenced_keys": stale_weak_referenced_keys,
        "unused_candidates": unused_candidates,
        "seeded_entries": seeded_entries,
        "pruned_keys": pruned_keys,
        "normalized_stale_keys": normalized_stale_keys,
        "translation_patch": translation_patch_result,
        "applied": catalog_mutated or translation_mutated,
        "dry_run_changes": (
            (bool(seeded_entries or pruned_keys or normalized_stale_keys) and not apply_changes)
            or translation_patch_result["dry_run_changes"]
        ),
    }


def format_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# XCStrings Audit",
        "",
        f"- Project root: `{report['project_root']}`",
        f"- Catalog count: {len(report['catalogs'])}",
    ]
    if report["planned_changes"] and not report["apply"] and not report.get("apply_translations"):
        lines.append("- Mutations are a dry run because `--apply` was not set.")
    if report["apply"]:
        lines.append("- Catalog maintenance mutations were written in place.")
    if report.get("apply_translations"):
        lines.append("- Translation patch mutations were written in place when validation passed.")
    if report.get("translation_patch_errors"):
        lines.append("- Translation patch grouping errors:")
        for error in report["translation_patch_errors"]:
            lines.append(f"  - {error}")

    for catalog in report["catalogs"]:
        translation_patch = catalog["translation_patch"]
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
                f"- Translation tasks: {len(catalog['translation_tasks'])}",
                f"- Stale keys: {catalog['stale_key_count']} (raw markers: {catalog['raw_stale_marker_count']})",
                f"- Stale unused candidates: {len(catalog['stale_unused_candidates'])}",
                f"- Stale strong references: {len(catalog['stale_strong_referenced_keys'])}",
                f"- Stale weak references: {len(catalog['stale_weak_referenced_keys'])}",
                f"- Unused candidates: {len(catalog['unused_candidates'])}",
            ]
        )
        if not catalog["stale_marker_count_matches"]:
            lines.append("- Stale marker mismatch: raw marker count differs from parsed stale keys.")

        if translation_patch["patch_count"]:
            lines.append(f"- Translation patch entries: {translation_patch['patch_count']}")
            lines.append(f"- Translation patch validated: {len(translation_patch['validated_entries'])}")
            lines.append(f"- Translation patch applied: {len(translation_patch['applied_entries'])}")
            if translation_patch["errors"]:
                lines.append("- Translation patch errors:")
                for error in translation_patch["errors"][:20]:
                    lines.append(f"  - {error}")
                if len(translation_patch["errors"]) > 20:
                    lines.append("  - ...")

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

        if catalog["translation_tasks"]:
            lines.append("")
            lines.append("### Translation Tasks")
            for task in catalog["translation_tasks"][:40]:
                reasons = ", ".join(task["reasons"])
                lines.append(
                    f"- `{task['key']}` -> `{task['locale']}` "
                    f"`{task['path_string']}`: {reasons}"
                )
            if len(catalog["translation_tasks"]) > 40:
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
                lines.append(f"- `{entry['key']}` ({entry['reference_strength']})")
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

    try:
        translation_patches = load_translation_patch(arguments.translation_patch)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Failed to load translation patch: {error}", file=sys.stderr)
        return 1

    grouped_translation_patches, translation_patch_errors = group_translation_patches(
        project_root,
        catalogs,
        translation_patches,
    )
    inferred_required_locales = (
        None if required_locales_override is not None else collect_project_locales(catalog_data)
    )

    reference_maps = build_literal_reference_maps(
        project_root,
        collect_catalog_keys(catalog_data),
        source_roots=source_roots,
    )

    catalog_reports = [
        audit_catalog(
            project_root=project_root,
            path=catalog_path,
            catalog=catalog_data[catalog_path],
            reference_maps=reference_maps,
            required_locales_override=required_locales_override,
            inferred_required_locales=inferred_required_locales,
            prune_unused=arguments.prune_unused,
            prune_stale_unused=arguments.prune_stale_unused,
            normalize_stale_referenced=arguments.normalize_stale_referenced,
            seed_missing_locales=arguments.seed_missing_locales,
            apply_changes=arguments.apply,
            translation_patches=grouped_translation_patches[catalog_path],
            apply_translations=arguments.apply_translations,
            source_roots=source_roots,
            raw_stale_marker_count=len(STALE_MARKER_PATTERN.findall(read_raw_text(catalog_path))),
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
        "apply_translations": arguments.apply_translations,
        "translation_patch_errors": translation_patch_errors,
        "planned_changes": any(
            catalog_report["seeded_entries"]
            or catalog_report["pruned_keys"]
            or catalog_report["normalized_stale_keys"]
            or catalog_report["translation_patch"]["validated_entries"]
            for catalog_report in catalog_reports
        ),
        "catalogs": catalog_reports,
    }

    if arguments.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_markdown(report), end="")

    has_translation_errors = bool(translation_patch_errors) or any(
        catalog_report["translation_patch"]["errors"]
        for catalog_report in catalog_reports
    )
    return 1 if has_translation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
