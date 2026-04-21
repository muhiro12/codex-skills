#!/usr/bin/env bash
set -euo pipefail

repo_path="${1:-.}"
max_todos="${MAX_TODOS:-80}"
max_changed_files="${MAX_CHANGED_FILES:-120}"
max_recent_paths="${MAX_RECENT_PATHS:-60}"

excluded_dirs=(
  ".build"
  "build"
  "DerivedData"
  ".git"
  ".swiftpm"
  "Pods"
  "Carthage"
)

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

clean_summary_line() {
  local line="$1"

  printf '%s' "$line" \
    | sed -E 's/^#+[[:space:]]*//; s/^[[:space:]]*[-*][[:space:]]*//; s/`//g; s/[[:space:]]+/ /g; s/^[[:space:]]*//; s/[[:space:]]*$//'
}

section() {
  printf "\n## %s\n" "$1"
}

if ! command -v git >/dev/null 2>&1; then
  echo "error: git is required" >&2
  exit 1
fi

if command -v rg >/dev/null 2>&1; then
  has_rg=1
else
  has_rg=0
fi

cd "$repo_path"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: not a git repository: $repo_path" >&2

  nested_repos=()
  while IFS= read -r line; do
    [ -n "$line" ] || continue
    nested_repos+=("$line")
  done < <(
    find . -mindepth 2 -maxdepth 3 -type d -name .git 2>/dev/null \
      | sed 's#/\.git$##' \
      | sort
  )

  if [[ "${#nested_repos[@]}" -gt 0 ]]; then
    echo "hint: found child git repositories:" >&2
    for nested_repo in "${nested_repos[@]}"; do
      echo "  - $nested_repo" >&2
    done
    echo "hint: rerun with one of the paths above." >&2
  fi

  exit 1
fi

has_make_target() {
  local target="$1"
  [ -f Makefile ] && grep -Eq "^[[:space:]]*$target:" Makefile
}

has_just_recipe() {
  local target="$1"
  [ -f justfile ] && grep -Eq "^[[:space:]]*$target:" justfile
}

has_package_script() {
  local script_name="$1"
  [ -f package.json ] && grep -Eq "\"$script_name\"[[:space:]]*:" package.json
}

resolve_ci_run_base() {
  local run_base=""

  if [ -f "AGENTS.md" ]; then
    run_base="$(
      grep -Eo '\.build/ci/runs/<RUN_ID>/' AGENTS.md 2>/dev/null \
        | head -n 1 \
        | sed 's#/<RUN_ID>/$##'
    )"
  fi

  if [ -z "$run_base" ]; then
    if [ -d ".build/ci/runs" ]; then
      run_base=".build/ci/runs"
    else
      run_base=".build/ci/runs"
    fi
  fi

  printf '%s\n' "$run_base"
}

print_latest_ci_run() {
  local run_base="${1:-}"
  local latest_run
  local run_dir
  local meta_path
  local summary_path
  local count

  if [ -z "$run_base" ]; then
    run_base="$(resolve_ci_run_base)"
  fi

  latest_run="$(latest_run_id "$run_base")"
  if [ -z "$latest_run" ]; then
    echo "(no runs)"
    return
  fi

  run_dir="$run_base/$latest_run"
  meta_path="$run_dir/meta.json"
  summary_path="$run_dir/summary.md"

  printf "run: %s\n" "$latest_run"
  printf "path: %s\n" "$run_dir"

  if [ -f "$meta_path" ]; then
    if command -v python3 >/dev/null 2>&1; then
      python3 - "$meta_path" <<'PY'
import json
import sys

with open(sys.argv[1], "r", encoding="utf-8") as handle:
    data = json.load(handle)

for key in ("status", "success", "failed_step", "failed_log"):
    value = data.get(key, "")
    if value not in ("", None):
        print(f"{key}: {value}")
PY
    else
      printf "meta.json: %s\n" "$meta_path"
    fi
  else
    echo "meta.json: (missing)"
  fi

  if [ -f "$summary_path" ]; then
    echo "summary:"
    count=0
    while IFS= read -r line; do
      cleaned="$(clean_summary_line "$line")"
      [ -n "$cleaned" ] || continue

      case "$cleaned" in
        "AI Run Summary"|"Overview")
          continue
          ;;
      esac

      printf -- "- %s\n" "$cleaned"
      count=$((count + 1))
      if [ "$count" -ge 6 ]; then
        break
      fi
    done < "$summary_path"

    if [ "$count" -eq 0 ]; then
      echo "- (empty)"
    fi
  else
    echo "summary.md: (missing)"
  fi
}

