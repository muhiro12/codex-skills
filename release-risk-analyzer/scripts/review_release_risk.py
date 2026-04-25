#!/usr/bin/env python3
"""Review release-blocking risk since the latest reachable release tag."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from fnmatch import fnmatchcase
from pathlib import Path

SEVERITY_ORDER = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

SEVERITY_DEFAULT_SCORES = {
    "none": 0,
    "low": 5,
    "medium": 18,
    "high": 30,
    "critical": 50,
}

SEVERITY_LABELS = {
    "none": "なし",
    "low": "低",
    "medium": "中",
    "high": "高",
    "critical": "重大",
}

SCORE_MAX = 100
HEURISTIC_SCORE_MAX = 95
FALLBACK_UNKNOWN_CHANGE_SCORE = 15

BUILTIN_RULES = [
    {
        "name": "一意ID・外部固定設定の変更",
        "severity": "critical",
        "category": "external-identity-config",
        "score": 25,
        "mode": "any",
        "paths": [
            "**/*.xcodeproj/project.pbxproj",
            "**/Info.plist",
            "**/*.entitlements",
            "**/*.xcconfig",
            "project.yml",
            "project.yaml",
            "**/project.yml",
            "**/project.yaml",
            "**/*.storekit",
            "**/StoreKit/**",
        ],
        "reason": "外部登録済みの一意IDや配布・連携設定値は、誤って出すと既存アプリ、外部サービス、ユーザー導線へ長く残りやすい。",
        "advice": "既存の配布設定、外部連携、チーム/署名、購入/クラウド/ドメイン設定と照合し、新規作成や変更が意図的か確認する。",
    },
    {
        "name": "永続化領域・スキーマ互換性の変更",
        "severity": "high",
        "category": "durable-state",
        "score": 30,
        "mode": "any",
        "paths": [
            "**/Persistence/**",
            "**/Database/**",
            "**/DB/**",
            "**/Realm/**",
            "**/CoreData/**",
            "**/Migration/**",
            "**/Migrations/**",
            "**/*Migration*.swift",
            "**/*Migrator*.swift",
            "**/Schema/**",
            "**/ModelContainerFactory.swift",
            "**/Database.swift",
            "**/*.sql",
            "**/*.sqlite",
            "**/*.xcdatamodeld/**",
        ],
        "reason": "端末やバックエンドに残る永続状態の構造・保存先・移行処理の変更は、既存ユーザーの起動不能やデータ不整合につながりやすい。",
        "advice": "既存データを持つ状態での起動、読み書き、移行、ロールバック時の扱いを先に確認する。",
    },
    {
        "name": "権限・セキュリティ面の変更",
        "severity": "high",
        "category": "security-capability",
        "score": 30,
        "mode": "any",
        "paths": [
            "**/Auth/**",
            "**/Authentication/**",
            "**/Security/**",
            "**/Crypto/**",
            "**/Credential/**",
            "**/Token/**",
            "**/Session/**",
            "**/Keychain/**",
            "**/*.entitlements",
        ],
        "reason": "権限や認証まわりの変更は審査・起動・既存ユーザー導線に影響しやすい。",
        "advice": "不要な権限追加がないか、既存導線が壊れていないかを確認する。",
    },
    {
        "name": "ビルド・依存関係・CI の変更",
        "severity": "high",
        "category": "packaging",
        "score": 25,
        "mode": "any",
        "paths": [
            ".github/workflows/**",
            "ci_scripts/**",
            "Dockerfile*",
            "docker/**",
            "**/*.xcodeproj/project.pbxproj",
            "Package.swift",
            "Package.resolved",
            "**/Package.resolved",
            "Podfile",
            "Podfile.lock",
            "Gemfile",
            "Gemfile.lock",
            "Cartfile",
            "Cartfile.resolved",
            "**/*.xcscheme",
        ],
        "reason": "ビルドや依存関係の変更は、コード差分以上に配布物へ影響することがある。",
        "advice": "クリーンビルドと配布フローを確認する。",
    },
    {
        "name": "共有ロジックの変更",
        "severity": "medium",
        "category": "shared-logic",
        "score": 15,
        "mode": "any",
        "paths": [
            "**/Domain/**",
            "**/Model/**",
            "**/Models/**",
            "**/UseCase/**",
            "**/Service/**",
            "**/Services/**",
            "**/Store/**",
            "**/Repository/**",
            "**/Repositories/**",
            "**/Provider/**",
            "**/Providers/**",
        ],
        "reason": "共有ロジックの変更は複数機能へ波及しやすい。",
        "advice": "変更機能だけでなく周辺導線も含めて回帰確認する。",
    },
    {
        "name": "API / 通信面の変更",
        "severity": "medium",
        "category": "networking",
        "score": 20,
        "mode": "any",
        "paths": [
            "**/API/**",
            "**/Network/**",
            "**/Networking/**",
            "**/HTTP/**",
            "**/Client/**",
            "**/Remote/**",
        ],
        "reason": "通信面の変更は実データ条件でのみ不具合化することがある。",
        "advice": "実データまたはステージング相当で通信経路を確認する。",
    },
    {
        "name": "UI・リソースのみの変更",
        "severity": "low",
        "category": "ui-resource",
        "score": 5,
        "mode": "all",
        "paths": [
            "Resources/**",
            "**/UI/**",
            "Views/**",
            "**/View/**",
            "**/Views/**",
            "Components/**",
            "**/Component/**",
            "**/Components/**",
            "**/Presentation/**",
            "**/Resources/**",
            "**/*.storyboard",
            "**/*.xib",
            "**/*.xcassets/**",
            "*.xcstrings",
            "**/*.xcstrings",
            "*.strings",
            "**/*.strings",
            "*.css",
            "**/*.css",
            "*.scss",
            "**/*.scss",
            "*.html",
            "**/*.html",
            "*.svg",
            "**/*.svg",
            "*.png",
            "**/*.png",
            "*.jpg",
            "**/*.jpg",
            "*.jpeg",
            "**/*.jpeg",
            "*.gif",
            "**/*.gif",
        ],
        "reason": "変更面が表示や同梱リソースに閉じている可能性が高い。",
        "advice": "対象画面の重点確認で進めやすい。",
    },
    {
        "name": "テスト・ドキュメントのみの変更",
        "severity": "low",
        "category": "tests-docs",
        "score": 0,
        "mode": "all",
        "paths": [
            "**/Tests/**",
            "docs/**",
            "*.md",
            "**/*.md",
            "*.txt",
            "**/*.txt",
        ],
        "reason": "テストやドキュメントのみの変更は通常、出荷挙動を直接変えにくい。",
        "advice": "生成物が意図せず変わっていないかだけ確認する。",
    },
]

IDENTIFIER_MARKER_PATTERNS = [
    re.compile(r"\bPRODUCT_BUNDLE_IDENTIFIER\s*=\s*([^;]+);?"),
    re.compile(r"\bDEVELOPMENT_TEAM\s*=\s*([^;]+);?"),
    re.compile(r"\bPROVISIONING_PROFILE_SPECIFIER\s*=\s*([^;]+);?"),
    re.compile(r"\bCODE_SIGN_ENTITLEMENTS\s*=\s*([^;]+);?"),
    re.compile(r"\b(?:CFBundleIdentifier|CFBundleURLName|CFBundleURLSchemes)\b"),
    re.compile(r"(group\.[A-Za-z0-9\.-]+)"),
    re.compile(r"(iCloud\.[A-Za-z0-9\.-]+)"),
    re.compile(r"(applinks:[^<>\s\",;]+)"),
    re.compile(r"(webcredentials:[^<>\s\",;]+)"),
    re.compile(r"(activitycontinuation:[^<>\s\",;]+)"),
    re.compile(r"(com\.apple\.security\.application-groups)"),
    re.compile(r"(com\.apple\.developer\.icloud-container-identifiers)"),
    re.compile(r"(com\.apple\.developer\.associated-domains)"),
    re.compile(r"(keychain-access-groups)"),
    re.compile(r"\b(?:productID|productIdentifier)\b\s*[:=]\s*\"([^\"]+)\""),
    re.compile(r"\bProduct\.products\s*\(\s*for:\s*(\[[^\]]+\])"),
]

CAPABILITY_MARKER_PATTERNS = [
    re.compile(
        r"<key>((?:NS[A-Za-z0-9]+UsageDescription)|(?:com\.apple\.[^<]+)|"
        r"(?:aps-environment)|(?:keychain-access-groups))</key>"
    ),
    re.compile(r"INFOPLIST_KEY_(NS[A-Za-z0-9]+UsageDescription)"),
    re.compile(r"(aps-environment|com\.apple\.developer\.[A-Za-z0-9\.-]+)"),
    re.compile(r"\bSystemCapabilities\b"),
]

PERSISTENT_USAGE_PATTERNS = [
    re.compile(r"@AppStorage\("),
    re.compile(r"\bAppStorage\("),
    re.compile(r"\bUserDefaults\("),
    re.compile(r"\.set\([^)]*forKey:"),
    re.compile(r"\.(?:string|bool|integer|double|object|data)\(forKey:"),
]

APP_STORAGE_CASE_PATTERN = re.compile(r"^\s*case\s+([A-Za-z_]\w*)\s*=")
MODEL_PROPERTY_PATTERN = re.compile(
    r"^\s*(?:(?:public|private|internal|fileprivate|open)\s+)*(?:private\(set\)\s+|public\(set\)\s+|package\(set\)\s+)*var\s+([A-Za-z_]\w*)\b"
)

DURABLE_STORAGE_INFRA_PATTERNS = [
    "**/Database.swift",
    "**/*Migrator*.swift",
    "**/ModelContainerFactory.swift",
    "**/*.xcdatamodeld/**",
    "**/*.sql",
    "**/*.sqlite",
]

DURABLE_MODEL_MARKERS = [
    "@Model",
    "NSManagedObject",
]

PERSISTENT_SETTINGS_PATTERNS = [
    "**/AppStorageKey.swift",
    "**/NotificationSettings.swift",
]

DEFAULT_IGNORE_USAGE_PATTERNS = [
    "**/Tests/**",
    "docs/**",
]


@dataclass
class Commit:
    hash: str
    short_hash: str
    date: str
    subject: str
    author: str


@dataclass
class FileChange:
    status: str
    path: str
    old_path: str | None = None


@dataclass
class RiskRule:
    name: str
    severity: str
    category: str
    score: int
    mode: str
    paths: list[str]
    exclude_paths: list[str]
    reason: str
    advice: str


@dataclass
class RiskSignal:
    name: str
    severity: str
    category: str
    score: int
    mode: str
    reason: str
    advice: str
    matched_files: list[str]


@dataclass
class DiffLines:
    added: list[str]
    removed: list[str]
    changed: list[str] = field(default_factory=list)


@dataclass
class DiffSnippet:
    title: str
    category: str
    source: str
    file: str
    lines: list[str]


@dataclass
class ReviewFinding:
    title: str
    severity: str
    category: str
    score: int
    reason: str
    advice: str
    files: list[str]
    evidence: list[str]


class GitCommandError(RuntimeError):
    """Raised when a git command fails."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Assess release-blocking risk between the latest tag and a target ref.",
    )
    parser.add_argument("--repo", required=True, help="Path to the git repository")
    parser.add_argument("--base-ref", help="Base git ref. Defaults to the latest reachable tag.")
    parser.add_argument("--head-ref", default="HEAD", help="Head git ref. Defaults to HEAD.")
    parser.add_argument(
        "--tag-pattern",
        help="Optional glob passed to git describe --match when auto-detecting the base tag.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=20,
        help="Maximum changed files to print in verbose markdown output",
    )
    parser.add_argument(
        "--max-commits",
        type=int,
        default=20,
        help="Maximum commits to print in verbose markdown output",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include full file and commit sections in markdown output",
    )
    return parser.parse_args()


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise GitCommandError(message)
    return result.stdout.strip()


