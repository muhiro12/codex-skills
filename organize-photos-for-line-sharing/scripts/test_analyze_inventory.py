#!/usr/bin/env python3

from __future__ import annotations

import argparse
import tempfile
import unittest
from pathlib import Path

from analyze_inventory import build_plan, read_inventory


FIXTURE = """\
2025\t12\t31\t23\t59\t59\tIMG_OLD.HEIC\tid-old\t100\t100
2026\t1\t1\t12\t0\t0\tIMG_0001.HEIC\tid-photo\t4000\t3000
2026\t1\t31\t23\t50\t1\tLINE_0001.JPG\tid-line-explicit\t1200\t800
2026\t2\t28\t23\t51\t2\t11111111-1111-1111-1111-111111111111.JPEG\tid-uuid-adjusted\t1200\t800
2026\t2\t2\t10\t20\t3\t22222222-2222-2222-2222-222222222222.PNG\tid-uuid-unadjusted\t800\t1200
2026\t2\t2\t10\t21\t4\t33333333-3333-3333-3333-333333333333.MP4\tid-uuid-video\t1920\t1080
"""


class AnalyzeInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.inventory = self.root / "inventory.tsv"
        self.inventory.write_text(FIXTURE, encoding="utf-8")

    def arguments(self, uuid_policy: str) -> argparse.Namespace:
        return argparse.Namespace(
            inventory=self.inventory,
            start_year=2026,
            through=(2026, 2),
            uuid_policy=uuid_policy,
            line_id_file=None,
            summary_only=False,
            output=None,
        )

    def test_candidate_policy_blocks_uuid_images_from_outbound_albums(self) -> None:
        plan = build_plan(self.arguments("candidate"))

        self.assertEqual(
            plan["totals"],
            {
                "media": 5,
                "images": 4,
                "videos": 1,
                "other": 0,
                "confirmed_line": 1,
                "ambiguous_line": 3,
                "outbound": 1,
            },
        )
        self.assertEqual(plan["monthly"]["202601"]["outbound_images"], 1)
        self.assertEqual(plan["monthly"]["202602"]["outbound_images"], 0)
        self.assertEqual(plan["monthly"]["202602"]["status"], "requires_review")
        self.assertEqual(
            plan["date_review"],
            {
                "confirmed_line_images": 1,
                "already_in_2350_band": 1,
                "not_in_2350_band": 0,
            },
        )

    def test_line_policy_confirms_uuid_media(self) -> None:
        plan = build_plan(self.arguments("line"))

        self.assertEqual(plan["totals"]["confirmed_line"], 4)
        self.assertEqual(plan["totals"]["ambiguous_line"], 0)
        self.assertEqual(plan["monthly"]["202602"]["confirmed_line_images"], 2)
        self.assertEqual(plan["monthly"]["202602"]["ambiguous_line_images"], 0)
        self.assertEqual(
            plan["date_review"],
            {
                "confirmed_line_images": 3,
                "already_in_2350_band": 2,
                "not_in_2350_band": 1,
            },
        )

    def test_duplicate_media_id_is_rejected(self) -> None:
        duplicate_inventory = self.root / "duplicate.tsv"
        duplicate_inventory.write_text(
            FIXTURE
            + "2026\t3\t1\t1\t2\t3\tIMG_DUP.HEIC\tid-photo\t100\t100\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "duplicate ID id-photo"):
            read_inventory(duplicate_inventory)


if __name__ == "__main__":
    unittest.main()
