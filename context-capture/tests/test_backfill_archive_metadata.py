from __future__ import annotations

import importlib.util
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "backfill_archive_metadata.py"
SPEC = importlib.util.spec_from_file_location("backfill_archive_metadata", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


LEGACY_RAW = """---
id: 2026-01-01-private-manual-001
record_type: raw
created_at: 2026-01-01T00:00:00+09:00
---
Body remains unchanged.
"""


class BackfillArchiveMetadataTests(unittest.TestCase):
    def test_find_markdown_files_skips_symbolic_links(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "archive"
            outside = Path(temporary_directory) / "outside"
            root.mkdir()
            outside.mkdir()
            accepted = root / "accepted.md"
            accepted.write_text(LEGACY_RAW, encoding="utf-8")
            outside_file = outside / "outside.md"
            outside_file.write_text(LEGACY_RAW, encoding="utf-8")
            (root / "linked-file.md").symlink_to(outside_file)
            (root / "linked-directory").symlink_to(outside, target_is_directory=True)

            self.assertEqual(MODULE.find_markdown_files([root]), [accepted])

    def test_apply_is_atomic_and_preserves_mode_and_body(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "legacy.md"
            path.write_text(LEGACY_RAW, encoding="utf-8")
            path.chmod(0o640)
            original_inode = path.stat().st_ino

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--apply", str(path)],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            updated = path.read_text(encoding="utf-8")
            self.assertIn("observer_perspective: user-provided-observer-record", updated)
            self.assertTrue(updated.endswith("Body remains unchanged.\n"))
            self.assertNotEqual(path.stat().st_ino, original_inode)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)
            self.assertEqual(list(path.parent.glob(f".{path.name}.*.tmp")), [])

    def test_apply_does_not_modify_symlink_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            target = root / "target.md"
            link = root / "link.md"
            target.write_text(LEGACY_RAW, encoding="utf-8")
            link.symlink_to(target)

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--apply", str(link)],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(target.read_text(encoding="utf-8"), LEGACY_RAW)
            self.assertIn("symbolic link", result.stderr)

    def test_second_apply_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "legacy.md"
            path.write_text(LEGACY_RAW, encoding="utf-8")

            first = subprocess.run(
                [sys.executable, str(SCRIPT), "--apply", str(path)],
                check=False,
                capture_output=True,
                text=True,
            )
            second = subprocess.run(
                [sys.executable, str(SCRIPT), "--apply", str(path)],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn("changed=0", second.stdout)


if __name__ == "__main__":
    unittest.main()