def normalize_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized or path


def short_ref(repo: Path, ref: str) -> str:
    return run_git(repo, "rev-parse", "--short", ref)


def detect_base_ref(repo: Path, head_ref: str, tag_pattern: str | None) -> str:
    args = ["describe", "--tags", "--abbrev=0"]
    if tag_pattern:
        args.extend(["--match", tag_pattern])
    args.append(head_ref)
    base_ref = run_git(repo, *args)
    if not base_ref:
        raise GitCommandError("到達可能なタグが見つかりません。--base-ref を指定してください。")
    return base_ref


def load_rules_from_dicts(raw_rules: list[dict]) -> list[RiskRule]:
    rules: list[RiskRule] = []
    for raw_rule in raw_rules:
        rules.append(
            RiskRule(
                name=raw_rule["name"],
                severity=raw_rule["severity"],
                category=raw_rule.get("category", raw_rule["name"]),
                score=int(raw_rule.get("score", SEVERITY_DEFAULT_SCORES[raw_rule["severity"]])),
                mode=raw_rule.get("mode", "any"),
                paths=[normalize_path(pattern) for pattern in raw_rule["paths"]],
                exclude_paths=[normalize_path(pattern) for pattern in raw_rule.get("exclude_paths", [])],
                reason=raw_rule.get("reason", ""),
                advice=raw_rule.get("advice", ""),
            )
        )
    return rules


