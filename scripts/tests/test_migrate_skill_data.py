from __future__ import annotations

import importlib.util
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "migrate_skill_data.py"
SPEC = importlib.util.spec_from_file_location("migrate_skill_data", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def write_apple_cache(root: Path, cache_path: str) -> None:
    sample_root = root / "samples/example-sample"
    sample_root.mkdir(parents=True)
    metadata = {
        "slug": "example-sample",
        "cache_path": cache_path,
    }
    (root / "manifest.json").write_text(
        json.dumps(
            {
                "version": 1,
                "samples": {"example-sample": metadata},
            }
        ),
        encoding="utf-8",
    )
    (sample_root / "metadata.json").write_text(
        json.dumps(metadata),
        encoding="utf-8",
    )


class MigrateSkillDataTests(unittest.TestCase):
    def test_list_files_does_not_follow_symbolic_links(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            source = base / "source"
            outside = base / "outside"
            source.mkdir()
            outside.mkdir()
            accepted = source / "accepted.md"
            accepted.write_text("accepted", encoding="utf-8")
            outside_file = outside / "outside.md"
            outside_file.write_text("outside", encoding="utf-8")
            (source / "linked-file.md").symlink_to(outside_file)
            (source / "linked-directory").symlink_to(outside, target_is_directory=True)

            self.assertEqual(MODULE.list_files(source), [accepted])

    def test_copy_file_rejects_symbolic_link_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            source = base / "source.md"
            outside = base / "outside.md"
            target = base / "target.md"
            source.write_text("new", encoding="utf-8")
            outside.write_text("new", encoding="utf-8")
            target.symlink_to(outside)
            stats = MODULE.MigrationStats()

            MODULE.copy_file(source, target, apply=True, stats=stats)

            self.assertEqual(stats.conflicts, 1)
            self.assertEqual(outside.read_text(encoding="utf-8"), "new")
            self.assertTrue(target.is_symlink())

    def test_copy_file_rejects_symbolic_link_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            source = base / "source.md"
            target_root = base / "target"
            outside = base / "outside"
            source.write_text("new", encoding="utf-8")
            target_root.mkdir()
            outside.mkdir()
            (target_root / "linked").symlink_to(outside, target_is_directory=True)
            target = target_root / "linked" / "target.md"
            stats = MODULE.MigrationStats()

            MODULE.copy_file(
                source,
                target,
                apply=True,
                stats=stats,
                target_boundary=target_root,
            )

            self.assertEqual(stats.conflicts, 1)
            self.assertFalse((outside / "target.md").exists())

    def test_atomic_copy_preserves_contents_and_leaves_no_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            source = base / "source.md"
            target_directory = base / "target"
            target = target_directory / "target.md"
            source.write_text("content", encoding="utf-8")
            source.chmod(0o640)
            target_directory.mkdir()
            stats = MODULE.MigrationStats()

            MODULE.copy_file(source, target, apply=True, stats=stats)

            self.assertEqual(stats.copied, 1)
            self.assertEqual(target.read_text(encoding="utf-8"), "content")
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o640)
            self.assertEqual(list(target_directory.glob(".target.md.*.tmp")), [])

    def test_private_permission_audit_and_apply_skip_links(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "records"
            directory = root / "principles"
            file_path = directory / "current.md"
            outside = Path(temporary_directory) / "outside.md"
            directory.mkdir(parents=True)
            file_path.write_text("private", encoding="utf-8")
            outside.write_text("outside", encoding="utf-8")
            root.chmod(0o755)
            directory.chmod(0o755)
            file_path.chmod(0o644)
            outside.chmod(0o644)
            (root / "linked.md").symlink_to(outside)

            dry_run = MODULE.MigrationStats()
            MODULE.enforce_private_permissions([root], apply=False, stats=dry_run)
            self.assertEqual(dry_run.permissions_would_change, 3)
            self.assertEqual(stat.S_IMODE(file_path.stat().st_mode), 0o644)

            applied = MODULE.MigrationStats()
            MODULE.enforce_private_permissions([root], apply=True, stats=applied)
            self.assertEqual(applied.permissions_changed, 3)
            self.assertEqual(stat.S_IMODE(root.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(directory.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(file_path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(outside.stat().st_mode), 0o644)

    def test_apple_cache_migration_rebases_manifest_and_metadata_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            skills_root = base / "skills"
            home = base / "home"
            source_root = home / ".codex/cache/apple-sample-code"
            source_sample = source_root / "samples/example-sample"
            source_sample.mkdir(parents=True)
            legacy_path = str(source_sample)
            metadata = {
                "slug": "example-sample",
                "cache_path": legacy_path,
            }
            (source_root / "manifest.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "samples": {"example-sample": metadata},
                    }
                ),
                encoding="utf-8",
            )
            (source_sample / "metadata.json").write_text(
                json.dumps(metadata),
                encoding="utf-8",
            )

            dry_run = MODULE.MigrationStats()
            MODULE.migrate_apple_cache(
                skills_root,
                home,
                apply=False,
                stats=dry_run,
            )
            self.assertEqual(dry_run.metadata_would_rebase, 2)
            self.assertFalse(
                (skills_root / "apple-sample-code-advisor/cache/manifest.json").exists()
            )

            applied = MODULE.MigrationStats()
            MODULE.migrate_apple_cache(
                skills_root,
                home,
                apply=True,
                stats=applied,
            )

            target_root = skills_root / "apple-sample-code-advisor/cache"
            desired_path = str((target_root / "samples/example-sample").resolve())
            target_manifest = json.loads(
                (target_root / "manifest.json").read_text(encoding="utf-8")
            )
            target_metadata = json.loads(
                (target_root / "samples/example-sample/metadata.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(applied.metadata_rebased, 2)
            self.assertEqual(
                target_manifest["samples"]["example-sample"]["cache_path"],
                desired_path,
            )
            self.assertEqual(target_metadata["cache_path"], desired_path)

            second_run = MODULE.MigrationStats()
            MODULE.migrate_apple_cache(
                skills_root,
                home,
                apply=True,
                stats=second_run,
            )
            self.assertEqual(second_run.metadata_rebased, 0)
            self.assertEqual(second_run.conflicts, 0)

    def test_apple_cache_migration_rejects_symbolic_link_target_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            skills_root = base / "skills"
            home = base / "home"
            source_root = home / ".codex/cache/apple-sample-code"
            target_root = skills_root / "apple-sample-code-advisor/cache"
            outside_root = base / "outside-cache"
            write_apple_cache(source_root, "legacy-source")
            write_apple_cache(outside_root, "outside-original")
            target_root.parent.mkdir(parents=True)
            target_root.symlink_to(outside_root, target_is_directory=True)
            original_manifest = (outside_root / "manifest.json").read_text(encoding="utf-8")
            original_metadata = (outside_root / "samples/example-sample/metadata.json").read_text(
                encoding="utf-8"
            )
            stats = MODULE.MigrationStats()

            MODULE.migrate_apple_cache(
                skills_root,
                home,
                apply=True,
                stats=stats,
            )

            self.assertEqual(stats.conflicts, 1)
            self.assertEqual(stats.metadata_rebased, 0)
            self.assertEqual(
                (outside_root / "manifest.json").read_text(encoding="utf-8"),
                original_manifest,
            )
            self.assertEqual(
                (outside_root / "samples/example-sample/metadata.json").read_text(
                    encoding="utf-8"
                ),
                original_metadata,
            )

    def test_apple_cache_migration_rejects_symbolic_link_sample_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            skills_root = base / "skills"
            home = base / "home"
            source_root = home / ".codex/cache/apple-sample-code"
            target_root = skills_root / "apple-sample-code-advisor/cache"
            outside_sample = base / "outside-sample"
            write_apple_cache(source_root, "legacy-source")
            target_root.joinpath("samples").mkdir(parents=True)
            outside_sample.mkdir()
            target_metadata = {
                "slug": "example-sample",
                "cache_path": "outside-original",
            }
            (target_root / "manifest.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "samples": {"example-sample": target_metadata},
                    }
                ),
                encoding="utf-8",
            )
            (outside_sample / "metadata.json").write_text(
                json.dumps(target_metadata),
                encoding="utf-8",
            )
            (target_root / "samples/example-sample").symlink_to(
                outside_sample,
                target_is_directory=True,
            )
            original_manifest = (target_root / "manifest.json").read_text(encoding="utf-8")
            original_metadata = (outside_sample / "metadata.json").read_text(encoding="utf-8")
            stats = MODULE.MigrationStats()

            MODULE.migrate_apple_cache(
                skills_root,
                home,
                apply=True,
                stats=stats,
            )

            self.assertEqual(stats.conflicts, 1)
            self.assertEqual(stats.metadata_rebased, 0)
            self.assertEqual(
                (target_root / "manifest.json").read_text(encoding="utf-8"),
                original_manifest,
            )
            self.assertEqual(
                (outside_sample / "metadata.json").read_text(encoding="utf-8"),
                original_metadata,
            )

    def test_apple_cache_migration_rejects_symbolic_link_sample_loop(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            skills_root = base / "skills"
            home = base / "home"
            source_root = home / ".codex/cache/apple-sample-code"
            target_root = skills_root / "apple-sample-code-advisor/cache"
            write_apple_cache(source_root, "legacy-source")
            target_root.joinpath("samples").mkdir(parents=True)
            target_metadata = {
                "slug": "example-sample",
                "cache_path": "target-original",
            }
            (target_root / "manifest.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "samples": {"example-sample": target_metadata},
                    }
                ),
                encoding="utf-8",
            )
            (target_root / "samples/example-sample").symlink_to(
                "example-sample",
                target_is_directory=True,
            )
            original_manifest = (target_root / "manifest.json").read_text(encoding="utf-8")
            stats = MODULE.MigrationStats()

            MODULE.migrate_apple_cache(
                skills_root,
                home,
                apply=True,
                stats=stats,
            )

            self.assertEqual(stats.conflicts, 1)
            self.assertEqual(stats.metadata_rebased, 0)
            self.assertEqual(
                (target_root / "manifest.json").read_text(encoding="utf-8"),
                original_manifest,
            )

    def test_apple_cache_migration_does_not_rebase_after_copy_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            skills_root = base / "skills"
            home = base / "home"
            source_root = home / ".codex/cache/apple-sample-code"
            target_root = skills_root / "apple-sample-code-advisor/cache"
            write_apple_cache(source_root, "legacy-source")
            write_apple_cache(target_root, "target-original")
            (source_root / "notes.txt").write_text("source", encoding="utf-8")
            (target_root / "notes.txt").write_text("target", encoding="utf-8")
            original_manifest = (target_root / "manifest.json").read_text(encoding="utf-8")
            original_metadata = (target_root / "samples/example-sample/metadata.json").read_text(
                encoding="utf-8"
            )
            stats = MODULE.MigrationStats()

            MODULE.migrate_apple_cache(
                skills_root,
                home,
                apply=True,
                stats=stats,
            )

            self.assertEqual(stats.conflicts, 1)
            self.assertEqual(stats.metadata_rebased, 0)
            self.assertEqual(
                (target_root / "manifest.json").read_text(encoding="utf-8"),
                original_manifest,
            )
            self.assertEqual(
                (target_root / "samples/example-sample/metadata.json").read_text(
                    encoding="utf-8"
                ),
                original_metadata,
            )

    def test_apple_cache_migration_ignores_preexisting_conflicts_for_rebase_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            skills_root = base / "skills"
            home = base / "home"
            source_root = home / ".codex/cache/apple-sample-code"
            write_apple_cache(source_root, "legacy-source")
            stats = MODULE.MigrationStats(conflicts=1)

            MODULE.migrate_apple_cache(
                skills_root,
                home,
                apply=True,
                stats=stats,
            )

            self.assertEqual(stats.conflicts, 1)
            self.assertEqual(stats.metadata_rebased, 2)


if __name__ == "__main__":
    unittest.main()
