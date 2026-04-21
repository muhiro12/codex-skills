#!/usr/bin/env python3
"""Analyze release-blocking risk since the latest reachable release tag."""

from __future__ import annotations

import argparse
import json
import runpy
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from fnmatch import fnmatchcase
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(
        str(Path(__file__).with_name("review_release_risk.py")),
        run_name="__main__",
    )
    raise SystemExit(0)

SEVERITY_ORDER = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

BUILTIN_RULES = [
    {
        "name": "Persistence or migration surface changed",
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
            "**/Schema/**",
            "**/*.sql",
            "**/*.sqlite",
            "**/*.xcdatamodeld/**",
        ],
        "reason": "Storage or migration changes can affect existing user data and upgrade safety.",
        "advice": "Run upgrade, migration, and persistence regression coverage before release.",
    },
    {
        "name": "Authentication or security surface changed",
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
        "reason": "Auth and security changes can block sign-in, permissions, or credential handling.",
        "advice": "Verify authentication flows, secure storage, and entitlement-sensitive behavior.",
    },
    {
        "name": "Build, packaging, or dependency configuration changed",
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
            "*.xcodeproj/project.pbxproj",
            "**/*.xcscheme",
            "**/*.plist",
        ],
        "reason": "Build and dependency changes can affect what ships even when feature code looks unchanged.",
        "advice": "Rebuild from a clean state and verify release automation, signing, and packaging.",
    },
    {
        "name": "Shared domain or business logic changed",
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
        "reason": "Shared logic changes often affect multiple features or targets.",
        "advice": "Run focused regression on the touched feature set and its integrations.",
    },
    {
        "name": "Networking or API client changed",
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
        "reason": "Transport and API changes can surface only when real data flows through the app.",
        "advice": "Verify request, response, retry, and error handling paths against real or staged data.",
    },
    {
        "name": "Only UI or resource files changed",
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
        "reason": "The change surface appears limited to presentation and bundled assets.",
        "advice": "Targeted manual checks are usually enough unless explicit custom rules raise the bar further.",
    },
    {
        "name": "Only docs or tests changed",
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
        "reason": "Documentation or test-only changes rarely change shipped behavior directly.",
        "advice": "Confirm that no generated or packaged artifacts changed unexpectedly.",
    },
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


