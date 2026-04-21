#!/usr/bin/env python3
"""Generate iOS App Store 'What's New' drafts from a git commit range."""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

CONVENTIONAL_PATTERN = re.compile(
    r"^(?P<type>feat|fix|perf|docs|chore|build|ci|refactor|style|test|revert)"
    r"(?P<breaking>!)?"
    r"(?:\([^)]+\))?:\s*(?P<message>.+)$",
    re.IGNORECASE,
)
PR_NUMBER_PATTERN = re.compile(r"#(\d+)")
KNOWN_VERB_PREFIXES = (
    "add ",
    "added ",
    "fix ",
    "fixed ",
    "improve ",
    "improved ",
    "update ",
    "updated ",
    "remove ",
    "removed ",
    "support ",
    "supported ",
    "allow ",
    "allowed ",
    "prevent ",
    "prevented ",
    "reduce ",
    "reduced ",
)
DEFAULT_EXCLUDE_SUBJECT_PATTERNS = (
    re.compile(r"^update agents\.md$", re.IGNORECASE),
    re.compile(r"^release notes?$", re.IGNORECASE),
    re.compile(r"^changelog$", re.IGNORECASE),
    re.compile(r"^(version )?bump", re.IGNORECASE),
    re.compile(r"^[a-z0-9._-]+\s+\d+(?:\.\d+){1,3}$", re.IGNORECASE),
)
DEFAULT_FALLBACK_LINE_BY_LOCALE = {
    "en": "Improved stability and usability.",
    "ja": "安定性と使いやすさを改善しました。",
    "es": "Mejoramos la estabilidad y la usabilidad.",
    "fr": "Nous avons amélioré la stabilité et la facilité d'utilisation.",
    "zh-Hans": "我们改进了稳定性和易用性。",
}
INTRO_TEMPLATE_BY_LOCALE = {
    "en": "In {product_label}, we improved usability and stability.",
    "ja": "{product_label}では、操作性と安定性を改善しました。",
    "es": "En {product_label}, mejoramos la usabilidad y la estabilidad.",
    "fr": "Avec {product_label}, nous avons amélioré la facilité d'utilisation et la stabilité.",
    "zh-Hans": "在 {product_label} 中，我们改进了易用性和稳定性。",
}
OUTRO_TEMPLATE_BY_LOCALE = {
    "en": "This update makes daily entry even smoother.",
    "ja": "日々の入力がさらにスムーズになるアップデートです。",
    "es": "Esta actualización hace que el registro diario sea aún más fluido.",
    "fr": "Cette mise à jour rend la saisie quotidienne encore plus fluide.",
    "zh-Hans": "此次更新让日常记录更加顺畅。",
}

IGNORED_DISCOVERY_DIRECTORIES = {
    ".git",
    ".build",
    "build",
    "DerivedData",
    "Pods",
    "Carthage",
    ".swiftpm",
    "node_modules",
}


@dataclass
class Commit:
    commit_hash: str
    subject: str
    body: str
    author: str


@dataclass
class DraftLine:
    category: str
    text: str


@dataclass
class LocaleNotes:
    intro: str | None
    items: list[str]
    outro: str | None