def path_matches(path: str, patterns: list[str]) -> bool:
    return any(
        fnmatchcase(path, pattern)
        or (pattern.startswith("**/") and fnmatchcase(path, pattern[3:]))
        for pattern in patterns
    )


def evaluate_rule(rule: RiskRule, files: list[FileChange]) -> RiskSignal | None:
    if not files:
        return None

    matched_files = [
        file.path
        for file in files
        if path_matches(file.path, rule.paths)
        and not path_matches(file.path, rule.exclude_paths)
    ]

    if rule.mode == "any":
        if not matched_files:
            return None
    else:
        if len(matched_files) != len(files):
            return None

    return RiskSignal(
        name=rule.name,
        severity=rule.severity,
        category=rule.category,
        score=rule.score,
        mode=rule.mode,
        reason=rule.reason,
        advice=rule.advice,
        matched_files=sorted(set(matched_files)),
    )


def get_commits(repo: Path, base_ref: str, head_ref: str) -> list[Commit]:
    output = run_git(
        repo,
        "log",
        "--date=short",
        "--reverse",
        "--pretty=format:%H%x1f%h%x1f%ad%x1f%s%x1f%an",
        f"{base_ref}..{head_ref}",
    )
    if not output:
        return []

    commits: list[Commit] = []
    for line in output.splitlines():
        full_hash, short_hash, date, subject, author = line.split("\x1f")
        commits.append(
            Commit(
                hash=full_hash,
                short_hash=short_hash,
                date=date,
                subject=subject,
                author=author,
            )
        )
    return commits


