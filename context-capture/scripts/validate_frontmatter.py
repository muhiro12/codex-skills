#!/usr/bin/env python3
"""Validate context archive Markdown frontmatter."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path
from typing import Any

RAW_REQUIRED = {
    "id",
    "record_type",
    "source",
    "scope",
    "capture_method",
    "captured_at",
    "occurred_at",
    "people",
    "projects",
    "topics",
    "sensitivity",
    "cross_project",
    "attachments",
}

DERIVED_REQUIRED = {"id", "record_type", "source_refs", "created_at"}

ALLOWED_RECORD_TYPES = {
    "raw",
    "derived-summary",
    "derived-timeline",
    "derived-decision",
    "derived-note",
    "derived-context",
    "derived-stance",
    "derived-analysis",
}

ALLOWED_SOURCES = {
    "slack",
    "backlog",
    "github",
    "chatgpt",
    "transcript",
    "manual",
    "email",
    "other",
}

ALLOWED_SCOPES = {"private", "work", "shared-safe"}
ALLOWED_CAPTURE_METHODS = {"paste", "manual", "copy", "transcript", "import", "other"}
ALLOWED_SENSITIVITY = {
    "public",
    "internal",
    "masked-work",
    "private",
    "confidential",
    "restricted",
    "unknown",
}

ALLOWED_USE_POLICIES = {
    "internal-reference-only",
    "private-reference-only",
    "work-internal-only",
    "do-not-share-externally",
    "rephrase-before-direct-discussion",
    "may-share-after-redaction",
    "unknown",
}

RECOMMENDED_COMMON = {
    "observer_perspective",
    "coverage_limitations",
    "use_policies",
}


def parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if value in {"null", "Null", "NULL", "~"}:
        return None
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if value == "[]":
        return []
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(item) for item in inner.split(",")]
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def parse_simple_yaml_mapping(frontmatter: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    lines = frontmatter.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        if line.startswith((" ", "\t")) or ":" not in line:
            raise ValueError(f"unsupported YAML line: {line}")

        key, raw_value = line.split(":", 1)
        key = key.strip()
        if not key:
            raise ValueError("empty YAML key")

        if raw_value.strip():
            data[key] = parse_scalar(raw_value)
            index += 1
            continue

        items: list[Any] = []
        index += 1
        while index < len(lines):
            item_line = lines[index]
            item_stripped = item_line.strip()
            if not item_stripped or item_stripped.startswith("#"):
                index += 1
                continue
            if not item_line.startswith((" ", "\t")):
                break
            if not item_stripped.startswith("- "):
                raise ValueError(f"unsupported nested YAML line for {key}: {item_line}")
            items.append(parse_scalar(item_stripped[2:]))
            index += 1
        data[key] = items
    return data


def load_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---(?:\n|$)", text, re.DOTALL)
    if not match:
        raise ValueError("missing YAML frontmatter block")

    data = parse_simple_yaml_mapping(match.group(1))
    if not isinstance(data, dict):
        raise ValueError("frontmatter must be a YAML mapping")
    return data


def require_keys(data: dict[str, Any], keys: set[str]) -> list[str]:
    return [f"missing required key: {key}" for key in sorted(keys - set(data))]


def validate_string(data: dict[str, Any], key: str, errors: list[str]) -> None:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{key} must be a non-empty string")


def validate_array(data: dict[str, Any], key: str, errors: list[str]) -> None:
    value = data.get(key)
    if not isinstance(value, list):
        errors.append(f"{key} must be an array")
        return
    if any(not isinstance(item, str) for item in value):
        errors.append(f"{key} must contain only strings")


def validate_optional_string(data: dict[str, Any], key: str, errors: list[str]) -> None:
    if key not in data:
        return
    validate_string(data, key, errors)


def validate_optional_array(
    data: dict[str, Any],
    key: str,
    errors: list[str],
    allowed_items: set[str] | None = None,
) -> None:
    if key not in data:
        return
    validate_array(data, key, errors)
    value = data.get(key)
    if not isinstance(value, list) or allowed_items is None:
        return
    invalid = sorted({item for item in value if item not in allowed_items})
    if invalid:
        errors.append(f"{key} contains unsupported values: {', '.join(invalid)}")


def validate_timestamp(data: dict[str, Any], key: str, errors: list[str], allow_null: bool) -> None:
    value = data.get(key)
    if value is None and allow_null:
        return
    if isinstance(value, dt.datetime):
        return
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{key} must be an ISO timestamp string")
        return
    try:
        dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{key} must be parseable as an ISO timestamp")


def validate_optional_timestamp(
    data: dict[str, Any],
    key: str,
    errors: list[str],
    allow_null: bool,
) -> None:
    if key not in data:
        return
    validate_timestamp(data, key, errors, allow_null=allow_null)


def validate_allowed(data: dict[str, Any], key: str, allowed: set[str], errors: list[str]) -> None:
    value = data.get(key)
    if value not in allowed:
        errors.append(f"{key} must be one of: {', '.join(sorted(allowed))}")


def validate_raw(data: dict[str, Any]) -> list[str]:
    errors = require_keys(data, RAW_REQUIRED)
    for key in ("id",):
        validate_string(data, key, errors)
    validate_allowed(data, "record_type", {"raw"}, errors)
    validate_allowed(data, "source", ALLOWED_SOURCES, errors)
    validate_allowed(data, "scope", ALLOWED_SCOPES, errors)
    validate_allowed(data, "capture_method", ALLOWED_CAPTURE_METHODS, errors)
    validate_allowed(data, "sensitivity", ALLOWED_SENSITIVITY, errors)
    validate_timestamp(data, "captured_at", errors, allow_null=False)
    validate_timestamp(data, "occurred_at", errors, allow_null=True)
    for key in ("people", "projects", "topics", "attachments"):
        validate_array(data, key, errors)
    if not isinstance(data.get("cross_project"), bool):
        errors.append("cross_project must be a boolean")
    validate_optional_string(data, "observer_perspective", errors)
    validate_optional_array(data, "coverage_limitations", errors)
    validate_optional_array(data, "use_policies", errors, ALLOWED_USE_POLICIES)
    return errors


def validate_derived(data: dict[str, Any]) -> list[str]:
    errors = require_keys(data, DERIVED_REQUIRED)
    validate_string(data, "id", errors)
    validate_allowed(data, "record_type", ALLOWED_RECORD_TYPES - {"raw"}, errors)
    validate_array(data, "source_refs", errors)
    if isinstance(data.get("source_refs"), list) and not data["source_refs"]:
        errors.append("source_refs must contain at least one path")
    validate_timestamp(data, "created_at", errors, allow_null=False)
    validate_optional_string(data, "observer_perspective", errors)
    validate_optional_array(data, "coverage_limitations", errors)
    validate_optional_array(data, "use_policies", errors, ALLOWED_USE_POLICIES)
    validate_optional_timestamp(data, "last_updated", errors, allow_null=False)
    validate_optional_timestamp(data, "review_due", errors, allow_null=True)
    validate_optional_array(data, "supersedes", errors)
    validate_optional_string(data, "revision_note", errors)
    validate_optional_string(data, "analysis_kind", errors)
    return errors


def collect_warnings(data: dict[str, Any]) -> list[str]:
    warnings = [
        f"recommended key missing: {key}"
        for key in sorted(RECOMMENDED_COMMON - set(data))
    ]
    if data.get("record_type") == "derived-context":
        for key in ("last_updated", "review_due"):
            if key not in data:
                warnings.append(f"recommended derived-context key missing: {key}")
    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()

    failed = False
    for path in args.paths:
        try:
            data = load_frontmatter(path)
            record_type = data.get("record_type")
            if record_type == "raw":
                errors = validate_raw(data)
            elif record_type in ALLOWED_RECORD_TYPES:
                errors = validate_derived(data)
            else:
                errors = [f"record_type must be one of: {', '.join(sorted(ALLOWED_RECORD_TYPES))}"]
            warnings = collect_warnings(data) if not errors else []
        except Exception as exc:
            errors = [str(exc)]
            warnings = []

        if errors:
            failed = True
            print(f"{path}: invalid", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
        elif warnings:
            print(f"{path}: valid with warnings")
            for warning in warnings:
                print(f"  - {warning}", file=sys.stderr)
        else:
            print(f"{path}: valid")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
