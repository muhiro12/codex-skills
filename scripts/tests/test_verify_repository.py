#!/usr/bin/env python3

import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "verify_repository.py"
SPEC = importlib.util.spec_from_file_location("verify_repository", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class VerifyRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        subprocess.run(
            ["git", "init", "-q", str(self.root)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.write(
            "AGENTS.md",
            "Run `bash scripts/verify_repository.sh` before completion.\n",
        )
        self.write("scripts/verify_repository.sh", "#!/usr/bin/env bash\n")
        self.write(
            "README.md",
            "# Skills\n\n## Included Skills\n\n"
            "- `example-skill`: Example.\n\n## Layout\n",
        )
        self.write(
            "example-skill/SKILL.md",
            "---\nname: example-skill\n"
            "description: |\n  A block scalar description.\n---\n\n# Example\n",
        )
        self.write(
            "example-skill/agents/openai.yaml",
            'interface:\n  display_name: "Example"\n'
            '  short_description: "Example skill"\n'
            '  default_prompt: "Use $example-skill for this task."\n',
        )
        self.stage_all()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def write(self, relative_path, contents):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")

    def stage_all(self):
        subprocess.run(
            ["git", "-C", str(self.root), "add", "-A"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_accepts_valid_metadata_and_block_scalar_description(self):
        self.assertEqual(VERIFY.verify_repository(self.root), [])

    def test_reports_readme_inventory_drift(self):
        self.write(
            "README.md",
            "# Skills\n\n## Included Skills\n\n## Layout\n",
        )
        self.stage_all()

        issues = VERIFY.verify_repository(self.root)

        self.assertIn(
            "README Included Skills is missing: example-skill",
            issues,
        )

    def test_ignores_untracked_runtime_skill(self):
        self.write(".gitignore", "/runtime-skill/\n")
        self.write(
            "runtime-skill/SKILL.md",
            "---\nname: runtime-skill\ndescription: Runtime.\n---\n",
        )
        self.stage_all()

        self.assertEqual(VERIFY.verify_repository(self.root), [])

    def test_reports_prompt_that_invokes_another_skill(self):
        self.write(
            "example-skill/agents/openai.yaml",
            'interface:\n  display_name: "Example"\n'
            '  short_description: "Example skill"\n'
            '  default_prompt: "Use $other-skill for this task."\n',
        )
        self.stage_all()

        issues = VERIFY.verify_repository(self.root)

        self.assertIn(
            "example-skill: default_prompt does not invoke $example-skill",
            issues,
        )

    def test_accepts_block_scalar_default_prompt(self):
        self.write(
            "example-skill/agents/openai.yaml",
            'interface:\n  display_name: "Example"\n'
            '  short_description: "Example skill"\n'
            "  default_prompt: |\n"
            "    Use $example-skill for this task.\n",
        )
        self.stage_all()

        self.assertEqual(VERIFY.verify_repository(self.root), [])

    def test_reports_volatile_xcode_tool_label_in_skill_contract(self):
        self.write(
            "example-skill/SKILL.md",
            "---\nname: example-skill\n"
            "description: Example.\n---\n\n"
            "Call `BuildProject` for verification.\n",
        )
        self.stage_all()

        issues = VERIFY.verify_repository(self.root)

        self.assertIn(
            "example-skill: SKILL.md hardcodes volatile Xcode tool labels: "
            "BuildProject",
            issues,
        )

    def test_accepts_capability_based_xcode_contract(self):
        self.write(
            "example-skill/SKILL.md",
            "---\nname: example-skill\n"
            "description: Example.\n---\n\n"
            "Resolve the active Xcode-native build capability at runtime.\n",
        )
        self.stage_all()

        self.assertEqual(VERIFY.verify_repository(self.root), [])

    def test_shell_entrypoint_runs_tracked_tests_without_scanning_ignored_data(self):
        shell_source = MODULE_PATH.with_suffix(".sh")
        shutil.copy2(MODULE_PATH, self.root / "scripts/verify_repository.py")
        shutil.copy2(shell_source, self.root / "scripts/verify_repository.sh")
        marker = self.root / "test-ran"
        shell_marker = self.root / "shell-test-ran"
        self.write(
            "example-skill/tests/test_tracked.py",
            "from pathlib import Path\n"
            f"Path({str(marker)!r}).write_text('yes', encoding='utf-8')\n",
        )
        self.write(
            "example-skill/tests/test_tracked.sh",
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            f"printf yes > {str(shell_marker)!r}\n",
        )
        self.write(
            ".gitignore",
            "/ignored-runtime/\n",
        )
        self.write(
            "ignored-runtime/test_invalid.py",
            "this is deliberately invalid Python !!!\n",
        )
        self.stage_all()

        completed = subprocess.run(
            ["bash", "scripts/verify_repository.sh"],
            cwd=self.root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(marker.read_text(encoding="utf-8"), "yes")
        self.assertEqual(shell_marker.read_text(encoding="utf-8"), "yes")


if __name__ == "__main__":
    unittest.main()