def get_files(repo: Path, base_ref: str, head_ref: str) -> list[FileChange]:
    output = run_git(repo, "diff", "--name-status", "--find-renames", f"{base_ref}..{head_ref}")
    if not output:
        return []

    files: list[FileChange] = []
    for line in output.splitlines():
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            files.append(
                FileChange(
                    status="R",
                    old_path=normalize_path(parts[1]),
                    path=normalize_path(parts[2]),
                )
            )
            continue

        if len(parts) >= 2:
            files.append(FileChange(status=status, path=normalize_path(parts[1])))

    return files


def get_diff_lines(repo: Path, base_ref: str, head_ref: str, files: list[FileChange]) -> dict[str, DiffLines]:
    diffs: dict[str, DiffLines] = {}
    for file in files:
        patch = run_git(
            repo,
            "diff",
            "--unified=0",
            "--no-color",
            f"{base_ref}..{head_ref}",
            "--",
            file.path,
        )
        added: list[str] = []
        removed: list[str] = []
        changed: list[str] = []
        for line in patch.splitlines():
            if line.startswith("+++ ") or line.startswith("--- "):
                continue
            if line.startswith("@@"):
                changed.append(line)
                continue
            if line.startswith("+"):
                changed.append(line)
                added.append(line[1:])
                continue
            if line.startswith("-"):
                changed.append(line)
                removed.append(line[1:])
        diffs[file.path] = DiffLines(added=added, removed=removed, changed=changed)
    return diffs


def read_file(repo: Path, path: str) -> str:
    file_path = repo / path
    if not file_path.exists() or not file_path.is_file():
        return ""
    return file_path.read_text(encoding="utf-8", errors="ignore")


def top_areas(files: list[FileChange], limit: int = 5) -> list[dict[str, int | str]]:
    counter: Counter[str] = Counter()
    for file in files:
        parts = Path(file.path).parts
        if not parts:
            continue
        if len(parts) >= 2 and not parts[0].startswith("."):
            label = "/".join(parts[:2])
        else:
            label = parts[0]
        counter[label] += 1

    return [{"area": area, "count": count} for area, count in counter.most_common(limit)]


def truncate_list(values: list[str], limit: int) -> list[str]:
    if len(values) <= limit:
        return values
    remaining = len(values) - limit
    return [*values[:limit], f"... (+{remaining} 件)"]


def unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def collect_markers(lines: list[str], patterns: list[re.Pattern[str]]) -> list[str]:
    markers: list[str] = []
    for line in lines:
        stripped = line.strip()
        for pattern in patterns:
            match = pattern.search(stripped)
            if not match:
                continue
            markers.append(match.group(1) if match.groups() else stripped)
            break
    return unique(markers)


def find_model_properties(lines: list[str]) -> list[str]:
    properties: list[str] = []
    for line in lines:
        stripped = line.strip()
        if "(" in stripped and "=" not in stripped and ":" not in stripped:
            continue
        match = MODEL_PROPERTY_PATTERN.match(stripped)
        if not match:
            continue
        properties.append(match.group(1))
    return unique(properties)


def matches_any(path: str, patterns: list[str]) -> bool:
    return path_matches(path, patterns)


def has_durable_model_marker(content: str, diff: DiffLines) -> bool:
    changed_lines = [*diff.added, *diff.removed]
    return (
        any(marker in content for marker in DURABLE_MODEL_MARKERS)
        or ("Object" in content and "Realm" in content)
        or any(marker in line for line in changed_lines for marker in DURABLE_MODEL_MARKERS)
    )


def detect_external_identity_config_findings(
    files: list[FileChange],
    diff_by_file: dict[str, DiffLines],
) -> list[ReviewFinding]:
    identifier_files = [
        file.path
        for file in files
        if file.path.endswith(".entitlements")
        or file.path.endswith("Info.plist")
        or file.path.endswith("project.pbxproj")
        or file.path.endswith(".xcconfig")
        or file.path.endswith(".storekit")
        or file.path.endswith("project.yml")
        or file.path.endswith("project.yaml")
        or "/StoreKit/" in file.path
    ]
    if not identifier_files:
        return []

    added_markers: list[str] = []
    removed_markers: list[str] = []
    for path in identifier_files:
        diff = diff_by_file.get(path)
        if not diff:
            continue
        added_markers.extend(collect_markers(diff.added, IDENTIFIER_MARKER_PATTERNS))
        removed_markers.extend(collect_markers(diff.removed, IDENTIFIER_MARKER_PATTERNS))

    if not added_markers and not removed_markers:
        return []

    evidence = truncate_list(unique([*added_markers, *removed_markers]), 8)
    return [
        ReviewFinding(
            title="一意ID・外部固定設定の変更候補",
            severity="critical",
            category="external-identity-config",
            score=80,
            reason="外部登録済みの一意IDや連携設定値は、誤って出すと既存アプリ、外部サービス、ユーザー導線へ長く残りやすく後戻りが難しい。",
            advice="配布・署名・クラウド・ドメイン・購入・連携先に登録済みの値と照合し、新規IDや設定値変更が意図的か確認する。",
            files=unique(identifier_files),
            evidence=evidence,
        )
    ]


