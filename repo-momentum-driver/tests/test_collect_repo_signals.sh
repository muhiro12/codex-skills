#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
collector="$script_dir/../scripts/collect_repo_signals.sh"
temporary_root="$(mktemp -d)"
trap 'rm -rf "$temporary_root"' EXIT

repo="$temporary_root/repo"
mkdir -p "$repo/Sources" "$repo/ignored-cache/Sample" "$repo/.build/Hidden"
git -C "$repo" init -q
git -C "$repo" config user.email "test@example.com"
git -C "$repo" config user.name "Test User"

printf '// package\n' > "$repo/Package.swift"
printf 'ignored-cache/\n' > "$repo/.gitignore"
printf '// tracked\n' > "$repo/Sources/App.swift"
printf '// ignored sample\n' > "$repo/ignored-cache/Sample/Package.swift"
printf '// generated sample\n' > "$repo/.build/Hidden/Package.swift"
git -C "$repo" add Package.swift .gitignore Sources/App.swift
git -C "$repo" commit -qm "Add fixture"

output="$(bash "$collector" "$repo")"
entrypoints="$(
  printf '%s\n' "$output" \
    | awk '/^## Potential Build\/Test Entry Points$/ { capture=1; next } /^## / { capture=0 } capture'
)"

if ! grep -Fxq './Package.swift' <<< "$entrypoints"; then
  echo "expected tracked Package.swift entrypoint" >&2
  exit 1
fi

if grep -Fq 'ignored-cache' <<< "$entrypoints"; then
  echo "ignored cache leaked into entrypoint discovery" >&2
  exit 1
fi

if grep -Fq '.build' <<< "$entrypoints"; then
  echo "generated .build tree leaked into entrypoint discovery" >&2
  exit 1
fi
