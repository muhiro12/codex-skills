# Release Risk Rules

この skill では release risk 判定を組み込みルールだけで行う。`release-risk-rules.toml` のような外部ルールファイルは使わない。

足りない観点が見つかった場合は、一時ファイルや repo-local 設定を足すのではなく、組み込みルールそのものを更新する。

## Canonical Source

判定ルールの正本は次のスクリプト。

1. `scripts/review_release_risk.py`

`scripts/analyze_release_diff.py` は互換ラッパーに留め、判定ロジックを重複させない。

## Rule Design

- `mode = "any"` は「このどれかが変わったら止めたい」に使う。
- `mode = "all"` は「この範囲だけなら比較的安全」に使う。
- `category` は独立したリスク面を表す。同一カテゴリでは最も強い根拠だけをスコアに入れる。
- `score` は加点材料ではなく絶対リスク値として扱う。`0` は意味のあるリリースリスクなし、`100` はそのまま出すと大きな問題につながる可能性が非常に高い状態。
- 総合スコアは単純合計しない。最も高いカテゴリスコアを基準にし、独立した追加リスクだけを小さく補正する。
- 通常のヒューリスティック検出は `95` 点を上限にし、`100` 点は既知の破壊的根拠がある場合にだけ使う。
- `80-100` は `Block`、`60-79` は `Hold for review`、`40-59` は `Proceed with caution`、`20-39` は `Review recommended`、`0-19` は `Proceed`。
- `critical` は、不可逆または外部登録済みのID/設定値、永続状態の互換性破壊、起動不能、データ破損、不要権限追加のような後戻りしづらい変更に使う。
- `high` は、配布物や永続設定に影響しうるが、追加確認で止血可能な変更に使う。
- `low` の safe-only ルールは狭く保つ。ロジックが混ざるディレクトリを入れない。
- 具体検出 (`ReviewFinding`) はパス一致 (`RiskSignal`) より強い根拠として高めの絶対リスク値にする。
- 単一ファイルの重複検出や複数カテゴリの存在だけで `100` 点にしない。
- SwiftData、Bundle ID、App Group などの固有名は検出アンカーの例に留める。スコアの根拠は「永続状態の互換性」「外部固定ID/設定値」「権限・Capability」などのリスク軸で説明する。
- リスクありの具体検出と medium+ のパス一致には、レビューしやすい短い `diff` 抜粋を付ける。抜粋は根拠確認用であり、完全な差分一覧の代替にはしない。

## Maintenance Guidance

- まずは 3-6 個の高信頼ルールだけ置く。
- 「一意ID・外部固定設定」「永続状態の互換性」「権限・Capability」「永続設定」「配布設定」「UI-only」のように、観点ごとに分ける。
- 広いパスに安全なものと危険なものが混ざるなら `exclude_paths` を使う。
- 「今回のリリースを止めたい理由」が名前を見ただけで分かるようにする。
- iOS 系では `PRODUCT_BUNDLE_IDENTIFIER`、`DEVELOPMENT_TEAM`、App Group、iCloud container、Keychain access group、Associated Domains、URL Scheme、StoreKit product ID を「一意ID・外部固定設定」の検出例として拾う。
- 永続化系では SwiftData、Core Data、Realm、SQL、保存先 URL、スキーマ、migration を「永続状態の互換性」の検出例として拾う。
- 例外運用や一時的な repo 別設定は追加しない。
