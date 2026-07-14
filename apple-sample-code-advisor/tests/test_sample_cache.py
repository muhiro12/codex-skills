#!/usr/bin/env python3
"""Regression tests for the Apple sample cache manager."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sample_cache.py"
SPEC = importlib.util.spec_from_file_location("sample_cache_for_tests", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class SampleCacheTests(unittest.TestCase):
    def run_cache(self, cache_root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--cache-root",
                str(cache_root),
                *arguments,
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    def add_local(
        self,
        cache_root: Path,
        source: Path,
        *,
        replace: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        arguments = [
            "add-local",
            "--source",
            str(source),
            "--title",
            "Example Sample",
            "--slug",
            "example-sample",
            "--apple-url",
            "https://developer.apple.com/example",
        ]
        if replace:
            arguments.append("--replace")
        return self.run_cache(cache_root, *arguments)

    def install_arguments(self, cache_root: Path, *, replace: bool) -> argparse.Namespace:
        return argparse.Namespace(
            cache_root=str(cache_root),
            title="Example Sample",
            slug="example-sample",
            apple_url="https://developer.apple.com/example",
            frameworks=[],
            notes="",
            replace=replace,
        )

    def test_replace_manifest_failure_restores_previous_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            cache_root = root / "cache"
            old_source = root / "old"
            old_source.mkdir()
            (old_source / "old.txt").write_text("old\n", encoding="utf-8")
            MODULE.install_source(
                self.install_arguments(cache_root, replace=False),
                old_source,
            )
            manifest_before = (cache_root / "manifest.json").read_text(encoding="utf-8")

            new_source = root / "new"
            new_source.mkdir()
            (new_source / "new.txt").write_text("new\n", encoding="utf-8")
            with mock.patch.object(
                MODULE,
                "save_manifest",
                side_effect=OSError("simulated manifest failure"),
            ):
                with self.assertRaisesRegex(MODULE.CacheError, "previous entry restored"):
                    MODULE.install_source(
                        self.install_arguments(cache_root, replace=True),
                        new_source,
                    )

            cached_source = cache_root / "samples" / "example-sample" / "source"
            self.assertEqual(
                (cached_source / "old.txt").read_text(encoding="utf-8"),
                "old\n",
            )
            self.assertFalse((cached_source / "new.txt").exists())
            self.assertEqual(
                (cache_root / "manifest.json").read_text(encoding="utf-8"),
                manifest_before,
            )
            self.assertEqual(
                [path.name for path in (cache_root / "samples").iterdir()],
                ["example-sample"],
            )

    def test_fetch_archive_preserves_local_tmp_archive(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as temporary_directory:
            root = Path(temporary_directory)
            archive_path = root / "local-sample.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("Sample/App.swift", "struct App {}\n")

            result = self.run_cache(
                root / "cache",
                "fetch-archive",
                "--url",
                str(archive_path),
                "--title",
                "Local Sample",
                "--slug",
                "local-sample",
                "--apple-url",
                "https://developer.apple.com/local-sample",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(archive_path.is_file())
            self.assertTrue(
                (root / "cache" / "samples" / "local-sample" / "source" / "App.swift").is_file()
            )

    def test_download_failure_removes_owned_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as temporary_directory:
            owned_path = Path(temporary_directory) / "owned-download.zip"

            def create_owned_temp(*_args: object, **_kwargs: object) -> tuple[int, str]:
                descriptor = os.open(
                    owned_path,
                    os.O_CREAT | os.O_EXCL | os.O_RDWR,
                    0o600,
                )
                return descriptor, str(owned_path)

            with mock.patch.object(
                MODULE.tempfile,
                "mkstemp",
                side_effect=create_owned_temp,
            ), mock.patch.object(
                MODULE.urllib.request,
                "urlopen",
                side_effect=OSError("offline"),
            ):
                with self.assertRaisesRegex(MODULE.CacheError, "Failed to download"):
                    MODULE.download_to_temp("https://example.invalid/sample.zip")

            self.assertFalse(owned_path.exists())

    def test_malicious_zip_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            cache_root = root / "cache"
            archive_path = root / "malicious.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("../../../../escaped.txt", "escaped\n")

            result = self.add_local(cache_root, archive_path)

            self.assertEqual(result.returncode, 1)
            self.assertIn("Unsafe zip member path", result.stderr)
            self.assertFalse((root / "escaped.txt").exists())
            self.assertFalse(
                (cache_root / "samples" / "example-sample").exists()
            )
            self.assertFalse((cache_root / "manifest.json").exists())

    def test_invalid_timestamp_is_never_pruned(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            cache_root = root / "cache"
            source = root / "source"
            source.mkdir()
            (source / "file.txt").write_text("keep\n", encoding="utf-8")
            result = self.add_local(cache_root, source)
            self.assertEqual(result.returncode, 0, result.stderr)

            manifest_path = cache_root / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["samples"]["example-sample"]["fetched_at"] = "not-a-date"
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            manifest_before = manifest_path.read_text(encoding="utf-8")

            result = self.run_cache(
                cache_root,
                "prune",
                "--max-age-days",
                "0",
                "--apply",
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("fetched_at is missing or invalid", result.stderr)
            self.assertTrue(
                (cache_root / "samples" / "example-sample" / "source" / "file.txt").is_file()
            )
            self.assertEqual(
                manifest_path.read_text(encoding="utf-8"),
                manifest_before,
            )

    def test_successful_replace_keeps_manifest_and_metadata_consistent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            cache_root = root / "cache"
            old_source = root / "old"
            old_source.mkdir()
            (old_source / "old.txt").write_text("old\n", encoding="utf-8")
            result = self.add_local(cache_root, old_source)
            self.assertEqual(result.returncode, 0, result.stderr)

            new_source = root / "new"
            new_source.mkdir()
            (new_source / "new.txt").write_text("new\n", encoding="utf-8")
            result = self.add_local(cache_root, new_source, replace=True)

            self.assertEqual(result.returncode, 0, result.stderr)
            sample_root = cache_root / "samples" / "example-sample"
            self.assertFalse((sample_root / "source" / "old.txt").exists())
            self.assertEqual(
                (sample_root / "source" / "new.txt").read_text(encoding="utf-8"),
                "new\n",
            )
            manifest = json.loads(
                (cache_root / "manifest.json").read_text(encoding="utf-8")
            )
            metadata = json.loads(
                (sample_root / "metadata.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["samples"]["example-sample"], metadata)
            self.assertEqual(metadata["cache_path"], str(sample_root.resolve()))
            self.assertEqual(
                [path.name for path in (cache_root / "samples").iterdir()],
                ["example-sample"],
            )


if __name__ == "__main__":
    unittest.main()
