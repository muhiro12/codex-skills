#!/usr/bin/env python3
"""Regression tests for generate_release_notes.py."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "generate_release_notes.py"
SPEC = importlib.util.spec_from_file_location("generate_release_notes_for_tests", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class GenerateReleaseNotesTests(unittest.TestCase):
    def notes(self, value: str) -> object:
        return MODULE.LocaleNotes(intro=None, items=[value], outro=None)

    def test_rejects_locale_path_traversal_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            output_directory = root / "output"

            with self.assertRaisesRegex(RuntimeError, "Invalid locale identifier"):
                MODULE.write_locale_files(
                    output_directory,
                    {"../escaped": self.notes("Unsafe")},
                )

            self.assertFalse((root / "escaped.txt").exists())
            self.assertFalse(output_directory.exists())

    def test_rewrites_owned_locale_set_without_touching_unrelated_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory) / "output"
            MODULE.write_locale_files(
                output_directory,
                {
                    "en": self.notes("English"),
                    "ja": self.notes("Japanese"),
                },
            )
            unrelated_path = output_directory / "review-notes.txt"
            unrelated_path.write_text("keep\n", encoding="utf-8")

            MODULE.write_locale_files(
                output_directory,
                {"en": self.notes("Updated English")},
            )

            self.assertEqual(
                (output_directory / "en.txt").read_text(encoding="utf-8"),
                "- Updated English\n",
            )
            self.assertFalse((output_directory / "ja.txt").exists())
            self.assertEqual(unrelated_path.read_text(encoding="utf-8"), "keep\n")
            manifest = json.loads(
                (output_directory / MODULE.OUTPUT_MANIFEST_NAME).read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["files"], ["en.txt"])

    def test_rejects_case_insensitive_locale_filename_collisions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory) / "output"

            with self.assertRaisesRegex(RuntimeError, "filenames collide"):
                MODULE.write_locale_files(
                    output_directory,
                    {
                        "en-US": self.notes("One"),
                        "EN-us": self.notes("Two"),
                    },
                )


if __name__ == "__main__":
    unittest.main()