def run_git_command(repository_path: Path, arguments: list[str]) -> str:
    process = subprocess.run(
        ["git", "-C", str(repository_path), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )

    if process.returncode != 0:
        error_message = process.stderr.strip() or "git command failed"
        raise RuntimeError(error_message)

    return process.stdout


def load_commits(
    repository_path: Path,
    from_ref: str,
    to_ref: str,
    include_merges: bool,
) -> list[Commit]:
    pretty_format = "%H%x1f%s%x1f%b%x1f%an%x1e"
    command = ["log", f"--pretty=format:{pretty_format}", f"{from_ref}..{to_ref}"]

    if not include_merges:
        command.insert(1, "--no-merges")

    raw_output = run_git_command(repository_path, command)

    commits: list[Commit] = []
    for raw_entry in raw_output.split("\x1e"):
        entry = raw_entry.strip()
        if not entry:
            continue

        fields = entry.split("\x1f")
        if len(fields) != 4:
            continue

        commits.append(
            Commit(
                commit_hash=fields[0].strip(),
                subject=fields[1].strip(),
                body=fields[2].strip(),
                author=fields[3].strip(),
            )
        )

    return commits


def is_breaking_change(commit: Commit, match: re.Match[str] | None) -> bool:
    subject_upper = commit.subject.upper()
    body_upper = commit.body.upper()

    if "BREAKING CHANGE" in body_upper:
        return True

    if "BREAKING CHANGE" in subject_upper or "BREAKING:" in subject_upper:
        return True

    if match and match.group("breaking"):
        return True

    return False


def classify_commit(commit: Commit) -> str:
    match = CONVENTIONAL_PATTERN.match(commit.subject)

    if is_breaking_change(commit, match):
        return "breaking"

    if not match:
        return "other"

    commit_type = match.group("type").lower()
    if commit_type == "feat":
        return "features"
    if commit_type in {"fix", "perf"}:
        return "fixes"
    if commit_type in {
        "docs",
        "chore",
        "build",
        "ci",
        "refactor",
        "style",
        "test",
        "revert",
    }:
        return "maintenance"

    return "other"


def clean_subject(subject: str) -> str:
    match = CONVENTIONAL_PATTERN.match(subject)
    if match:
        subject = match.group("message")

    subject = PR_NUMBER_PATTERN.sub("", subject)
    subject = re.sub(r"\s+", " ", subject)
    subject = subject.strip(" -")
    return subject.rstrip(".")


def lowercase_first_character(value: str) -> str:
    if not value:
        return value

    if len(value) == 1:
        return value.lower()

    if value[0].isalpha() and value[1].islower():
        return value[0].lower() + value[1:]

    return value


def to_sentence(value: str) -> str:
    if not value:
        return value

    return value[0].upper() + value[1:]


def extract_pull_request_number(commit: Commit) -> str | None:
    for text in (commit.subject, commit.body):
        pull_request_match = PR_NUMBER_PATTERN.search(text)
        if pull_request_match:
            return pull_request_match.group(1)
    return None


def build_user_facing_line(
    commit: Commit,
    category: str,
    include_pull_request_numbers: bool,
) -> str | None:
    message = clean_subject(commit.subject)
    if not message:
        return None

    lower_message = message.lower()
    if lower_message.startswith(KNOWN_VERB_PREFIXES):
        sentence = to_sentence(message)
    else:
        leading_verb = {
            "breaking": "Changed",
            "features": "Added",
            "fixes": "Fixed",
            "maintenance": "Improved",
            "other": "Improved",
        }[category]
        sentence = f"{leading_verb} {lowercase_first_character(message)}"

    if include_pull_request_numbers:
        pull_request_number = extract_pull_request_number(commit)
        if pull_request_number:
            sentence = f"{sentence} (#{pull_request_number})"

    sentence = sentence.rstrip(".") + "."
    return sentence


def should_exclude_subject(subject: str, patterns: list[re.Pattern[str]]) -> bool:
    normalized = clean_subject(subject).lower()
    if not normalized:
        return True

    for pattern in patterns:
        if pattern.search(normalized):
            return True

    return False


def choose_whats_new_lines(
    commits: list[Commit],
    max_items: int,
    include_pull_request_numbers: bool,
    exclude_subject_patterns: list[re.Pattern[str]],
) -> list[DraftLine]:
    categorized_lines: dict[str, list[DraftLine]] = {
        "breaking": [],
        "features": [],
        "fixes": [],
        "maintenance": [],
        "other": [],
    }

    seen: set[str] = set()
    for commit in commits:
        if should_exclude_subject(commit.subject, exclude_subject_patterns):
            continue

        category = classify_commit(commit)
        line_text = build_user_facing_line(
            commit=commit,
            category=category,
            include_pull_request_numbers=include_pull_request_numbers,
        )
        if not line_text:
            continue

        dedupe_key = line_text.lower()
        if dedupe_key in seen:
            continue

        seen.add(dedupe_key)
        categorized_lines[category].append(DraftLine(category=category, text=line_text))

    selected: list[DraftLine] = []
    for category in ("breaking", "features", "fixes", "maintenance", "other"):
        for line in categorized_lines[category]:
            selected.append(line)
            if len(selected) >= max_items:
                return selected

    return selected


def load_locales_from_xcstrings(xcstrings_path: Path) -> tuple[str | None, set[str]]:
    try:
        payload = json.loads(xcstrings_path.read_text())
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Failed to parse xcstrings file: {error}") from error

    source_language = payload.get("sourceLanguage")
    locales: set[str] = set()

    if isinstance(source_language, str) and source_language.strip():
        locales.add(source_language.strip())

    strings_payload = payload.get("strings", {})
    if isinstance(strings_payload, dict):
        for value in strings_payload.values():
            if not isinstance(value, dict):
                continue

            localizations = value.get("localizations", {})
            if not isinstance(localizations, dict):
                continue

            for locale in localizations.keys():
                if isinstance(locale, str) and locale.strip():
                    locales.add(locale.strip())

    return source_language, locales


def resolve_pbxproj_path(project_path: Path) -> Path:
    if project_path.is_file() and project_path.name == "project.pbxproj":
        return project_path

    if project_path.is_dir() and project_path.suffix == ".xcodeproj":
        pbxproj_path = project_path / "project.pbxproj"
        if pbxproj_path.exists():
            return pbxproj_path

    raise RuntimeError(f"Could not locate project.pbxproj from: {project_path}")


def load_locales_from_pbxproj(project_path: Path) -> set[str]:
    pbxproj_path = resolve_pbxproj_path(project_path)
    content = pbxproj_path.read_text()

    match = re.search(r"knownRegions\s*=\s*\((.*?)\);", content, re.DOTALL)
    if not match:
        return set()

    body = match.group(1)
    locales: set[str] = set()
    for raw_line in body.splitlines():
        normalized = raw_line.strip().strip(",").strip('"').strip()
        if not normalized:
            continue
        locales.add(normalized)

    return locales


def normalize_locale_order(locales: set[str], source_locale: str) -> list[str]:
    filtered = {locale for locale in locales if locale and locale != "Base"}
    if not filtered:
        filtered = {source_locale}

    if source_locale not in filtered:
        filtered.add(source_locale)

    sorted_locales = sorted(locale for locale in filtered if locale != source_locale)
    return [source_locale, *sorted_locales]


def parse_locale_override(raw_locales: str) -> list[str]:
    locales: list[str] = []
    seen: set[str] = set()

    for raw_locale in raw_locales.split(","):
        locale = raw_locale.strip()
        if not locale or locale == "Base":
            continue
        if locale in seen:
            continue

        seen.add(locale)
        locales.append(locale)

    return locales


def normalize_items_from_unknown_payload(value: object) -> list[str]:
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]

    if isinstance(value, str):
        items: list[str] = []
        for raw_line in value.splitlines():
            normalized = raw_line.strip()
            if not normalized:
                continue
            normalized = re.sub(r"^[\-*•]\s*", "", normalized).strip()
            if normalized:
                items.append(normalized)
        return items

    return []


