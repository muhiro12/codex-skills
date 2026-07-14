#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

temporary_root="$(mktemp -d "${TMPDIR:-/tmp}/codex-skills-verify.XXXXXX")"
cleanup() {
  rm -rf "$temporary_root"
}
trap cleanup EXIT INT TERM

printf '[verify] repository metadata\n'
python3 scripts/verify_repository.py "$repo_root"

python_files=()
while IFS= read -r -d '' path; do
  python_files+=("$path")
done < <(git ls-files -z -- '*.py')

printf '[verify] Python syntax (%s files)\n' "${#python_files[@]}"
if [ "${#python_files[@]}" -gt 0 ]; then
  PYTHONPYCACHEPREFIX="$temporary_root/pycache" \
    python3 -m py_compile "${python_files[@]}"
fi

shell_files=()
while IFS= read -r -d '' path; do
  shell_files+=("$path")
done < <(git ls-files -z -- '*.sh')

printf '[verify] shell syntax (%s files)\n' "${#shell_files[@]}"
for path in "${shell_files[@]}"; do
  bash -n "$path"
done

test_files=()
while IFS= read -r -d '' path; do
  case "$path" in
    */fixtures/*)
      ;;
    */tests/test_*.py | */scripts/test_*.py)
      test_files+=("$path")
      ;;
  esac
done < <(git ls-files -z -- '*.py')

printf '[verify] Python tests (%s files)\n' "${#test_files[@]}"
for path in "${test_files[@]}"; do
  printf '  %s\n' "$path"
  PYTHONDONTWRITEBYTECODE=1 python3 "$path"
done

shell_test_files=()
while IFS= read -r -d '' path; do
  case "$path" in
    */fixtures/*)
      ;;
    */tests/test_*.sh)
      shell_test_files+=("$path")
      ;;
  esac
done < <(git ls-files -z -- '*.sh')

printf '[verify] shell tests (%s files)\n' "${#shell_test_files[@]}"
for path in "${shell_test_files[@]}"; do
  printf '  %s\n' "$path"
  bash "$path"
done

printf '[verify] whitespace\n'
git diff --check
git diff --cached --check

printf '[verify] success\n'
