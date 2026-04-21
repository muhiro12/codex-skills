#!/usr/bin/env python3
"""Review release-blocking risk since the latest reachable release tag."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from fnmatch import fnmatchcase
from pathlib import Path

SEVERITY_ORDER = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

SEVERITY_LABELS = {
    "none": "なし",
    "low": "低",
    "medium": "中",
    "high": "高",
    "critical": "重大",
}

BUILTIN_RULES = [
    {
        "name": "永続データ・マイグレーション面の変更",
        "severity": "high",
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
        "reason": "永続データや移行処理の変更は、既存ユーザーの起動不能やデータ不整合につながりやすい。",
        "advice": "既存データを持つ状態での起動と移行成否を先に確認する。",
    },
    {
        "name": "権限・セキュリティ面の変更",
        "severity": "high",
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
        "mode": "any",
        "paths": [
            ".github/workflows/**",
            "ci_scripts/**",
            "Dockerfile*",
            "docker/**",
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

CAPABILITY_MARKER_PATTERNS = [
    re.compile(r"<key>([^<]+)</key>"),
    re.compile(r"INFOPLIST_KEY_(NS[A-Za-z0-9]+UsageDescription)"),
    re.compile(r"(aps-environment|com\.apple\.developer\.[A-Za-z0-9\.-]+)"),
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

STORAGE_INFRA_PATTERNS = [
    "**/Database.swift",
    "**/*Migrator*.swift",
    "**/ModelContainerFactory.swift",
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
    mode: str
    paths: list[str]
    exclude_paths: list[str]
    reason: str
    advice: str


@dataclass
class RiskSignal:
    name: str
    severity: str
    mode: str
    reason: str
    advice: str
    matched_files: list[str]


@dataclass
class DiffLines:
    added: list[str]
    removed: list[str]


@dataclass
class ReviewFinding:
    title: str
    severity: str
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
                mode=raw_rule.get("mode", "any"),
                paths=[normalize_path(pattern) for pattern in raw_rule["paths"]],
                exclude_paths=[normalize_path(pattern) for pattern in raw_rule.get("exclude_paths", [])],
                reason=raw_rule.get("reason", ""),
                advice=raw_rule.get("advice", ""),
            )
        )
    return rules


def path_matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatchcase(path, pattern) for pattern in patterns)


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
        for line in patch.splitlines():
            if line.startswith("+++ ") or line.startswith("--- ") or line.startswith("@@"):
                continue
            if line.startswith("+"):
                added.append(line[1:])
                continue
            if line.startswith("-"):
                removed.append(line[1:])
        diffs[file.path] = DiffLines(added=added, removed=removed)
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
    return any(fnmatchcase(path, pattern) for pattern in patterns)


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
            reason="不要な権限要求や審査リスク、既存機能の破壊につながる変更面。",
            advice="entitlements / Info.plist / project 設定の差分が意図通りかを手動確認する。",
            files=unique(capability_files),
            evidence=evidence,
        )
    ]


def detect_swiftdata_findings(
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
        if matches_any(path, STORAGE_INFRA_PATTERNS):
            storage_infra_files.append(path)

        if "@Model" in content or any("@Model" in line for line in [*diff.added, *diff.removed]):
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
                if any(token in line for token in ["ModelContainer", "Database", "legacyURL", "fileName", "url"])
            )
        findings.append(
            ReviewFinding(
                title="SwiftData の保存先・移行導線の変更候補",
                severity="critical",
                reason="保存先 URL や移行処理の変更は、既存 DB の起動不能やデータ欠落に直結しやすい。",
                advice="既存 DB を持つ端末/シミュレータで起動し、移行とデータ維持を確認する。",
                files=unique(storage_infra_files),
                evidence=truncate_list(unique(evidence), 6),
            )
        )

    if model_files:
        findings.append(
            ReviewFinding(
                title="SwiftData モデル変更候補",
                severity="high" if not property_changes else "critical",
                reason="`@Model` の変更は永続スキーマへ影響する可能性がある。",
                advice="保存プロパティ追加・削除・型変更の意図と移行影響を確認する。",
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
        *detect_capability_findings(files, diff_by_file),
        *detect_swiftdata_findings(repo, files, diff_by_file),
        *detect_persistent_settings_findings(files, diff_by_file),
    ]
    return sorted(findings, key=lambda finding: (-SEVERITY_ORDER[finding.severity], finding.title))


def overall_risk(files: list[FileChange], findings: list[ReviewFinding], signals: list[RiskSignal]) -> str:
    if not files:
        return "none"

    severities = [finding.severity for finding in findings] + [signal.severity for signal in signals]
    if not severities:
        return "medium"
    return max(severities, key=lambda severity: SEVERITY_ORDER[severity])


def release_posture(risk: str, findings: list[ReviewFinding]) -> str:
    if risk == "none":
        return "未リリース差分は見つかっていません。"
    if any(SEVERITY_ORDER[finding.severity] >= SEVERITY_ORDER["high"] for finding in findings):
        return "先に手動レビューを入れてから出す方が安全です。"
    if risk == "low":
        return "限定的な確認で進めやすい状態です。"
    if risk == "medium":
        return "機能周辺の回帰確認をしてから出すのが無難です。"
    if risk == "high":
        return "急いで出さず、変更意図と検証結果を揃えてから出す方が安全です。"
    return "重大な変更候補があります。根拠を確認し終えるまでリリースを止めるべきです。"


def confidence(findings: list[ReviewFinding], signals: list[RiskSignal]) -> str:
    if findings or signals:
        return "中"
    return "低"

def sort_signals(signals: list[RiskSignal]) -> list[RiskSignal]:
    return sorted(
        signals,
        key=lambda signal: (
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
        lines.append(f"- `[{format_severity(finding.severity)}]` {finding.title}")
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
        lines.append(f"- `[{format_severity(signal.severity)}]` {signal.name}")
        lines.append(f"  理由: {signal.reason or '理由なし'}")
        lines.append(f"  対象: {', '.join(truncate_list(signal.matched_files, 4))}")
        lines.append(f"  確認: {signal.advice or '確認手順なし'}")
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
    lines.append(f"- 総合リスク: `{format_severity(report['overall_risk'])}`")
    lines.append(f"- リリース方針: {report['release_posture']}")
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

    risk = overall_risk(files, findings, signals)
    return {
        "repo": str(repo),
        "range": f"{base_ref}..{head_ref}",
        "base_ref": base_ref,
        "head_ref": head_ref,
        "head_commit": short_ref(repo, head_ref),
        "commit_count": len(commits),
        "file_count": len(files),
        "overall_risk": risk,
        "confidence": confidence(findings, signals),
        "release_posture": release_posture(risk, findings),
        "top_areas": top_areas(files),
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
