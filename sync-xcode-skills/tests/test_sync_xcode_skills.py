from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT_DIRECTORY = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIRECTORY))

import sync_xcode_skills  # noqa: E402


class SyncXcodeSkillsTests(unittest.TestCase):
    name_prefix = "xcode-skill-"
    xcode_version = "Xcode Test\nBuild version TEST123"

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.export_root = self.root / "export"
        self.skills_root = self.root / "skills"
        self.state_root = self.root / "state"
        self.export_root.mkdir()
        self.skills_root.mkdir()

    def write_exported_skill(
        self,
        directory_name: str,
        *,
        skill_name: str,
        description: str = "Exported test skill.",
    ) -> Path:
        skill_directory = self.export_root / directory_name
        skill_directory.mkdir()
        (skill_directory / "SKILL.md").write_text(
            "---\n"
            f"name: {skill_name}\n"
            f"description: {description}\n"
            "---\n"
            f"\n# {directory_name}\n",
            encoding="utf-8",
        )
        return skill_directory

    def write_managed_skill(self, original_name: str, *, sentinel: str) -> Path:
        installed_name = f"{self.name_prefix}{original_name}"
        skill_directory = self.skills_root / installed_name
        skill_directory.mkdir()
        (skill_directory / "SKILL.md").write_text(
            "---\n"
            f"name: {installed_name}\n"
            'description: "Previously installed skill."\n'
            "---\n\n# Previously Installed\n",
            encoding="utf-8",
        )
        (skill_directory / "sentinel.txt").write_text(sentinel, encoding="utf-8")
        marker = {
            "managed_by": sync_xcode_skills.MANAGED_BY,
            "original_name": original_name,
            "installed_name": installed_name,
            "synced_at": "2026-01-01T00:00:00+00:00",
            "xcode_version": "Old Xcode",
        }
        (skill_directory / sync_xcode_skills.MARKER_FILE).write_text(
            json.dumps(marker),
            encoding="utf-8",
        )
        return skill_directory

    def synchronize(
        self,
        *,
        name_prefix: str | None = None,
    ) -> tuple[list[dict[str, str]], list[str], list[str]]:
        return sync_xcode_skills.synchronize_exported_skills(
            self.export_root,
            self.skills_root,
            state_dir=self.state_root,
            developer_dir=Path("/Applications/Xcode.app/Contents/Developer"),
            name_prefix=name_prefix or self.name_prefix,
            xcode_version=self.xcode_version,
        )

    def assert_no_transaction_directories(self) -> None:
        leftovers = [
            path.name
            for root in (self.skills_root, self.state_root)
            if root.exists()
            for path in root.iterdir()
            if path.name.startswith((".sync-xcode-skills-", ".catalog-transaction-"))
        ]
        self.assertEqual(leftovers, [])

    def test_rejects_unsafe_exported_skill_name(self) -> None:
        self.write_exported_skill("unsafe", skill_name="../../outside")

        with self.assertRaisesRegex(sync_xcode_skills.SyncError, "Invalid exported skill name"):
            self.synchronize()

        self.assertFalse(self.state_root.exists())
        self.assertFalse((self.root / "outside").exists())

    def test_rejects_unsafe_name_prefix(self) -> None:
        self.write_exported_skill("alpha", skill_name="alpha")

        with self.assertRaisesRegex(sync_xcode_skills.SyncError, "Invalid name prefix"):
            self.synchronize(name_prefix="../xcode-skill-")

        self.assertFalse(self.state_root.exists())

    def test_rejects_install_target_symlink_outside_skills_root(self) -> None:
        self.write_exported_skill("alpha", skill_name="alpha")
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "sentinel.txt").write_text("outside", encoding="utf-8")
        (self.skills_root / "xcode-skill-alpha").symlink_to(outside, target_is_directory=True)

        with self.assertRaisesRegex(sync_xcode_skills.SyncError, "symbolic link"):
            self.synchronize()

        self.assertEqual((outside / "sentinel.txt").read_text(encoding="utf-8"), "outside")

    def test_rejects_symbolic_link_inside_exported_skill(self) -> None:
        skill = self.write_exported_skill("alpha", skill_name="alpha")
        outside = self.root / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        (skill / "linked.txt").symlink_to(outside)

        with self.assertRaisesRegex(sync_xcode_skills.SyncError, "must not contain symbolic links"):
            self.synchronize()

        self.assertEqual(outside.read_text(encoding="utf-8"), "outside")
        self.assertFalse((self.skills_root / "xcode-skill-alpha").exists())
        self.assertFalse(self.state_root.exists())

    def test_rejects_duplicate_installed_names_before_mutation(self) -> None:
        self.write_exported_skill("first", skill_name="duplicate")
        self.write_exported_skill("second", skill_name="Duplicate")
        existing = self.write_managed_skill("duplicate", sentinel="old")

        with self.assertRaisesRegex(sync_xcode_skills.SyncError, "Duplicate installed skill name"):
            self.synchronize()

        self.assertEqual((existing / "sentinel.txt").read_text(encoding="utf-8"), "old")
        self.assertFalse(self.state_root.exists())

    def test_corrupt_marker_remains_a_reserved_prefix_collision(self) -> None:
        self.write_exported_skill("alpha", skill_name="alpha")
        existing = self.skills_root / "xcode-skill-alpha"
        existing.mkdir()
        (existing / "sentinel.txt").write_text("do not replace", encoding="utf-8")
        (existing / sync_xcode_skills.MARKER_FILE).write_text("{", encoding="utf-8")

        with self.assertRaisesRegex(sync_xcode_skills.SyncError, "reserved for Xcode-provided"):
            self.synchronize()

        self.assertEqual(
            (existing / "sentinel.txt").read_text(encoding="utf-8"),
            "do not replace",
        )

    def test_non_mapping_marker_remains_a_reserved_prefix_collision(self) -> None:
        self.write_exported_skill("alpha", skill_name="alpha")
        existing = self.skills_root / "xcode-skill-alpha"
        existing.mkdir()
        (existing / "sentinel.txt").write_text("do not replace", encoding="utf-8")
        (existing / sync_xcode_skills.MARKER_FILE).write_text("[]", encoding="utf-8")

        with self.assertRaisesRegex(sync_xcode_skills.SyncError, "reserved for Xcode-provided"):
            self.synchronize()

        self.assertEqual(
            (existing / "sentinel.txt").read_text(encoding="utf-8"),
            "do not replace",
        )

    def test_staging_failure_leaves_all_existing_skills_untouched(self) -> None:
        self.write_exported_skill("alpha", skill_name="alpha")
        self.write_exported_skill("beta", skill_name="beta")
        alpha = self.write_managed_skill("alpha", sentinel="old alpha")
        beta = self.write_managed_skill("beta", sentinel="old beta")
        original_validate = sync_xcode_skills.validate_staged_skill

        def fail_second_staged_validation(
            skill_dir: Path,
            *,
            original_name: str,
            installed_name: str,
            xcode_version: str,
        ) -> None:
            if installed_name == "xcode-skill-beta":
                raise sync_xcode_skills.SyncError("injected staged validation failure")
            original_validate(
                skill_dir,
                original_name=original_name,
                installed_name=installed_name,
                xcode_version=xcode_version,
            )

        with mock.patch.object(
            sync_xcode_skills,
            "validate_staged_skill",
            side_effect=fail_second_staged_validation,
        ):
            with self.assertRaisesRegex(
                sync_xcode_skills.SyncError,
                "injected staged validation failure",
            ):
                self.synchronize()

        self.assertEqual((alpha / "sentinel.txt").read_text(encoding="utf-8"), "old alpha")
        self.assertEqual((beta / "sentinel.txt").read_text(encoding="utf-8"), "old beta")
        self.assertFalse(self.state_root.exists())
        self.assert_no_transaction_directories()

    def test_swap_failure_rolls_back_all_existing_skills(self) -> None:
        self.write_exported_skill("aardvark", skill_name="aardvark")
        self.write_exported_skill("alpha", skill_name="alpha")
        self.write_exported_skill("beta", skill_name="beta")
        alpha = self.write_managed_skill("alpha", sentinel="old alpha")
        beta = self.write_managed_skill("beta", sentinel="old beta")
        original_move = sync_xcode_skills.move_path

        def fail_during_second_staged_swap(source: Path, target: Path) -> None:
            if (
                source.parent.name.startswith(".sync-xcode-skills-stage-")
                and source.name == "xcode-skill-beta"
            ):
                raise OSError("injected staged swap failure")
            original_move(source, target)

        with mock.patch.object(
            sync_xcode_skills,
            "move_path",
            side_effect=fail_during_second_staged_swap,
        ):
            with self.assertRaisesRegex(sync_xcode_skills.SyncError, "injected staged swap failure"):
                self.synchronize()

        self.assertEqual((alpha / "sentinel.txt").read_text(encoding="utf-8"), "old alpha")
        self.assertEqual((beta / "sentinel.txt").read_text(encoding="utf-8"), "old beta")
        self.assertFalse((self.skills_root / "xcode-skill-aardvark").exists())
        self.assertFalse(self.state_root.exists())
        self.assert_no_transaction_directories()

    def test_catalog_pair_failure_restores_skills_and_both_catalogs(self) -> None:
        self.write_exported_skill("alpha", skill_name="alpha")
        alpha = self.write_managed_skill("alpha", sentinel="old alpha")
        stale = self.write_managed_skill("stale", sentinel="old stale")
        self.state_root.mkdir()
        old_json = '{"old": true}\n'
        old_markdown = "# Old Catalog\n"
        (self.state_root / "catalog.json").write_text(old_json, encoding="utf-8")
        (self.state_root / "catalog.md").write_text(old_markdown, encoding="utf-8")
        original_replace = sync_xcode_skills.os.replace

        def fail_second_catalog_replace(source: Path, target: Path) -> None:
            source_path = Path(source)
            if source_path.parent.name == "new" and source_path.name == "catalog.md":
                raise OSError("injected catalog pair failure")
            original_replace(source, target)

        with mock.patch.object(
            sync_xcode_skills.os,
            "replace",
            side_effect=fail_second_catalog_replace,
        ):
            with self.assertRaisesRegex(sync_xcode_skills.SyncError, "catalog pair failure"):
                self.synchronize()

        self.assertEqual((alpha / "sentinel.txt").read_text(encoding="utf-8"), "old alpha")
        self.assertEqual((stale / "sentinel.txt").read_text(encoding="utf-8"), "old stale")
        self.assertEqual((self.state_root / "catalog.json").read_text(encoding="utf-8"), old_json)
        self.assertEqual(
            (self.state_root / "catalog.md").read_text(encoding="utf-8"),
            old_markdown,
        )
        self.assert_no_transaction_directories()

    def test_successful_transaction_prunes_stale_skill_and_writes_consistent_catalogs(self) -> None:
        self.write_exported_skill("alpha", skill_name="alpha")
        self.write_exported_skill("beta", skill_name="beta")
        alpha = self.write_managed_skill("alpha", sentinel="old alpha")
        stale = self.write_managed_skill("stale", sentinel="old stale")

        installed, skipped, pruned = self.synchronize()

        installed_names = [item["installed_name"] for item in installed]
        self.assertEqual(installed_names, ["xcode-skill-alpha", "xcode-skill-beta"])
        self.assertEqual(skipped, [])
        self.assertEqual(pruned, ["xcode-skill-stale"])
        self.assertFalse((alpha / "sentinel.txt").exists())
        self.assertFalse(stale.exists())
        markers = [
            json.loads(
                (self.skills_root / name / sync_xcode_skills.MARKER_FILE).read_text(
                    encoding="utf-8"
                )
            )
            for name in installed_names
        ]
        catalog = json.loads((self.state_root / "catalog.json").read_text(encoding="utf-8"))
        catalog_markdown = (self.state_root / "catalog.md").read_text(encoding="utf-8")
        self.assertEqual(
            [marker["xcode_version"] for marker in markers],
            [self.xcode_version, self.xcode_version],
        )
        self.assertEqual(catalog["xcode_version"], self.xcode_version)
        self.assertEqual(
            [skill["installed_name"] for skill in catalog["skills"]],
            installed_names,
        )
        self.assertIn(f"Generated at: `{catalog['generated_at']}`", catalog_markdown)
        self.assertIn("Xcode version: `Xcode Test Build version TEST123`", catalog_markdown)
        self.assertIn("`xcode-skill-alpha`", catalog_markdown)
        self.assertIn("`xcode-skill-beta`", catalog_markdown)
        self.assertIn("`xcode-skill-stale`", catalog_markdown)
        self.assert_no_transaction_directories()


if __name__ == "__main__":
    unittest.main()