class GitCommandError(RuntimeError):
    """Raised when a git command fails."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize the diff between the latest release tag and a target ref.",
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
        default=40,
        help="Maximum changed files to print in markdown output",
    )
    parser.add_argument(
        "--max-commits",
        type=int,
        default=30,
        help="Maximum commits to print in markdown output",
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
    normalized = path.replace("\\", "/").lstrip("./")
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
        raise GitCommandError("No reachable tag found. Pass --base-ref explicitly.")
    return base_ref


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

    return [
        {"area": area, "count": count}
        for area, count in counter.most_common(limit)
    ]


def truncate_list(values: list[str], limit: int) -> list[str]:
    if len(values) <= limit:
        return values
    remaining = len(values) - limit
    return [*values[:limit], f"... (+{remaining} more)"]


def overall_risk(signals: list[RiskSignal], files: list[FileChange]) -> str:
    if not files:
        return "none"
    if not signals:
        return "medium"
    return max(signals, key=lambda signal: SEVERITY_ORDER[signal.severity]).severity


def release_posture(risk: str) -> str:
    if risk == "none":
        return "No unreleased changes were detected."
    if risk == "low":
        return "Keep validation targeted. The blast radius appears limited."
    if risk == "medium":
        return "Run focused regression on touched features and their integrations."
    if risk == "high":
        return "Run broader regression and avoid a rushed rollout."
    return "Treat this as a careful release candidate with rollback awareness."


def confidence(signals: list[RiskSignal]) -> str:
    if signals:
        return "medium"
    return "low"


def render_markdown(report: dict, max_files: int, max_commits: int) -> str:
    lines: list[str] = []
    lines.append("# Release Diff Analysis")
    lines.append("")
    lines.append("## Scope")
    lines.append(f"- Repository: `{report['repo']}`")
    lines.append(f"- Range: `{report['range']}`")
    lines.append(f"- Base ref: `{report['base_ref']}`")
    lines.append(f"- Head ref: `{report['head_ref']}`")
    lines.append(f"- Head commit: `{report['head_commit']}`")
    lines.append(f"- Commits: `{report['commit_count']}`")
    lines.append(f"- Changed files: `{report['file_count']}`")
    lines.append("- Rule source: `built-in`")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append(f"- Overall risk: `{report['overall_risk']}`")
    lines.append(f"- Confidence: `{report['confidence']}`")
    lines.append(f"- Release posture: {report['release_posture']}")
    if report["top_areas"]:
        areas = ", ".join(
            f"`{entry['area']}` ({entry['count']})"
            for entry in report["top_areas"]
        )
        lines.append(f"- Main areas: {areas}")
    lines.append("")
    lines.append("## Risk Signals")
    if report["risk_signals"]:
        for signal in report["risk_signals"]:
            lines.append(f"- `{signal['severity']}` {signal['name']}")
            lines.append(f"  Reason: {signal['reason'] or 'No reason supplied.'}")
            files = ", ".join(truncate_list(signal["matched_files"], 5))
            lines.append(f"  Files: {files or 'None'}")
            lines.append(f"  Advice: {signal['advice'] or 'No advice supplied.'}")
    else:
        lines.append("- No risk signals matched.")
    lines.append("")
    lines.append("## Change Surface")
    if report["top_areas"]:
        for entry in report["top_areas"]:
            lines.append(f"- `{entry['area']}`: {entry['count']} files")
    else:
        lines.append("- No changed files.")
    lines.append("")
    lines.append("## Files")
    if report["files"]:
        for file in report["files"][:max_files]:
            old_path = f" <- `{file['old_path']}`" if file["old_path"] else ""
            lines.append(f"- `{file['status']}` `{file['path']}`{old_path}")
        remaining_files = report["file_count"] - min(report["file_count"], max_files)
        if remaining_files > 0:
            lines.append(f"- ... (+{remaining_files} more files)")
    else:
        lines.append("- No changed files.")
    lines.append("")
    lines.append("## Commits")
    if report["commits"]:
        for commit in report["commits"][:max_commits]:
            lines.append(
                f"- `{commit['date']}` `{commit['short_hash']}` {commit['subject']} ({commit['author']})"
            )
        remaining_commits = report["commit_count"] - min(report["commit_count"], max_commits)
        if remaining_commits > 0:
            lines.append(f"- ... (+{remaining_commits} more commits)")
    else:
        lines.append("- No unreleased commits.")
    return "\n".join(lines)


def build_report(args: argparse.Namespace) -> dict:
    repo = Path(args.repo).resolve()
    if not repo.exists():
        raise FileNotFoundError(f"Repository not found: {repo}")

    base_ref = args.base_ref or detect_base_ref(repo, args.head_ref, args.tag_pattern)
    head_ref = args.head_ref
    commits = get_commits(repo, base_ref, head_ref)
    files = get_files(repo, base_ref, head_ref)

    rules = load_rules_from_dicts(BUILTIN_RULES)

    signals = [signal for signal in (evaluate_rule(rule, files) for rule in rules) if signal]
    signals = sort_signals(signals)

    risk = overall_risk(signals, files)
    report = {
        "repo": str(repo),
        "range": f"{base_ref}..{head_ref}",
        "base_ref": base_ref,
        "head_ref": head_ref,
        "head_commit": short_ref(repo, head_ref),
        "commit_count": len(commits),
        "file_count": len(files),
        "overall_risk": risk,
        "confidence": confidence(signals),
        "release_posture": release_posture(risk),
        "top_areas": top_areas(files),
        "risk_signals": [asdict(signal) for signal in signals],
        "files": [asdict(file) for file in files],
        "commits": [asdict(commit) for commit in commits],
    }
    return report


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


def sort_signals(signals: list[RiskSignal]) -> list[RiskSignal]:
    return sorted(
        signals,
        key=lambda signal: (
            -SEVERITY_ORDER[signal.severity],
            signal.name.lower(),
        ),
    )


def main() -> int:
    args = parse_args()
    try:
        report = build_report(args)
    except (FileNotFoundError, GitCommandError, ValueError) as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report, args.max_files, args.max_commits))
    return 0


if __name__ == "__main__":
    sys.exit(main())
