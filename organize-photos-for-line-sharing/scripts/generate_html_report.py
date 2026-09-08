#!/usr/bin/env python3
"""Generate a self-contained visual report for a Photos organization run."""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping


STATUS_LABELS = {
    "ja": {"ready": "共有準備完了", "review": "要確認", "blocked": "作業停止"},
    "en": {"ready": "Ready to share", "review": "Review required", "blocked": "Blocked"},
}


def require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def require_list(value: Any, field: str) -> List[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    return value


def require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def require_count(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def validate_report(raw: Mapping[str, Any]) -> Dict[str, Any]:
    report = dict(raw)
    language = report.get("language", "ja")
    if language not in STATUS_LABELS:
        raise ValueError("language must be ja or en")
    report["language"] = language
    report["title"] = require_text(
        report.get("title", "Photos LINE Sharing Report"), "title"
    )
    report["generated_at"] = require_text(report.get("generated_at"), "generated_at")
    status = report.get("status")
    if status not in {"ready", "review", "blocked"}:
        raise ValueError("status must be ready, review, or blocked")

    scope = dict(require_mapping(report.get("scope"), "scope"))
    for key in ("start", "end", "purpose"):
        scope[key] = require_text(scope.get(key), f"scope.{key}")
    report["scope"] = scope

    library = dict(require_mapping(report.get("library"), "library"))
    for phase in ("before", "after"):
        values = dict(require_mapping(library.get(phase), f"library.{phase}"))
        values["photos"] = require_count(
            values.get("photos"), f"library.{phase}.photos"
        )
        values["videos"] = require_count(
            values.get("videos"), f"library.{phase}.videos"
        )
        library[phase] = values
    library["new_arrivals"] = require_count(
        library.get("new_arrivals", 0), "library.new_arrivals"
    )
    library["sync_status"] = require_text(
        library.get("sync_status"), "library.sync_status"
    )
    before_total = library["before"]["photos"] + library["before"]["videos"]
    after_total = library["after"]["photos"] + library["after"]["videos"]
    if after_total < before_total:
        raise ValueError("library total decreased; investigate before reporting completion")
    report["library"] = library

    albums = require_list(report.get("albums"), "albums")
    normalized_albums: List[Dict[str, Any]] = []
    for index, value in enumerate(albums):
        album = dict(require_mapping(value, f"albums[{index}]"))
        album["name"] = require_text(album.get("name"), f"albums[{index}].name")
        for key in (
            "before",
            "confirmed_line_excluded",
            "ambiguous_excluded",
            "new_arrivals",
            "final",
            "missing",
            "extra",
            "duplicates",
        ):
            album[key] = require_count(album.get(key, 0), f"albums[{index}].{key}")
        normalized_albums.append(album)
    report["albums"] = normalized_albums

    date_review = dict(
        require_mapping(report.get("line_date_review"), "line_date_review")
    )
    for key in ("reviewed", "corrected", "already_2350", "skipped"):
        date_review[key] = require_count(
            date_review.get(key), f"line_date_review.{key}"
        )
    report["line_date_review"] = date_review

    orientation = dict(require_mapping(report.get("orientation"), "orientation"))
    self_captured = dict(
        require_mapping(orientation.get("self_captured"), "orientation.self_captured")
    )
    for key in ("portrait_candidates", "rotated", "kept_portrait", "unresolved"):
        self_captured[key] = require_count(
            self_captured.get(key), f"orientation.self_captured.{key}"
        )
    self_classified = (
        self_captured["rotated"]
        + self_captured["kept_portrait"]
        + self_captured["unresolved"]
    )
    if self_classified != self_captured["portrait_candidates"]:
        raise ValueError(
            "self-captured orientation classifications must equal portrait_candidates"
        )

    confirmed_line = dict(
        require_mapping(orientation.get("confirmed_line"), "orientation.confirmed_line")
    )
    for key in ("reviewed", "rotated", "unchanged", "unresolved"):
        confirmed_line[key] = require_count(
            confirmed_line.get(key), f"orientation.confirmed_line.{key}"
        )
    line_classified = (
        confirmed_line["rotated"]
        + confirmed_line["unchanged"]
        + confirmed_line["unresolved"]
    )
    if line_classified != confirmed_line["reviewed"]:
        raise ValueError(
            "confirmed LINE orientation classifications must equal reviewed"
        )
    orientation["self_captured"] = self_captured
    orientation["confirmed_line"] = confirmed_line
    report["orientation"] = orientation

    safety = dict(require_mapping(report.get("safety"), "safety"))
    for key in (
        "media_deleted",
        "albums_deleted",
        "date_changes",
        "non_line_date_changes",
        "rotations",
    ):
        safety[key] = require_count(safety.get(key), f"safety.{key}")
    if safety["media_deleted"] != 0:
        raise ValueError("media_deleted must be zero for this skill")
    if safety["non_line_date_changes"] != 0:
        raise ValueError("non_line_date_changes must be zero for this skill")
    if safety["date_changes"] != date_review["corrected"]:
        raise ValueError("safety.date_changes must match line_date_review.corrected")
    expected_rotations = self_captured["rotated"] + confirmed_line["rotated"]
    if safety["rotations"] != expected_rotations:
        raise ValueError("safety.rotations must match source-specific rotation totals")
    report["safety"] = safety

    report["backups"] = [
        require_text(value, f"backups[{index}]")
        for index, value in enumerate(require_list(report.get("backups", []), "backups"))
    ]
    report["notes"] = [
        require_text(value, f"notes[{index}]")
        for index, value in enumerate(require_list(report.get("notes", []), "notes"))
    ]
    return report


def escaped(value: Any) -> str:
    return html.escape(str(value), quote=True)


def render_report(report: Mapping[str, Any]) -> str:
    data = validate_report(report)
    language = data["language"]
    is_ja = language == "ja"
    labels = {
        "scope": "対象" if is_ja else "Scope",
        "outbound": "共有用画像" if is_ja else "Outbound images",
        "line": "LINE取得を除外" if is_ja else "LINE downloads excluded",
        "rotations": "回転（合計）" if is_ja else "Rotations (total)",
        "self_short": "自分で撮影" if is_ja else "Self-captured",
        "line_short": "LINE取得" if is_ja else "LINE downloads",
        "deleted": "写真・動画の削除" if is_ja else "Media deleted",
        "albums": "月別共有アルバム" if is_ja else "Monthly outbound albums",
        "final": "最終" if is_ja else "Final",
        "excluded": "LINE除外" if is_ja else "LINE excluded",
        "ambiguous": "判定保留を除外" if is_ja else "Ambiguous excluded",
        "self_orientation": "自分で撮った写真の向き（積極的）" if is_ja else "Self-captured orientation (active)",
        "line_orientation": "LINE画像の向き（消極的）" if is_ja else "LINE orientation (conservative)",
        "portrait_candidates": "縦画像候補" if is_ja else "Portrait candidates",
        "rotated": "回転" if is_ja else "Rotated",
        "kept_portrait": "明確な縦構図" if is_ja else "Clearly portrait",
        "line_reviewed": "向きを確認" if is_ja else "Reviewed",
        "line_unchanged": "変更なし" if is_ja else "Unchanged",
        "unresolved": "未確定" if is_ja else "Unresolved",
        "dates": "LINE画像の日付判定" if is_ja else "LINE date review",
        "non_line_dates": "自分で撮った写真の日付変更" if is_ja else "Self-captured date changes",
        "reviewed": "確認" if is_ja else "Reviewed",
        "corrected": "補正" if is_ja else "Corrected",
        "already": "23:50台済み" if is_ja else "Already in 23:50 band",
        "skipped": "変更なし" if is_ja else "Skipped",
        "safety": "安全確認" if is_ja else "Safety verification",
        "before": "作業前" if is_ja else "Before",
        "after": "作業後" if is_ja else "After",
        "photos": "写真" if is_ja else "photos",
        "videos": "ビデオ" if is_ja else "videos",
        "new_arrivals": "同期による新着" if is_ja else "Synchronized arrivals",
        "sync": "同期状態" if is_ja else "Sync status",
        "membership": "ID照合" if is_ja else "ID verification",
        "missing": "不足" if is_ja else "Missing",
        "extra": "余分" if is_ja else "Extra",
        "duplicates": "重複" if is_ja else "Duplicates",
        "backups": "退避した旧アルバム" if is_ja else "Retained backup albums",
        "notes": "注記" if is_ja else "Notes",
        "generated": "生成日時" if is_ja else "Generated",
    }

    albums = data["albums"]
    outbound_total = sum(album["final"] for album in albums)
    line_total = sum(album["confirmed_line_excluded"] for album in albums)
    ambiguous_total = sum(album["ambiguous_excluded"] for album in albums)
    max_album_total = max(
        [
            album["final"]
            + album["confirmed_line_excluded"]
            + album["ambiguous_excluded"]
            for album in albums
        ]
        or [1]
    )

    album_rows = []
    for album in albums:
        scale_total = (
            album["final"]
            + album["confirmed_line_excluded"]
            + album["ambiguous_excluded"]
        )
        track_width = 100.0 * scale_total / max_album_total if max_album_total else 0
        denominator = max(scale_total, 1)
        final_width = 100.0 * album["final"] / denominator
        line_width = 100.0 * album["confirmed_line_excluded"] / denominator
        ambiguous_width = 100.0 * album["ambiguous_excluded"] / denominator
        album_rows.append(
            f"""
            <div class="album-row">
              <div class="album-name">{escaped(album['name'])}</div>
              <div class="bar-space">
                <div class="bar-track" style="width:{track_width:.2f}%" role="img" aria-label="{escaped(album['name'])}: {labels['final']} {album['final']}, {labels['excluded']} {album['confirmed_line_excluded']}, {labels['ambiguous']} {album['ambiguous_excluded']}">
                  <span class="segment final" style="width:{final_width:.2f}%"></span>
                  <span class="segment line" style="width:{line_width:.2f}%"></span>
                  <span class="segment ambiguous" style="width:{ambiguous_width:.2f}%"></span>
                </div>
              </div>
              <div class="album-count">{album['final']}</div>
            </div>"""
        )

    verification_rows = "".join(
        f"<tr><th>{escaped(album['name'])}</th><td>{album['missing']}</td><td>{album['extra']}</td><td>{album['duplicates']}</td></tr>"
        for album in albums
    )
    backup_items = "".join(
        f"<li><code>{escaped(name)}</code></li>" for name in data["backups"]
    ) or "<li>—</li>"
    note_items = "".join(f"<li>{escaped(note)}</li>" for note in data["notes"]) or "<li>—</li>"
    before = data["library"]["before"]
    after = data["library"]["after"]
    self_orientation = data["orientation"]["self_captured"]
    line_orientation = data["orientation"]["confirmed_line"]
    date_review = data["line_date_review"]
    safety = data["safety"]
    status = data["status"]

    return f"""<!doctype html>
<html lang="{language}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped(data['title'])}</title>
  <style>
    :root {{ color-scheme: light dark; --bg:#f5f7fb; --surface:#ffffff; --text:#172033; --muted:#667085; --line:#d8dee9; --blue:#2563eb; --blue-soft:#dbeafe; --orange:#d97706; --orange-soft:#ffedd5; --purple:#7c3aed; --purple-soft:#ede9fe; --green:#15803d; --green-soft:#dcfce7; --red:#b42318; --red-soft:#fee4e2; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; line-height:1.5; }}
    main {{ width:min(1080px,100%); margin:0 auto; padding:28px; display:grid; gap:22px; }}
    header {{ display:grid; gap:8px; }}
    h1,h2,p {{ margin:0; }}
    h1 {{ font-size:clamp(1.6rem,4vw,2.4rem); }}
    h2 {{ font-size:1.15rem; }}
    .subhead,.muted {{ color:var(--muted); }}
    .status {{ display:inline-flex; width:max-content; padding:5px 10px; border-radius:999px; font-weight:700; background:var(--green-soft); color:var(--green); }}
    .status.review {{ background:var(--orange-soft); color:var(--orange); }}
    .status.blocked {{ background:var(--red-soft); color:var(--red); }}
    .metrics {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }}
    .card {{ background:var(--surface); border:1px solid var(--line); border-radius:14px; padding:16px; box-shadow:0 4px 16px rgba(15,23,42,.06); }}
    .metric {{ display:grid; gap:4px; }}
    .metric strong {{ font-size:1.65rem; }}
    .section {{ display:grid; gap:14px; }}
    .legend {{ display:flex; gap:16px; flex-wrap:wrap; color:var(--muted); font-size:.9rem; }}
    .key {{ display:inline-flex; gap:6px; align-items:center; }}
    .swatch {{ width:12px; height:12px; border-radius:3px; background:var(--blue); }}
    .swatch.line {{ background:var(--orange); }}
    .swatch.ambiguous {{ background:var(--purple); }}
    .album-grid {{ display:grid; gap:10px; }}
    .album-row {{ display:grid; grid-template-columns:72px minmax(0,1fr) 54px; gap:10px; align-items:center; }}
    .album-name,.album-count {{ font-variant-numeric:tabular-nums; font-weight:650; }}
    .album-count {{ text-align:right; }}
    .bar-space {{ min-width:0; }}
    .bar-track {{ height:22px; min-width:2px; display:flex; overflow:hidden; border-radius:6px; background:var(--line); }}
    .segment {{ height:100%; }}
    .segment.final {{ background:var(--blue); }}
    .segment.line {{ background:var(--orange); }}
    .segment.ambiguous {{ background:var(--purple); }}
    .two-column {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; }}
    .flow {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:8px; }}
    .flow div {{ padding:12px; border-top:4px solid var(--blue); background:var(--blue-soft); color:#172033; }}
    .flow div:nth-child(2) {{ border-color:var(--green); background:var(--green-soft); }}
    .flow div:nth-child(3) {{ border-color:var(--orange); background:var(--orange-soft); }}
    .flow div:nth-child(4) {{ border-color:var(--purple); background:var(--purple-soft); }}
    .flow strong {{ display:block; font-size:1.4rem; }}
    .before-after {{ display:grid; grid-template-columns:1fr auto 1fr; gap:12px; align-items:center; text-align:center; }}
    .before-after strong {{ display:block; font-size:1.5rem; }}
    table {{ width:100%; border-collapse:collapse; font-variant-numeric:tabular-nums; }}
    th,td {{ padding:9px 8px; border-bottom:1px solid var(--line); text-align:right; }}
    th:first-child,td:first-child {{ text-align:left; }}
    ul {{ margin:0; padding-left:20px; }}
    code {{ overflow-wrap:anywhere; }}
    .safe {{ background:var(--green-soft); color:var(--green); border:1px solid color-mix(in srgb,var(--green) 30%,transparent); }}
    .safe strong {{ font-size:1.25rem; }}
    @media (prefers-color-scheme:dark) {{ :root {{ --bg:#0f172a; --surface:#172033; --text:#f8fafc; --muted:#cbd5e1; --line:#334155; --blue:#60a5fa; --blue-soft:#1e3a5f; --orange:#f59e0b; --orange-soft:#4a2b08; --purple:#a78bfa; --purple-soft:#35245f; --green:#4ade80; --green-soft:#123d25; --red:#f97066; --red-soft:#4b1d1d; }} .flow div {{ color:var(--text); }} }}
    @media (max-width:720px) {{ main {{ padding:16px; }} .metrics,.two-column {{ grid-template-columns:repeat(2,minmax(0,1fr)); }} .flow {{ grid-template-columns:1fr 1fr; }} }}
    @media (max-width:440px) {{ .metrics,.two-column,.flow {{ grid-template-columns:1fr; }} .album-row {{ grid-template-columns:64px minmax(0,1fr) 42px; }} .before-after {{ grid-template-columns:1fr; }} .arrow {{ transform:rotate(90deg); }} }}
    @media print {{ body {{ background:white; }} main {{ width:100%; padding:0; }} .card {{ box-shadow:none; break-inside:avoid; }} }}
  </style>
</head>
<body>
<main>
  <header>
    <span class="status {escaped(status)}">{escaped(STATUS_LABELS[language][status])}</span>
    <h1>{escaped(data['title'])}</h1>
    <p class="subhead">{labels['scope']}: {escaped(data['scope']['start'])} – {escaped(data['scope']['end'])} · {escaped(data['scope']['purpose'])}</p>
    <p class="muted">{labels['generated']}: {escaped(data['generated_at'])}</p>
  </header>

  <section class="metrics" aria-label="Summary">
    <div class="card metric"><span class="muted">{labels['outbound']}</span><strong>{outbound_total}</strong></div>
    <div class="card metric"><span class="muted">{labels['line']}</span><strong>{line_total}</strong><span class="muted">+ {ambiguous_total} {labels['ambiguous']}</span></div>
    <div class="card metric"><span class="muted">{labels['rotations']}</span><strong>{safety['rotations']}</strong><span class="muted">{labels['self_short']} {self_orientation['rotated']} · {labels['line_short']} {line_orientation['rotated']}</span></div>
    <div class="card metric safe"><span>{labels['deleted']}</span><strong>{safety['media_deleted']}件</strong></div>
  </section>

  <section class="card section">
    <h2>{labels['albums']}</h2>
    <div class="legend"><span class="key"><span class="swatch"></span>{labels['final']}</span><span class="key"><span class="swatch line"></span>{labels['excluded']}</span><span class="key"><span class="swatch ambiguous"></span>{labels['ambiguous']}</span></div>
    <div class="album-grid">{''.join(album_rows)}</div>
  </section>

  <section class="two-column">
    <div class="card section">
      <h2>{labels['self_orientation']}</h2>
      <div class="flow">
        <div><span>{labels['portrait_candidates']}</span><strong>{self_orientation['portrait_candidates']}</strong></div>
        <div><span>{labels['rotated']}</span><strong>{self_orientation['rotated']}</strong></div>
        <div><span>{labels['kept_portrait']}</span><strong>{self_orientation['kept_portrait']}</strong></div>
        <div><span>{labels['unresolved']}</span><strong>{self_orientation['unresolved']}</strong></div>
      </div>
    </div>
    <div class="card section">
      <h2>{labels['line_orientation']}</h2>
      <div class="flow">
        <div><span>{labels['line_reviewed']}</span><strong>{line_orientation['reviewed']}</strong></div>
        <div><span>{labels['rotated']}</span><strong>{line_orientation['rotated']}</strong></div>
        <div><span>{labels['line_unchanged']}</span><strong>{line_orientation['unchanged']}</strong></div>
        <div><span>{labels['unresolved']}</span><strong>{line_orientation['unresolved']}</strong></div>
      </div>
    </div>
  </section>

  <section class="two-column">
    <div class="card section">
      <h2>{labels['dates']}</h2>
      <div class="flow">
        <div><span>{labels['reviewed']}</span><strong>{date_review['reviewed']}</strong></div>
        <div><span>{labels['corrected']}</span><strong>{date_review['corrected']}</strong></div>
        <div><span>{labels['already']}</span><strong>{date_review['already_2350']}</strong></div>
        <div><span>{labels['skipped']}</span><strong>{date_review['skipped']}</strong></div>
      </div>
      <div class="safe card"><span>{labels['non_line_dates']}</span><strong>{safety['non_line_date_changes']}件</strong></div>
    </div>
    <div class="card section">
      <h2>{labels['safety']}</h2>
      <div class="before-after">
        <div><span class="muted">{labels['before']}</span><strong>{before['photos'] + before['videos']}</strong><span>{before['photos']} {labels['photos']} · {before['videos']} {labels['videos']}</span></div>
        <span class="arrow">→</span>
        <div><span class="muted">{labels['after']}</span><strong>{after['photos'] + after['videos']}</strong><span>{after['photos']} {labels['photos']} · {after['videos']} {labels['videos']}</span></div>
      </div>
      <p>{labels['new_arrivals']}: <strong>{data['library']['new_arrivals']}</strong></p>
      <p>{labels['sync']}: {escaped(data['library']['sync_status'])}</p>
    </div>
  </section>

  <section class="card section">
    <h2>{labels['membership']}</h2>
    <div style="overflow-x:auto">
      <table><thead><tr><th>Album</th><th>{labels['missing']}</th><th>{labels['extra']}</th><th>{labels['duplicates']}</th></tr></thead><tbody>{verification_rows}</tbody></table>
    </div>
  </section>

  <section class="two-column">
    <div class="card section"><h2>{labels['backups']}</h2><ul>{backup_items}</ul></div>
    <div class="card section"><h2>{labels['notes']}</h2><ul>{note_items}</ul></div>
  </section>
</main>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a visual HTML report from a Photos run manifest."
    )
    parser.add_argument("report", type=Path, help="run-report.json")
    parser.add_argument("output", type=Path, help="destination HTML path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        raw = json.loads(args.report.read_text(encoding="utf-8"))
        document = render_report(require_mapping(raw, "report"))
        args.output.write_text(document, encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