def detect_capability_findings(files: list[FileChange], diff_by_file: dict[str, DiffLines]) -> list[ReviewFinding]:
    capability_files = [
        file.path
        for file in files
        if file.path.endswith(".entitlements")
        or file.path.endswith("Info.plist")
        or file.path.endswith("project.pbxproj")
    ]
    if not capability_files:
        return []

    added_markers: list[str] = []
    removed_markers: list[str] = []
    for path in capability_files:
        diff = diff_by_file.get(path)
        if not diff:
            continue
        added_markers.extend(collect_markers(diff.added, CAPABILITY_MARKER_PATTERNS))
        removed_markers.extend(collect_markers(diff.removed, CAPABILITY_MARKER_PATTERNS))

    if not added_markers and not removed_markers and not any(path.endswith(".entitlements") for path in capability_files):
        return []

    severity = "critical" if added_markers else "high"
    evidence = truncate_list(unique([*added_markers, *removed_markers]), 6)
    return [
        ReviewFinding(
            title="権限・Capability の追加/変更候補",
            severity=severity,
            category="security-capability",
            score=70 if severity == "critical" else 50,
            reason="不要な権限要求や審査リスク、既存機能の破壊につながる変更面。",
            advice="entitlements / Info.plist / project 設定の差分が意図通りかを手動確認する。",
            files=unique(capability_files),
            evidence=evidence,
        )
    ]


def detect_durable_state_findings(
    repo: Path,
    files: list[FileChange],
    diff_by_file: dict[str, DiffLines],
) -> list[ReviewFinding]:
    storage_infra_files: list[str] = []
    model_files: list[str] = []
    property_changes: list[str] = []

    for file in files:
        path = file.path
        diff = diff_by_file.get(path, DiffLines([], []))
        content = read_file(repo, path)
        if matches_any(path, DURABLE_STORAGE_INFRA_PATTERNS):
            storage_infra_files.append(path)

        if has_durable_model_marker(content, diff):
            model_files.append(path)
            property_changes.extend(find_model_properties(diff.added))
            property_changes.extend(find_model_properties(diff.removed))

    findings: list[ReviewFinding] = []
    if storage_infra_files:
        evidence: list[str] = []
        for path in storage_infra_files:
            diff = diff_by_file.get(path, DiffLines([], []))
            evidence.extend(
                line.strip()
                for line in [*diff.added, *diff.removed]
                if any(
                    token in line
                    for token in [
                        "ModelContainer",
                        "Database",
                        "Migration",
                        "legacyURL",
                        "fileName",
                        "url",
                        "Schema",
                    ]
                )
            )
        findings.append(
            ReviewFinding(
                title="永続化領域の保存先・移行導線の変更候補",
                severity="critical",
                category="durable-state",
                score=75,
                reason="保存先、スキーマ定義、移行処理、既存データ読込経路の変更は、起動不能やデータ欠落に直結しやすい。",
                advice="既存データを持つ環境で起動、読み書き、移行、失敗時の扱いを確認する。",
                files=unique(storage_infra_files),
                evidence=truncate_list(unique(evidence), 6),
            )
        )

    if model_files:
        findings.append(
            ReviewFinding(
                title="永続化モデル・保存プロパティ変更候補",
                severity="high" if not property_changes else "critical",
                category="durable-state",
                score=40 if not property_changes else 55,
                reason="保存モデルや永続化プロパティの追加・削除・型変更は、既存データとの互換性に影響する可能性がある。",
                advice="追加・削除・型変更・既定値・optional 化の意図と、旧データからの読み込み可否を確認する。",
                files=unique(model_files),
                evidence=truncate_list([f"保存プロパティ候補: {name}" for name in unique(property_changes)], 6),
            )
        )

    return findings


def detect_persistent_settings_findings(
    files: list[FileChange],
    diff_by_file: dict[str, DiffLines],
) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []

    settings_files = [file.path for file in files if matches_any(file.path, PERSISTENT_SETTINGS_PATTERNS)]
    if settings_files:
        key_changes: list[str] = []
        for path in settings_files:
            diff = diff_by_file.get(path, DiffLines([], []))
            key_changes.extend(
                match.group(1)
                for line in [*diff.added, *diff.removed]
                if (match := APP_STORAGE_CASE_PATTERN.match(line.strip()))
            )
        findings.append(
            ReviewFinding(
                title="永続設定キーの追加/変更候補",
                severity="high",
                category="persistent-settings",
                score=30,
                reason="UserDefaults / AppStorage のキーは一度導入すると長く背負いやすい。",
                advice="その設定が本当に永続化すべきか、名称と寿命が妥当かを確認する。",
                files=unique(settings_files),
                evidence=truncate_list([f"キー候補: {name}" for name in unique(key_changes)], 6),
            )
        )

    usage_files: list[str] = []
    usage_evidence: list[str] = []
    for file in files:
        path = file.path
        if matches_any(path, DEFAULT_IGNORE_USAGE_PATTERNS):
            continue
        diff = diff_by_file.get(path, DiffLines([], []))
        matched_lines = [
            line.strip()
            for line in diff.added
            if any(pattern.search(line) for pattern in PERSISTENT_USAGE_PATTERNS)
        ]
        if not matched_lines:
            continue
        usage_files.append(path)
        usage_evidence.extend(matched_lines)

    if usage_files:
        findings.append(
            ReviewFinding(
                title="永続設定の利用箇所追加候補",
                severity="medium",
                category="persistent-settings",
                score=25,
                reason="新しい保存値や読み出し前提が増えると、将来の開発で考慮し続ける必要が出る。",
                advice="その値が永続化である必要があるか、一時状態で済まないかを確認する。",
                files=unique(usage_files),
                evidence=truncate_list(unique(usage_evidence), 6),
            )
        )

    return findings