def parse_translations(path: Path) -> dict[str, LocaleNotes]:
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Failed to parse translations JSON: {error}") from error

    if not isinstance(payload, dict):
        raise RuntimeError("Translations JSON must be an object keyed by locale")

    translations: dict[str, LocaleNotes] = {}
    for locale, value in payload.items():
        if not isinstance(locale, str):
            continue

        intro: str | None = None
        outro: str | None = None
        items: list[str] = []

        if isinstance(value, dict):
            raw_intro = value.get("intro")
            raw_outro = value.get("outro")
            intro = raw_intro.strip() if isinstance(raw_intro, str) and raw_intro.strip() else None
            outro = raw_outro.strip() if isinstance(raw_outro, str) and raw_outro.strip() else None
            items = normalize_items_from_unknown_payload(value.get("items"))
        else:
            items = normalize_items_from_unknown_payload(value)

        translations[locale] = LocaleNotes(intro=intro, items=items, outro=outro)

    return translations


def product_label(app_name: str, version: str | None) -> str:
    if version:
        return f"{app_name} {version}"
    return app_name


def compose_intro(locale: str, app_name: str, version: str | None) -> str:
    template = INTRO_TEMPLATE_BY_LOCALE.get(locale, INTRO_TEMPLATE_BY_LOCALE["en"])
    return template.format(product_label=product_label(app_name, version))


