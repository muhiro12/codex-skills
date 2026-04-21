#!/usr/bin/env bash
set -euo pipefail

latest_run_id() {
  local run_base="$1"
  if [ ! -d "$run_base" ]; then
    return 0
  fi

  {
    for path in "$run_base"/*; do
      [ -d "$path" ] || continue
      basename "$path"
    done
  } | sort | tail -n 1
}

extract_agents_entrypoint() {
  local agents_path="$1"
  python3 - "$agents_path" <<'PY'
import re
import sys
from pathlib import Path

agents_path = Path(sys.argv[1])
if not agents_path.is_file():
    raise SystemExit(0)

text = agents_path.read_text(encoding="utf-8")
commands = re.findall(r"bash\s+(ci_scripts/[A-Za-z0-9_./-]+\.sh)", text)
if not commands:
    raise SystemExit(0)

for command in commands:
    if command.endswith("verify.sh"):
        print(command)
        raise SystemExit(0)

print(commands[0])
PY
}

detect_verify_entrypoint() {
  local agents_entrypoint=""
  local rel_path=""

  agents_entrypoint="$(extract_agents_entrypoint "AGENTS.md")"
  if [ -n "$agents_entrypoint" ] && [ -f "$agents_entrypoint" ]; then
    printf '%s\n' "$agents_entrypoint"
    return 0
  fi

  for rel_path in \
    "ci_scripts/tasks/verify_task_completion.sh" \
    "ci_scripts/tasks/verify.sh" \
    "ci_scripts/verify.sh" \
    "ci_scripts/tasks/verify_repository_state.sh" \
    "ci_scripts/tasks/run_required_builds.sh" \
    "ci_scripts/run_required_builds.sh"
  do
    if [ -f "$rel_path" ]; then
      printf '%s\n' "$rel_path"
      return 0
    fi
  done

  if [ -d "ci_scripts" ]; then
    find "ci_scripts" -type f -name "*.sh" | sort | head -n 1
    return 0
  fi
}

verify_output="/tmp/ci_verify_and_summarize_last.log"
: > "$verify_output"

run_base=".build/ci/runs"
pre_run="$(latest_run_id "$run_base")"
verify_entrypoint="$(detect_verify_entrypoint)"

if [ -z "$verify_entrypoint" ]; then
  echo "結果: ❌ failure"
  echo "最新RUN: (なし)"
  echo "要約:"
  echo "- このリポジトリでは verify 系CIエントリポイントを解決できず、最終ゲートを開始できません。"
  echo "- AGENTS.md の \`bash ci_scripts/...sh\` 記述、または ci_scripts 配下の標準 verify スクリプトが必要です。"
  echo "- git diff / staged diff レビューも未実施です。"
  echo "Pushリスク: high"
  echo "リスク理由:"
  echo "- verify 実行前提が欠けており、現時点では push 非推奨です。"
  echo "- 最終ゲートとして必要な latest run と git diff の確認が成立していません。"
  echo "次の一手:"
  echo "- AGENTS.md か ci_scripts/ に標準 verify エントリポイントを定義してください。"
  echo "- git 管理下のリポジトリルートで再実行してください。"
  exit 1
fi

verify_command="bash $verify_entrypoint"

set +e
bash "$verify_entrypoint" >"$verify_output" 2>&1
verify_exit=$?
set -e

post_run="$(latest_run_id "$run_base")"
latest_run="$post_run"
run_is_new="false"
if [ -n "$post_run" ] && [ "$pre_run" != "$post_run" ]; then
  run_is_new="true"
fi

run_dir=""
if [ -n "$latest_run" ]; then
  run_dir="$run_base/$latest_run"
fi

python3 - "$latest_run" "$run_dir" "$verify_exit" "$verify_command" "$verify_output" "$run_is_new" <<'PY'
import json
import re
import subprocess
import sys
from pathlib import Path


def read_text(path: Path | None) -> str:
    if path is None or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def clean_summary_line(line: str) -> str:
    line = re.sub(r"^#+\s*", "", line.strip())
    line = re.sub(r"^[-*]\s*", "", line)
    line = line.replace("`", "")
    return re.sub(r"\s+", " ", line).strip()


def load_summary_lines(path: Path | None) -> list[str]:
    if path is None or not path.is_file():
        return []

    lines: list[str] = []
    for raw_line in read_text(path).splitlines():
        cleaned = clean_summary_line(raw_line)
        if not cleaned:
            continue
        if cleaned in {"AI Run Summary", "CI Run Summary", "Overview"}:
            continue
        lines.append(cleaned)
        if len(lines) >= 6:
            break
    return lines


def parse_meta(path: Path | None) -> tuple[dict[str, object], str]:
    if path is None or not path.is_file():
        return {}, "meta.json が存在しません。"

    try:
        return json.loads(read_text(path)), ""
    except Exception as error:  # pragma: no cover - defensive
        return {}, f"meta.json の読取で問題がありました: {error}"


def normalize_lower(value: object) -> str:
    return str(value).strip().lower()


def resolve_failed_log(run_dir: Path | None, failed_log_value: str) -> Path | None:
    if not failed_log_value:
        return None

    direct = Path(failed_log_value)
    if direct.is_file():
        return direct

    if run_dir is not None:
        candidate = run_dir / failed_log_value
        if candidate.is_file():
            return candidate

    return None


def collect_warning_samples(*paths: Path | None) -> list[str]:
    samples: list[str] = []
    seen: set[str] = set()

    for path in paths:
        if path is None or not path.is_file():
            continue

        for raw_line in read_text(path).splitlines():
            cleaned = " ".join(raw_line.split())
            lower = cleaned.lower()
            if "warning" not in lower:
                continue
            if "no warning" in lower or "0 warning" in lower:
                continue
            if cleaned in seen:
                continue
            seen.add(cleaned)
            samples.append(cleaned[:160])
            if len(samples) >= 3:
                return samples

    return samples


def warning_looks_external(sample: str) -> bool:
    lower = sample.lower()
    external_markers = (
        "/pods/",
        "pods/",
        "/carthage/",
        "carthage/",
        ".build/checkouts/",
        "sourcepackages/checkouts/",
        "source packages/checkouts/",
    )
    return any(marker in lower for marker in external_markers)


def warning_matches_current_change(sample: str, changed_files: list[str]) -> bool:
    lower = sample.lower()
    path_match = re.match(r"(.+?):\d+(?::\d+)?:\s*warning", sample, re.IGNORECASE)
    if path_match:
        warning_path = path_match.group(1).replace("\\", "/").lower()
        for changed_file in changed_files:
            normalized_changed_file = changed_file.replace("\\", "/").lower()
            if warning_path.endswith(normalized_changed_file):
                return True

    for changed_file in changed_files:
        basename = Path(changed_file).name.lower()
        if basename and basename in lower:
            return True

    return False


def run_command(command: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            text=True,
        )
    except FileNotFoundError:
        return None

    if completed.returncode != 0:
        return None

    return completed.stdout


def parse_name_status(text: str) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        entries.append((parts[0], parts[-1]))
    return entries


def parse_numstat(text: str) -> tuple[list[tuple[str, int, int]], int]:
    entries: list[tuple[str, int, int]] = []
    total_lines = 0

    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        added = 0 if parts[0] == "-" else int(parts[0])
        deleted = 0 if parts[1] == "-" else int(parts[1])
        path = parts[2]
        entries.append((path, added, deleted))
        total_lines += added + deleted

    return entries, total_lines


def collect_git_state() -> dict[str, object]:
    git_root = run_command(["git", "rev-parse", "--show-toplevel"])
    if git_root is None:
        return {
            "available": False,
            "staged_files": [],
            "unstaged_files": [],
            "all_files": [],
            "total_lines": 0,
            "combined_patch_lower": "",
        }

    staged_status = parse_name_status(
        run_command(["git", "diff", "--cached", "--name-status", "--find-renames", "--relative"]) or ""
    )
    unstaged_status = parse_name_status(
        run_command(["git", "diff", "--name-status", "--find-renames", "--relative"]) or ""
    )
    _, staged_lines = parse_numstat(
        run_command(["git", "diff", "--cached", "--numstat", "--relative"]) or ""
    )
    _, unstaged_lines = parse_numstat(
        run_command(["git", "diff", "--numstat", "--relative"]) or ""
    )

    staged_files = sorted({path for _, path in staged_status})
    unstaged_files = sorted({path for _, path in unstaged_status})
    all_files = sorted(set(staged_files) | set(unstaged_files))
    staged_patch = run_command(["git", "diff", "--cached", "--no-color", "--unified=0", "--relative"]) or ""
    unstaged_patch = run_command(["git", "diff", "--no-color", "--unified=0", "--relative"]) or ""

    return {
        "available": True,
        "git_root": git_root.strip(),
        "staged_files": staged_files,
        "unstaged_files": unstaged_files,
        "all_files": all_files,
        "staged_count": len(staged_files),
        "unstaged_count": len(unstaged_files),
        "total_files": len(all_files),
        "total_lines": staged_lines + unstaged_lines,
        "combined_patch_lower": f"{staged_patch}\n{unstaged_patch}".lower(),
    }


def matching_paths(paths: list[str], pattern: str) -> list[str]:
    regex = re.compile(pattern, re.IGNORECASE)
    return [path for path in paths if regex.search(path)]


def dedupe_lines(lines: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for line in lines:
        if not line or line in seen:
            continue
        result.append(line)
        seen.add(line)
    return result


def limit_lines(lines: list[str], limit: int) -> list[str]:
    return dedupe_lines(lines)[:limit]


latest_run_arg, run_dir_arg, verify_exit_arg, verify_command, verify_output_arg, run_is_new_arg = sys.argv[1:7]
latest_run = latest_run_arg or "(なし)"
run_dir = Path(run_dir_arg) if run_dir_arg else None
verify_exit = int(verify_exit_arg)
verify_output = Path(verify_output_arg)
run_is_new = run_is_new_arg == "true"

summary_path = run_dir / "summary.md" if run_dir is not None else None
meta_path = run_dir / "meta.json" if run_dir is not None else None
commands_path = run_dir / "commands.txt" if run_dir is not None else None

summary_lines = load_summary_lines(summary_path)
meta, meta_error = parse_meta(meta_path)
status_field = str(meta.get("status", ""))
result_field = str(meta.get("result", ""))
success_field = meta.get("success", "")
failed_step = str(meta.get("failed_step", ""))
failed_log_value = str(meta.get("failed_log", ""))
resolved_failed_log = resolve_failed_log(run_dir, failed_log_value)

status_lower = normalize_lower(status_field)
result_lower = normalize_lower(result_field)
success_lower = normalize_lower(success_field)
meta_says_failure = success_lower == "false" or status_lower in {"failure", "failed", "error"} or result_lower in {"failure", "failed", "error"}
verify_failed = verify_exit != 0 or meta_says_failure
missing_run = run_dir is None

warning_samples = collect_warning_samples(verify_output, resolved_failed_log)
git_state = collect_git_state()
all_files = git_state.get("all_files", [])
repo_warning_samples = [
    sample for sample in warning_samples
    if not warning_looks_external(sample) and warning_matches_current_change(sample, all_files)
]
preexisting_warning_samples = [
    sample for sample in warning_samples
    if not warning_looks_external(sample) and not warning_matches_current_change(sample, all_files)
]
external_warning_samples = [sample for sample in warning_samples if warning_looks_external(sample)]
staged_count = int(git_state.get("staged_count", 0))
unstaged_count = int(git_state.get("unstaged_count", 0))
if bool(git_state.get("available")) and staged_count == 0 and unstaged_count == 0:
    diff_overview = "stage済み 0件 / 未stage 0件を確認しました。作業ツリーに差分はありません。"
else:
    diff_overview = f"stage済み {staged_count}件 / 未stage {unstaged_count}件を確認しました。"

if missing_run:
    summary_lines = [
        f"{verify_command} を実行しましたが、.build/ci/runs/ にRUNがありません。",
        f"verify_exit={verify_exit}",
        f"verifyログ: {verify_output}",
    ]
else:
    if not summary_lines:
        summary_lines.append("summary.md が見つかりません。")
    if len(summary_lines) < 3 and status_field:
        summary_lines.append(f"meta.json status: {status_field}")
    if len(summary_lines) < 3 and result_field:
        summary_lines.append(f"meta.json result: {result_field}")
    if len(summary_lines) < 3 and success_field != "":
        summary_lines.append(f"meta.json success: {success_field}")
    if len(summary_lines) < 3:
        summary_lines.append(f"verify_exit={verify_exit}")
    if not run_is_new and len(summary_lines) < 6:
        summary_lines.append("今回の実行では新しいRUNが作られず、既存の最新RUNを参照しました。")
    if meta_error and len(summary_lines) < 6:
        summary_lines.append(meta_error)
    if len(summary_lines) < 6:
        summary_lines.append(diff_overview)
    if len(summary_lines) < 6:
        summary_lines.append(f"実行コマンド: {verify_command}")

summary_lines = limit_lines(summary_lines, 6)

risk_rank = {"low": 0, "medium": 1, "high": 2}
risk_level = "low"
risk_reasons: list[str] = []
next_steps: list[str] = []


def raise_risk(level: str) -> None:
    global risk_level
    if risk_rank[level] > risk_rank[risk_level]:
        risk_level = level


def add_reason(level: str, message: str) -> None:
    raise_risk(level)
    risk_reasons.append(message)


combined_patch_lower = str(git_state.get("combined_patch_lower", ""))
total_files = int(git_state.get("total_files", 0))
total_lines = int(git_state.get("total_lines", 0))

if missing_run:
    add_reason("high", "latest run を確認できず、verify 結果を確定できません。現時点では push 非推奨です。")
    next_steps.append(f"{verify_output} を確認し、RUNが作られる状態にしてから再実行してください。")

if verify_failed:
    failed_step_text = failed_step or f"{verify_command} (exit={verify_exit})"
    if resolved_failed_log is not None:
        add_reason(
            "high",
            f"verify が失敗しています ({failed_step_text})。失敗ログ {resolved_failed_log} を確認するまで push 非推奨です。",
        )
        next_steps.append(f"{resolved_failed_log} を確認して verify 失敗を解消してください。")
    else:
        add_reason(
            "high",
            f"verify が失敗しています ({failed_step_text})。{verify_output} を確認するまで push 非推奨です。",
        )
        next_steps.append(f"{verify_output} を確認して verify 失敗を解消してください。")
    if commands_path is not None and commands_path.is_file():
        next_steps.append(f"{commands_path} で失敗コマンドを再確認してください。")

if not bool(git_state.get("available")):
    add_reason("high", "git diff / staged diff を確認できず、最終 push 判定が不完全です。現時点では push 非推奨です。")
    next_steps.append("git 管理下のリポジトリルートで再実行してください。")
else:
    if unstaged_count > 0:
        add_reason("medium", f"未stage差分が {unstaged_count} 件あり、push 対象が未固定です。")
        next_steps.append("未stage差分を整理し、push 対象を固定してから再判定してください。")

    if re.search(r"--no-verify\b", combined_patch_lower):
        add_reason("high", "差分に `--no-verify` があり、標準フック回避が疑われます。現時点では push 非推奨です。")
        next_steps.append("`--no-verify` を差分から外し、標準 verify フローに戻してください。")

    category_rules = [
        (
            "high",
            "entitlements / capabilities",
            r"(\.entitlements$|project\.pbxproj$|info\.plist$)",
            r"(aps-environment|com\.apple\.developer|associated-domains|app groups|push notifications|healthkit)",
        ),
        (
            "high",
            "persistence / migration / schema",
            r"(migration|schema|xcdatamodel|swiftdata|coredata|sqlite|realm|database|persistent|modelcontainer)",
            r"(migration|schema|swiftdata|coredata|sqlite|realm|database|persistent|modelcontainer)",
        ),
        (
            "medium",
            "notifications / background behavior",
            r"(notification|background|bgtask|push)",
            r"(notification|background|bgtask|push)",
        ),
        (
            "high",
            "remote config / force update",
            r"(remote.?config|force.?update|minimum.?version|required.?version|feature.?flag|kill.?switch|rollout)",
            r"(remote.?config|force.?update|minimum.?version|required.?version|feature.?flag|kill.?switch|rollout)",
        ),
        (
            "high",
            "ads / subscription / monetization",
            r"(admob|paywall|storekit|revenuecat|subscription|purchase|monet)",
            r"(admob|paywall|storekit|revenuecat|subscription|purchase|monet)",
        ),
        (
            "medium",
            "widgets / app intents / watch / deeplinks",
            r"(widget|appintent|appintents|appshortcut|watch|deeplink|universal.?link|urlscheme)",
            r"(widget|appintent|appintents|appshortcut|watch|deeplink|universal.?link|urlscheme)",
        ),
    ]

    for severity, label, path_pattern, patch_pattern in category_rules:
        hits = matching_paths(all_files, path_pattern)
        patch_hit = bool(re.search(patch_pattern, combined_patch_lower))
        if not hits and not patch_hit:
            continue

        if hits:
            shown = ", ".join(sorted(hits)[:2])
            add_reason(severity, f"{label} に関わる差分を検出しました: {shown}")
        else:
            add_reason(severity, f"{label} に関わる差分キーワードを検出しました。")

    if total_files >= 25 or total_lines >= 800:
        add_reason("high", f"差分が広く ({total_files} files, ±{total_lines} lines)、想定外の巻き込みがないか追加確認が必要です。")
        next_steps.append("差分を分割し、広い変更を push 前に個別レビューしてください。")
    elif total_files >= 10 or total_lines >= 250:
        add_reason("medium", f"差分がやや広く ({total_files} files, ±{total_lines} lines)、最終確認コストが高めです。")
        next_steps.append("差分を絞れるなら分割し、主要変更点を目視確認してください。")

if repo_warning_samples:
    add_reason(
        "high",
        f"verify 出力に現在変更または repo 管理範囲の warning が残っています: {repo_warning_samples[0]} 現時点では push 非推奨です。",
    )
    next_steps.append("warning を解消してから再度 verify を通してください。")
elif external_warning_samples:
    add_reason(
        "medium",
        f"verify 出力に外部依存または既存要因の可能性が高い warning が残っています: {external_warning_samples[0]}",
    )
    next_steps.append("warning の発生源が current change ではないことを確認し、必要なら別タスクで追跡してください。")
elif preexisting_warning_samples:
    add_reason(
        "medium",
        f"verify 出力に既存の未解消 warning の可能性が高い項目が残っています: {preexisting_warning_samples[0]}",
    )
    next_steps.append("warning の発生源が current change ではないことを確認し、必要なら別タスクで追跡してください。")

if not risk_reasons:
    risk_reasons.append(f"{diff_overview} 重大カテゴリ差分や warning は見当たりませんでした。")

if risk_level == "high" and not any("push 非推奨" in reason for reason in risk_reasons):
    risk_reasons.insert(0, "高リスク差分があるため、現時点では push 非推奨です。")

if not next_steps:
    if risk_level == "low" and not verify_failed and not missing_run:
        if staged_count == 0 and unstaged_count == 0:
            next_steps.append("差分はないため、この verify 結果を基準に次の変更へ進めます。")
        else:
            next_steps.append("このまま commit / push 前の最終確認へ進めます。")
    else:
        next_steps.append("リスク理由を解消または確認した後に再度このゲートを通してください。")

result_label = "✅ success"
if verify_failed or missing_run:
    result_label = "❌ failure"

print(f"結果: {result_label}")
print(f"最新RUN: {latest_run}")
print("要約:")
for line in summary_lines:
    print(f"- {line}")

print(f"Pushリスク: {risk_level}")
print("リスク理由:")
for line in limit_lines(risk_reasons, 4):
    print(f"- {line}")

print("次の一手:")
for line in limit_lines(next_steps, 3):
    print(f"- {line}")

if verify_failed or risk_level == "high":
    raise SystemExit(1)
raise SystemExit(0)
PY
