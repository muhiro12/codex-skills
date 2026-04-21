import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "audit_skills_batch.py"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


class AuditSkillsBatchCLITests(unittest.TestCase):
    maxDiff = None

    def _materialize_fixture_skill_files(self, destination: Path) -> None:
        for fixture_path in destination.rglob("SKILL.fixture.md"):
            shutil.copyfile(fixture_path, fixture_path.with_name("SKILL.md"))

        for fixture_path in destination.rglob("openai.fixture.yaml"):
            shutil.copyfile(fixture_path, fixture_path.with_name("openai.yaml"))

    def _copy_fixture(self, destination_root: Path, category: str, name: str) -> Path:
        source_root = FIXTURES_DIR / category / name
        destination = destination_root / category
        shutil.copytree(source_root, destination)
        if category == "skills":
            self._materialize_fixture_skill_files(destination)
        return destination

    def _run_cli(self, repo_fixture: str, skills_fixture: str, *extra_args: str) -> str:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temp_root = Path(temporary_directory)
            repo_root = self._copy_fixture(temp_root, "repos", repo_fixture)
            skills_root = self._copy_fixture(temp_root, "skills", skills_fixture)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--repo-root",
                    str(repo_root),
                    "--skills-root",
                    str(skills_root),
                    "--scope",
                    "custom",
                    *extra_args,
                ],
                capture_output=True,
                check=True,
                text=True,
            )

            return completed.stdout

    def _run_json(self, repo_fixture: str, skills_fixture: str, *extra_args: str) -> dict[str, object]:
        return json.loads(self._run_cli(repo_fixture, skills_fixture, "--format", "json", *extra_args))

    def _find_report_item(self, payload: dict[str, object], skill_name: str) -> dict[str, object]:
        for item in payload["drift_report"]:
            if item["name"] == skill_name:
                return item
        self.fail(f"Skill report not found: {skill_name}")

    def test_markdown_output_uses_japanese_sections_and_recommendation_cap(self) -> None:
        output = self._run_cli("with_ci", "mixed", "--format", "markdown")

        self.assertIn("1) 監査結果（優先順）", output)
        self.assertIn("2) 更新バンドル（一括提案）", output)
        self.assertIn("3) 任意: 単発の推奨事項", output)
        self.assertIn("- 実装モード: report-only", output)
        self.assertIn("--- SKILL: internal-fixture-ci-drift-skill ---", output)
        self.assertIn("Description: Internal fixture for CI drift checks in skills-batch-auditor.", output)
        self.assertIn("Instructions:", output)

        recommendation_block = output.split("3) 任意: 単発の推奨事項", 1)[1].strip().splitlines()
        recommendation_lines = [line for line in recommendation_block if line.startswith("- ")]
        self.assertEqual(len(recommendation_lines), 3)

    def test_ci_alignment_checks_are_skipped_without_ground_truth(self) -> None:
        payload = self._run_json("without_ci", "mixed")

        ground_truth = payload["ground_truth"]
        self.assertEqual(ground_truth["canonical_entrypoint"], "")
        self.assertFalse(ground_truth["ci_ground_truth_available"])

        ci_drift_item = self._find_report_item(payload, "internal-fixture-ci-drift-skill")
        self.assertEqual(ci_drift_item["status"], "aligned")
        self.assertNotIn("ci_entrypoint_not_aligned", ci_drift_item["issue_codes"])
        self.assertNotIn("ci_policy_not_dynamic", ci_drift_item["issue_codes"])

    def test_include_self_opt_in_controls_self_audit(self) -> None:
        default_payload = self._run_json("without_ci", "mixed")
        default_names = {item["name"] for item in default_payload["drift_report"]}
        self.assertNotIn("internal-fixture-self-audit-skills-batch-auditor", default_names)
        self.assertNotIn("internal-fixture-nested-fixture-skill", default_names)

        with_self_payload = self._run_json("without_ci", "mixed", "--include-self")
        with_self_names = {item["name"] for item in with_self_payload["drift_report"]}
        self.assertIn("internal-fixture-self-audit-skills-batch-auditor", with_self_names)

    def test_openai_interface_parser_supports_quote_variants(self) -> None:
        payload = self._run_json("without_ci", "quote_variants")

        for skill_name in [
            "internal-fixture-double-quoted-skill",
            "internal-fixture-single-quoted-skill",
            "internal-fixture-bare-scalar-skill",
        ]:
            item = self._find_report_item(payload, skill_name)
            self.assertEqual(item["status"], "aligned")
            self.assertEqual(item["issue_codes"], [])

    def test_internal_visibility_allows_missing_openai_yaml(self) -> None:
        payload = self._run_json("without_ci", "mixed")

        item = self._find_report_item(payload, "internal-fixture-visibility-skill")
        self.assertEqual(item["status"], "aligned")
        self.assertEqual(item["visibility"], "internal")
        self.assertNotIn("missing_openai_yaml", item["issue_codes"])

    def test_prioritization_output_includes_scores_classification_and_actions(self) -> None:
        payload = self._run_json("without_ci", "prioritization")

        core_item = self._find_report_item(payload, "internal-fixture-core-keeper-skill")
        self.assertEqual(core_item["portfolio_classification"], "core")
        self.assertEqual(core_item["recommended_action"], "keep as-is")
        self.assertEqual(
            set(core_item["scores"]),
            {
                "reuse value",
                "clarity of invocation",
                "safety",
                "maintenance burden",
            },
        )

        improve_item = self._find_report_item(payload, "internal-fixture-improve-next-skill")
        self.assertEqual(improve_item["portfolio_classification"], "useful")
        self.assertEqual(improve_item["recommended_action"], "improve next")
        self.assertIn("default_prompt_missing_skill_reference", improve_item["issue_codes"])

        merge_item = self._find_report_item(payload, "internal-fixture-overview-refresh-skill")
        self.assertEqual(merge_item["portfolio_classification"], "optional")
        self.assertEqual(merge_item["recommended_action"], "merge with another skill")
        self.assertEqual(merge_item["merge_target"], "internal-fixture-overview-sync-skill")

        specialized_item = self._find_report_item(payload, "internal-fixture-specialized-keeper-skill")
        self.assertEqual(specialized_item["portfolio_classification"], "useful")
        self.assertEqual(specialized_item["recommended_action"], "keep as-is")
        self.assertEqual(specialized_item["scores"]["maintenance burden"], 3)

        retire_item = self._find_report_item(payload, "internal-fixture-retire-candidate-skill")
        self.assertEqual(retire_item["portfolio_classification"], "retire candidate")
        self.assertEqual(retire_item["recommended_action"], "retire")
        self.assertIn("recursive_generated_scan", retire_item["issue_codes"])

        batch_decisions = payload["batch_decisions"]
        self.assertEqual(
            [entry["name"] for entry in batch_decisions["keep as-is"]],
            [
                "internal-fixture-specialized-keeper-skill",
                "internal-fixture-core-keeper-skill",
                "internal-fixture-overview-sync-skill",
            ],
        )
        self.assertEqual(
            [entry["name"] for entry in batch_decisions["improve next"]],
            ["internal-fixture-improve-next-skill"],
        )
        self.assertEqual(
            [
                (entry["name"], entry["merge_target"])
                for entry in batch_decisions["merge with another skill"]
            ],
            [
                (
                    "internal-fixture-overview-refresh-skill",
                    "internal-fixture-overview-sync-skill",
                )
            ],
        )
        self.assertEqual(
            [entry["name"] for entry in batch_decisions["retire"]],
            ["internal-fixture-retire-candidate-skill"],
        )

    def test_markdown_output_lists_batch_decision_buckets_in_japanese_report(self) -> None:
        output = self._run_cli("without_ci", "prioritization", "--format", "markdown")

        self.assertIn(
            "- keep as-is: internal-fixture-specialized-keeper-skill, internal-fixture-core-keeper-skill, internal-fixture-overview-sync-skill",
            output,
        )
        self.assertIn("- improve next: internal-fixture-improve-next-skill", output)
        self.assertIn(
            "- merge with another skill: internal-fixture-overview-refresh-skill -> internal-fixture-overview-sync-skill",
            output,
        )
        self.assertIn("- retire: internal-fixture-retire-candidate-skill", output)
        self.assertIn("  - 評価軸スコア:", output)
        self.assertIn("  - 分類: core", output)
        self.assertIn("  - 推奨アクション: improve next", output)

    def test_low_risk_mode_separates_eligible_and_manual_review_items(self) -> None:
        payload = self._run_json("with_ci", "mixed", "--implementation-mode", "low-risk")

        implementation = payload["implementation"]
        self.assertEqual(implementation["mode"], "low-risk")
        self.assertIn("internal-fixture-ci-drift-skill", implementation["eligible_skills"])
        self.assertIn("internal-fixture-manual-review-skill", implementation["manual_review_skills"])

        ci_drift_item = self._find_report_item(payload, "internal-fixture-ci-drift-skill")
        self.assertIn("ci_entrypoint_not_aligned", ci_drift_item["low_risk_issue_codes"])
        self.assertIn("ci_policy_not_dynamic", ci_drift_item["low_risk_issue_codes"])
        self.assertEqual(ci_drift_item["manual_review_issue_codes"], [])

        manual_review_item = self._find_report_item(payload, "internal-fixture-manual-review-skill")
        self.assertEqual(manual_review_item["low_risk_issue_codes"], [])
        self.assertIn("missing_openai_yaml", manual_review_item["manual_review_issue_codes"])

        bundle_names = {entry["name"] for entry in payload["batch_update_bundle"]["entries"]}
        self.assertIn("internal-fixture-ci-drift-skill", bundle_names)
        self.assertNotIn("internal-fixture-manual-review-skill", bundle_names)

    def test_distinct_roles_fixture_blocks_false_positive_merge_targets(self) -> None:
        payload = self._run_json("without_ci", "distinct_roles")

        kept_skill_names = [
            "internal-fixture-release-risk-skill",
            "internal-fixture-app-store-release-notes-skill",
            "internal-fixture-footprint-diagnosis-skill",
            "internal-fixture-skills-portfolio-auditor-skill",
            "internal-fixture-swiftdata-schema-skill",
            "internal-fixture-ci-push-readiness-skill",
            "internal-fixture-repo-momentum-skill",
            "internal-fixture-repo-specific-dev-skill",
        ]

        for skill_name in kept_skill_names:
            item = self._find_report_item(payload, skill_name)
            self.assertEqual(item["status"], "aligned")
            self.assertEqual(item["recommended_action"], "keep as-is")
            self.assertEqual(item["merge_target"], "")

        self.assertEqual(
            [entry["name"] for entry in payload["batch_decisions"]["merge with another skill"]],
            [],
        )

    def test_verify_bootstrap_and_contract_maintenance_stay_separate(self) -> None:
        payload = self._run_json("without_ci", "distinct_verify_roles")

        for skill_name in [
            "internal-fixture-apple-verify-bootstrap-skill",
            "internal-fixture-verify-contract-maintenance-skill",
        ]:
            item = self._find_report_item(payload, skill_name)
            self.assertEqual(item["status"], "aligned")
            self.assertEqual(item["recommended_action"], "keep as-is")
            self.assertEqual(item["merge_target"], "")

        self.assertEqual(
            [entry["name"] for entry in payload["batch_decisions"]["merge with another skill"]],
            [],
        )


if __name__ == "__main__":
    unittest.main()
