import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_verify_and_summarize.sh"


class RunVerifyAndSummarizeTests(unittest.TestCase):
    maxDiff = None

    def _write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")

    def _write_executable(self, path: Path, content: str) -> None:
        self._write_text(path, content)
        path.chmod(0o755)

    def _git(self, repo_root: Path, *args: str) -> str:
        completed = subprocess.run(
            ["git", *args],
            capture_output=True,
            check=True,
            cwd=repo_root,
            text=True,
        )
        return completed.stdout

    def _init_git_repo(self, repo_root: Path) -> None:
        self._git(repo_root, "init")
        self._git(repo_root, "config", "user.email", "skill-test@example.com")
        self._git(repo_root, "config", "user.name", "Skill Test")

    def _write_success_verify_script(
        self,
        repo_root: Path,
        *,
        extra_output: str = "",
        status: str = "success",
        success: str = "true",
    ) -> None:
        self._write_executable(
            repo_root / "ci_scripts" / "tasks" / "verify.sh",
            f"""
            #!/usr/bin/env bash
            set -euo pipefail
            run_dir=".build/ci/runs/20260310-010203-0000"
            mkdir -p "$run_dir"
            cat <<'EOF' > "$run_dir/summary.md"
            # AI Run Summary
            - Verify completed
            - Lint completed
            - Tests completed
            EOF
            cat <<'EOF' > "$run_dir/meta.json"
            {{"result":"{status}","success":{success}}}
            EOF
            {extra_output}
            """,
        )

    def _commit_all(self, repo_root: Path, message: str) -> None:
        self._git(repo_root, "add", ".")
        self._git(repo_root, "commit", "-m", message)

    def _run_helper(self, repo_root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(SCRIPT_PATH)],
            capture_output=True,
            cwd=repo_root,
            text=True,
        )

    def test_reports_not_applicable_when_no_verify_entrypoint_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._write_text(repo_root / "README.md", "fixture")

            completed = self._run_helper(repo_root)

        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
        self.assertIn("結果: ❌ failure", completed.stdout)
        self.assertIn("Pushリスク: high", completed.stdout)
        self.assertIn("最終ゲートを開始できません", completed.stdout)

    def test_low_risk_success_reviews_staged_diff(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._init_git_repo(repo_root)
            self._write_success_verify_script(repo_root)
            self._write_text(repo_root / "docs" / "overview.md", "before\n")
            self._commit_all(repo_root, "Initial")

            self._write_text(repo_root / "docs" / "overview.md", "after\n")
            self._git(repo_root, "add", "docs/overview.md")

            completed = self._run_helper(repo_root)

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("結果: ✅ success", completed.stdout)
        self.assertIn("Pushリスク: low", completed.stdout)
        self.assertIn("stage済み 1件 / 未stage 0件", completed.stdout)
        self.assertIn("重大カテゴリ差分や warning は見当たりませんでした。", completed.stdout)

    def test_low_risk_success_on_clean_worktree_still_reports_useful_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._init_git_repo(repo_root)
            self._write_success_verify_script(repo_root)
            self._write_text(repo_root / "README.md", "base\n")
            self._commit_all(repo_root, "Initial")

            completed = self._run_helper(repo_root)

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("結果: ✅ success", completed.stdout)
        self.assertIn("Pushリスク: low", completed.stdout)
        self.assertIn("stage済み 0件 / 未stage 0件を確認しました。作業ツリーに差分はありません。", completed.stdout)
        self.assertIn("差分はないため、この verify 結果を基準に次の変更へ進めます。", completed.stdout)

    def test_high_risk_when_current_change_warning_is_present(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._init_git_repo(repo_root)
            self._write_success_verify_script(
                repo_root,
                extra_output='echo "Sources/Feature.swift:10: warning: deprecated API is still used"\n',
            )
            self._write_text(repo_root / "Sources" / "Feature.swift", "let value = 1\n")
            self._commit_all(repo_root, "Initial")

            self._write_text(repo_root / "Sources" / "Feature.swift", "let value = 2\n")
            self._git(repo_root, "add", "Sources/Feature.swift")

            completed = self._run_helper(repo_root)

        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
        self.assertIn("Pushリスク: high", completed.stdout)
        self.assertIn("warning", completed.stdout)
        self.assertIn("warning を解消してから再度 verify を通してください。", completed.stdout)

    def test_medium_risk_when_preexisting_repo_warning_is_present(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._init_git_repo(repo_root)
            self._write_success_verify_script(
                repo_root,
                extra_output='echo "Sources/Legacy.swift:10: warning: deprecated API is still used"\n',
            )
            self._write_text(repo_root / "Sources" / "Legacy.swift", "let legacy = 1\n")
            self._write_text(repo_root / "Sources" / "Feature.swift", "let value = 1\n")
            self._commit_all(repo_root, "Initial")

            self._write_text(repo_root / "Sources" / "Feature.swift", "let value = 2\n")
            self._git(repo_root, "add", "Sources/Feature.swift")

            completed = self._run_helper(repo_root)

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("Pushリスク: medium", completed.stdout)
        self.assertIn("既存の未解消 warning の可能性が高い項目", completed.stdout)
        self.assertIn("current change ではないことを確認", completed.stdout)

    def test_medium_risk_when_external_package_warning_is_present(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._init_git_repo(repo_root)
            self._write_success_verify_script(
                repo_root,
                extra_output='echo "SourcePackages/checkouts/SomePkg/Sources/Lib.swift:10: warning: deprecated API is still used"\n',
            )
            self._write_text(repo_root / "Sources" / "Feature.swift", "let value = 1\n")
            self._commit_all(repo_root, "Initial")

            self._write_text(repo_root / "Sources" / "Feature.swift", "let value = 2\n")
            self._git(repo_root, "add", "Sources/Feature.swift")

            completed = self._run_helper(repo_root)

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("Pushリスク: medium", completed.stdout)
        self.assertIn("外部依存または既存要因の可能性が高い warning", completed.stdout)
        self.assertIn("current change ではないことを確認", completed.stdout)

    def test_high_risk_blocks_push_when_no_verify_flag_is_in_diff(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._init_git_repo(repo_root)
            self._write_success_verify_script(repo_root)
            self._write_text(
                repo_root / "scripts" / "release.sh",
                """
                #!/usr/bin/env bash
                git push origin main
                """,
            )
            self._commit_all(repo_root, "Initial")

            self._write_text(
                repo_root / "scripts" / "release.sh",
                """
                #!/usr/bin/env bash
                git push --no-verify origin main
                """,
            )
            self._git(repo_root, "add", "scripts/release.sh")

            completed = self._run_helper(repo_root)

        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
        self.assertIn("結果: ✅ success", completed.stdout)
        self.assertIn("Pushリスク: high", completed.stdout)
        self.assertIn("push 非推奨", completed.stdout)
        self.assertIn("`--no-verify`", completed.stdout)

    def test_verify_failure_keeps_branch_non_push_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._init_git_repo(repo_root)
            self._write_executable(
                repo_root / "ci_scripts" / "tasks" / "verify.sh",
                """
                #!/usr/bin/env bash
                set -euo pipefail
                run_dir=".build/ci/runs/20260310-010203-0000"
                mkdir -p "$run_dir"
                cat <<'EOF' > "$run_dir/summary.md"
                # AI Run Summary
                - Build failed
                - Tests did not complete
                EOF
                cat <<'EOF' > "$run_dir/meta.json"
                {"result":"failure","success":false,"failed_step":"tests","failed_log":"failed.log"}
                EOF
                cat <<'EOF' > "$run_dir/failed.log"
                error: test failure
                EOF
                cat <<'EOF' > "$run_dir/commands.txt"
                swift test
                EOF
                exit 1
                """,
            )
            self._write_text(repo_root / "README.md", "base\n")
            self._commit_all(repo_root, "Initial")

            completed = self._run_helper(repo_root)

        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
        self.assertIn("結果: ❌ failure", completed.stdout)
        self.assertIn("Pushリスク: high", completed.stdout)
        self.assertIn("verify が失敗しています", completed.stdout)
        self.assertIn("push 非推奨", completed.stdout)


if __name__ == "__main__":
    unittest.main()