def build_review_findings(
    repo: Path,
    files: list[FileChange],
    diff_by_file: dict[str, DiffLines],
) -> list[ReviewFinding]:
    findings = [
        *detect_external_identity_config_findings(files, diff_by_file),
        *detect_capability_findings(files, diff_by_file),
        *detect_durable_state_findings(repo, files, diff_by_file),
        *detect_persistent_settings_findings(files, diff_by_file),
    ]
    return sorted(findings, key=lambda finding: (-finding.score, -SEVERITY_ORDER[finding.severity], finding.title))


def score_items(
    files: list[FileChange],
    findings: list[ReviewFinding],
    signals: list[RiskSignal],
) -> list[dict[str, int | str]]:
    items: list[dict[str, int | str]] = []
    covered_finding_paths = {path for finding in findings for path in finding.files}
    for finding in findings:
        items.append(
            {
                "source": "finding",
                "name": finding.title,
                "severity": finding.severity,
                "category": finding.category,
                "score": finding.score,
            }
        )
    for signal in signals:
        if signal.matched_files and set(signal.matched_files).issubset(covered_finding_paths):
            continue
        items.append(
            {
                "source": "path-rule",
                "name": signal.name,
                "severity": signal.severity,
                "category": signal.category,
                "score": signal.score,
            }
        )

    if files and not items:
        items.append(
            {
                "source": "fallback",
                "name": "未分類の出荷差分",
                "severity": "medium",
                "category": "unknown-change",
                "score": FALLBACK_UNKNOWN_CHANGE_SCORE,
            }
        )

    strongest_by_category: dict[str, dict[str, int | str]] = {}
    for item in items:
        category = str(item["category"])
        existing = strongest_by_category.get(category)
        if existing is None:
            strongest_by_category[category] = item
            continue

        item_score = int(item["score"])
        existing_score = int(existing["score"])
        if item_score > existing_score:
            strongest_by_category[category] = item
            continue

        if (
            item_score == existing_score
            and SEVERITY_ORDER[str(item["severity"])] > SEVERITY_ORDER[str(existing["severity"])]
        ):
            strongest_by_category[category] = item

    return sorted(
        strongest_by_category.values(),
        key=lambda item: (-int(item["score"]), str(item["name"])),
    )


def truncate_diff_lines(lines: list[str], limit: int) -> list[str]:
    if len(lines) <= limit:
        return lines
    remaining = len(lines) - limit
    return [*lines[:limit], f"... (+{remaining} 行)"]


def build_snippets_for_files(
    title: str,
    category: str,
    source: str,
    files: list[str],
    diff_by_file: dict[str, DiffLines],
    *,
    max_files: int = 3,
    max_lines: int = 14,
) -> list[DiffSnippet]:
    snippets: list[DiffSnippet] = []
    for path in unique(files)[:max_files]:
        diff = diff_by_file.get(path)
        if not diff or not diff.changed:
            continue
        snippets.append(
            DiffSnippet(
                title=title,
                category=category,
                source=source,
                file=path,
                lines=truncate_diff_lines(diff.changed, max_lines),
            )
        )
    return snippets


def build_risk_diff_snippets(
    findings: list[ReviewFinding],
    signals: list[RiskSignal],
    diff_by_file: dict[str, DiffLines],
    *,
    max_snippets: int = 8,
) -> list[DiffSnippet]:
    snippets: list[DiffSnippet] = []
    covered_finding_paths = {path for finding in findings for path in finding.files}

    for finding in findings:
        if finding.score < 20:
            continue
        snippets.extend(
            build_snippets_for_files(
                finding.title,
                finding.category,
                "finding",
                finding.files,
                diff_by_file,
            )
        )

    for signal in signals:
        if signal.score < 20:
            continue
        if signal.matched_files and set(signal.matched_files).issubset(covered_finding_paths):
            continue
        snippets.extend(
            build_snippets_for_files(
                signal.name,
                signal.category,
                "path-rule",
                signal.matched_files,
                diff_by_file,
            )
        )

    return snippets[:max_snippets]


def total_score(items: list[dict[str, int | str]]) -> int:
    scores = sorted((int(item["score"]) for item in items), reverse=True)
    if not scores:
        return 0

    score = scores[0]
    for secondary_score in scores[1:]:
        if secondary_score >= 60:
            score += 5
        elif secondary_score >= 40:
            score += 3
        elif secondary_score >= 25:
            score += 1

    return min(HEURISTIC_SCORE_MAX, score)


def risk_from_score(score: int) -> str:
    if score <= 0:
        return "none"
    if score < 20:
        return "low"
    if score < 40:
        return "medium"
    if score < 80:
        return "high"
    return "critical"


