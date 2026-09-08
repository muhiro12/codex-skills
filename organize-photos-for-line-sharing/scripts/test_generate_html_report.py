#!/usr/bin/env python3

from __future__ import annotations

import unittest

from generate_html_report import render_report, validate_report


def valid_report() -> dict[str, object]:
    return {
        "title": "2026年 写真・LINE共有整理レポート",
        "language": "ja",
        "generated_at": "2026-08-22T17:00:00+09:00",
        "status": "ready",
        "scope": {
            "start": "2026-01-01",
            "end": "2026-08-22",
            "purpose": "LINEへの共有",
        },
        "library": {
            "before": {"photos": 100, "videos": 5},
            "after": {"photos": 102, "videos": 5},
            "new_arrivals": 2,
            "sync_status": "同期済み",
        },
        "albums": [
            {
                "name": "202608",
                "before": 30,
                "confirmed_line_excluded": 4,
                "ambiguous_excluded": 1,
                "new_arrivals": 2,
                "final": 27,
                "missing": 0,
                "extra": 0,
                "duplicates": 0,
            }
        ],
        "line_date_review": {
            "reviewed": 5,
            "corrected": 2,
            "already_2350": 2,
            "skipped": 1,
        },
        "orientation": {
            "self_captured": {
                "portrait_candidates": 8,
                "rotated": 6,
                "kept_portrait": 1,
                "unresolved": 1,
            },
            "confirmed_line": {
                "reviewed": 4,
                "rotated": 1,
                "unchanged": 2,
                "unresolved": 1,
            },
        },
        "safety": {
            "media_deleted": 0,
            "albums_deleted": 0,
            "date_changes": 2,
            "non_line_date_changes": 0,
            "rotations": 7,
        },
        "backups": ["202608_LINE_INCLUDED_BACKUP_20260822"],
        "notes": ["判断できない画像は変更していません。"],
    }


class GenerateHTMLReportTests(unittest.TestCase):
    def test_valid_report_renders_visual_summary(self) -> None:
        document = render_report(valid_report())

        self.assertIn("<!doctype html>", document)
        self.assertIn("2026年 写真・LINE共有整理レポート", document)
        self.assertIn("写真・動画の削除", document)
        self.assertIn("<strong>0件</strong>", document)
        self.assertIn("自分で撮った写真の向き（積極的）", document)
        self.assertIn("LINE画像の向き（消極的）", document)
        self.assertIn("自分で撮った写真の日付変更", document)
        self.assertIn("202608_LINE_INCLUDED_BACKUP_20260822", document)

    def test_user_supplied_text_is_escaped(self) -> None:
        report = valid_report()
        report["notes"] = ["<script>alert('private')</script>"]

        document = render_report(report)

        self.assertNotIn("<script>", document)
        self.assertIn("&lt;script&gt;", document)

    def test_nonzero_media_deletion_is_rejected(self) -> None:
        report = valid_report()
        report["safety"]["media_deleted"] = 1  # type: ignore[index]

        with self.assertRaisesRegex(ValueError, "media_deleted must be zero"):
            validate_report(report)

    def test_orientation_total_mismatch_is_rejected(self) -> None:
        report = valid_report()
        report["orientation"]["self_captured"]["unresolved"] = 2  # type: ignore[index]

        with self.assertRaisesRegex(ValueError, "self-captured orientation"):
            validate_report(report)

    def test_confirmed_line_orientation_total_mismatch_is_rejected(self) -> None:
        report = valid_report()
        report["orientation"]["confirmed_line"]["unchanged"] = 3  # type: ignore[index]

        with self.assertRaisesRegex(ValueError, "confirmed LINE orientation"):
            validate_report(report)

    def test_non_line_date_change_is_rejected(self) -> None:
        report = valid_report()
        report["safety"]["non_line_date_changes"] = 1  # type: ignore[index]

        with self.assertRaisesRegex(ValueError, "non_line_date_changes must be zero"):
            validate_report(report)

    def test_non_line_date_change_field_is_required(self) -> None:
        report = valid_report()
        del report["safety"]["non_line_date_changes"]  # type: ignore[index]

        with self.assertRaisesRegex(ValueError, "safety.non_line_date_changes"):
            validate_report(report)

    def test_rotation_total_mismatch_is_rejected(self) -> None:
        report = valid_report()
        report["safety"]["rotations"] = 6  # type: ignore[index]

        with self.assertRaisesRegex(ValueError, "source-specific rotation totals"):
            validate_report(report)

    def test_decreasing_library_total_is_rejected(self) -> None:
        report = valid_report()
        report["library"]["after"] = {"photos": 99, "videos": 5}  # type: ignore[index]

        with self.assertRaisesRegex(ValueError, "library total decreased"):
            validate_report(report)


if __name__ == "__main__":
    unittest.main()