def compose_outro(locale: str) -> str:
    return OUTRO_TEMPLATE_BY_LOCALE.get(locale, OUTRO_TEMPLATE_BY_LOCALE["en"])


def fallback_line_for_locale(locale: str) -> str:
    return DEFAULT_FALLBACK_LINE_BY_LOCALE.get(locale, DEFAULT_FALLBACK_LINE_BY_LOCALE["en"])


def build_localized_notes(
    source_lines: list[DraftLine],
    source_locale: str,
    locales: list[str],
    copy_source_to_all_locales: bool,
    translations: dict[str, LocaleNotes],
    style: str,
    include_outro: bool,
    app_name: str,
    version: str | None,
) -> dict[str, LocaleNotes]:
    source_items = [line.text for line in source_lines]
    if not source_items:
        source_items = [fallback_line_for_locale(source_locale)]

    localized_notes: dict[str, LocaleNotes] = {}
    for locale in locales:
        translated = translations.get(locale)

        if translated:
            items = translated.items or (
                source_items
                if (locale == source_locale or copy_source_to_all_locales)
                else [f"TODO: Translate from {source_locale}: {line}" for line in source_items]
            )
            intro = translated.intro
            outro = translated.outro
        else:
            if locale == source_locale or copy_source_to_all_locales:
                items = source_items
            else:
                items = [f"TODO: Translate from {source_locale}: {line}" for line in source_items]
            intro = None
            outro = None

        if style == "app-store":
            if intro is None:
                if locale == source_locale or copy_source_to_all_locales:
                    intro = compose_intro(locale, app_name, version)
                else:
                    source_intro = compose_intro(source_locale, app_name, version)
                    intro = f"TODO: Translate from {source_locale}: {source_intro}"

            if include_outro and outro is None:
                if locale == source_locale or copy_source_to_all_locales:
                    outro = compose_outro(locale)
                else:
                    source_outro = compose_outro(source_locale)
                    outro = f"TODO: Translate from {source_locale}: {source_outro}"

        localized_notes[locale] = LocaleNotes(intro=intro, items=items, outro=outro)

    return localized_notes


def render_locale_text(locale_notes: LocaleNotes) -> str:
    lines: list[str] = []

    if locale_notes.intro:
        lines.append(locale_notes.intro)
        lines.append("")

    for entry in locale_notes.items:
        lines.append(f"- {entry}")

    if locale_notes.outro:
        lines.append("")
        lines.append(locale_notes.outro)

    return "\n".join(lines).strip()