print_verification_candidates() {
  local candidate_index=0

  print_candidate() {
    local command="$1"
    candidate_index=$((candidate_index + 1))
    printf "%d. %s\n" "$candidate_index" "$command"
  }

  if [ -f "ci_scripts/tasks/verify_task_completion.sh" ]; then
    print_candidate "bash ci_scripts/tasks/verify_task_completion.sh"
  fi

  if [ -f "ci_scripts/tasks/verify_repository_state.sh" ]; then
    print_candidate "bash ci_scripts/tasks/verify_repository_state.sh"
  fi

  if [ -f "ci_scripts/tasks/verify.sh" ]; then
    print_candidate "bash ci_scripts/tasks/verify.sh"
  fi

  if [ -f "ci_scripts/tasks/run_required_builds.sh" ]; then
    print_candidate "bash ci_scripts/tasks/run_required_builds.sh"
  fi

  if has_make_target "verify"; then
    print_candidate "make verify"
  fi
  if has_make_target "check"; then
    print_candidate "make check"
  fi
  if has_make_target "test"; then
    print_candidate "make test"
  fi

  if has_just_recipe "verify"; then
    print_candidate "just verify"
  fi
  if has_just_recipe "check"; then
    print_candidate "just check"
  fi
  if has_just_recipe "test"; then
    print_candidate "just test"
  fi

  if has_package_script "verify"; then
    print_candidate "npm run verify"
  fi
  if has_package_script "check"; then
    print_candidate "npm run check"
  fi
  if has_package_script "test"; then
    print_candidate "npm run test"
  fi

  if [ -f "Package.swift" ]; then
    print_candidate "swift test"
  fi
  if [ -f "Cargo.toml" ]; then
    print_candidate "cargo test"
  fi
  if [ -f "go.mod" ]; then
    print_candidate "go test ./..."
  fi
  if [ -f "pyproject.toml" ] || [ -f "pytest.ini" ] || [ -f "tox.ini" ] || [ -f "setup.cfg" ]; then
    print_candidate "pytest"
  fi

  if [ "$candidate_index" -eq 0 ]; then
    echo "(no obvious repo-wide entrypoint found)"
  fi
}

recent_paths=()
while IFS= read -r line; do
  [ -n "$line" ] || continue
  recent_paths+=("$line")
done < <(
  {
    git --no-pager diff --name-only HEAD 2>/dev/null || true
    git --no-pager show --name-only --format='' --no-renames HEAD 2>/dev/null || true
  } | awk 'NF && !seen[$0]++' | head -n "$max_recent_paths"
)

recent_existing_paths=()
for path in "${recent_paths[@]}"; do
  if [ -e "$path" ]; then
    recent_existing_paths+=("$path")
  fi
done

section "Repo"
printf "path: %s\n" "$(pwd)"

section "Branch"
git rev-parse --abbrev-ref HEAD

section "Status (--short --branch)"
git status --short --branch

section "Recent Commits (last 12)"
git --no-pager log --oneline --decorate -n 12

section "Recent Paths (working tree + HEAD)"
if [[ "${#recent_paths[@]}" -eq 0 ]]; then
  echo "(none)"
else
  printf "%s\n" "${recent_paths[@]}"
fi

section "Changed Files (HEAD vs working tree/index)"
git --no-pager diff --name-status HEAD | head -n "$max_changed_files" || true

section "Unmerged Paths"
git diff --name-only --diff-filter=U || true

section "TODO/FIXME in Recent Paths"
if [[ "${#recent_existing_paths[@]}" -eq 0 ]]; then
  echo "(none)"
else
  if [[ "$has_rg" -eq 1 ]]; then
    recent_todos="$(rg -n '\b(TODO|FIXME|HACK|XXX)\b' -- "${recent_existing_paths[@]}" | head -n "$max_todos" || true)"
  else
    recent_todos="$(grep -nHE '\b(TODO|FIXME|HACK|XXX)\b' "${recent_existing_paths[@]}" | head -n "$max_todos" || true)"
  fi

  if [ -n "$recent_todos" ]; then
    printf "%s\n" "$recent_todos"
  else
    echo "(none)"
  fi
fi

section "Top TODO/FIXME/HACK/XXX"
if [[ "$has_rg" -eq 1 ]]; then
  top_todos="$(rg -n --hidden \
    --glob '!.git' \
    --glob '!.build' \
    --glob '!build' \
    --glob '!DerivedData' \
    --glob '!.swiftpm' \
    --glob '!Pods' \
    --glob '!Carthage' \
    '\b(TODO|FIXME|HACK|XXX)\b' \
    | head -n "$max_todos" || true)"
else
  top_todos="$(grep -RInE \
    --exclude-dir=.git \
    --exclude-dir=.build \
    --exclude-dir=build \
    --exclude-dir=DerivedData \
    --exclude-dir=.swiftpm \
    --exclude-dir=Pods \
    --exclude-dir=Carthage \
    '\b(TODO|FIXME|HACK|XXX)\b' \
    . | head -n "$max_todos" || true)"
fi

if [ -n "$top_todos" ]; then
  printf "%s\n" "$top_todos"
else
  echo "(none)"
fi

ci_run_base="$(resolve_ci_run_base)"
section "Latest CI Run ($ci_run_base)"
print_latest_ci_run "$ci_run_base"

section "Potential Build/Test Entry Points"
find . \
  \( -type d \
    \( -name '.git' -o -name '.build' -o -name 'build' -o -name 'DerivedData' -o -name '.swiftpm' -o -name 'Pods' -o -name 'Carthage' \) \
    -prune \
  \) -o \
  \( -type f \
    \( -name 'Package.swift' \
    -o -name '*.xcodeproj' \
    -o -name '*.xcworkspace' \
    -o -name 'Makefile' \
    -o -name 'justfile' \
    -o -name 'pyproject.toml' \
    -o -name 'package.json' \
    -o -name 'Cargo.toml' \
    -o -name 'go.mod' \
    -o -name 'build.gradle' \) \
    -print \
  \) \
  | sort

section "Verification Entrypoint Candidates"
print_verification_candidates

section "CI / Script Hints"
if [[ "$has_rg" -eq 1 ]]; then
  rg -n --hidden --glob '!.git' --glob 'ci_scripts/**' '(test|build|lint|check|verify)' | head -n 60 || true
else
  find ci_scripts -type f 2>/dev/null | head -n 60 || true
fi