def release_decision(score: int) -> str:
    if score >= 80:
        return "Block"
    if score >= 60:
        return "Hold for review"
    if score >= 40:
        return "Proceed with caution"
    if score >= 20:
        return "Review recommended"
    return "Proceed"


def release_posture(score: int, files: list[FileChange], findings: list[ReviewFinding]) -> str:
    if not files:
        return "未リリース差分は見つかっていません。"
    if score >= 90:
        return "そのまま出すと大きな問題につながる可能性が高い変更候補があります。リリースを止めて原因を確認するべきです。"
    if score >= 80:
        return "重大な変更候補があります。根拠を確認し終えるまでリリースを止めるべきです。"
    if score >= 60:
        return "リリース前に手動レビューで可否を判断するべき変更候補があります。"
    if score >= 40:
        return "明確なリスク候補があります。変更意図と重点検証を揃えてから出す方が安全です。"
    if score >= 20:
        return "軽い手動レビューで変更意図を確認してから進めるのが無難です。"
    return "限定的な確認で進めやすい状態です。"


def confidence(findings: list[ReviewFinding], signals: list[RiskSignal]) -> str:
    if findings or signals:
        return "中"
    return "低"


def sort_signals(signals: list[RiskSignal]) -> list[RiskSignal]:
    return sorted(
        signals,
        key=lambda signal: (
            -signal.score,
            -SEVERITY_ORDER[signal.severity],
            signal.name.lower(),
        ),
    )


def format_severity(severity: str) -> str:
    return SEVERITY_LABELS.get(severity, severity)


def render_findings(title: str, findings: list[ReviewFinding]) -> list[str]:
    lines = [f"## {title}"]
    if not findings:
        lines.append("- 該当なし")
        return lines

    for finding in findings:
        lines.append(f"- `[{format_severity(finding.severity)} / {finding.score}点]` {finding.title}")
        lines.append(f"  理由: {finding.reason}")
        lines.append(f"  対象: {', '.join(truncate_list(finding.files, 4))}")
        if finding.evidence:
            lines.append(f"  手がかり: {', '.join(truncate_list(finding.evidence, 4))}")
        lines.append(f"  確認: {finding.advice}")
    return lines


def render_signals(title: str, signals: list[RiskSignal]) -> list[str]:
    lines = [f"## {title}"]
    if not signals:
        lines.append("- 該当なし")
        return lines

    for signal in signals:
        lines.append(f"- `[{format_severity(signal.severity)} / {signal.score}点]` {signal.name}")
        lines.append(f"  理由: {signal.reason or '理由なし'}")
        lines.append(f"  対象: {', '.join(truncate_list(signal.matched_files, 4))}")
        lines.append(f"  確認: {signal.advice or '確認手順なし'}")
    return lines


def render_score_breakdown(items: list[dict[str, int | str]]) -> list[str]:
    lines = ["## スコア内訳"]
    if not items:
        lines.append("- `0/100` 未リリース差分なし")
        return lines

    for item in items[:8]:
        lines.append(
            f"- `{item['score']}点` {item['name']} ({format_severity(str(item['severity']))}, {item['source']}, {item['category']})"
        )
    if len(items) > 8:
        lines.append(f"- ... (+{len(items) - 8} 件)")
    lines.append("- 点数は単純合計ではありません。最も高いリスク軸を基準に、独立した追加リスクだけを小さく補正します。")
    lines.append("- `100点` は大きな実害がほぼ避けられないと判断できる場合の上限で、通常のヒューリスティック検出は `95点` を上限にします。")
    return lines


def render_diff_snippets(snippets: list[dict]) -> list[str]:
    lines = ["## リスク差分抜粋"]
    if not snippets:
        lines.append("- 該当なし")
        return lines

    for snippet in snippets:
        lines.append(
            f"- {snippet['title']} (`{snippet['category']}`, {snippet['source']}) / `{snippet['file']}`"
        )
        lines.append("```diff")
        lines.extend(snippet["lines"])
        lines.append("```")
    lines.append("- 抜粋はリスク確認用に短く丸めています。全差分が必要なら `--verbose` と `git diff` を併用してください。")
    return lines


