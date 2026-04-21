# Release Risk Rules

この skill では release risk 判定を組み込みルールだけで行う。`release-risk-rules.toml` のような外部ルールファイルは使わない。

足りない観点が見つかった場合は、一時ファイルや repo-local 設定を足すのではなく、組み込みルールそのものを更新する。

## Canonical Source

判定ルールの正本は次の 2 つ。

1. `scripts/review_release_risk.py`
2. `scripts/analyze_release_diff.py`

両方の `BUILTIN_RULES` を同期して保つ。

## Rule Design

- `mode = "any"` は「このどれかが変わったら止めたい」に使う。
- `mode = "all"` は「この範囲だけなら比較的安全」に使う。
- `critical` は、起動不能、データ破損、不要権限追加のような後戻りしづらい変更に使う。
- `high` は、配布物や永続設定に影響しうるが、追加確認で止血可能な変更に使う。
- `low` の safe-only ルールは狭く保つ。ロジックが混ざるディレクトリを入れない。

## Maintenance Guidance

- まずは 3-6 個の高信頼ルールだけ置く。
- 「永続データ」「権限」「永続設定」「配布設定」「UI-only」のように、観点ごとに分ける。
- 広いパスに安全なものと危険なものが混ざるなら `exclude_paths` を使う。
- 「今回のリリースを止めたい理由」が名前を見ただけで分かるようにする。
- 例外運用や一時的な repo 別設定は追加しない。