def render_markdown(
    localized_notes: dict[str, LocaleNotes],
    version: str | None,
    release_date: str,
    from_ref: str,
    to_ref: str,
    source_locale: str,
    style: str,
) -> str:
    title = "What's New Draft"
    if version:
        title = f"What's New Draft - {version}"

    locales = list(localized_notes.keys())
    lines: list[str] = [f"# {title}", ""]

    if version:
        lines.append(f"Version: {version}")
    lines.append(f"Release date: {release_date}")
    lines.append(f"Commit range: `{from_ref}..{to_ref}`")
    lines.append(f"Source locale: {source_locale}")
    lines.append(f"Target locales: {', '.join(locales)}")
    lines.append(f"Style: {style}")
    lines.append("")

    for locale in locales:
        lines.append(f"## {locale}")
        lines.append("```text")
        lines.append(render_locale_text(localized_notes[locale]))
        lines.append("```")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def render_json(
    localized_notes: dict[str, LocaleNotes],
    version: str | None,
    release_date: str,
    from_ref: str,
    to_ref: str,
    source_locale: str,
    style: str,
) -> str:
    payload = {
        "version": version,
        "releaseDate": release_date,
        "commitRange": f"{from_ref}..{to_ref}",
        "sourceLocale": source_locale,
        "style": style,
        "locales": {
            locale: {
                "intro": notes.intro,
                "items": notes.items,
                "outro": notes.outro,
            }
            for locale, notes in localized_notes.items()
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def write_locale_files(output_dir: Path, localized_notes: dict[str, LocaleNotes]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for locale, notes in localized_notes.items():
        output_path = output_dir / f"{locale}.txt"
        output_path.write_text(render_locale_text(notes) + "\n")


def iter_repo_files(repository_path: Path, *, file_name: str | None = None, suffix: str | None = None) -> list[Path]:
    matches: list[Path] = []
    for root, dir_names, file_names in os.walk(repository_path):
        dir_names[:] = sorted(
            [name for name in dir_names if name not in IGNORED_DISCOVERY_DIRECTORIES]
        )

        root_path = Path(root)
        for entry_name in sorted(file_names):
            if file_name and entry_name != file_name:
                continue
            if suffix and not entry_name.endswith(suffix):
                continue
            matches.append(root_path / entry_name)

    return matches


def choose_preferred_path(paths: list[Path]) -> Path | None:
    if not paths:
        return None

    def score(path: Path) -> tuple[int, int, str]:
        relative_parts = path.parts
        resources_bonus = 0 if "Resources" in relative_parts else 1
        return (len(relative_parts), resources_bonus, str(path))

    return sorted(paths, key=score)[0]


def detect_default_xcstrings(repository_path: Path) -> Path | None:
    direct_candidates = [
        repository_path / "Localizable.xcstrings",
        repository_path / "Resources" / "Localizable.xcstrings",
    ]
    existing_direct = [candidate for candidate in direct_candidates if candidate.exists()]
    if existing_direct:
        return choose_preferred_path(existing_direct)

    discovered = iter_repo_files(repository_path, file_name="Localizable.xcstrings")
    return choose_preferred_path(discovered)


def detect_default_project(repository_path: Path) -> Path | None:
    direct_candidates = sorted(repository_path.glob("*.xcodeproj"))
    if direct_candidates:
        return direct_candidates[0]

    discovered = iter_repo_files(repository_path, suffix=".xcodeproj")
    return choose_preferred_path(discovered)


def validate_repository(repository_path: Path) -> None:
    if not repository_path.exists():
        raise FileNotFoundError(f"Repository path does not exist: {repository_path}")

    git_directory = repository_path / ".git"
    if not git_directory.exists():
        raise RuntimeError(f"Not a git repository: {repository_path}")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate iOS App Store 'What's New' drafts from a git commit range.",
    )
    parser.add_argument("--repo", default=".", help="Path to a git repository")
    parser.add_argument("--from-ref", required=True, help="Start reference (exclusive)")
    parser.add_argument("--to-ref", default="HEAD", help="End reference (inclusive)")
    parser.add_argument("--app-name", help="Display app name in intro text (default: repository name)")
    parser.add_argument("--version", help="App version label")
    parser.add_argument("--date", help="Release date in YYYY-MM-DD format")
    parser.add_argument("--max-items", type=int, default=4, help="Max bullets per locale")
    parser.add_argument(
        "--include-merges",
        action="store_true",
        help="Include merge commits in the analyzed commit range",
    )
    parser.add_argument(
        "--include-pr-numbers",
        action="store_true",
        help="Append pull request numbers to generated lines",
    )
    parser.add_argument(
        "--exclude-subject-regex",
        action="append",
        default=[],
        help="Regex to exclude commit subjects (repeatable)",
    )
    parser.add_argument("--xcstrings", help="Path to Localizable.xcstrings")
    parser.add_argument("--project", help="Path to .xcodeproj or project.pbxproj")
    parser.add_argument(
        "--source-locale",
        help="Force source locale (for example: en or ja)",
    )
    parser.add_argument(
        "--locales",
        help="Comma-separated locales override (for example: en,ja,es,fr,zh-Hans)",
    )
    parser.add_argument(
        "--copy-source-to-all-locales",
        action="store_true",
        help="Fill every locale with source locale text",
    )
    parser.add_argument(
        "--translations-json",
        help="Path to JSON locale map for finalized translations",
    )
    parser.add_argument(
        "--style",
        choices=("bullet-list", "app-store"),
        default="app-store",
        help="Output style",
    )
    parser.add_argument(
        "--include-outro",
        action="store_true",
        help="Append a short closing sentence for app-store style",
    )
    parser.add_argument(
        "--output-format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format",
    )
    parser.add_argument("--output", help="Output file path (default: stdout)")
    parser.add_argument(
        "--output-dir",
        help="Optional directory to emit one <locale>.txt file per locale",
    )

    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()

    if arguments.max_items < 1:
        print("--max-items must be at least 1", file=sys.stderr)
        return 1

    repository_path = Path(arguments.repo).resolve()

    try:
        validate_repository(repository_path)

        release_date = arguments.date
        if not release_date:
            release_date = datetime.date.today().isoformat()

        exclude_patterns = list(DEFAULT_EXCLUDE_SUBJECT_PATTERNS)
        for raw_pattern in arguments.exclude_subject_regex:
            try:
                exclude_patterns.append(re.compile(raw_pattern, re.IGNORECASE))
            except re.error as error:
                raise RuntimeError(f"Invalid --exclude-subject-regex '{raw_pattern}': {error}") from error

        commits = load_commits(
            repository_path=repository_path,
            from_ref=arguments.from_ref,
            to_ref=arguments.to_ref,
            include_merges=arguments.include_merges,
        )

        source_lines = choose_whats_new_lines(
            commits=commits,
            max_items=arguments.max_items,
            include_pull_request_numbers=arguments.include_pr_numbers,
            exclude_subject_patterns=exclude_patterns,
        )

        detected_source_locale = "en"
        detected_locales: set[str] = set()

        xcstrings_path: Path | None = None
        if arguments.xcstrings:
            xcstrings_path = Path(arguments.xcstrings).resolve()
        else:
            xcstrings_path = detect_default_xcstrings(repository_path)

        if xcstrings_path and xcstrings_path.exists():
            source_locale_candidate, locales = load_locales_from_xcstrings(xcstrings_path)
            if source_locale_candidate:
                detected_source_locale = source_locale_candidate
            detected_locales.update(locales)

        project_path: Path | None = None
        if arguments.project:
            project_path = Path(arguments.project).resolve()
        else:
            project_path = detect_default_project(repository_path)

        if project_path and project_path.exists():
            detected_locales.update(load_locales_from_pbxproj(project_path))

        if arguments.locales:
            locales = parse_locale_override(arguments.locales)
            if not locales:
                raise RuntimeError("--locales did not contain any valid locale values")
        else:
            locales = normalize_locale_order(detected_locales, detected_source_locale)

        source_locale = detected_source_locale
        if arguments.source_locale:
            source_locale = arguments.source_locale.strip()
            if not source_locale or source_locale == "Base":
                raise RuntimeError("--source-locale must be a valid locale code")

        if source_locale in locales:
            locales = [source_locale, *[locale for locale in locales if locale != source_locale]]
        else:
            locales = [source_locale, *locales]

        app_name = arguments.app_name or repository_path.name

        translations: dict[str, LocaleNotes] = {}
        if arguments.translations_json:
            translations = parse_translations(Path(arguments.translations_json).resolve())

        localized_notes = build_localized_notes(
            source_lines=source_lines,
            source_locale=source_locale,
            locales=locales,
            copy_source_to_all_locales=arguments.copy_source_to_all_locales,
            translations=translations,
            style=arguments.style,
            include_outro=arguments.include_outro,
            app_name=app_name,
            version=arguments.version,
        )

        output_content: str
        if arguments.output_format == "json":
            output_content = render_json(
                localized_notes=localized_notes,
                version=arguments.version,
                release_date=release_date,
                from_ref=arguments.from_ref,
                to_ref=arguments.to_ref,
                source_locale=source_locale,
                style=arguments.style,
            )
        else:
            output_content = render_markdown(
                localized_notes=localized_notes,
                version=arguments.version,
                release_date=release_date,
                from_ref=arguments.from_ref,
                to_ref=arguments.to_ref,
                source_locale=source_locale,
                style=arguments.style,
            )
    except (FileNotFoundError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 1

    if arguments.output:
        output_path = Path(arguments.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_content)
    else:
        print(output_content, end="")

    if arguments.output_dir:
        output_directory = Path(arguments.output_dir).resolve()
        write_locale_files(output_directory, localized_notes)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