def render_markdown(report: dict, max_files: int, max_commits: int, verbose: bool) -> str:
    blocker_findings = [
        ReviewFinding(**finding)
        for finding in report["review_findings"]
        if SEVERITY_ORDER[finding["severity"]] >= SEVERITY_ORDER["high"]
    ]
    minor_findings = [
        ReviewFinding(**finding)
        for finding in report["review_findings"]
        if SEVERITY_ORDER[finding["severity"]] < SEVERITY_ORDER["high"]
    ]
    signals = [RiskSignal(**signal) for signal in report["risk_signals"]]

    lines: list[str] = []
    lines.append("# リリースリスク診断")
    lines.append("")
    lines.append("## 判定")
    lines.append(f"- リスクスコア: `{report['risk_score']}/{report['risk_score_max']}`")
    lines.append(f"- ヒューリスティック上限: `{report['heuristic_score_max']}`")
    lines.append(f"- 総合リスク: `{format_severity(report['overall_risk'])}`")
    lines.append(f"- リリース判定: `{report['release_decision']}`")
    lines.append(f"- リリース方針: {report['release_posture']}")
    lines.append(
        "- 判定しきい値: `80-100=Block`, `60-79=Hold for review`, "
        "`40-59=Proceed with caution`, `20-39=Review recommended`, `0-19=Proceed`"
    )
    lines.append(f"- 信頼度: `{report['confidence']}`")
    lines.append(f"- 比較範囲: `{report['range']}`")
    lines.append(f"- 基準タグ: `{report['base_ref']}`")
    lines.append(f"- 先頭コミット: `{report['head_commit']}`")
    lines.append(f"- コミット数: `{report['commit_count']}`")
    lines.append(f"- 変更ファイル数: `{report['file_count']}`")
    lines.append("- ルールソース: `built-in`")
    if report["top_areas"]:
        areas = ", ".join(
            f"`{entry['area']}` ({entry['count']})" for entry in report["top_areas"]
        )
        lines.append(f"- 主な変更領域: {areas}")
    lines.append("")

    lines.extend(render_score_breakdown(report["score_breakdown"]))
    lines.append("")
    lines.extend(render_diff_snippets(report["risk_diff_snippets"]))
    lines.append("")
    lines.extend(render_findings("先に止めて確認したい項目", blocker_findings))
    lines.append("")
    lines.extend(render_findings("追加で確認したい項目", minor_findings))
    lines.append("")
    lines.extend(render_signals("変更面から見たリスクシグナル", signals))

    if not verbose:
        lines.append("")
        lines.append("## 補足")
        lines.append("- 差分一覧は省略しています。必要なら `--verbose` でファイル一覧とコミット一覧を表示できます。")
        return "\n".join(lines)

    lines.append("")
    lines.append("## 変更ファイル")
    if report["files"]:
        for file in report["files"][:max_files]:
            old_path = f" <- `{file['old_path']}`" if file["old_path"] else ""
            lines.append(f"- `{file['status']}` `{file['path']}`{old_path}")
        remaining_files = report["file_count"] - min(report["file_count"], max_files)
        if remaining_files > 0:
            lines.append(f"- ... (+{remaining_files} 件)")
    else:
        lines.append("- 該当なし")

    lines.append("")
    lines.append("## コミット")
    if report["commits"]:
        for commit in report["commits"][:max_commits]:
            lines.append(
                f"- `{commit['date']}` `{commit['short_hash']}` {commit['subject']} ({commit['author']})"
            )
        remaining_commits = report["commit_count"] - min(report["commit_count"], max_commits)
        if remaining_commits > 0:
            lines.append(f"- ... (+{remaining_commits} 件)")
    else:
        lines.append("- 該当なし")

    return "\n".join(lines)


def build_report(args: argparse.Namespace) -> dict:
    repo = Path(args.repo).resolve()
    if not repo.exists():
        raise FileNotFoundError(f"Repository not found: {repo}")

    base_ref = args.base_ref or detect_base_ref(repo, args.head_ref, args.tag_pattern)
    head_ref = args.head_ref
    commits = get_commits(repo, base_ref, head_ref)
    files = get_files(repo, base_ref, head_ref)
    diff_by_file = get_diff_lines(repo, base_ref, head_ref, files)

    rules = load_rules_from_dicts(BUILTIN_RULES)

    signals = [signal for signal in (evaluate_rule(rule, files) for rule in rules) if signal]
    signals = sort_signals(signals)

    findings = build_review_findings(repo, files, diff_by_file)

    score_breakdown = score_items(files, findings, signals)
    risk_diff_snippets = build_risk_diff_snippets(findings, signals, diff_by_file)
    risk_score = total_score(score_breakdown)
    risk = risk_from_score(risk_score)
    return {
        "repo": str(repo),
        "range": f"{base_ref}..{head_ref}",
        "base_ref": base_ref,
        "head_ref": head_ref,
        "head_commit": short_ref(repo, head_ref),
        "commit_count": len(commits),
        "file_count": len(files),
        "risk_score": risk_score,
        "risk_score_max": SCORE_MAX,
        "heuristic_score_max": HEURISTIC_SCORE_MAX,
        "overall_risk": risk,
        "release_decision": release_decision(risk_score),
        "confidence": confidence(findings, signals),
        "release_posture": release_posture(risk_score, files, findings),
        "top_areas": top_areas(files),
        "score_breakdown": score_breakdown,
        "risk_diff_snippets": [asdict(snippet) for snippet in risk_diff_snippets],
        "review_findings": [asdict(finding) for finding in findings],
        "risk_signals": [asdict(signal) for signal in signals],
        "files": [asdict(file) for file in files],
        "commits": [asdict(commit) for commit in commits],
    }


def main() -> int:
    args = parse_args()
    try:
        report = build_report(args)
    except (FileNotFoundError, GitCommandError, ValueError) as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render_markdown(report, args.max_files, args.max_commits, args.verbose))
    return 0


if __name__ == "__main__":
    sys.exit(main())
