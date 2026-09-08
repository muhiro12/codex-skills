# Visual report schema

Create one JSON manifest after each skill run and retain it beside the generated HTML. The HTML generator rejects media deletion, a decreasing library count, any non-LINE date change, inconsistent source-specific orientation totals, and inconsistent mutation totals.

## Required shape

The following dates, counts, and album names are synthetic examples, not a library snapshot.

```json
{
  "title": "Example Photos LINE Sharing Report",
  "language": "ja",
  "generated_at": "2030-02-01T12:00:00Z",
  "status": "review",
  "scope": {
    "start": "2030-01-01",
    "end": "2030-01-31",
    "purpose": "Outbound LINE sharing"
  },
  "library": {
    "before": {"photos": 100, "videos": 5},
    "after": {"photos": 102, "videos": 5},
    "new_arrivals": 2,
    "sync_status": "Last synced 1 minute ago"
  },
  "albums": [
    {
      "name": "203001",
      "before": 30,
      "confirmed_line_excluded": 4,
      "ambiguous_excluded": 1,
      "new_arrivals": 2,
      "final": 27,
      "missing": 0,
      "extra": 0,
      "duplicates": 0
    }
  ],
  "line_date_review": {
    "reviewed": 5,
    "corrected": 2,
    "already_2350": 2,
    "skipped": 1
  },
  "orientation": {
    "self_captured": {
      "portrait_candidates": 8,
      "rotated": 6,
      "kept_portrait": 1,
      "unresolved": 1
    },
    "confirmed_line": {
      "reviewed": 4,
      "rotated": 1,
      "unchanged": 2,
      "unresolved": 1
    }
  },
  "safety": {
    "media_deleted": 0,
    "albums_deleted": 0,
    "date_changes": 2,
    "non_line_date_changes": 0,
    "rotations": 7
  },
  "backups": ["203001_LINE_INCLUDED_BACKUP_20300201"],
  "notes": ["Two new camera photos arrived through iCloud during this fictional run."]
}
```

## Field rules

- `language`: `ja` or `en`; defaults to `ja`.
- `status`: `ready`, `review`, or `blocked`.
- `library.after` total must not be lower than `library.before`.
- `albums`: include every requested monthly outbound album, including unchanged months.
- `confirmed_line_excluded`: confirmed inbound LINE still images omitted from the album.
- `ambiguous_excluded`: unresolved possible inbound LINE still images omitted from sharing.
- `new_arrivals`: newly synchronized still images confirmed as self-captured outbound originals and added during the run.
- `line_date_review`: contains confirmed LINE downloads only. Never include a self-captured or other non-LINE original.
- `orientation.self_captured.portrait_candidates` must equal `rotated + kept_portrait + unresolved`. Review these candidates actively with landscape as the normal intent.
- `orientation.self_captured.kept_portrait`: require positive evidence of intentional portrait composition.
- `orientation.confirmed_line.reviewed` must equal `rotated + unchanged + unresolved`.
- `orientation.confirmed_line.rotated`: include only confirmed LINE items whose visible content was clearly sideways. Portrait dimensions alone are not evidence.
- `orientation.confirmed_line.unchanged`: include reviewed LINE items whose current orientation remained plausible.
- `safety.media_deleted`: must always be `0`.
- `safety.non_line_date_changes`: must always be `0`.
- `safety.date_changes`: must equal `line_date_review.corrected` because only confirmed LINE dates may change.
- `safety.rotations`: must equal the sum of the self-captured and confirmed-LINE rotation counts.
- `backups`: list retained album containers; never imply that a backup contains duplicate library media.
- `notes`: explain synchronized arrivals, blockers, skipped uncertainty, and other context needed to interpret the charts.

Use counts only. Do not embed private photos, thumbnails, faces, locations, or Photos media IDs in the HTML report.
